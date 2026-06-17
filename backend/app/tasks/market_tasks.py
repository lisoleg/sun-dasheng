"""行情采集定时任务 - Celery Beat调度"""

import asyncio
from datetime import datetime, timezone

from loguru import logger

from app.tasks.celery_app import celery_app


@celery_app.task(
    name="app.tasks.market_tasks.fetch_market_data",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def fetch_market_data(self) -> dict:
    """行情采集定时任务

    由Celery Beat每60秒触发（配置在celery_app.py的beat_schedule中）。
    调用MarketDataProvider获取最新K线数据，并触发信号计算任务。

    Returns:
        任务执行结果摘要
    """
    try:
        logger.info("开始行情采集任务...")

        # 使用事件循环执行异步代码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_fetch_and_process())
        finally:
            loop.close()

        logger.info(f"行情采集任务完成: {result}")
        return result

    except Exception as exc:
        logger.error(f"行情采集任务失败: {exc}")
        # 重试
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("行情采集任务重试次数已达上限")
            return {"status": "failed", "error": str(exc)}


async def _fetch_and_process() -> dict:
    """异步执行行情采集和信号处理

    1. 从配置中获取监控标的列表
    2. 连接数据提供商获取最新K线
    3. 调用理论引擎计算信号
    4. 广播信号到WebSocket客户端
    """
    from app.config import settings
    from app.services.market_data.binance_provider import BinanceProvider
    from app.services.market_data.tdx_provider import TdxProvider
    from app.services.theory.taiji import TaijiEngine
    from app.services.theory.spiral import SpiralEngine
    from app.services.theory.elliott_wave import ElliottWaveEngine

    symbols = [s.strip() for s in settings.MARKET_SYMBOLS.split(",") if s.strip()]
    results: list = []

    # 初始化理论引擎
    taiji_engine = TaijiEngine()
    spiral_engine = SpiralEngine()
    elliott_engine = ElliottWaveEngine()

    for symbol in symbols:
        try:
            # 判断市场类型
            if symbol.endswith("USDT") or symbol.endswith("BUSD"):
                provider = BinanceProvider(
                    api_key=settings.BINANCE_API_KEY,
                    api_secret=settings.BINANCE_API_SECRET,
                    testnet=settings.BINANCE_TESTNET,
                )
                market = "crypto"
            else:
                provider = TdxProvider()
                market = "a_share"

            # 连接数据提供商
            await provider.connect()

            try:
                # 获取K线数据
                bars = await provider.get_bars(symbol=symbol, timeframe="1d", limit=200)

                if not bars:
                    results.append({
                        "symbol": symbol,
                        "status": "no_data",
                        "bar_count": 0,
                    })
                    continue

                # 转换为字典列表供理论引擎使用
                bars_dict = [bar.model_dump() for bar in bars]

                # 执行理论分析
                signals = []

                # 太极中心律分析
                taiji_result = taiji_engine.analyze(bars_dict)
                if taiji_result.hints:
                    for hint in taiji_result.hints:
                        signals.append({
                            "symbol": symbol,
                            "market": market,
                            "direction": hint.get("direction", "HOLD").upper(),
                            "confidence": hint.get("confidence", 0.0),
                            "source_engine": "taiji",
                            "theory_name": taiji_engine.name,
                            "description": hint.get("description", ""),
                        })

                # 螺旋律分析
                spiral_result = spiral_engine.analyze(bars_dict)
                if spiral_result.hints:
                    for hint in spiral_result.hints:
                        signals.append({
                            "symbol": symbol,
                            "market": market,
                            "direction": hint.get("direction", "HOLD").upper(),
                            "confidence": hint.get("confidence", 0.0),
                            "source_engine": "spiral",
                            "theory_name": spiral_engine.name,
                            "description": hint.get("description", ""),
                        })

                # 波浪理论分析
                elliott_result = elliott_engine.analyze(bars_dict)
                if elliott_result.hints:
                    for hint in elliott_result.hints:
                        signals.append({
                            "symbol": symbol,
                            "market": market,
                            "direction": hint.get("direction", "HOLD").upper(),
                            "confidence": hint.get("confidence", 0.0),
                            "source_engine": "elliott",
                            "theory_name": elliott_engine.name,
                            "description": hint.get("description", ""),
                        })

                results.append({
                    "symbol": symbol,
                    "market": market,
                    "status": "success",
                    "bar_count": len(bars),
                    "signal_count": len(signals),
                    "signals": signals[:10],  # 只返回前10个信号
                })

                # 广播信号到WebSocket
                if signals:
                    await _broadcast_signals(signals)

            finally:
                await provider.disconnect()

        except Exception as e:
            logger.error(f"行情采集异常 {symbol}: {e}")
            results.append({
                "symbol": symbol,
                "status": "error",
                "error": str(e),
            })

    return {
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol_count": len(symbols),
        "results": results,
    }


async def _broadcast_signals(signals: list) -> None:
    """将信号广播到WebSocket客户端"""
    try:
        from app.main import ws_hub

        for signal in signals:
            await ws_hub.broadcast("signals", {
                "type": "signal_generated",
                "payload": signal,
            })
    except Exception as e:
        logger.warning(f"WebSocket广播信号失败: {e}")
