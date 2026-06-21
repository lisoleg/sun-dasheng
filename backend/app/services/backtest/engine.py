"""回测引擎入口 — BacktestEngine"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import Bar, BacktestConfig, BacktestResult
from app.services.backtest.event_loop import BacktestEventLoop
from app.services.theory.base import TheoryEngine
from app.services.theory import get_all_engines


class BacktestEngine:
    """回测引擎入口

    协调回测流程：
    1. 加载历史K线
    2. 初始化理论引擎
    3. 运行事件循环
    4. 计算绩效指标
    5. 保存结果
    """

    def __init__(self, config: BacktestConfig) -> None:
        """初始化回测引擎

        Args:
            config: 回测配置
        """
        self.config = config
        self._theories: List[TheoryEngine] = []

    async def run(self) -> BacktestResult:
        """运行回测

        Returns:
            回测结果
        """
        logger.info(
            f"BacktestEngine: starting backtest for {self.config.symbol} "
            f"({self.config.start_date} to {self.config.end_date})"
        )

        # 1. 加载历史K线
        bars = await self._load_bars()
        if not bars:
            logger.error("BacktestEngine: no bars loaded")
            return BacktestResult(config=self.config)

        logger.info(f"BacktestEngine: loaded {len(bars)} bars")

        # 2. 初始化理论引擎
        theories = self._init_theory_engines()
        logger.info(f"BacktestEngine: initialized {len(theories)} theory engines")

        # 3. 运行事件循环
        event_loop = BacktestEventLoop(self.config)
        result = event_loop.run(self.config, bars, theories)

        # 4. 计算绩效指标（需要导入 metrics 模块）
        try:
            from app.services.backtest.metrics import MetricsCalculator

            calculator = MetricsCalculator()
            metrics = calculator.calculate(result)
            result.sharpe_ratio = metrics.get("sharpe_ratio", 0.0)
            result.sortino_ratio = metrics.get("sortino_ratio", 0.0)
            result.calmar_ratio = metrics.get("calmar_ratio", 0.0)
            result.annual_return = metrics.get("annual_return", 0.0)
            result.profit_loss_ratio = metrics.get("profit_loss_ratio", 0.0)
            result.monthly_returns = metrics.get("monthly_returns", {})
        except ImportError:
            logger.warning("BacktestEngine: metrics module not available")

        # 5. 保存结果（简化：暂不持久化）
        # await self._save_result(result)

        logger.info(
            f"BacktestEngine: backtest completed, "
            f"total_return={result.total_return:.2%}, "
            f"sharpe={result.sharpe_ratio:.2f}, "
            f"max_drawdown={result.max_drawdown:.2%}"
        )

        return result

    async def _load_bars(self) -> List[Bar]:
        """加载历史K线数据

        简化实现：从数据库或CSV加载。
        实际实现需要连接行情数据源。

        Returns:
            K线数据列表
        """
        # 简化：返回模拟数据
        # 实际实现应该从数据库或文件加载
        logger.warning("BacktestEngine: using mock bar data")

        import random
        from datetime import timedelta

        bars = []
        start = datetime.fromisoformat(self.config.start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.config.end_date.replace("Z", "+00:00"))

        current = start
        price = 50000.0  # 模拟BTC价格

        while current <= end:
            # 生成随机K线
            change = random.uniform(-0.02, 0.02)
            open_price = price
            close_price = price * (1 + change)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))

            bar = Bar(
                timestamp=current,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=random.uniform(100, 1000),
                symbol=self.config.symbol,
            )
            bars.append(bar)

            price = close_price
            current += timedelta(days=1)  # 假设日线

        return bars

    def _init_theory_engines(self) -> List[TheoryEngine]:
        """初始化理论引擎

        Returns:
            理论引擎列表
        """
        if self._theories:
            return self._theories

        # 获取所有启用的理论引擎
        all_engines = get_all_engines()

        # 如果配置了启用的理论，则过滤
        if self.config.theory_weights:
            enabled_theories = self.config.theory_weights.keys()
            all_engines = [
                e for e in all_engines
                if hasattr(e, "theory_name") and e.theory_name in enabled_theories
            ]

        self._theories = all_engines
        return all_engines
