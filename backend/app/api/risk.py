"""风控API端点骨架"""

import random
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.schemas.risk import RiskConfigUpdate

router = APIRouter()


# 内存中的模拟风控配置
_mock_risk_config: Dict[str, Any] = {
    "id": "risk-config-default",
    "name": "default",
    "symbol": "*",
    "market": "*",
    "max_position_pct": 0.1,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10,
    "max_drawdown_pct": 0.20,
    "trailing_stop_enabled": True,
    "trailing_stop_pct": 0.03,
    "is_active": True,
}


def _generate_mock_alerts(limit: int) -> List[Dict[str, Any]]:
    """生成模拟风控告警"""
    now = datetime.now(timezone.utc).isoformat()
    alert_types = ["STOP_LOSS", "TAKE_PROFIT", "DRAWDOWN", "POSITION_LIMIT"]
    severities = ["INFO", "WARNING", "CRITICAL"]
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    alerts = []
    for i in range(limit):
        alert_type = random.choice(alert_types)
        severity = "CRITICAL" if alert_type in ["STOP_LOSS", "DRAWDOWN"] else random.choice(severities)
        symbol = random.choice(symbols)

        messages = {
            "STOP_LOSS": f"{symbol} 止损触发，当前价格已低于止损线",
            "TAKE_PROFIT": f"{symbol} 止盈触发，当前价格已达到止盈目标",
            "DRAWDOWN": f"账户回撤已超过 {_mock_risk_config['max_drawdown_pct'] * 100}% 限制",
            "POSITION_LIMIT": f"{symbol} 仓位已超过 {_mock_risk_config['max_position_pct'] * 100}% 限制",
        }

        alerts.append({
            "id": f"alert-{i:06d}",
            "alert_type": alert_type,
            "symbol": symbol,
            "message": messages[alert_type],
            "severity": severity,
            "timestamp": now,
            "details": {
                "current_price": round(random.uniform(60000, 70000), 2),
                "threshold": round(random.uniform(58000, 62000), 2),
            },
        })

    return alerts


@router.get("/config")
async def get_risk_config() -> Dict[str, Any]:
    """获取风控配置"""
    return {
        "code": 0,
        "data": _mock_risk_config,
        "message": "ok",
    }


@router.put("/config")
async def update_risk_config(config: RiskConfigUpdate) -> Dict[str, Any]:
    """更新风控配置"""
    update_data = config.model_dump(exclude_none=True)
    _mock_risk_config.update(update_data)
    return {
        "code": 0,
        "data": _mock_risk_config,
        "message": "ok",
    }


@router.get("/alerts")
async def get_risk_alerts(
    severity: str = Query(None, description="筛选严重级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
) -> Dict[str, Any]:
    """获取风控告警"""
    alerts = _generate_mock_alerts(25)

    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]

    total = len(alerts)
    start = (page - 1) * page_size
    end = start + page_size
    items = alerts[start:end]

    return {
        "code": 0,
        "data": {
            "total": total,
            "items": items,
        },
        "message": "ok",
    }
