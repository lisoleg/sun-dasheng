"""Position持仓模型"""

from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class Position(Base, BaseMixin):
    """持仓模型，记录当前持仓状态"""

    __tablename__ = "positions"

    position_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="持仓唯一ID")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, comment="标的代码")
    market: Mapped[str] = mapped_column(String(16), nullable=False, comment="市场类型：crypto / a_share")
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="持仓数量")
    entry_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="入场价格")
    current_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="当前价格")
    stop_loss_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="止损价格")
    take_profit_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="止盈价格")
    unrealized_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="未实现盈亏")
    opened_at: Mapped[str] = mapped_column(String(64), nullable=False, comment="开仓时间 ISO 8601")

    __table_args__ = (
        Index("ix_positions_symbol", "symbol"),
    )

    def __repr__(self) -> str:
        return f"<Position({self.position_id} {self.symbol} qty={self.quantity} pnl={self.unrealized_pnl})>"
