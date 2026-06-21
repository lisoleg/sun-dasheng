"""资金账户管理 — PortfolioManager"""

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from app.services.backtest.models import (
    Bar,
    Portfolio,
    Position,
    Trade,
    Direction,
)


class PortfolioManager:
    """管理仓位和资金

    负责：
    1. 开仓/平仓
    2. 标记持仓市值
    3. 计算账户权益和回撤
    4. 记录交易
    """

    def __init__(self, initial_cash: float) -> None:
        """初始化资金账户

        Args:
            initial_cash: 初始资金
        """
        self.portfolio = Portfolio(
            cash=initial_cash,
            initial_cash=initial_cash,
        )
        self._trade_counter = 0
        self._open_trades: Dict[str, Trade] = {}  # symbol -> open trade

    def open_position(
        self,
        symbol: str,
        direction: Direction,
        price: float,
        quantity: float,
        commission: float,
        timestamp: datetime,
        signal_source: str = "",
        theory_name: Optional[str] = None,
        confidence: float = 0.0,
    ) -> Trade:
        """开仓

        Args:
            symbol: 交易标的
            direction: 交易方向（BUY/SELL）
            price: 成交价格
            quantity: 成交数量
            commission: 手续费
            timestamp: 成交时间
            signal_source: 信号来源
            theory_name: 理论名称
            confidence: 信号置信度

        Returns:
            交易记录
        """
        # 创建交易记录
        self._trade_counter += 1
        trade = Trade(
            trade_id=f"trade-{self._trade_counter}",
            symbol=symbol,
            direction=direction,
            open_time=timestamp,
            open_price=price,
            quantity=quantity,
            signal_source=signal_source,
            theory_name=theory_name,
            confidence=confidence,
        )

        # 更新资金
        cost = price * quantity + commission
        self.portfolio.cash -= cost

        # 更新或创建持仓
        if symbol not in self.portfolio.positions:
            self.portfolio.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity if direction == Direction.BUY else -quantity,
                avg_cost=price,
            )
        else:
            position = self.portfolio.positions[symbol]
            if direction == Direction.BUY:
                # 加仓：更新平均成本
                total_quantity = position.quantity + quantity
                if total_quantity > 0:
                    position.avg_cost = (
                        position.avg_cost * position.quantity + price * quantity
                    ) / total_quantity
                position.quantity = total_quantity
            else:
                # 减仓或做空（A股不支持做空，这里仅处理减仓）
                position.quantity -= quantity
                if abs(position.quantity) < 1e-6:
                    # 清仓
                    del self.portfolio.positions[symbol]

        # 记录未平仓交易
        self._open_trades[symbol] = trade

        logger.debug(f"Portfolio: opened {direction.value} {quantity} {symbol} @ {price:.2f}")
        return trade

    def close_position(
        self,
        symbol: str,
        price: float,
        commission: float,
        timestamp: datetime,
        exit_reason: str = "SIGNAL",
    ) -> Optional[Trade]:
        """平仓

        Args:
            symbol: 交易标的
            price: 成交价格
            commission: 手续费
            timestamp: 成交时间
            exit_reason: 平仓原因

        Returns:
            完成的交易记录，如无未平仓交易则返回None
        """
        if symbol not in self._open_trades:
            logger.warning(f"Portfolio: no open trade for {symbol}")
            return None

        trade = self._open_trades[symbol]
        trade.close_time = timestamp
        trade.close_price = price
        trade.exit_reason = exit_reason

        # 计算盈亏
        if trade.direction == Direction.BUY:
            trade.pnl = (price - trade.open_price) * trade.quantity - commission
            trade.pnl_pct = (price - trade.open_price) / trade.open_price if trade.open_price > 0 else 0
        else:
            # 做空平仓（A股暂不支持）
            trade.pnl = (trade.open_price - price) * trade.quantity - commission
            trade.pnl_pct = (trade.open_price - price) / trade.open_price if trade.open_price > 0 else 0

        # 计算持仓时长
        if trade.open_time and trade.close_time:
            delta = trade.close_time - trade.open_time
            trade.holding_hours = delta.total_seconds() / 3600

        # 更新资金
        proceeds = price * trade.quantity - commission
        self.portfolio.cash += proceeds

        # 清除持仓
        if symbol in self.portfolio.positions:
            del self.portfolio.positions[symbol]

        # 记录完成交易
        self.portfolio.trades.append(trade)
        del self._open_trades[symbol]

        logger.debug(
            f"Portfolio: closed {trade.direction.value} {symbol} @ {price:.2f}, "
            f"pnl={trade.pnl:.2f} ({trade.pnl_pct:.2%})"
        )
        return trade

    def mark_to_market(self, current_bars: Dict[str, Bar]) -> None:
        """标记持仓市值

        Args:
            current_bars: 当前K线数据 {symbol: Bar}
        """
        self.portfolio.mark_to_market(current_bars)

    def get_equity(self) -> float:
        """获取当前权益"""
        return self.portfolio.equity

    def get_cash(self) -> float:
        """获取可用资金"""
        return self.portfolio.cash

    def get_positions(self) -> Dict[str, Position]:
        """获取当前持仓"""
        return self.portfolio.positions

    def get_trades(self) -> List[Trade]:
        """获取所有完成交易"""
        return self.portfolio.trades

    def get_equity_curve(self) -> List[float]:
        """获取权益曲线"""
        return self.portfolio.equity_curve

    def get_drawdown_curve(self) -> List[float]:
        """获取回撤曲线"""
        return self.portfolio.drawdown_curve

    def has_open_position(self, symbol: str) -> bool:
        """检查是否有未平仓持仓"""
        return symbol in self._open_trades

    def get_open_trade(self, symbol: str) -> Optional[Trade]:
        """获取未平仓交易"""
        return self._open_trades.get(symbol)
