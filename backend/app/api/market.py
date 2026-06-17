"""行情API端点 - 连接真实数据服务"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from loguru import logger

from app.config import settings
from app.services.market_data.tdx_provider import TdxProvider
from app.services.market_data.binance_provider import BinanceProvider

router = APIRouter()

# 延迟初始化的数据提供者实例
_tdx_provider: Optional[TdxProvider] = None
_binance_provider: Optional[BinanceProvider] = None


async def _get_tdx_provider() -> TdxProvider:
    """获取或创建通达信数据提供者（单例）"""
    global _tdx_provider
    if _tdx_provider is None:
        _tdx_provider = TdxProvider()
        await _tdx_provider.connect()
        logger.info("TdxProvider initialized")
    return _tdx_provider


async def _get_binance_provider() -> BinanceProvider:
    """获取或创建币安数据提供者（单例）"""
    global _binance_provider
    if _binance_provider is None:
        _binance_provider = BinanceProvider()
        await _binance_provider.connect()
        logger.info("BinanceProvider initialized")
    return _binance_provider


def _get_provider_for_symbol(symbol: str):
    """根据标的代码判断使用哪个数据提供者"""
    # 币安交易对：如 BTCUSDT, ETHUSDT
    if symbol.endswith("USDT") or symbol.endswith("BUSD") or symbol.endswith("USDC"):
        return "binance", _get_binance_provider()
    # 通达信股票代码：如 sh600000, sz000001, 000001.SZ, 600000.SH
    else:
        return "tdx", _get_tdx_provider()


@router.get("/bars")
async def get_bars(
    symbol: str = Query("BTCUSDT", description="标的代码"),
    timeframe: str = Query("1m", description="时间周期"),
    limit: int = Query(100, ge=1, le=1000, description="数据条数"),
) -> Dict[str, Any]:
    """获取K线数据 - 从真实数据源获取"""
    try:
        # 判断使用哪个数据提供者
        if symbol.endswith("USDT") or symbol.endswith("BUSD"):
            # 币安
            provider = await _get_binance_provider()
        else:
            # 通达信
            provider = await _get_tdx_provider()

        # 调用真实API获取数据
        bars_data = await provider.get_bars(symbol, timeframe, limit)

        # 转换为响应格式
        items = [
            {
                "id": f"bar-{i:06d}",
                "symbol": bar.symbol,
                "market": bar.market if hasattr(bar, "market") else ("crypto" if "USDT" in symbol else "a_share"),
                "timeframe": bar.timeframe,
                "timestamp": bar.timestamp.isoformat() if hasattr(bar.timestamp, "isoformat") else str(bar.timestamp),
                "open": round(float(bar.open), 2),
                "high": round(float(bar.high), 2),
                "low": round(float(bar.low), 2),
                "close": round(float(bar.close), 2),
                "volume": round(float(bar.volume), 4) if hasattr(bar, "volume") else 0.0,
            }
            for i, bar in enumerate(bars_data)
        ]

        logger.info(f"API /bars: symbol={symbol}, timeframe={timeframe}, limit={limit}, returned={len(items)}")
        return {
            "code": 0,
            "data": {
                "total": len(items),
                "items": items,
            },
            "message": "ok",
        }

    except Exception as e:
        logger.error(f"API /bars error: {e}")
        return {
            "code": 2001,
            "data": {"total": 0, "items": []},
            "message": f"行情数据获取失败: {str(e)}",
        }


@router.get("/symbols")
async def get_symbols(
    market: Optional[str] = Query(None, description="市场过滤：crypto/a_share"),
) -> Dict[str, Any]:
    """获取可用标的列表"""
    # 静态列表（实际生产环境应从数据库或配置文件读取）
    all_symbols = [
        {"symbol": "BTCUSDT", "market": "crypto", "name": "比特币/USDT", "status": "active"},
        {"symbol": "ETHUSDT", "market": "crypto", "name": "以太坊/USDT", "status": "active"},
        {"symbol": "BNBUSDT", "market": "crypto", "name": "币安币/USDT", "status": "active"},
        {"symbol": "000001.SZ", "market": "a_share", "name": "平安银行", "status": "active"},
        {"symbol": "600519.SH", "market": "a_share", "name": "贵州茅台", "status": "active"},
        {"symbol": "000858.SZ", "market": "a_share", "name": "五粮液", "status": "active"},
    ]

    # 按市场过滤
    if market:
        filtered = [s for s in all_symbols if s["market"] == market]
    else:
        filtered = all_symbols

    return {
        "code": 0,
        "data": {
            "total": len(filtered),
            "items": filtered,
        },
        "message": "ok",
    }


@router.on_event("shutdown")
async def _cleanup_providers():
    """应用关闭时清理资源"""
    global _tdx_provider, _binance_provider
    if _tdx_provider:
        await _tdx_provider.disconnect()
        logger.info("TdxProvider disconnected")
    if _binance_provider:
        await _binance_provider.disconnect()
        logger.info("BinanceProvider disconnected")
