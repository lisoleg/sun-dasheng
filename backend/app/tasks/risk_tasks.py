"""风控检查Celery定时任务

每1秒触发，检查所有活跃持仓的止损/止盈。
触发止损/止盈时调用OrderManager紧急平仓。
推送风控告警到WebSocket。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from loguru import logger

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.risk_tasks.check_risk_positions", bind=True, max_retries=1)
def check_risk_positions(self) -> Dict[str, Any]:
    """风控检查Celery定时任务

    每1秒触发，检查所有活跃持仓的止损/止盈。
    触发止损/止盈时调用OrderManager紧急平仓。

    Returns:
        Dict: 风控检查报告
    """
    try:
        from app.services.risk.stop_loss import StopLossManager, StopCheckResult
        from app.services.execution.order_manager import OrderManager
        from app.services.execution.binance_trader import BinanceTrader

        # 创建服务实例
        stop_loss_mgr = StopLossManager()
        trader = BinanceTrader()
        order_manager = OrderManager(
            trader=trader,
            stop_loss_manager=stop_loss_mgr,
        )

        # 获取所有持仓
        positions = order_manager.get_positions()

        if not positions:
            return {
                "status": "success",
                "safe_count": 0,
                "triggered_count": 0,
                "alerts": [],
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

        safe_count = 0
        triggered_count = 0
        alerts: List[Dict[str, Any]] = []

        for position in positions:
            position_id = position.get("position_id", "")
            symbol = position.get("symbol", "")
            current_price = position.get("current_price", 0.0)
            entry_price = position.get("entry_price", 0.0)

            # 检查止损止盈
            check_result = stop_loss_mgr.check_stop_loss(position, current_price)

            if check_result == StopCheckResult.POSITION_SAFE:
                safe_count += 1

                # 更新追踪止损
                stop_config = stop_loss_mgr.get_stop_config(position_id)
                if stop_config and stop_config.stop_loss_type.value == "trailing":
                    atr_value = stop_config.atr_value
                    if atr_value > 0:
                        new_trailing = stop_loss_mgr.calculate_trailing_stop(
                            entry_price, atr_value
                        )
                        # 更新持仓止损价
                        position["stop_loss_price"] = new_trailing

            elif check_result == StopCheckResult.STOP_LOSS_TRIGGERED:
                triggered_count += 1
                alert = _create_alert(
                    position=position,
                    alert_type="STOP_LOSS",
                    message=f"{symbol} 止损触发，当前价格{current_price:.2f}已低于止损线",
                    severity="CRITICAL",
                )
                alerts.append(alert)

                # 紧急平仓
                _emergency_close_position(order_manager, position, "止损触发")

                # 推送告警
                _push_risk_alert(alert)

            elif check_result == StopCheckResult.TAKE_PROFIT_TRIGGERED:
                triggered_count += 1
                alert = _create_alert(
                    position=position,
                    alert_type="TAKE_PROFIT",
                    message=f"{symbol} 止盈触发，当前价格{current_price:.2f}已达到止盈目标",
                    severity="INFO",
                )
                alerts.append(alert)

                # 执行止盈
                _emergency_close_position(order_manager, position, "止盈触发")

                # 推送告警
                _push_risk_alert(alert)

        result = {
            "status": "success",
            "safe_count": safe_count,
            "triggered_count": triggered_count,
            "alerts": alerts,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        if triggered_count > 0:
            logger.warning(
                f"Risk check: {triggered_count} positions triggered, "
                f"{safe_count} safe"
            )
        else:
            logger.debug(f"Risk check: all {safe_count} positions safe")

        return result

    except Exception as e:
        logger.error(f"Risk check task error: {e}")
        # 风控异常时保守处理：不采取任何行动，保持现有止损
        return {
            "status": "error",
            "safe_count": 0,
            "triggered_count": 0,
            "alerts": [],
            "error": str(e),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def _create_alert(
    position: Dict[str, Any],
    alert_type: str,
    message: str,
    severity: str,
) -> Dict[str, Any]:
    """创建风控告警

    Args:
        position: 持仓信息
        alert_type: 告警类型
        message: 告警消息
        severity: 严重级别

    Returns:
        Dict: 告警数据
    """
    return {
        "alert_type": alert_type,
        "symbol": position.get("symbol", ""),
        "position_id": position.get("position_id", ""),
        "message": message,
        "severity": severity,
        "details": {
            "entry_price": position.get("entry_price", 0.0),
            "current_price": position.get("current_price", 0.0),
            "stop_loss_price": position.get("stop_loss_price", 0.0),
            "take_profit_price": position.get("take_profit_price", 0.0),
            "unrealized_pnl": position.get("unrealized_pnl", 0.0),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _emergency_close_position(
    order_manager: Any, position: Dict[str, Any], reason: str
) -> None:
    """紧急平仓

    Args:
        order_manager: 订单管理器
        position: 持仓信息
        reason: 平仓原因
    """
    import uuid

    symbol = position.get("symbol", "")
    quantity = abs(position.get("quantity", 0.0))
    position_id = position.get("position_id", "")

    if quantity <= 0:
        logger.warning(f"Emergency close: no quantity for position {position_id}")
        return

    # 判断平仓方向（反向操作）
    original_quantity = position.get("quantity", 0.0)
    close_side = "SELL" if original_quantity > 0 else "BUY"

    logger.critical(
        f"EMERGENCY CLOSE: {symbol} {close_side} {quantity} - reason: {reason}"
    )

    try:
        import asyncio

        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            order_manager.trader.place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=quantity,
            )
        )

        logger.info(
            f"Emergency close result: order_id={result.order_id}, "
            f"status={result.status}"
        )

    except Exception as e:
        logger.error(f"Emergency close failed: {e}")


def _push_risk_alert(alert: Dict[str, Any]) -> None:
    """推送风控告警到WebSocket

    Args:
        alert: 告警数据
    """
    try:
        from app.main import ws_hub

        import asyncio

        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    ws_hub.broadcast("signals", {
                        "type": "risk_alert",
                        "payload": alert,
                    })
                )
            else:
                loop.run_until_complete(
                    ws_hub.broadcast("signals", {
                        "type": "risk_alert",
                        "payload": alert,
                    })
                )
        except RuntimeError:
            logger.debug("WebSocket push skipped: no event loop available")

    except ImportError:
        logger.debug("WebSocket hub not available, skipping risk alert push")
    except Exception as e:
        logger.warning(f"Risk alert WebSocket push error: {e}")
