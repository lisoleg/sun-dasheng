"""通达信数据提供商 - 通过pytdx获取A股行情数据"""

import asyncio
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from loguru import logger

from app.schemas.market import BarResponse
from app.services.market_data.base import MarketDataProvider

# pytdx时间周期映射
TDX_TIMEFRAME_MAP: Dict[str, int] = {
    "5m": 0,    # 5分钟
    "15m": 1,   # 15分钟
    "30m": 2,   # 30分钟
    "1h": 3,    # 60分钟
    "1d": 4,    # 日线
    "1w": 5,    # 周线
    "1M": 6,    # 月线
}

# pytdx市场代码映射
TDX_MARKET_MAP: Dict[str, int] = {
    "sh": 1,  # 上海
    "sz": 0,  # 深圳
}

# 默认通达信服务器列表
TDX_SERVERS = [
    ("119.147.212.81", 7709),
    ("112.74.214.43", 7727),
    ("221.231.141.60", 7709),
    ("101.227.73.20", 7709),
    ("101.227.77.254", 7709),
    ("14.215.128.18", 7709),
    ("59.173.18.140", 7709),
]


class TdxProvider(MarketDataProvider):
    """通达信数据提供商

    使用pytdx库的ExtendedMarket类连接通达信服务器获取A股行情。
    A股不支持实时WebSocket订阅，使用定时轮询模拟。
    支持股票代码格式：sh600000, sz000001
    """

    def __init__(self) -> None:
        self._api = None
        self._connected: bool = False
        self._subscribed: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, Callable] = {}

    async def connect(self) -> None:
        """连接通达信服务器"""
        try:
            from pytdx.hq import TdxHq_API

            self._api = TdxHq_API()

            # 尝试连接服务器列表中的服务器
            connected = False
            for ip, port in TDX_SERVERS:
                try:
                    if self._api.connect(ip, port):
                        connected = True
                        logger.info(f"通达信连接成功: {ip}:{port}")
                        break
                except Exception as e:
                    logger.warning(f"通达信连接失败 {ip}:{port}: {e}")
                    continue

            if not connected:
                raise ConnectionError("无法连接任何通达信服务器")

            self._connected = True

        except ImportError:
            logger.error("pytdx未安装，请执行: pip install pytdx")
            raise

    async def disconnect(self) -> None:
        """断开通达信连接"""
        if self._api and self._connected:
            try:
                self._api.disconnect()
                logger.info("通达信连接已断开")
            except Exception as e:
                logger.warning(f"通达信断开连接异常: {e}")
            finally:
                self._connected = False
                self._api = None

        # 取消所有订阅任务
        for symbol, task in self._subscribed.items():
            task.cancel()
        self._subscribed.clear()
        self._callbacks.clear()

    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
    ) -> List[BarResponse]:
        """获取A股K线数据

        Args:
            symbol: 股票代码，格式 sh600000 或 sz000001
            timeframe: 时间周期
            limit: 数据条数
        """
        if not self._connected or not self._api:
            raise RuntimeError("通达信未连接，请先调用connect()")

        # 解析股票代码
        market_code, stock_code = self._parse_symbol(symbol)
        tdx_timeframe = TDX_TIMEFRAME_MAP.get(timeframe, 4)

        try:
            # pytdx获取K线数据（每次最多800条，需要分页）
            bars: List[BarResponse] = []
            remaining = limit
            start = 0

            while remaining > 0:
                batch_size = min(remaining, 800)
                # to_df返回DataFrame格式数据
                df = self._api.to_df(
                    self._api.get_kline(
                        market=market_code,
                        code=stock_code,
                        category=tdx_timeframe,
                        start=start,
                        count=batch_size,
                    )
                )

                if df is None or df.empty:
                    break

                for _, row in df.iterrows():
                    bar = BarResponse(
                        id=f"tdx-{symbol}-{row.get('datetime', '')}",
                        symbol=symbol,
                        market="a_share",
                        timeframe=timeframe,
                        timestamp=str(row.get("datetime", "")),
                        open=float(row.get("open", 0)),
                        high=float(row.get("high", 0)),
                        low=float(row.get("low", 0)),
                        close=float(row.get("close", 0)),
                        volume=float(row.get("vol", 0)),
                    )
                    bars.append(bar)

                fetched = len(df)
                if fetched < batch_size:
                    break
                remaining -= fetched
                start += fetched

            logger.info(f"通达信获取K线: {symbol} {timeframe} 共{len(bars)}条")
            return bars

        except Exception as e:
            logger.error(f"通达信获取K线失败: {symbol} - {e}")
            raise

    async def subscribe(self, symbol: str, callback: Callable) -> None:
        """订阅A股实时行情（通过定时轮询模拟）

        A股不支持WebSocket推送，使用5秒间隔轮询模拟实时数据。
        """
        if symbol in self._subscribed:
            logger.warning(f"已订阅 {symbol}，跳过重复订阅")
            return

        self._callbacks[symbol] = callback

        async def _poll_loop() -> None:
            """轮询循环"""
            while True:
                try:
                    bars = await self.get_bars(symbol, timeframe="1m", limit=1)
                    if bars and symbol in self._callbacks:
                        callback(bars[-1])
                except Exception as e:
                    logger.error(f"A股轮询异常 {symbol}: {e}")

                await asyncio.sleep(5)

        task = asyncio.create_task(_poll_loop())
        self._subscribed[symbol] = task
        logger.info(f"已订阅A股实时行情: {symbol} (轮询模式)")

    async def unsubscribe(self, symbol: str) -> None:
        """取消A股实时行情订阅"""
        if symbol in self._subscribed:
            self._subscribed[symbol].cancel()
            del self._subscribed[symbol]
        if symbol in self._callbacks:
            del self._callbacks[symbol]
        logger.info(f"已取消A股订阅: {symbol}")

    def _parse_symbol(self, symbol: str) -> tuple:
        """解析股票代码

        Args:
            symbol: 格式如 sh600000 或 sz000001

        Returns:
            (市场代码, 纯数字代码) 如 (1, "600000")
        """
        if len(symbol) < 8:
            raise ValueError(f"无效的A股代码格式: {symbol}，应为 sh600000 或 sz000001")

        prefix = symbol[:2].lower()
        code = symbol[2:]

        market_code = TDX_MARKET_MAP.get(prefix)
        if market_code is None:
            raise ValueError(f"无效的市场前缀: {prefix}，应为 sh 或 sz")

        return market_code, code
