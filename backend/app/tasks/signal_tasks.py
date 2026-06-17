"""信号计算Celery异步任务

被market_tasks触发，调用SignalGenerator.generate()
结果通过WebSocket推送到前端
"""

from typing import Any, Dict, List

from loguru import logger

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.signal_tasks.generate_signals", bind=True, max_retries=2)
def generate_signals(self, bars_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """信号计算Celery异步任务

    被market_tasks触发，调用SignalGenerator.generate()生成交易信号。
    生成的信号通过WebSocket推送到前端。

    Args:
        bars_data: K线数据列表（序列化后的dict列表）

    Returns:
        Dict: 任务结果，包含生成的信号列表
    """
    logger.info(f"Signal task: generating signals for {len(bars_data)} bars")

    try:
        # 延迟导入避免循环依赖
        from app.services.signal.generator import SignalGenerator
        from app.services.signal.fusion import SignalFusion
        from app.services.tomas.token_bridge import TomasBridge
        from app.services.tomas.translator import Translator, EMLStore
        from app.services.tomas.writer import Writer

        # 创建服务实例
        eml_store = EMLStore()
        translator = Translator(eml_store=eml_store)
        writer = Writer()
        tomas_bridge = TomasBridge(translator=translator, writer=writer)
        fusion = SignalFusion()
        generator = SignalGenerator(tomas_bridge=tomas_bridge, fusion=fusion)

        # 异步调用需要使用asyncio
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

        signals = loop.run_until_complete(generator.generate(bars_data))
        signal_dicts = [s.to_dict() for s in signals]

        # 通过WebSocket推送信号到前端
        _push_signals_to_ws(signal_dicts)

        logger.info(f"Signal task: generated {len(signal_dicts)} signals")

        return {
            "status": "success",
            "signal_count": len(signal_dicts),
            "signals": signal_dicts,
        }

    except Exception as e:
        logger.error(f"Signal task error: {e}")
        # 重试机制
        try:
            raise self.retry(exc=e, countdown=5)
        except self.MaxRetriesExceededError:
            logger.error(f"Signal task failed after max retries: {e}")
            return {
                "status": "error",
                "signal_count": 0,
                "signals": [],
                "error": str(e),
            }


def _push_signals_to_ws(signals: List[Dict[str, Any]]) -> None:
    """通过WebSocket推送信号到前端

    Args:
        signals: 信号列表（字典格式）
    """
    try:
        # 延迟导入避免循环依赖
        from app.main import ws_hub

        import asyncio

        for signal in signals:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.ensure_future(
                        ws_hub.broadcast("signals", {
                            "type": "signal_generated",
                            "payload": signal,
                        })
                    )
                else:
                    loop.run_until_complete(
                        ws_hub.broadcast("signals", {
                            "type": "signal_generated",
                            "payload": signal,
                        })
                    )
            except RuntimeError:
                # 事件循环不可用，跳过WebSocket推送
                logger.debug("WebSocket push skipped: no event loop available")
                break

    except ImportError:
        logger.debug("WebSocket hub not available, skipping signal push")
    except Exception as e:
        logger.warning(f"WebSocket signal push error: {e}")
