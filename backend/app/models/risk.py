"""RiskConfig风控配置模型 + StopLossConfig"""

from sqlalchemy import Boolean, Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class RiskConfig(Base, BaseMixin):
    """风控配置模型，记录全局与按标的风控参数"""

    __tablename__ = "risk_configs"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="配置名称")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, default="*", comment="标的代码，*表示全局")
    market: Mapped[str] = mapped_column(String(16), nullable=False, default="*", comment="市场类型，*表示全局")
    max_position_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.1, comment="单笔最大仓位比例")
    stop_loss_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.05, comment="默认止损比例")
    take_profit_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.10, comment="默认止盈比例")
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.20, comment="最大回撤比例")
    trailing_stop_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="启用追踪止损")
    trailing_stop_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.03, comment="追踪止损比例")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    __table_args__ = (
        Index("ix_risk_configs_symbol", "symbol"),
    )

    def __repr__(self) -> str:
        return f"<RiskConfig({self.name} symbol={self.symbol})>"


class StopLossConfig(Base, BaseMixin):
    """止损配置模型，记录持仓的止损止盈参数"""

    __tablename__ = "stop_loss_configs"

    position_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="关联持仓ID")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, comment="标的代码")
    stop_loss_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="止损价格")
    take_profit_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="止盈价格")
    trailing_stop_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="追踪止损比例")
    is_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否已触发")
    config_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="扩展配置")

    __table_args__ = (
        Index("ix_stop_loss_position_id", "position_id"),
    )

    def __repr__(self) -> str:
        return f"<StopLossConfig(position={self.position_id} sl={self.stop_loss_price} tp={self.take_profit_price})>"
