"""订单管理器 - 信号→下单全流程

核心功能：
- execute_signal(signal): 信号→下单全流程（风控检查→下单→设置止损止盈→记录订单）
- cancel_order(order_id): 取消订单
- monitor_open_orders(): 监控未完成订单

与RiskEngine交互进行风控检查。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.execution.binance_trader import BinanceTrader, OrderResult
from app.services.signal.generator import Signal
from app.services.risk.position_sizer import PositionSizer
from app.services.risk.stop_loss import StopLossManager, StopCheckResult


@dataclass
class RiskCheckResult:
    """风控检查结果"""

    approved: bool = False
    position_size: float = 0.0
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "approved": self.approved,
            "position_size": self.position_size,
            "reason": self.reason,
            "details": self.details,
        }


class OrderManager:
    """订单管理器

    负责信号→下单的完整流程：
    1. 接收交易信号
    2. 风控检查（仓位限制、止损设置等）
    3. 执行下单
    4. 设置止损止盈
    5. 记录订单信息
    6. 推送通知

    与RiskEngine交互进行风控检查，
    与BinanceTrader交互执行实际下单。
    """

    def __init__(
        self,
        trader: BinanceTrader,
        stop_loss_manager: Optional[StopLossManager] = None,
        position_sizer: Optional[PositionSizer] = None,
    ) -> None:
        """初始化订单管理器

        Args:
            trader: 币安交易执行器
            stop_loss_manager: 止损止盈管理器
            position_sizer: 仓位管理器
        """
        self.trader = trader
        self.stop_loss_mgr = stop_loss_manager or StopLossManager()
        self.position_sizer = position_sizer or PositionSizer()
        self._open_orders: Dict[str, Dict[str, Any]] = {}
        self._positions: Dict[str, Dict[str, Any]] = {}

    async def execute_signal(self, signal: Signal) -> OrderResult:
        """信号→下单全流程

        流程：风控检查 → 计算仓位 → 下单 → 设置止损止盈 → 记录订单

        Args:
            signal: 交易信号

        Returns:
            OrderResult: 下单结果
        """
        logger.info(
            f"OrderManager: executing signal {signal.signal_id} "
            f"direction={signal.direction} symbol={signal.symbol} "
            f"confidence={signal.confidence:.4f}"
        )

        # HOLD信号不下单
        if signal.direction == "HOLD":
            logger.info(f"OrderManager: signal {signal.signal_id} is HOLD, skipping")
            return OrderResult(
                order_id="",
                symbol=signal.symbol,
                status="CANCELLED",
                error="HOLD signal, no order placed",
            )

        # 步骤1：风控检查
        risk_check = self._check_risk(signal)
        if not risk_check.approved:
            logger.warning(
                f"OrderManager: signal {signal.signal_id} rejected by risk check: "
                f"{risk_check.reason}"
            )
            return OrderResult(
                order_id="",
                symbol=signal.symbol,
                status="REJECTED",
                error=f"Risk check failed: {risk_check.reason}",
            )

        # 步骤2：执行下单
        side = "BUY" if signal.direction == "LONG" else "SELL"
        quantity = risk_check.position_size

        order_result = await self.trader.place_market_order(
            symbol=signal.symbol,
            side=side,
            quantity=quantity,
        )

        # 步骤3：下单成功后设置止损止盈
        if order_result.status == "FILLED":
            await self._setup_stop_loss(signal, order_result, risk_check)
            logger.info(
                f"OrderManager: order filled - "
                f"order_id={order_result.order_id}, "
                f"symbol={signal.symbol}, "
                f"side={side}, "
                f"qty={quantity}"
            )
        else:
            logger.warning(
                f"OrderManager: order not filled - "
                f"order_id={order_result.order_id}, "
                f"status={order_result.status}"
            )

        # 步骤4：记录订单
        self._record_order(signal, order_result, risk_check)

        return order_result

    async def cancel_order(self, order_id: str, symbol: str = "") -> OrderResult:
        """取消订单

        Args:
            order_id: 订单ID
            symbol: 交易对（币安API需要）

        Returns:
            OrderResult: 取消结果
        """
        logger.info(f"OrderManager: cancelling order {order_id}")

        # 查找订单信息
        order_info = self._open_orders.get(order_id)
        if not order_info and not symbol:
            logger.error(f"OrderManager: order {order_id} not found and symbol not provided")
            return OrderResult(
                order_id=order_id,
                status="REJECTED",
                error="Order not found",
            )

        effective_symbol = symbol or order_info.get("symbol", "")

        result = await self.trader.cancel_order(
            symbol=effective_symbol,
            order_id=order_id,
        )

        # 从未完成订单列表移除
        if order_id in self._open_orders and result.status == "CANCELLED":
            del self._open_orders[order_id]

        return result

    async def monitor_open_orders(self) -> List[Dict[str, Any]]:
        """监控未完成订单

        查询所有未完成订单的最新状态。

        Returns:
            List[Dict]: 未完成订单列表及最新状态
        """
        monitored: List[Dict[str, Any]] = []

        for order_id, order_info in list(self._open_orders.items()):
            symbol = order_info.get("symbol", "")
            try:
                result = await self.trader.get_order_status(
                    symbol=symbol, order_id=order_id
                )

                # 更新订单状态
                order_info["status"] = result.status
                order_info["updated_at"] = datetime.now(timezone.utc).isoformat()

                # 如果订单已完成/取消，从未完成列表移除
                if result.status in ("FILLED", "CANCELLED", "REJECTED"):
                    del self._open_orders[order_id]

                monitored.append(order_info)

            except Exception as e:
                logger.error(f"OrderManager: monitor order {order_id} error: {e}")
                monitored.append({
                    **order_info,
                    "monitor_error": str(e),
                })

        logger.info(f"OrderManager: monitoring {len(monitored)} open orders")
        return monitored

    def _check_risk(self, signal: Signal) -> RiskCheckResult:
        """风控检查

        检查信号是否符合风控要求：
        1. 信号置信度是否足够
        2. 仓位是否超过限制
        3. 计算建议仓位大小

        Args:
            signal: 交易信号

        Returns:
            RiskCheckResult: 风控检查结果
        """
        # 检查1：信号置信度
        if signal.confidence < 0.3:
            return RiskCheckResult(
                approved=False,
                reason=f"Signal confidence too low: {signal.confidence:.4f} < 0.3",
            )

        # 检查2：计算仓位大小
        # 假设总资金为10000 USDT（实际应从账户余额获取）
        capital = 10000.0
        entry_price = signal.price if signal.price > 0 else 1.0

        # 止损价格：默认5%
        stop_price = entry_price * 0.95 if signal.direction == "LONG" else entry_price * 1.05
        risk_pct = 0.02  # 每笔风险2%

        position_size = self.position_sizer.calculate_size(
            capital=capital,
            risk_pct=risk_pct,
            entry_price=entry_price,
            stop_price=stop_price,
        )

        # 检查3：仓位限制
        current_total = sum(
            p.get("quantity", 0) * p.get("entry_price", 0)
            for p in self._positions.values()
        )
        new_position_value = position_size * entry_price

        if not self.position_sizer.validate_position(current_total, new_position_value):
            return RiskCheckResult(
                approved=False,
                reason=f"Position size exceeds limit: {new_position_value:.2f}",
                details={
                    "current_total": current_total,
                    "new_position_value": new_position_value,
                },
            )

        return RiskCheckResult(
            approved=True,
            position_size=round(position_size, 8),
            reason="Risk check passed",
            details={
                "capital": capital,
                "risk_pct": risk_pct,
                "entry_price": entry_price,
                "stop_price": stop_price,
                "position_size": position_size,
                "current_total": current_total,
            },
        )

    async def _setup_stop_loss(
        self,
        signal: Signal,
        order_result: OrderResult,
        risk_check: RiskCheckResult,
    ) -> None:
        """设置止损止盈

        Args:
            signal: 交易信号
            order_result: 下单结果
            risk_check: 风控检查结果
        """
        entry_price = order_result.filled_price or signal.price

        # 计算止损止盈价格
        from app.config import settings as app_settings

        stop_loss_pct = app_settings.RISK_STOP_LOSS_PCT
        take_profit_pct = app_settings.RISK_TAKE_PROFIT_PCT

        if signal.direction == "LONG":
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            take_profit_price = entry_price * (1 + take_profit_pct)
        else:
            stop_loss_price = entry_price * (1 + stop_loss_pct)
            take_profit_price = entry_price * (1 - take_profit_pct)

        # 创建持仓记录
        position_id = f"pos-{uuid.uuid4().hex[:8]}"
        position = {
            "position_id": position_id,
            "symbol": signal.symbol,
            "market": signal.market,
            "quantity": order_result.filled_quantity,
            "entry_price": entry_price,
            "current_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price,
            "opened_at": datetime.now(timezone.utc).isoformat(),
        }

        self._positions[position_id] = position

        logger.info(
            f"OrderManager: stop loss set for {signal.symbol} - "
            f"entry={entry_price:.2f}, "
            f"stop_loss={stop_loss_price:.2f}, "
            f"take_profit={take_profit_price:.2f}"
        )

    def _record_order(
        self,
        signal: Signal,
        order_result: OrderResult,
        risk_check: RiskCheckResult,
    ) -> None:
        """记录订单信息

        Args:
            signal: 交易信号
            order_result: 下单结果
            risk_check: 风控检查结果
        """
        order_record = {
            "order_id": order_result.order_id,
            "signal_id": signal.signal_id,
            "symbol": signal.symbol,
            "market": signal.market,
            "side": "BUY" if signal.direction == "LONG" else "SELL",
            "direction": signal.direction,
            "type": order_result.type,
            "price": order_result.filled_price or signal.price,
            "quantity": order_result.filled_quantity,
            "status": order_result.status,
            "confidence": signal.confidence,
            "risk_approved": risk_check.approved,
            "position_size": risk_check.position_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # 如果订单还在pending状态，加入未完成列表
        if order_result.status == "PENDING":
            self._open_orders[order_result.order_id] = order_record

        logger.info(
            f"OrderManager: order recorded - "
            f"order_id={order_result.order_id}, "
            f"status={order_result.status}"
        )

    @property
    def open_order_count(self) -> int:
        """未完成订单数量"""
        return len(self._open_orders)

    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len(self._positions)

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取所有持仓"""
        return list(self._positions.values())
