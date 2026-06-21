"""参数扫描优化器 — ParameterOptimizer

对参数网格进行批量回测，找出最优参数组合。
"""

from itertools import product
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import BacktestConfig, BacktestResult
from app.services.backtest.engine import BacktestEngine


class ParameterOptimizer:
    """参数扫描优化器

    功能：
    1. 生成参数网格的所有组合
    2. 对每组参数运行回测
    3. 按优化目标排序
    4. 返回最优参数组合
    """

    def __init__(
        self,
        optimization_target: str = "sharpe_ratio",
    ) -> None:
        """初始化参数优化器

        Args:
            optimization_target: 优化目标 (sharpe_ratio / total_return / max_drawdown)
        """
        self.optimization_target = optimization_target

    async def grid_search(
        self,
        config_base: BacktestConfig,
        param_ranges: Dict[str, List[float]],
        max_combinations: int = 1000,
    ) -> List[Dict[str, Any]]:
        """网格搜索

        Args:
            config_base: 基础回测配置
            param_ranges: 参数范围 {param_name: [values]}
            max_combinations: 最大参数组合数

        Returns:
            按优化目标排序的结果列表
        """
        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        all_combos = list(product(*param_values))

        # 限制组合数
        if len(all_combos) > max_combinations:
            logger.warning(
                f"ParameterOptimizer: {len(all_combos)} combinations exceed "
                f"limit {max_combinations}, truncating"
            )
            all_combos = all_combos[:max_combinations]

        logger.info(
            f"ParameterOptimizer: starting grid search with {len(all_combos)} combinations, "
            f"target={self.optimization_target}"
        )

        results = []
        for i, combo in enumerate(all_combos):
            params = dict(zip(param_names, combo))

            # 创建配置副本
            config = self._apply_params(config_base, params)

            # 运行回测
            engine = BacktestEngine(config)
            result = await engine.run()

            # 收集结果
            result_item = {
                "params": params,
                "metrics": {
                    "sharpe_ratio": result.sharpe_ratio,
                    "total_return": result.total_return,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades,
                },
            }
            results.append(result_item)

            # 进度日志
            if (i + 1) % 10 == 0:
                logger.info(
                    f"ParameterOptimizer: completed {i + 1}/{len(all_combos)} combinations"
                )

        # 排序
        results.sort(
            key=lambda r: r["metrics"].get(self.optimization_target, 0),
            reverse=True,
        )

        logger.info(
            f"ParameterOptimizer: completed, "
            f"best {self.optimization_target} = "
            f"{results[0]['metrics'].get(self.optimization_target, 0):.4f}"
        )

        return results

    def _apply_params(
        self, config: BacktestConfig, params: Dict[str, Any]
    ) -> BacktestConfig:
        """将参数应用到配置

        Args:
            config: 原配置
            params: 参数字典

        Returns:
            新配置
        """
        # 创建新配置（简化：直接修改原配置）
        import copy

        new_config = copy.deepcopy(config)

        for key, value in params.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)

        return new_config
