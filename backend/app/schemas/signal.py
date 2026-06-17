"""信号Pydantic Schema"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    """信号创建Schema"""

    signal_id: str = Field(..., description="信号唯一ID")
    symbol: str = Field(..., description="标的代码")
    market: str = Field(..., description="市场类型：crypto / a_share")
    direction: str = Field(..., description="方向：LONG / SHORT / HOLD")
    price: float = Field(..., description="信号价格")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="置信度 0-1")
    source_engine: str = Field(..., description="来源引擎：taiji/spiral/elliott/tomas")
    theory_name: str = Field("", description="理论名称")
    timestamp: str = Field(..., description="信号时间戳 ISO 8601")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="信号元数据")


class SignalResponse(BaseModel):
    """信号响应Schema"""

    id: str = Field(..., description="记录ID")
    signal_id: str = Field(..., description="信号唯一ID")
    symbol: str = Field(..., description="标的代码")
    market: str = Field(..., description="市场类型")
    direction: str = Field(..., description="方向")
    price: float = Field(..., description="信号价格")
    confidence: float = Field(..., description="置信度")
    source_engine: str = Field(..., description="来源引擎")
    theory_name: str = Field(..., description="理论名称")
    timestamp: str = Field(..., description="信号时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="信号元数据")
    created_at: str = Field("", description="创建时间")

    model_config = {"from_attributes": True}


class SignalListResponse(BaseModel):
    """信号列表响应Schema"""

    total: int = Field(0, description="总数")
    items: List[SignalResponse] = Field(default_factory=list, description="信号列表")
