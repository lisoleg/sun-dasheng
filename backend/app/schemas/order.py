"""订单Pydantic Schema"""

from typing import List, Optional

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """订单创建Schema"""

    symbol: str = Field(..., description="标的代码")
    market: str = Field("crypto", description="市场类型：crypto / a_share")
    side: str = Field(..., description="买卖方向：BUY / SELL")
    type: str = Field("MARKET", description="订单类型：MARKET / LIMIT")
    price: float = Field(0.0, description="下单价格(LIMIT单必填)")
    quantity: float = Field(..., gt=0, description="下单数量")


class OrderResponse(BaseModel):
    """订单响应Schema"""

    id: str = Field(..., description="记录ID")
    order_id: str = Field(..., description="订单唯一ID")
    symbol: str = Field(..., description="标的代码")
    market: str = Field(..., description="市场类型")
    side: str = Field(..., description="买卖方向")
    type: str = Field(..., description="订单类型")
    price: float = Field(..., description="下单价格")
    quantity: float = Field(..., description="下单数量")
    status: str = Field(..., description="订单状态")
    created_at: str = Field("", description="创建时间")
    updated_at: str = Field("", description="更新时间")

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """订单列表响应Schema"""

    total: int = Field(0, description="总数")
    items: List[OrderResponse] = Field(default_factory=list, description="订单列表")
