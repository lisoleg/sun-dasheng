"""信号执行器 — SignalRunner

将理论引擎产生的信号转化为订单。
支持信号过滤、仓位管理、风险控制。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import (
    Bar,
    Direction,
    Order,
    OrderType,
    BacktestConfig,
)
from app.services.backtest.position_manager import PositionSizer
from app.services.signal.fusion import SignalFusion
from app.services.signal.generator import Signal


class SignalRunner:
    """信号执行器

    将理论信号转化为订单，考虑：
    1. 信号置信度阈值
    2. 仓位管理规则
    3. 止损止盈
    4. 最大仓位限制
    """

    def __init__(
        self,
        config: BacktestConfig,
        signal_fusion: Optional[SignalFusion] = None,
    ) -> None:
        """初始化信号执行器

        Args:
            config: 回测配置
            signal_fusion: 信号融合器
        """
        self.config = config
        self.signal_fusion = signal_fusion
        self._order_counter = 0

    def process_bar(
        self,
        bar: Bar,
        theories: List[Any],
        portfolio_manager: Any,
        current_bar_index: int,
    ) -> List[Order]:
        """处理当前K线，生成订单

        Args:
            bar: 当前K线
            theories: 理论引擎列表
            portfolio_manager: 资金账户管理器
            current_bar_index: 当前K线索引

        Returns:
            订单列表
        """
        orders = []

        # 检查是否需要平仓（止损止盈）
        close_orders = self._check_stop_loss_take_profit(
            bar, portfolio_manager, current_bar_index
        )
        orders.extend(close_orders)

        # 运行理论引擎生成信号
        signals = self._run_theories(bar, theories)

        # 如果信号为空，不生成新订单
        if not signals:
            return orders

        # 生成开仓订单
        open_orders = self._generate_open_orders(
            bar, signals, portfolio_manager, current_bar_index
        )
        orders.extend(open_orders)

        return orders

    def _run_theories(self, bar: Bar, theories: List[Any]) -> List[Signal]:
        """运行理论引擎生成信号

        Args:
            bar: 当前K线（完整历史用于分析）
            theories: 理论引擎列表

        Returns:
            信号列表
        """
        # 构建K线数据供理论引擎分析
        # 注意：这里需要传入历史K线数据，简化处理传入单根K线
        bar_dict = [
            {
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "timestamp": bar.timestamp.isoformat(),
                "symbol": bar.symbol,
            }
        ]

        signals = []
        for theory in theories:
            try:
                result = theory.analyze(bar_dict)
                # 从结果中提取信号
                if hasattr(result, "hints") and result.hints:
                    for hint in result.hints:
                        if hasattr(hint, "direction"):
                            direction = hint.direction
                        elif isinstance(hint, dict):
                            direction = hint.get("direction", "HOLD")
                        else:
                            continue

                        if direction != "HOLD" and direction != "hold":
                            signal = Signal(
                                symbol=bar.symbol,
                                direction=direction,
                                confidence=(
                                    hint.confidence
                                    if hasattr(hint, "confidence")
                                    else 0.5
                                ),
                                source_engine=theory.theory_name
                                if hasattr(theory, "theory_name")
                                else theory.name,
                                theory_name=theory.name
                                if hasattr(theory, "name")
                                else "",
                            )
                            signals.append(signal)
            except Exception as e:
                logger.error(f"SignalRunner: theory {theory} failed: {e}")
                continue

        return signals

    def _generate_open_orders(
        self,
        bar: Bar,
        signals: List[Signal],
        portfolio_manager: Any,
        current_bar_index: int,
    ) -> List[Order]:
        """根据信号生成开仓订单

        Args:
            bar: 当前K线
            signals: 信号列表
            portfolio_manager: 资金账户管理器
            current_bar_index: 当前K线索引

        Returns:
            开仓订单列表
        """
        orders = []

        if not signals:
            return orders

        # 按方向分组信号
        long_signals = [s for s in signals if s.direction == "LONG" or s.direction == "BUY"]
        short_signals = [s for s in signals if s.direction == "SHORT" or s.direction == "SELL"]

        # 决定交易方向（简化：取信号数多的方向）
        if len(long_signals) > len(short_signals):
            direction = Direction.BUY
            selected_signals = long_signals
        elif len(short_signals) > 0:
            direction = Direction.SELL
            selected_signals = short_signals
        else:
            return orders

        # 检查是否已有同向持仓
        symbol = bar.symbol
        if portfolio_manager.has_open_position(symbol):
            open_trade = portfolio_manager.get_open_trade(symbol)
            if open_trade and (
                (direction == Direction.BUY and open_trade.direction == Direction.BUY)
                or (direction == Direction.SELL and open_trade.direction == Direction.SELL)
            ):
                # 已有同向持仓，不再加仓
                return orders

        # 计算平均置信度
        avg_confidence = (
            sum(s.confidence for s in selected_signals) / len(selected_signals)
            if selected_signals
            else 0.5
        )

        # 计算仓位大小
        position_size = PositionSizer.calculate_position_size(
            method=self.config.position_sizing,
            portfolio=portfolio_manager.portfolio,
            signal_confidence=avg_confidence,
            entry_price=bar.close,
            max_position_pct=self.config.max_position_pct,
        )

        if position_size <= 0:
            return orders

        # 创建订单
        self._order_counter += 1
        order = Order(
            id=f"order-{self._order_counter}",
            bar_index=current_bar_index,
            symbol=symbol,
            direction=direction,
            order_type=OrderType.MARKET,
            price=bar.close,
            quantity=position_size,
            signal_source=",".join(s.source_engine for s in selected_signals),
            theory_name=selected_signals[0].theory_name if selected_signals else "",
            confidence=avg_confidence,
        )
        orders.append(order)

        return orders

    def _check_stop_loss_take_profit(
        self,
        bar: Bar,
        portfolio_manager: Any,
        current_bar_index: int,
    ) -> List[Order]:
        """检查止损止盈，生成平仓订单

        Args:
            bar: 当前K线
            portfolio_manager: 资金账户管理器
            current_bar_index: 当前K线索引

        Returns:
            平仓订单列表
        """
        orders = []
        symbol = bar.symbol

        if not portfolio_manager.has_open_position(symbol):
            return orders

        open_trade = portfolio_manager.get_open_trade(symbol)
        if not open_trade:
            return orders

        should_close = False
        exit_reason = ""

        # 检查止损
        if self.config.stop_loss_pct and open_trade.direction == Direction.BUY:
            stop_loss_price = open_trade.open_price * (1 - self.config.stop_loss_pct)
            if bar.low <= stop_loss_price:
                should_close = True
                exit_reason = "STOP_LOSS"

        # 检查止盈
        if self.config.take_profit_pct and open_trade.direction == Direction.BUY:
            take_profit_price = open_trade.open_price * (1 + self.config.take_profit_pct)
            if bar.high >= take_profit_price:
                should_close = True
                exit_reason = "TAKE_PROFIT"

        if should_close:
            # 创建平仓订单
            self._order_counter += 1
            close_direction = (
                Direction.SELL
                if open_trade.direction == Direction.BUY
                else Direction.BUY
            )
            order = Order(
                id=f"order-{self._order_counter}",
                bar_index=current_bar_index,
                symbol=symbol,
                direction=close_direction,
                order_type=OrderType.MARKET,
                price=bar.close,
                quantity=open_trade.quantity,
                signal_source="risk_manager",
                theory_name=None,
                confidence=1.0,
            )
            orders.append(order)
            logger.info(
                f"SignalRunner: {exit_reason} triggered for {symbol} @ {bar.close:.2f}"
            )

        return orders
