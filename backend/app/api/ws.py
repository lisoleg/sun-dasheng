"""WebSocket端点 - 行情与信号实时推送"""

from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.main import ws_hub

router = APIRouter()


@router.websocket("/market")
async def websocket_market(websocket: WebSocket) -> None:
    """行情实时推送WebSocket端点"""
    await ws_hub.connect("market", websocket)
    try:
        while True:
            # 接收客户端消息（用于心跳/订阅控制）
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                symbol = data.get("symbol", "BTCUSDT")
                logger.info(f"WebSocket market subscribe: {symbol}")
                await websocket.send_json({
                    "type": "subscribed",
                    "payload": {"symbol": symbol, "status": "ok"},
                })
    except WebSocketDisconnect:
        ws_hub.disconnect("market", websocket)
        logger.info("Market WebSocket disconnected")


@router.websocket("/signals")
async def websocket_signals(websocket: WebSocket) -> None:
    """信号实时推送WebSocket端点"""
    await ws_hub.connect("signals", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                direction = data.get("direction", "all")
                logger.info(f"WebSocket signals subscribe: {direction}")
                await websocket.send_json({
                    "type": "subscribed",
                    "payload": {"direction": direction, "status": "ok"},
                })
    except WebSocketDisconnect:
        ws_hub.disconnect("signals", websocket)
        logger.info("Signals WebSocket disconnected")
