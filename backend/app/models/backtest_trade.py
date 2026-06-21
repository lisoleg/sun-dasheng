"""回测交易明细数据库模型 — BacktestTrade"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import Base, BaseMixin


class ExitReason(str, enum.Enum):
    """平仓原因"""
    SIGNAL = "SIGNAL"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    END_OF_DATA = "END_OF_DATA"


class TradeSide(str, enum.Enum):
    """交易方向"""
    BUY = "BUY"
    SELL = "SELL"


class BacktestTrade(Base, BaseMixin):
    """回测交易明细表

    Attributes:
        trade_id: 交易唯一标识
        backtest_id: 关联的回测ID
        symbol: 交易标的
        side: 交易方向(BUY/SELL)
        open_time: 开仓时间
        open_price: 开仓价格
        close_time: 平仓时间
        close_price: 平仓价格
        quantity: 交易数量
        pnl: 盈亏(绝对值)
        pnl_pct: 盈亏(百分比)
        holding_hours: 持仓时长(小时)
        theory_tags: 触发的理论模块列表
        confidence: 信号置信度
        exit_reason: 平仓原因
    """
    __tablename__ = "backtest_trades"

    trade_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4())
    )
    backtest_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[TradeSide] = mapped_column(SAEnum(TradeSide), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    close_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    holding_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    theory_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    exit_reason: Mapped[Optional[ExitReason]] = mapped_column(SAEnum(ExitReason), nullable=True)
