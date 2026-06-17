"""币安数据提供商 - 通过python-binance获取加密货币行情数据"""

import asyncio
import json
from typing import Callable, Dict, List, Optional
from datetime import datetime, timezone

from loguru import logger

from app.schemas.market import BarResponse
from app.services.market_data.base import MarketDataProvider

# 币安K线间隔映射
BINANCE_INTERVAL_MAP: Dict[str, str] = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
    "3d": "3d",
    "1w": "1w",
    "1M": "1M",
}


class BinanceProvider(MarketDataProvider):
    """币安数据提供商

    使用python-binance库获取币安行情数据。
    支持REST API获取历史K线，以及WebSocket订阅实时行情。
    支持交易对格式：BTCUSDT, ETHUSDT
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._testnet = testnet
        self._client = None
        self._connected: bool = False
        self._ws_manager = None
        self._ws_connections: Dict[str, object] = {}
        self._callbacks: Dict[str, Callable] = {}

    async def connect(self) -> None:
        """连接币安API"""
        try:
            from binance.client import Client

            self._client = Client(
                api_key=self._api_key,
                api_secret=self._api_secret,
                testnet=self._testnet,
            )

            # 测试连接
            self._client.ping()
            self._connected = True
            mode = "测试网" if self._testnet else "主网"
            logger.info(f"币安连接成功 ({mode})")

        except ImportError:
            logger.error("python-binance未安装，请执行: pip install python-binance")
            raise
        except Exception as e:
            logger.error(f"币安连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开币安连接"""
        # 关闭所有WebSocket订阅
        for symbol in list(self._ws_connections.keys()):
            await self.unsubscribe(symbol)

        if self._client:
            try:
                self._client.close_connection()
            except Exception as e:
                logger.warning(f"币安断开连接异常: {e}")
            finally:
                self._connected = False
                self._client = None

        logger.info("币安连接已断开")

    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
    ) -> List[BarResponse]:
        """获取币安K线数据

        Args:
            symbol: 交易对，如 BTCUSDT, ETHUSDT
            timeframe: 时间周期
            limit: 数据条数
        """
        if not self._connected or not self._client:
            raise RuntimeError("币安未连接，请先调用connect()")

        interval = BINANCE_INTERVAL_MAP.get(timeframe, "1d")

        try:
            klines = self._client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
            )

            bars: List[BarResponse] = []
            for i, kline in enumerate(klines):
                # 币安K线数据格式:
                # [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, ...]
                open_time = kline[0]
                timestamp = datetime.fromtimestamp(
                    open_time / 1000.0, tz=timezone.utc
                ).isoformat()

                bar = BarResponse(
                    id=f"bn-{symbol}-{open_time}",
                    symbol=symbol,
                    market="crypto",
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                )
                bars.append(bar)

            logger.info(f"币安获取K线: {symbol} {timeframe} 共{len(bars)}条")
            return bars

        except Exception as e:
            logger.error(f"币安获取K线失败: {symbol} - {e}")
            raise

    async def subscribe(self, symbol: str, callback: Callable) -> None:
        """订阅币安实时行情（WebSocket）

        使用binance.websocket模块订阅K线更新。
        """
        if symbol in self._ws_connections:
            logger.warning(f"已订阅 {symbol}，跳过重复订阅")
            return

        self._callbacks[symbol] = callback

        try:
            from binance.websocket.spot.websocket_client import SpotWebsocketClient

            if self._ws_manager is None:
                self._ws_manager = SpotWebsocketClient()

            def _on_message(_, message: str) -> None:
                """WebSocket消息回调"""
                try:
                    data = json.loads(message)
                    # 处理kline格式的WebSocket消息
                    if "k" in data:
                        kline = data["k"]
                        timestamp = datetime.fromtimestamp(
                            kline["t"] / 1000.0, tz=timezone.utc
                        ).isoformat()

                        bar = BarResponse(
                            id=f"bn-{symbol}-{kline['t']}",
                            symbol=symbol,
                            market="crypto",
                            timeframe=kline.get("i", "1m"),
                            timestamp=timestamp,
                            open=float(kline["o"]),
                            high=float(kline["h"]),
                            low=float(kline["l"]),
                            close=float(kline["c"]),
                            volume=float(kline["v"]),
                        )

                        if symbol in self._callbacks:
                            self._callbacks[symbol](bar)
                except Exception as e:
                    logger.error(f"币安WebSocket消息处理异常: {e}")

            # 订阅K线流
            stream_name = f"{symbol.lower()}@kline_1m"
            self._ws_manager.kline(
                symbol=symbol.lower(),
                interval="1m",
                callback=_on_message,
            )
            self._ws_connections[symbol] = True
            logger.info(f"已订阅币安实时行情: {symbol} (WebSocket)")

        except ImportError:
            logger.warning("python-binance WebSocket模块不可用，降级为轮询模式")
            await self._subscribe_polling(symbol, callback)

        except Exception as e:
            logger.error(f"币安WebSocket订阅失败: {symbol} - {e}")
            await self._subscribe_polling(symbol, callback)

    async def unsubscribe(self, symbol: str) -> None:
        """取消币安实时行情订阅"""
        if symbol in self._ws_connections:
            del self._ws_connections[symbol]
        if symbol in self._callbacks:
            del self._callbacks[symbol]
        logger.info(f"已取消币安订阅: {symbol}")

    async def _subscribe_polling(self, symbol: str, callback: Callable) -> None:
        """降级轮询订阅模式（WebSocket不可用时使用）"""
        if symbol in self._ws_connections:
            return

        self._callbacks[symbol] = callback

        async def _poll_loop() -> None:
            """轮询循环"""
            while True:
                try:
                    bars = await self.get_bars(symbol, timeframe="1m", limit=1)
                    if bars and symbol in self._callbacks:
                        self._callbacks[symbol](bars[-1])
                except Exception as e:
                    logger.error(f"币安轮询异常 {symbol}: {e}")
                await asyncio.sleep(2)

        task = asyncio.create_task(_poll_loop())
        self._ws_connections[symbol] = task
        logger.info(f"已订阅币安实时行情: {symbol} (轮询降级模式)")
