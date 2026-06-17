"""行情Pydantic Schema"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BarCreate(BaseModel):
    """K线数据创建Schema"""

    symbol: str = Field(..., description="标的代码，如 BTCUSDT")
    market: str = Field(..., description="市场类型：crypto / a_share")
    timeframe: str = Field("1m", description="时间周期：1m/5m/15m/1h/4h/1d")
    timestamp: str = Field(..., description="K线时间戳 ISO 8601")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(0.0, description="成交量")


class BarResponse(BaseModel):
    """K线数据响应Schema"""

    id: str = Field(..., description="记录ID")
    symbol: str = Field(..., description="标的代码")
    market: str = Field(..., description="市场类型")
    timeframe: str = Field(..., description="时间周期")
    timestamp: str = Field(..., description="K线时间戳")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")

    model_config = {"from_attributes": True}


class BarListResponse(BaseModel):
    """K线数据列表响应Schema"""

    total: int = Field(0, description="总数")
    items: List[BarResponse] = Field(default_factory=list, description="K线数据列表")


class UnifiedResponse(BaseModel):
    """统一API响应格式"""

    code: int = Field(0, description="响应码：0=成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: str = Field("ok", description="响应消息")
