"""FastAPI应用入口、中间件注册、生命周期管理、WebSocket Hub"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.router import api_router
from app.config import settings


class WebSocketHub:
    """WebSocket连接管理中心，支持频道订阅与消息广播"""

    def __init__(self) -> None:
        self._channels: Dict[str, List[WebSocket]] = {}

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        """接受WebSocket连接并加入指定频道"""
        await websocket.accept()
        if channel not in self._channels:
            self._channels[channel] = []
        self._channels[channel].append(websocket)
        logger.info(f"WebSocket connected to channel: {channel}, total: {len(self._channels[channel])}")

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        """从频道中移除WebSocket连接"""
        if channel in self._channels:
            if websocket in self._channels[channel]:
                self._channels[channel].remove(websocket)
            if not self._channels[channel]:
                del self._channels[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")

    async def broadcast(self, channel: str, message: Dict[str, Any]) -> None:
        """向指定频道广播消息"""
        if channel not in self._channels:
            return
        disconnected: List[WebSocket] = []
        for websocket in self._channels[channel]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        for ws in disconnected:
            self.disconnect(channel, ws)

    async def send_to_all(self, message: Dict[str, Any]) -> None:
        """向所有频道广播消息"""
        for channel in list(self._channels.keys()):
            await self.broadcast(channel, message)

    def get_channel_count(self, channel: str) -> int:
        """获取指定频道的连接数"""
        return len(self._channels.get(channel, []))

    def get_total_connections(self) -> int:
        """获取所有频道的总连接数"""
        return sum(len(conns) for conns in self._channels.values())


# 全局WebSocket Hub实例
ws_hub = WebSocketHub()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动与关闭时的资源初始化/清理"""
    logger.info("孙大圣量化交易系统启动中...")
    logger.info(f"数据库: {settings.DATABASE_URL}")
    logger.info(f"Redis: {settings.REDIS_URL}")
    logger.info(f"币安API Key: {settings.BINANCE_API_KEY[:4]}****" if settings.BINANCE_API_KEY else "币安API Key: 未配置")

    # 启动后台任务：WebSocket模拟数据推送
    push_task = asyncio.create_task(_mock_push_loop())

    yield

    # 清理资源
    push_task.cancel()
    try:
        await push_task
    except asyncio.CancelledError:
        pass
    logger.info("孙大圣量化交易系统已关闭")


async def _mock_push_loop() -> None:
    """后台任务：定期向WebSocket频道推送模拟数据"""
    import random
    from datetime import datetime, timezone

    while True:
        try:
            await asyncio.sleep(2)

            # 模拟K线更新
            now = datetime.now(timezone.utc).isoformat()
            await ws_hub.broadcast("market", {
                "type": "bar_update",
                "payload": {
                    "symbol": "BTCUSDT",
                    "market": "crypto",
                    "timeframe": "1m",
                    "timestamp": now,
                    "open": round(random.uniform(60000, 70000), 2),
                    "high": round(random.uniform(70000, 72000), 2),
                    "low": round(random.uniform(58000, 60000), 2),
                    "close": round(random.uniform(60000, 70000), 2),
                    "volume": round(random.uniform(100, 500), 4),
                },
            })

            # 模拟信号推送
            if random.random() > 0.7:
                await ws_hub.broadcast("signals", {
                    "type": "signal_generated",
                    "payload": {
                        "signal_id": f"sig-{random.randint(10000, 99999)}",
                        "symbol": "BTCUSDT",
                        "market": "crypto",
                        "direction": random.choice(["LONG", "SHORT", "HOLD"]),
                        "price": round(random.uniform(60000, 70000), 2),
                        "confidence": round(random.uniform(0.3, 0.95), 2),
                        "source_engine": "taiji",
                        "theory_name": "太极中心律",
                        "timestamp": now,
                        "metadata": {},
                    },
                })

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Mock push error: {e}")


# 创建FastAPI应用实例
app = FastAPI(
    title="孙大圣量化交易系统",
    description="基于鲁兆理论的A股/加密货币量化交易系统",
    version="0.2.0",
    lifespan=lifespan,
)

# 注册CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["系统"])
async def health_check() -> Dict[str, Any]:
    """系统健康检查端点"""
    return {
        "code": 0,
        "data": {
            "status": "healthy",
            "version": "0.2.0",
            "ws_connections": ws_hub.get_total_connections(),
        },
        "message": "ok",
    }
