"""订单API端点 - 连接真实订单服务"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from loguru import logger
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.order import Order
from app.schemas.order import OrderCreate
from app.services.execution.binance_trader import BinanceTrader, OrderResult
from app.services.execution.order_manager import OrderManager, RiskCheckResult

router = APIRouter()

# 延迟初始化的订单管理器实例
_order_manager: Optional[OrderManager] = None


async def _get_order_manager() -> Optional[OrderManager]:
    """获取或创建订单管理器（单例）"""
    global _order_manager
    if _order_manager is None:
        # 只有在配置了币安API Key时才创建真实订单管理器
        if settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET:
            trader = BinanceTrader(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_API_SECRET,
                testnet=settings.BINANCE_TESTNET,
            )
            _order_manager = OrderManager(trader=trader)
            logger.info("OrderManager initialized with real BinanceTrader")
        else:
            logger.warning("BINANCE_API_KEY not configured, OrderManager will not function")
            return None
    return _order_manager


async def _save_order_to_db(order_result: OrderResult, signal_id: Optional[str] = None) -> Order:
    """将订单结果保存到数据库"""
    async with async_session() as session:
        order = Order(
            order_id=order_result.order_id,
            symbol=order_result.symbol,
            market="crypto" if "USDT" in order_result.symbol else "a_share",
            side=order_result.side,
            type=order_result.type,
            price=order_result.price,
            quantity=order_result.quantity,
            status=order_result.status,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata=order_result.raw_response or {},
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


async def _order_result_to_dict(order_result: OrderResult) -> Dict[str, Any]:
    """将OrderResult转换为API响应格式"""
    return {
        "order_id": order_result.order_id,
        "symbol": order_result.symbol,
        "side": order_result.side,
        "type": order_result.type,
        "price": round(order_result.price, 8),
        "quantity": round(order_result.quantity, 8),
        "status": order_result.status,
        "filled_price": round(order_result.filled_price, 8),
        "filled_quantity": round(order_result.filled_quantity, 8),
        "commission": round(order_result.commission, 8),
        "created_at": order_result.timestamp,
        "updated_at": order_result.timestamp,
        "error": order_result.error,
    }


@router.post("")
async def create_order(order: OrderCreate) -> Dict[str, Any]:
    """创建订单（手动下单）"""
    try:
        # 如果配置了币安API，使用真实订单管理器
        order_manager = await _get_order_manager()

        if order_manager:
            # 创建模拟Signal对象（用于OrderManager.execute_signal）
            from dataclasses import dataclass

            @dataclass
            class MockSignal:
                symbol: str
                direction: str  # LONG/SHORT
                price: float
                confidence: float = 0.5
                source_engine: str = "manual"
                theory_name: str = "Manual Order"

            mock_signal = MockSignal(
                symbol=order.symbol,
                direction="BUY" if order.side == "BUY" else "SELL",
                price=order.price or 0.0,
            )

            # 执行信号（下单）
            order_result = await order_manager.execute_signal(mock_signal)

            # 保存到数据库
            db_order = await _save_order_to_db(order_result)

            logger.info(f"API POST /orders: created order {order_result.order_id}, status={order_result.status}")
            return {
                "code": 0 if order_result.status != "REJECTED" else 4001,
                "data": await _order_result_to_dict(order_result),
                "message": "ok" if order_result.status != "REJECTED" else order_result.error or "下单失败",
            }
        else:
            # 未配置币安API，返回模拟订单（用于开发测试）
            logger.warning("API POST /orders: Binance API not configured, returning mock order")
            mock_order_id = f"mock-{uuid.uuid4().hex[:8]}"
            return {
                "code": 0,
                "data": {
                    "order_id": mock_order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "type": order.type,
                    "price": order.price or 0.0,
                    "quantity": order.quantity,
                    "status": "PENDING",
                    "filled_price": 0.0,
                    "filled_quantity": 0.0,
                    "commission": 0.0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "error": None,
                },
                "message": "ok (mock - configure BINANCE_API_KEY to enable real trading)",
            }

    except Exception as e:
        logger.error(f"API POST /orders error: {e}")
        return {
            "code": 4001,
            "data": None,
            "message": f"下单失败: {str(e)}",
        }


@router.get("")
async def get_orders(
    symbol: Optional[str] = Query(None, description="筛选标的代码"),
    status: Optional[str] = Query(None, description="筛选状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
) -> Dict[str, Any]:
    """获取订单列表（从数据库查询）"""
    try:
        async with async_session() as session:
            # 构建查询
            stmt = select(Order).order_by(desc(Order.created_at))

            # 过滤条件
            if symbol:
                stmt = stmt.where(Order.symbol == symbol)
            if status:
                stmt = stmt.where(Order.status == status)

            # 统计总数
            total_result = await session.execute(select(Order.id))
            total = len(total_result.scalars().all())

            if symbol:
                total_result = await session.execute(select(Order.id).where(Order.symbol == symbol))
                total = len(total_result.scalars().all())
            if status:
                total_result = await session.execute(select(Order.id).where(Order.status == status))
                total = len(total_result.scalars().all())

            # 分页
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            result = await session.execute(stmt)
            orders = result.scalars().all()

            items = [
                {
                    "order_id": o.order_id,
                    "symbol": o.symbol,
                    "side": o.side,
                    "type": o.type,
                    "price": round(float(o.price), 8),
                    "quantity": round(float(o.quantity), 8),
                    "status": o.status,
                    "created_at": o.created_at.isoformat(),
                    "updated_at": o.updated_at.isoformat(),
                }
                for o in orders
            ]

            logger.info(f"API GET /orders: returned {len(items)}/{total} orders")
            return {
                "code": 0,
                "data": {
                    "total": total,
                    "items": items,
                },
                "message": "ok",
            }

    except Exception as e:
        logger.error(f"API GET /orders error: {e}")
        return {
            "code": 4001,
            "data": {"total": 0, "items": []},
            "message": f"订单查询失败: {str(e)}",
        }


@router.get("/{order_id}")
async def get_order(order_id: str) -> Dict[str, Any]:
    """获取订单详情（从数据库查询）"""
    try:
        async with async_session() as session:
            stmt = select(Order).where(Order.order_id == order_id)
            result = await session.execute(stmt)
            order = result.scalar_one_or_none()

            if not order:
                return {
                    "code": 404,
                    "data": None,
                    "message": f"订单不存在: {order_id}",
                }

            return {
                "code": 0,
                "data": {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "type": order.type,
                    "price": round(float(order.price), 8),
                    "quantity": round(float(order.quantity), 8),
                    "status": order.status,
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                },
                "message": "ok",
            }

    except Exception as e:
        logger.error(f"API GET /orders/{{order_id}} error: {e}")
        return {
            "code": 4001,
            "data": None,
            "message": f"订单查询失败: {str(e)}",
        }


@router.delete("/{order_id}")
async def cancel_order(order_id: str) -> Dict[str, Any]:
    """取消订单"""
    try:
        # 先从数据库查询订单
        async with async_session() as session:
            stmt = select(Order).where(Order.order_id == order_id)
            result = await session.execute(stmt)
            db_order = result.scalar_one_or_none()

            if not db_order:
                return {
                    "code": 404,
                    "data": None,
                    "message": f"订单不存在: {order_id}",
                }

            # 如果配置了币安API，尝试取消真实订单
            order_manager = await _get_order_manager()
            if order_manager and db_order.status in ["PENDING", "PARTIALLY_FILLED"]:
                order_result = await order_manager.cancel_order(db_order.symbol, order_id)

                # 更新数据库状态
                db_order.status = "CANCELLED"
                db_order.updated_at = datetime.now(timezone.utc)
                await session.commit()

                logger.info(f"API DELETE /orders/{{order_id}}: cancelled order {order_id}")
                return {
                    "code": 0,
                    "data": await _order_result_to_dict(order_result),
                    "message": "订单已取消",
                }
            else:
                # 未配置币安API或订单已成交，仅更新数据库状态
                db_order.status = "CANCELLED"
                db_order.updated_at = datetime.now(timezone.utc)
                await session.commit()

                logger.info(f"API DELETE /orders/{{order_id}}: cancelled mock order {order_id}")
                return {
                    "code": 0,
                    "data": {
                        "order_id": order_id,
                        "status": "CANCELLED",
                    },
                    "message": "订单已取消 (mock)",
                }

    except Exception as e:
        logger.error(f"API DELETE /orders/{{order_id}} error: {e}")
        return {
            "code": 4001,
            "data": None,
            "message": f"取消订单失败: {str(e)}",
        }
