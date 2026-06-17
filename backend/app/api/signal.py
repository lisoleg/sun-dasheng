"""信号API端点 - 连接真实信号服务"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from loguru import logger
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.signal import Signal
from app.services.signal.generator import SignalGenerator
from app.services.tomas.token_bridge import TomasBridge

router = APIRouter()

# 延迟初始化的信号生成器
_signal_generator: Optional[SignalGenerator] = None


async def _get_signal_generator() -> SignalGenerator:
    """获取或创建信号生成器（单例）"""
    global _signal_generator
    if _signal_generator is None:
        from app.services.tomas.translator import Translator
        from app.services.tomas.writer import Writer
        from app.services.theory.taiji import TaijiEngine
        from app.services.theory.spiral import SpiralEngine
        from app.services.theory.elliott_wave import ElliottWaveEngine

        translator = Translator()
        writer = Writer()
        tomas_bridge = TomasBridge(translator=translator, writer=writer)

        theory_engines = [
            TaijiEngine(),
            SpiralEngine(),
            ElliottWaveEngine(),
        ]

        _signal_generator = SignalGenerator(
            theory_engines=theory_engines,
            tomas_bridge=tomas_bridge,
        )
        logger.info("SignalGenerator initialized")

    return _signal_generator


@router.get("")
async def get_signals(
    symbol: Optional[str] = Query(None, description="筛选标的代码"),
    direction: Optional[str] = Query(None, description="筛选方向：LONG/SHORT/HOLD"),
    source_engine: Optional[str] = Query(None, description="筛选来源引擎"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="最小置信度"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
) -> Dict[str, Any]:
    """获取信号列表（分页，从数据库查询真实信号）"""
    try:
        async with async_session() as session:
            # 构建查询
            stmt = select(Signal).order_by(desc(Signal.timestamp))

            # 过滤条件
            if symbol:
                stmt = stmt.where(Signal.symbol == symbol)
            if direction:
                stmt = stmt.where(Signal.direction == direction)
            if source_engine:
                stmt = stmt.where(Signal.source_engine == source_engine)
            if min_confidence > 0.0:
                stmt = stmt.where(Signal.confidence >= min_confidence)

            # 统计总数
            total_stmt = select(Signal.id)
            if symbol:
                total_stmt = total_stmt.where(Signal.symbol == symbol)
            if direction:
                total_stmt = total_stmt.where(Signal.direction == direction)
            if source_engine:
                total_stmt = total_stmt.where(Signal.source_engine == source_engine)
            if min_confidence > 0.0:
                total_stmt = total_stmt.where(Signal.confidence >= min_confidence)

            total_result = await session.execute(total_stmt)
            total = len(total_result.scalars().all())

            # 分页
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            result = await session.execute(stmt)
            signals = result.scalars().all()

            items = [
                {
                    "signal_id": s.signal_id,
                    "symbol": s.symbol,
                    "market": s.market,
                    "direction": s.direction,
                    "price": round(float(s.price), 4),
                    "confidence": round(float(s.confidence), 4),
                    "source_engine": s.source_engine,
                    "theory_name": s.theory_name,
                    "timestamp": s.timestamp.isoformat(),
                    "created_at": s.created_at.isoformat(),
                    "metadata": s.metadata or {},
                }
                for s in signals
            ]

            logger.info(f"API /signals: returned {len(items)}/{total} signals")
            return {
                "code": 0,
                "data": {
                    "total": total,
                    "items": items,
                },
                "message": "ok",
            }

    except Exception as e:
        logger.error(f"API /signals error: {e}")
        return {
            "code": 3001,
            "data": {"total": 0, "items": []},
            "message": f"信号查询失败: {str(e)}",
        }


@router.get("/latest")
async def get_latest_signals(
    limit: int = Query(10, ge=1, le=50, description="返回条数"),
) -> Dict[str, Any]:
    """获取最新信号（从数据库查询）"""
    try:
        async with async_session() as session:
            stmt = (
                select(Signal)
                .order_by(desc(Signal.timestamp))
                .limit(limit)
            )
            result = await session.execute(stmt)
            signals = result.scalars().all()

            items = [
                {
                    "signal_id": s.signal_id,
                    "symbol": s.symbol,
                    "market": s.market,
                    "direction": s.direction,
                    "price": round(float(s.price), 4),
                    "confidence": round(float(s.confidence), 4),
                    "source_engine": s.source_engine,
                    "theory_name": s.theory_name,
                    "timestamp": s.timestamp.isoformat(),
                    "created_at": s.created_at.isoformat(),
                }
                for s in signals
            ]

            return {
                "code": 0,
                "data": {
                    "total": len(items),
                    "items": items,
                },
                "message": "ok",
            }

    except Exception as e:
        logger.error(f"API /signals/latest error: {e}")
        # 如果数据库无数据，返回空列表（不报错）
        return {
            "code": 0,
            "data": {"total": 0, "items": []},
            "message": "ok",
        }


@router.post("/generate")
async def generate_signals(
    symbol: str = Query(..., description="标的代码"),
    timeframe: str = Query("1d", description="时间周期"),
    limit: int = Query(200, ge=50, le=1000, description="K线条数"),
) -> Dict[str, Any]:
    """手动触发信号计算（调用SignalGenerator）"""
    try:
        # 获取市场数据
        from app.services.market_data.binance_provider import BinanceProvider
        from app.services.market_data.tdx_provider import TdxProvider

        if symbol.endswith("USDT") or symbol.endswith("BUSD"):
            provider = BinanceProvider()
            await provider.connect()
            bars_data = await provider.get_bars(symbol, timeframe, limit)
            await provider.disconnect()
        else:
            provider = TdxProvider()
            await provider.connect()
            bars_data = await provider.get_bars(symbol, timeframe, limit)
            await provider.disconnect()

        # 转换为字典格式
        bars = [
            {
                "timestamp": b.timestamp.isoformat() if hasattr(b.timestamp, "isoformat") else str(b.timestamp),
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": float(b.volume) if hasattr(b, "volume") else 0.0,
            }
            for b in bars_data
        ]

        # 生成信号
        generator = await _get_signal_generator()
        signals = await generator.generate(bars)

        # 保存到数据库
        saved_count = 0
        async with async_session() as session:
            for sig in signals:
                signal_model = Signal(
                    signal_id=sig.get("signal_id", f"sig-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    symbol=symbol,
                    market="crypto" if "USDT" in symbol else "a_share",
                    direction=sig.get("direction", "HOLD"),
                    price=sig.get("price", 0.0),
                    confidence=sig.get("confidence", 0.0),
                    source_engine=sig.get("source_engine", "unknown"),
                    theory_name=sig.get("theory_name", ""),
                    timestamp=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    metadata=sig.get("metadata", {}),
                )
                session.add(signal_model)
                saved_count += 1

            await session.commit()

        logger.info(f"API /signals/generate: generated {saved_count} signals for {symbol}")

        # 通过WebSocket推送
        from app.main import ws_hub
        await ws_hub.broadcast("signals", {
            "type": "signals_generated",
            "payload": {
                "symbol": symbol,
                "count": saved_count,
                "signals": signals[:5],  # 只推送前5条
            },
        })

        return {
            "code": 0,
            "data": {
                "symbol": symbol,
                "generated": saved_count,
                "signals": signals,
            },
            "message": f"成功生成 {saved_count} 条信号",
        }

    except Exception as e:
        logger.error(f"API /signals/generate error: {e}")
        return {
            "code": 3001,
            "data": {"generated": 0, "signals": []},
            "message": f"信号生成失败: {str(e)}",
        }
