"""仓位管理器 — PositionSizer

支持多种仓位管理策略：
- fixed_pct: 固定比例仓位（按账户权益的固定百分比）
- fixed_amount: 固定金额仓位
- kelly: Kelly公式仓位（基于历史胜率和盈亏比）
- risk_parity: 风险平价仓位（基于波动率调整）
"""


from dataclasses import dataclass
from typing import Dict, Optional

from loguru import logger

from app.services.backtest.models import Portfolio, Direction


class PositionSizer:
    """仓位管理器

    根据策略和当前账户状态计算应开仓数量。
    """

    @staticmethod
    def calculate_position_size(
        method: str,
        portfolio: Portfolio,
        signal_confidence: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        **kwargs,
    ) -> float:
        """计算仓位大小

        Args:
            method: 仓位管理方法 (fixed_pct/fixed_amount/kelly/risk_parity)
            portfolio: 当前账户状态
            signal_confidence: 信号置信度
            entry_price: 入场价格
            stop_loss_price: 止损价格（用于risk_parity和kelly）
            **kwargs: 其他参数

        Returns:
            应开仓数量（正数表示买入，负数表示卖出）
        """
        if method == "fixed_pct":
            return PositionSizer._fixed_pct(
                portfolio, signal_confidence, entry_price, **kwargs
            )
        elif method == "fixed_amount":
            return PositionSizer._fixed_amount(
                portfolio, entry_price, **kwargs
            )
        elif method == "kelly":
            return PositionSizer._kelly(
                portfolio, signal_confidence, entry_price, stop_loss_price, **kwargs
            )
        elif method == "risk_parity":
            return PositionSizer._risk_parity(
                portfolio, entry_price, stop_loss_price, **kwargs
            )
        else:
            logger.warning(f"PositionSizer: unknown method '{method}', using fixed_pct")
            return PositionSizer._fixed_pct(
                portfolio, signal_confidence, entry_price, **kwargs
            )

    @staticmethod
    def _fixed_pct(
        portfolio: Portfolio,
        signal_confidence: float,
        entry_price: float,
        max_position_pct: float = 0.3,
        **kwargs,
    ) -> float:
        """固定比例仓位

        仓位大小 = 账户权益 * 最大仓位比例 * 信号置信度 / 入场价格

        Args:
            portfolio: 账户状态
            signal_confidence: 信号置信度
            entry_price: 入场价格
            max_position_pct: 最大仓位比例

        Returns:
            应开仓数量
        """
        equity = portfolio.equity if portfolio.equity > 0 else portfolio.initial_cash
        position_value = equity * max_position_pct * signal_confidence
        quantity = position_value / entry_price if entry_price > 0 else 0
        return quantity

    @staticmethod
    def _fixed_amount(
        portfolio: Portfolio,
        entry_price: float,
        fixed_amount: float = 10000.0,
        **kwargs,
    ) -> float:
        """固定金额仓位

        仓位大小 = 固定金额 / 入场价格

        Args:
            portfolio: 账户状态
            entry_price: 入场价格
            fixed_amount: 固定金额

        Returns:
            应开仓数量
        """
        quantity = fixed_amount / entry_price if entry_price > 0 else 0
        return quantity

    @staticmethod
    def _kelly(
        portfolio: Portfolio,
        signal_confidence: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        win_rate: float = 0.5,
        avg_win: float = 0.02,
        avg_loss: float = 0.01,
        **kwargs,
    ) -> float:
        """Kelly公式仓位

        Kelly公式：f = (p * b - q) / b
        其中 p=胜率, q=败率, b=盈亏比

        Args:
            portfolio: 账户状态
            signal_confidence: 信号置信度
            entry_price: 入场价格
            stop_loss_price: 止损价格
            win_rate: 历史胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损

        Returns:
            应开仓数量
        """
        # 简化Kelly：使用信号置信度作为胜率估计
        p = (win_rate + signal_confidence) / 2
        q = 1 - p

        if avg_loss > 0:
            b = avg_win / avg_loss  # 盈亏比
        else:
            b = 1.0

        kelly_fraction = (p * b - q) / b if b > 0 else 0
        kelly_fraction = max(0, min(kelly_fraction, 0.5))  # 限制Kelly分数在0-50%

        equity = portfolio.equity if portfolio.equity > 0 else portfolio.initial_cash
        position_value = equity * kelly_fraction
        quantity = position_value / entry_price if entry_price > 0 else 0

        return quantity

    @staticmethod
    def _risk_parity(
        portfolio: Portfolio,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        risk_per_trade: float = 0.02,
        **kwargs,
    ) -> float:
        """风险平价仓位

        根据止损幅度计算仓位，使每笔交易风险相等。

        仓位大小 = 账户权益 * 每笔风险比例 / |入场价 - 止损价|

        Args:
            portfolio: 账户状态
            entry_price: 入场价格
            stop_loss_price: 止损价格
            risk_per_trade: 每笔交易风险比例

        Returns:
            应开仓数量
        """
        if stop_loss_price is None or stop_loss_price <= 0:
            # 无止损价，使用2%默认止损
            stop_loss_price = entry_price * 0.98

        risk_amount = portfolio.equity * risk_per_trade
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk > 0:
            quantity = risk_amount / price_risk
        else:
            quantity = 0

        return quantity
