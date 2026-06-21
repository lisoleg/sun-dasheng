"""滑点模型 — SlippageModel"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SlippageModel:
    """滑点模型（基点滑点）

    模拟订单成交时的滑点：
    - 市价单：成交价格 = 请求价格 * (1 + slippage_rate)
    - 限价单：如果当前价格优于限价，则按限价成交；否则不成交

    滑点率通常为正（实际成交价劣于请求价）。
    买单滑点使成交价更高，卖单滑点使成交价更低。
    """

    slippage_bps: float = 5.0  # 基点滑点，默认5 bps = 0.05%

    def apply(self, order_price: float, direction: str, fill_price: Optional[float] = None) -> float:
        """应用滑点

        Args:
            order_price: 订单请求价格
            direction: 交易方向 (BUY/SELL)
            fill_price: 实际成交价（如果已有，则基于此计算滑点）

        Returns:
            考虑滑点后的成交价
        """
        slippage_rate = self.slippage_bps / 10000.0  # 转换基点为百分比

        if fill_price is None:
            fill_price = order_price

        # 应用滑点
        if direction == "BUY":
            # 买单：成交价偏高
            slipped_price = fill_price * (1 + slippage_rate)
        elif direction == "SELL":
            # 卖单：成交价偏低
            slipped_price = fill_price * (1 - slippage_rate)
        else:
            slipped_price = fill_price

        return slipped_price

    def calc_commission(self, price: float, quantity: float, commission_rate: float) -> float:
        """计算手续费

        Args:
            price: 成交价格
            quantity: 成交数量
            commission_rate: 手续费率

        Returns:
            手续费金额
        """
        return price * quantity * commission_rate
