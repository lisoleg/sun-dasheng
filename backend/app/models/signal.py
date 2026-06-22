"""Signal交易信号模型"""

from sqlalchemy import Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class Signal(Base, BaseMixin):
    """交易信号模型，记录理论引擎和TOMAS-AGI产生的信号"""

    __tablename__ = "signals"

    signal_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="信号唯一ID")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, comment="标的代码")
    market: Mapped[str] = mapped_column(String(16), nullable=False, comment="市场类型：crypto / a_share")
    direction: Mapped[str] = mapped_column(String(8), nullable=False, comment="方向：LONG / SHORT / HOLD")
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="信号价格")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="置信度 0-1")
    source_engine: Mapped[str] = mapped_column(String(32), nullable=False, comment="来源引擎：taiji/spiral/elliott/tomas")
    theory_name: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="理论名称")
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False, comment="信号时间戳 ISO 8601")
    meta_data: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, comment="信号元数据")

    __table_args__ = (
        Index("ix_signals_symbol", "symbol"),
        Index("ix_signals_direction", "direction"),
        Index("ix_signals_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Signal({self.signal_id} {self.symbol} {self.direction} conf={self.confidence})>"
