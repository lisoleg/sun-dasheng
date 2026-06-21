"""WebSocket端点 - 行情、信号、回测实时推送"""

from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import Query
from loguru import logger

from app.main import ws_hub

router = APIRouter()


@router.websocket("/market")
async def websocket_market(websocket: WebSocket) -> None:
    """行情实时推送WebSocket端点"""
    await ws_hub.connect("market", websocket)
    try:
        while True:
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


@router.websocket("/backtest")
async def websocket_backtest(websocket: WebSocket) -> None:
    """回测进度实时推送WebSocket端点

    客户端订阅消息格式：
    { "action": "subscribe", "channel": "backtest", "task_id": "bt-xxx" }

    服务端推送格式：
    {
        "type": "backtest_progress",
        "channel": "backtest",
        "payload": {
            "backtest_id": "bt-xxx",
            "status": "running",
            "progress": 45,
            "stage": "computing_signals",
            "current_bar": 820,
            "total_bars": 1825
        },
        "timestamp": "2026-06-17T12:34:56Z"
    }
    """
    await ws_hub.connect("backtest", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action") or data.get("type")

            if action == "ping":
                await websocket.send_json({"type": "pong"})
            elif action == "subscribe":
                task_id = data.get("task_id", "all")
                logger.info(f"WebSocket backtest subscribe: task_id={task_id}")
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": "backtest",
                    "payload": {"task_id": task_id, "status": "ok"},
                })
            elif action == "set_mode":
                mode = data.get("mode", "real-time")
                logger.info(f"WebSocket backtest mode change: {mode}")
                await websocket.send_json({
                    "type": "mode_changed",
                    "channel": "backtest",
                    "payload": {"mode": mode},
                })
    except WebSocketDisconnect:
        ws_hub.disconnect("backtest", websocket)
        logger.info("Backtest WebSocket disconnected")


@router.websocket("/orders")
async def websocket_orders(websocket: WebSocket) -> None:
    """订单实时推送WebSocket端点"""
    await ws_hub.connect("orders", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_hub.disconnect("orders", websocket)
        logger.info("Orders WebSocket disconnected")


@router.websocket("/risk")
async def websocket_risk(websocket: WebSocket) -> None:
    """风控实时推送WebSocket端点"""
    await ws_hub.connect("risk", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_hub.disconnect("risk", websocket)
        logger.info("Risk WebSocket disconnected")
