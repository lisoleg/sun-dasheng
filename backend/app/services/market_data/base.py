"""行情数据提供商抽象基类 - 定义统一数据接入接口"""

from abc import ABC, abstractmethod
from typing import Callable, List

from app.schemas.market import BarResponse


class MarketDataProvider(ABC):
    """行情数据提供商抽象基类

    所有数据源（通达信、币安等）必须实现此接口，确保上层调用的一致性。
    """

    @abstractmethod
    async def connect(self) -> None:
        """建立与数据源的连接"""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """断开与数据源的连接"""
        ...

    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
    ) -> List[BarResponse]:
        """获取K线数据

        Args:
            symbol: 标的代码，如 sh600000, sz000001, BTCUSDT
            timeframe: 时间周期，如 1m/5m/15m/1h/4h/1d
            limit: 请求数据条数上限

        Returns:
            BarResponse列表
        """
        ...

    @abstractmethod
    async def subscribe(self, symbol: str, callback: Callable) -> None:
        """订阅实时行情数据

        Args:
            symbol: 标的代码
            callback: 数据回调函数，接收BarResponse参数
        """
        ...

    @abstractmethod
    async def unsubscribe(self, symbol: str) -> None:
        """取消实时行情订阅

        Args:
            symbol: 标的代码
        """
        ...
