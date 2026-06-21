"""基准收益计算 — benchmark

计算基准收益（沪深300/BTC/ETH），用于对比回测表现。
"""


from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from app.services.backtest.models import Bar


def calculate_benchmark_return(
    bars: List[Bar],
    start_date: datetime,
    end_date: datetime,
    benchmark: str = "btc",
) -> float:
    """计算基准收益

    Args:
        bars: K线数据列表（用于提取基准价格）
        start_date: 开始日期
        end_date: 结束日期
        benchmark: 基准类型 (csi300/btc/eth/none)

    Returns:
        基准收益率
    """
    if benchmark == "none" or not bars:
        return 0.0

    if len(bars) < 2:
        return 0.0

    # 使用回测数据的第一根和最后一根K线作为基准
    start_price = bars[0].close
    end_price = bars[-1].close

    benchmark_return = (end_price - start_price) / start_price if start_price > 0 else 0

    logger.info(
        f"Benchmark ({benchmark}): start={start_price:.2f}, "
        f"end={end_price:.2f}, return={benchmark_return:.2%}"
    )

    return benchmark_return


def get_benchmark_data(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str = "1d",
) -> List[Bar]:
    """获取基准K线数据

    Args:
        symbol: 基准标的代码
        start_date: 开始日期
        end_date: 结束日期
        timeframe: 周期

    Returns:
        基准K线数据列表
    """
    # 简化实现：返回空列表
    # 实际实现应从行情数据库加载基准数据
    logger.warning(f"get_benchmark_data: not implemented for {symbol}")
    return []
