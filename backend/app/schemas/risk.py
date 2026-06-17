"""风控Pydantic Schema"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskConfigResponse(BaseModel):
    """风控配置响应Schema"""

    id: str = Field(..., description="记录ID")
    name: str = Field(..., description="配置名称")
    symbol: str = Field(..., description="标的代码")
    market: str = Field(..., description="市场类型")
    max_position_pct: float = Field(..., description="单笔最大仓位比例")
    stop_loss_pct: float = Field(..., description="默认止损比例")
    take_profit_pct: float = Field(..., description="默认止盈比例")
    max_drawdown_pct: float = Field(..., description="最大回撤比例")
    trailing_stop_enabled: bool = Field(..., description="启用追踪止损")
    trailing_stop_pct: float = Field(..., description="追踪止损比例")
    is_active: bool = Field(..., description="是否启用")

    model_config = {"from_attributes": True}


class RiskConfigUpdate(BaseModel):
    """风控配置更新Schema"""

    name: Optional[str] = Field(None, description="配置名称")
    max_position_pct: Optional[float] = Field(None, ge=0.01, le=1.0, description="单笔最大仓位比例")
    stop_loss_pct: Optional[float] = Field(None, ge=0.01, le=0.5, description="默认止损比例")
    take_profit_pct: Optional[float] = Field(None, ge=0.01, le=1.0, description="默认止盈比例")
    max_drawdown_pct: Optional[float] = Field(None, ge=0.01, le=0.5, description="最大回撤比例")
    trailing_stop_enabled: Optional[bool] = Field(None, description="启用追踪止损")
    trailing_stop_pct: Optional[float] = Field(None, ge=0.005, le=0.2, description="追踪止损比例")
    is_active: Optional[bool] = Field(None, description="是否启用")


class RiskAlertResponse(BaseModel):
    """风控告警响应Schema"""

    id: str = Field(..., description="告警ID")
    alert_type: str = Field(..., description="告警类型：STOP_LOSS / TAKE_PROFIT / DRAWDOWN / POSITION_LIMIT")
    symbol: str = Field(..., description="标的代码")
    message: str = Field(..., description="告警消息")
    severity: str = Field(..., description="严重级别：INFO / WARNING / CRITICAL")
    timestamp: str = Field(..., description="告警时间戳")
    details: Dict[str, Any] = Field(default_factory=dict, description="告警详情")

    model_config = {"from_attributes": True}


class RiskAlertListResponse(BaseModel):
    """风控告警列表响应Schema"""

    total: int = Field(0, description="总数")
    items: List[RiskAlertResponse] = Field(default_factory=list, description="告警列表")
