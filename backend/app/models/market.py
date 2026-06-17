"""Bar K线数据模型"""

from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class Bar(Base, BaseMixin):
    """K线数据模型，支持A股和加密货币市场"""

    __tablename__ = "bars"

    symbol: Mapped[str] = mapped_column(String(32), nullable=False, comment="标的代码，如 BTCUSDT / 000001.SZ")
    market: Mapped[str] = mapped_column(String(16), nullable=False, comment="市场类型：crypto / a_share")
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False, comment="时间周期：1m/5m/15m/1h/4h/1d")
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False, comment="K线时间戳 ISO 8601")
    open: Mapped[float] = mapped_column(Float, nullable=False, comment="开盘价")
    high: Mapped[float] = mapped_column(Float, nullable=False, comment="最高价")
    low: Mapped[float] = mapped_column(Float, nullable=False, comment="最低价")
    close: Mapped[float] = mapped_column(Float, nullable=False, comment="收盘价")
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="成交量")

    __table_args__ = (
        Index("ix_bars_symbol_timeframe", "symbol", "timeframe"),
        Index("ix_bars_symbol_timestamp", "symbol", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Bar({self.symbol} {self.timeframe} {self.timestamp})>"
