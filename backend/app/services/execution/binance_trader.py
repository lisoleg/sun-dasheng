"""币安交易执行器 - 使用python-binance库

核心功能：
- place_market_order: 市价下单
- place_limit_order: 限价下单
- cancel_order: 取消订单
- get_order_status: 查询订单状态
- get_account_balance: 查询账户余额

支持testnet模式，避免实盘误操作。
所有下单操作需记录日志。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.config import settings


@dataclass
class OrderResult:
    """订单执行结果"""

    order_id: str = ""
    symbol: str = ""
    side: str = ""  # BUY / SELL
    type: str = ""  # MARKET / LIMIT
    price: float = 0.0
    quantity: float = 0.0
    status: str = "PENDING"  # PENDING / FILLED / CANCELLED / REJECTED
    filled_price: float = 0.0
    filled_quantity: float = 0.0
    commission: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "type": self.type,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "filled_price": self.filled_price,
            "filled_quantity": self.filled_quantity,
            "commission": self.commission,
            "timestamp": self.timestamp,
        }


class BinanceTrader:
    """币安交易执行器

    使用python-binance库对接币安交易所，支持现货交易。
    支持testnet模式，所有下单操作记录日志。

    重要安全措施：
    - 默认启用testnet模式
    - API Key脱敏记录
    - 下单失败自动重试（3次指数退避）
    - 敏感信息不记录到DEBUG日志
    """

    MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: float = 1.0  # 基础重试延迟（秒）

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: Optional[bool] = None,
    ) -> None:
        """初始化币安交易执行器

        Args:
            api_key: 币安API Key，默认从配置读取
            api_secret: 币安API Secret，默认从配置读取
            testnet: 是否使用testnet，默认从配置读取
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.testnet = testnet if testnet is not None else settings.BINANCE_TESTNET
        self._client: Optional[Any] = None

        # 日志脱敏
        masked_key = f"{self.api_key[:4]}****" if len(self.api_key) > 4 else "****"
        logger.info(
            f"BinanceTrader initialized: testnet={self.testnet}, "
            f"api_key={masked_key}"
        )

    def _get_client(self) -> Any:
        """获取或创建币安客户端（延迟初始化）

        Returns:
            币安Client实例
        """
        if self._client is None:
            try:
                from binance.client import Client

                self._client = Client(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=self.testnet,
                )
                logger.info(
                    f"BinanceTrader client created: testnet={self.testnet}"
                )
            except ImportError:
                logger.error("python-binance not installed, BinanceTrader will not function")
                raise
        return self._client

    async def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> OrderResult:
        """市价下单

        Args:
            symbol: 交易对，如 "BTCUSDT"
            side: 买卖方向 "BUY" / "SELL"
            quantity: 下单数量

        Returns:
            OrderResult: 订单执行结果
        """
        logger.info(
            f"BinanceTrader: placing market order - "
            f"symbol={symbol}, side={side}, quantity={quantity}"
        )

        return await self._execute_with_retry(
            self._place_market_order_sync, symbol, side, quantity
        )

    async def place_limit_order(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> OrderResult:
        """限价下单

        Args:
            symbol: 交易对
            side: 买卖方向 "BUY" / "SELL"
            quantity: 下单数量
            price: 限价价格

        Returns:
            OrderResult: 订单执行结果
        """
        logger.info(
            f"BinanceTrader: placing limit order - "
            f"symbol={symbol}, side={side}, quantity={quantity}, price={price}"
        )

        return await self._execute_with_retry(
            self._place_limit_order_sync, symbol, side, quantity, price
        )

    async def cancel_order(self, symbol: str, order_id: str) -> OrderResult:
        """取消订单

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            OrderResult: 取消结果
        """
        logger.info(f"BinanceTrader: cancelling order - symbol={symbol}, order_id={order_id}")

        try:
            client = self._get_client()
            result = client.cancel_order(symbol=symbol, orderId=order_id)
            return self._parse_order_response(result, status="CANCELLED")
        except Exception as e:
            logger.error(f"BinanceTrader cancel order error: {e}")
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                status="REJECTED",
                error=str(e),
            )

    async def get_order_status(self, symbol: str, order_id: str) -> OrderResult:
        """查询订单状态

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            OrderResult: 订单状态
        """
        try:
            client = self._get_client()
            result = client.get_order(symbol=symbol, orderId=order_id)
            return self._parse_order_response(result)
        except Exception as e:
            logger.error(f"BinanceTrader get order status error: {e}")
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                status="REJECTED",
                error=str(e),
            )

    async def get_account_balance(self) -> Dict[str, Any]:
        """查询账户余额

        Returns:
            Dict: 账户余额信息
        """
        try:
            client = self._get_client()
            account = client.get_account()
            balances = [
                {
                    "asset": b["asset"],
                    "free": float(b["free"]),
                    "locked": float(b["locked"]),
                }
                for b in account.get("balances", [])
                if float(b["free"]) > 0 or float(b["locked"]) > 0
            ]
            # 不在DEBUG日志中记录具体余额
            logger.info(f"BinanceTrader: account balance retrieved, {len(balances)} assets")
            return {"balances": balances}
        except Exception as e:
            logger.error(f"BinanceTrader get account balance error: {e}")
            return {"balances": [], "error": str(e)}

    def _place_market_order_sync(
        self, symbol: str, side: str, quantity: float
    ) -> OrderResult:
        """同步市价下单

        Args:
            symbol: 交易对
            side: 买卖方向
            quantity: 下单数量

        Returns:
            OrderResult: 订单执行结果
        """
        client = self._get_client()
        result = client.order_market(symbol=symbol, side=side, quantity=quantity)
        return self._parse_order_response(result)

    def _place_limit_order_sync(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> OrderResult:
        """同步限价下单

        Args:
            symbol: 交易对
            side: 买卖方向
            quantity: 下单数量
            price: 限价价格

        Returns:
            OrderResult: 订单执行结果
        """
        client = self._get_client()
        result = client.order_limit(
            symbol=symbol, side=side, quantity=quantity, price=price
        )
        return self._parse_order_response(result)

    async def _execute_with_retry(self, func, *args, **kwargs) -> OrderResult:
        """带重试的执行器（指数退避）

        下单失败自动重试3次，3次失败后推送告警。

        Args:
            func: 同步执行函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            OrderResult: 执行结果
        """
        import asyncio

        last_error: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                # 在线程池中执行同步IO操作
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
                return result
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        f"BinanceTrader: attempt {attempt}/{self.MAX_RETRIES} failed: {e}, "
                        f"retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"BinanceTrader: all {self.MAX_RETRIES} attempts failed: {e}"
                    )

        return OrderResult(
            order_id="",
            status="REJECTED",
            error=f"Failed after {self.MAX_RETRIES} retries: {str(last_error)}",
        )

    @staticmethod
    def _parse_order_response(
        response: Dict[str, Any], status: Optional[str] = None
    ) -> OrderResult:
        """解析币安API订单响应

        Args:
            response: 币安API原始响应
            status: 覆盖状态（用于取消订单等场景）

        Returns:
            OrderResult: 标准化的订单结果
        """
        # 解析成交信息
        fills = response.get("fills", [])
        filled_price = 0.0
        filled_quantity = 0.0
        commission = 0.0

        if fills:
            total_qty = sum(float(f.get("qty", 0)) for f in fills)
            total_quote = sum(
                float(f.get("qty", 0)) * float(f.get("price", 0)) for f in fills
            )
            filled_quantity = total_qty
            filled_price = total_quote / total_qty if total_qty > 0 else 0.0
            commission = sum(float(f.get("commission", 0)) for f in fills)

        order_status = status or _map_binance_status(
            response.get("status", "NEW")
        )

        return OrderResult(
            order_id=str(response.get("orderId", "")),
            symbol=response.get("symbol", ""),
            side=response.get("side", ""),
            type=response.get("type", "MARKET"),
            price=float(response.get("price", 0) or 0),
            quantity=float(response.get("origQty", 0) or 0),
            status=order_status,
            filled_price=round(filled_price, 8),
            filled_quantity=round(filled_quantity, 8),
            commission=round(commission, 8),
            raw_response=response,
        )


def _map_binance_status(binance_status: str) -> str:
    """映射币安订单状态到系统状态

    Args:
        binance_status: 币安原始状态

    Returns:
        str: 系统状态
    """
    status_map = {
        "NEW": "PENDING",
        "PARTIALLY_FILLED": "PENDING",
        "FILLED": "FILLED",
        "CANCELED": "CANCELLED",
        "REJECTED": "REJECTED",
        "EXPIRED": "CANCELLED",
    }
    return status_map.get(binance_status, "PENDING")
