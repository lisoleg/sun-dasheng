"""API路由聚合"""

from fastapi import APIRouter

from app.api.market import router as market_router
from app.api.signal import router as signal_router
from app.api.order import router as order_router
from app.api.risk import router as risk_router
from app.api.strategy import router as strategy_router

api_router = APIRouter(prefix="")

# 注册各模块路由
api_router.include_router(market_router, prefix="/market", tags=["行情"])
api_router.include_router(signal_router, prefix="/signals", tags=["信号"])
api_router.include_router(order_router, prefix="/orders", tags=["订单"])
api_router.include_router(risk_router, prefix="/risk", tags=["风控"])
api_router.include_router(strategy_router, prefix="/strategy", tags=["策略"])
