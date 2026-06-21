"""绩效指标计算器 — MetricsCalculator

计算16项绩效指标（numpy向量化）。
"""

import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import BacktestResult, Trade


class MetricsCalculator:
    """16项绩效指标计算器

    指标列表：
    1. total_return - 总收益率
    2. annualized_return - 年化收益率
    3. sharpe_ratio - 夏普比率
    4. sortino_ratio - 索提诺比率
    5. calmar_ratio - 卡尔玛比率
    6. max_drawdown - 最大回撤
    7. max_drawdown_duration_days - 最大回撤持续天数
    8. win_rate - 胜率
    9. profit_factor - 盈亏比
    10. total_trades - 总交易次数
    11. avg_trade_return - 平均每笔收益
    12. avg_holding_period_hours - 平均持仓时长
    13. volatility - 年化波动率
    14. var_95 - 95% VaR
    15. cvar_95 - 95% CVaR
    16. benchmark_return - 基准收益率
    """

    def calculate(self, result: BacktestResult) -> Dict[str, float]:
        """计算所有绩效指标

        Args:
            result: 回测结果

        Returns:
            绩效指标字典
        """
        logger.info("MetricsCalculator: calculating performance metrics")

        metrics: Dict[str, float] = {}

        equity_curve = np.array(result.equity_curve) if result.equity_curve else np.array([])
        trades = result.trades

        # 1. 总收益率
        metrics["total_return"] = result.total_return

        # 2. 年化收益率
        metrics["annualized_return"] = self._calc_annualized_return(
            result.total_return, len(result.equity_curve)
        )

        # 3. 夏普比率
        returns = self._calc_daily_returns(equity_curve)
        metrics["sharpe_ratio"] = self._calc_sharpe_ratio(returns)

        # 4. 索提诺比率
        metrics["sortino_ratio"] = self._calc_sortino_ratio(returns)

        # 5. 卡尔玛比率
        metrics["calmar_ratio"] = self._calc_calmar_ratio(
            metrics["annualized_return"], result.max_drawdown
        )

        # 6. 最大回撤
        metrics["max_drawdown"] = result.max_drawdown

        # 7. 最大回撤持续天数
        metrics["max_drawdown_duration_days"] = self._calc_max_drawdown_duration(
            equity_curve, result.equity_curve
        )

        # 8. 胜率
        metrics["win_rate"] = result.win_rate

        # 9. 盈亏比
        metrics["profit_factor"] = self._calc_profit_factor(trades)

        # 10. 总交易次数
        metrics["total_trades"] = result.total_trades

        # 11. 平均每笔收益
        metrics["avg_trade_return"] = self._calc_avg_trade_return(trades)

        # 12. 平均持仓时长
        metrics["avg_holding_period_hours"] = self._calc_avg_holding_period(trades)

        # 13. 年化波动率
        metrics["volatility"] = self._calc_volatility(returns)

        # 14. 95% VaR
        metrics["var_95"] = self._calc_var(returns, 0.95)

        # 15. 95% CVaR
        metrics["cvar_95"] = self._calc_cvar(returns, 0.95)

        # 16. 基准收益率
        metrics["benchmark_return"] = result.benchmark_return or 0.0

        # 更新 result 对象
        result.sharpe_ratio = metrics["sharpe_ratio"]
        result.sortino_ratio = metrics["sortino_ratio"]
        result.calmar_ratio = metrics["calmar_ratio"]
        result.annual_return = metrics["annualized_return"]

        logger.info(
            f"MetricsCalculator: completed, "
            f"sharpe={metrics['sharpe_ratio']:.2f}, "
            f"sortino={metrics['sortino_ratio']:.2f}, "
            f"calmar={metrics['calmar_ratio']:.2f}"
        )

        return metrics

    def _calc_daily_returns(self, equity_curve: np.ndarray) -> np.ndarray:
        """计算日收益率序列

        Args:
            equity_curve: 权益曲线

        Returns:
            日收益率数组
        """
        if len(equity_curve) < 2:
            return np.array([])

        returns = np.diff(equity_curve) / equity_curve[:-1]
        return returns

    def _calc_annualized_return(self, total_return: float, num_bars: int) -> float:
        """计算年化收益率

        Args:
            total_return: 总收益率
            num_bars: K线数量（假设日线）

        Returns:
            年化收益率
        """
        if num_bars < 2:
            return 0.0

        # 假设252个交易日/年
        years = num_bars / 252.0
        if years > 0:
            annualized = (1 + total_return) ** (1 / years) - 1
        else:
            annualized = 0.0

        return annualized

    def _calc_sharpe_ratio(
        self, returns: np.ndarray, risk_free_rate: float = 0.0
    ) -> float:
        """计算夏普比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率

        Returns:
            夏普比率
        """
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / 252.0  # 日化无风险利率
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns, ddof=1)

        if std_return > 0:
            sharpe = (mean_return / std_return) * np.sqrt(252)
        else:
            sharpe = 0.0

        return sharpe

    def _calc_sortino_ratio(
        self, returns: np.ndarray, risk_free_rate: float = 0.0
    ) -> float:
        """计算索提诺比率

        仅使用下行偏差（负收益的标准差）

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率

        Returns:
            索提诺比率
        """
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / 252.0
        mean_return = np.mean(excess_returns)

        # 下行偏差
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = np.std(downside_returns, ddof=1)
        else:
            downside_deviation = 0.0

        if downside_deviation > 0:
            sortino = (mean_return / downside_deviation) * np.sqrt(252)
        else:
            sortino = 0.0

        return sortino

    def _calc_calmar_ratio(
        self, annualized_return: float, max_drawdown: float
    ) -> float:
        """计算卡尔玛比率

        Args:
            annualized_return: 年化收益率
            max_drawdown: 最大回撤（负数）

        Returns:
            卡尔玛比率
        """
        if max_drawdown < 0:
            calmar = annualized_return / abs(max_drawdown)
        else:
            calmar = 0.0

        return calmar

    def _calc_max_drawdown(self, equity: np.ndarray) -> float:
        """计算最大回撤

        Args:
            equity: 权益曲线

        Returns:
            最大回撤（负数）
        """
        if len(equity) < 2:
            return 0.0

        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_dd = float(np.min(drawdown))

        return max_dd

    def _calc_max_drawdown_duration(
        self, equity: np.ndarray, equity_curve: List[float]
    ) -> int:
        """计算最大回撤持续天数

        Args:
            equity: 权益数组
            equity_curve: 权益曲线（用于计算持续天数）

        Returns:
            最大回撤持续天数
        """
        if len(equity) < 2:
            return 0

        # 简化：返回0
        # 实际实现需要记录每个回撤的开始和结束时间
        return 0

    def _calc_profit_factor(self, trades: List[Trade]) -> float:
        """计算盈亏比

        Args:
            trades: 交易列表

        Returns:
            盈亏比（总盈利 / 总亏损）
        """
        if not trades:
            return 0.0

        total_profit = sum(t.pnl for t in trades if t.pnl and t.pnl > 0)
        total_loss = sum(abs(t.pnl) for t in trades if t.pnl and t.pnl < 0)

        if total_loss > 0:
            profit_factor = total_profit / total_loss
        else:
            profit_factor = float(len([t for t in trades if t.pnl and t.pnl > 0]))

        return profit_factor

    def _calc_avg_trade_return(self, trades: List[Trade]) -> float:
        """计算平均每笔收益

        Args:
            trades: 交易列表

        Returns:
            平均每笔收益（百分比）
        """
        if not trades:
            return 0.0

        returns = [t.pnl_pct for t in trades if t.pnl_pct is not None]
        if returns:
            return float(np.mean(returns))
        else:
            return 0.0

    def _calc_avg_holding_period(self, trades: List[Trade]) -> float:
        """计算平均持仓时长

        Args:
            trades: 交易列表

        Returns:
            平均持仓时长（小时）
        """
        if not trades:
            return 0.0

        hours = [t.holding_hours for t in trades if t.holding_hours is not None]
        if hours:
            return float(np.mean(hours))
        else:
            return 0.0

    def _calc_volatility(self, returns: np.ndarray) -> float:
        """计算年化波动率

        Args:
            returns: 收益率序列

        Returns:
            年化波动率
        """
        if len(returns) < 2:
            return 0.0

        daily_vol = np.std(returns, ddof=1)
        annual_vol = daily_vol * np.sqrt(252)

        return annual_vol

    def _calc_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """计算VaR（Value at Risk）

        Args:
            returns: 收益率序列
            confidence: 置信水平

        Returns:
            VaR（负数）
        """
        if len(returns) < 2:
            return 0.0

        var = float(np.percentile(returns, (1 - confidence) * 100))
        return var

    def _calc_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """计算CVaR（Conditional VaR）

        Args:
            returns: 收益率序列
            confidence: 置信水平

        Returns:
            CVaR（负数）
        """
        if len(returns) < 2:
            return 0.0

        var = self._calc_var(returns, confidence)
        cvar = float(np.mean(returns[returns <= var]))

        return cvar
