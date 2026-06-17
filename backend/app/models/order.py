"""Order订单模型"""

from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class Order(Base, BaseMixin):
    """订单模型，记录手动和自动下单"""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="订单唯一ID")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, comment="标的代码")
    market: Mapped[str] = mapped_column(String(16), nullable=False, comment="市场类型：crypto / a_share")
    side: Mapped[str] = mapped_column(String(8), nullable=False, comment="买卖方向：BUY / SELL")
    type: Mapped[str] = mapped_column(String(16), nullable=False, comment="订单类型：MARKET / LIMIT")
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="下单价格")
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="下单数量")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PENDING", comment="状态：PENDING/FILLED/CANCELLED/REJECTED"
    )

    __table_args__ = (
        Index("ix_orders_symbol", "symbol"),
        Index("ix_orders_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Order({self.order_id} {self.symbol} {self.side} {self.status})>"
