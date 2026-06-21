"""订单簿 — OrderBook

管理回测中的待成交和已成交订单。
简化实现：假设所有市价单在下一根K线成交。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from app.services.backtest.models import Bar, Direction, Order, Fill, OrderType
from app.services.backtest.slippage_model import SlippageModel


@dataclass
class OrderBook:
    """订单簿

    管理待成交和已成交订单。
    回测中简化处理：
    - 市价单：在当前K线或下一K线以近似价格成交
    - 限价单：当价格触及限价时成交
    """

    slippage_model: SlippageModel = field(default_factory=SlippageModel)

    def __post_init__(self) -> None:
        self._pending_orders: List[Order] = []
        self._filled_orders: List[Fill] = []

    def add_order(self, order: Order) -> None:
        """添加订单到订单簿

        Args:
            order: 订单
        """
        self._pending_orders.append(order)
        logger.debug(
            f"OrderBook: added {order.direction.value} order "
            f"{order.quantity} @ {order.price} (bar={order.bar_index})"
        )

    def match_orders(
        self,
        current_bar: Bar,
        commission_rate: float = 0.001,
    ) -> List[Fill]:
        """撮合订单

        简化的撮合逻辑：
        - 市价单：以当前K线的均价成交
        - 限价单：如果当前价格优于限价则成交

        Args:
            current_bar: 当前K线
            commission_rate: 手续费率

        Returns:
            成交列表
        """
        fills = []
        remaining_orders = []

        avg_price = (current_bar.open + current_bar.close) / 2

        for order in self._pending_orders:
            fill = self._try_fill_order(order, current_bar, avg_price, commission_rate)
            if fill:
                fills.append(fill)
                self._filled_orders.append(fill)
            else:
                remaining_orders.append(order)

        self._pending_orders = remaining_orders
        return fills

    def _try_fill_order(
        self,
        order: Order,
        current_bar: Bar,
        avg_price: float,
        commission_rate: float,
    ) -> Optional[Fill]:
        """尝试撮合单个订单

        Args:
            order: 订单
            current_bar: 当前K线
            avg_price: 当前均价
            commission_rate: 手续费率

        Returns:
            成交记录（如果成交），否则None
        """
        fill_price = avg_price

        if order.order_type == OrderType.MARKET:
            # 市价单：直接成交，考虑滑点
            fill_price = self.slippage_model.apply(avg_price, order.direction.value)
        elif order.order_type == OrderType.LIMIT:
            # 限价单：检查是否触及限价
            if order.direction == Direction.BUY and current_bar.low <= order.price:
                fill_price = order.price
            elif order.direction == Direction.SELL and current_bar.high >= order.price:
                fill_price = order.price
            else:
                return None  # 未触及限价，不成交
        else:
            # 其他类型订单暂不处理
            return None

        # 计算手续费
        commission = self.slippage_model.calc_commission(
            fill_price, order.quantity, commission_rate
        )

        # 创建成交记录
        fill = Fill(
            order_id=order.id,
            bar_index=order.bar_index,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            commission=commission,
            timestamp=current_bar.timestamp,
        )

        logger.debug(
            f"OrderBook: filled {order.direction.value} {order.quantity} @ {fill_price:.2f} "
            f"(commission={commission:.2f})"
        )

        return fill

    def get_pending_orders(self) -> List[Order]:
        """获取待成交订单"""
        return self._pending_orders

    def get_filled_orders(self) -> List[Fill]:
        """获取已成交订单"""
        return self._filled_orders

    def clear(self) -> None:
        """清空订单簿"""
        self._pending_orders.clear()
        self._filled_orders.clear()
