"""Celery 异步回测任务 — backtest_tasks

定义回测相关的 Celery 异步任务：
1. run_backtest_task - 运行回测
2. run_parameter_scan_task - 参数扫描
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from celery import Task
from loguru import logger

from app.tasks.celery_app import celery_app
from app.services.backtest.engine import BacktestEngine
from app.services.backtest.models import BacktestConfig, BacktestResult
from app.services.backtest.repository import BacktestRepository
from app.services.backtest.metrics import MetricsCalculator


class BacktestTask(Task):
    """回测任务基类

    提供通用的任务状态更新和错误处理。
    """

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功完成时调用"""
        logger.info(f"BacktestTask: task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时调用"""
        logger.error(f"BacktestTask: task {task_id} failed: {exc}")
        # 更新数据库状态为 failed
        try:
            from app.database import async_session

            repository = BacktestRepository(async_session)
            import asyncio
            asyncio.run(repository.update_run_status(
                backtest_id=task_id,
                status="failed",
                result={"error": str(exc)},
            ))
        except Exception as e:
            logger.error(f"BacktestTask: failed to update status: {e}")


@celery_app.task(bind=True, base=BacktestTask)
def run_backtest_task(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Celery 异步回测任务

    执行完整的回测流程：
    1. 更新状态为 running
    2. 实例化 BacktestEngine
    3. 运行回测
    4. 计算绩效指标
    5. 保存结果到数据库
    6. 广播 WebSocket 完成消息

    Args:
        config_dict: 回测配置字典

    Returns:
        回测结果字典
    """
    task_id = self.request.id
    logger.info(f"run_backtest_task: started task {task_id}")

    try:
        # 1. 更新状态为 running
        import asyncio
        from app.database import async_session

        repository = BacktestRepository(async_session)
        asyncio.run(repository.update_run_status(
            backtest_id=task_id,
            status="running",
            progress=0.0,
        ))

        # 2. 实例化 BacktestEngine
        config = BacktestConfig(**config_dict)
        engine = BacktestEngine(config)

        # 3. 运行回测
        import asyncio
        result = asyncio.run(engine.run())

        # 4. 计算绩效指标
        calculator = MetricsCalculator()
        metrics = calculator.calculate(result)
        result.sharpe_ratio = metrics.get("sharpe_ratio", 0.0)
        result.sortino_ratio = metrics.get("sortino_ratio", 0.0)
        result.calmar_ratio = metrics.get("calmar_ratio", 0.0)
        result.annual_return = metrics.get("annualized_return", 0.0)
        result.profit_loss_ratio = metrics.get("profit_factor", 0.0)
        result.monthly_returns = metrics.get("monthly_returns", {})

        # 5. 保存结果到数据库
        result_dict = _result_to_dict(result)
        asyncio.run(repository.update_run_status(
            backtest_id=task_id,
            status="completed",
            progress=1.0,
            result=result_dict,
        ))

        # 保存交易明细
        if result.trades:
            trades_dict = [_trade_to_dict(t) for t in result.trades]
            asyncio.run(repository.save_trades(task_id, trades_dict))

        # 6. 广播 WebSocket 完成消息
        try:
            from app.api.ws import ws_hub

            asyncio.run(ws_hub.broadcast(
                f"backtest_{task_id}",
                {
                    "type": "backtest_complete",
                    "run_id": task_id,
                    "status": "completed",
                    "result": {
                        "total_return": result.total_return,
                        "sharpe_ratio": result.sharpe_ratio,
                        "max_drawdown": result.max_drawdown,
                        "total_trades": result.total_trades,
                    },
                },
            ))
        except Exception as e:
            logger.warning(f"run_backtest_task: WebSocket broadcast failed: {e}")

        logger.info(f"run_backtest_task: task {task_id} completed")
        return result_dict

    except Exception as e:
        logger.error(f"run_backtest_task: task {task_id} failed: {e}")
        # 更新状态为 failed
        try:
            from app.database import async_session

            repository = BacktestRepository(async_session)
            asyncio.run(repository.update_run_status(
                backtest_id=task_id,
                status="failed",
                result={"error": str(e)},
            ))
        except Exception as inner_e:
            logger.error(f"run_backtest_task: failed to update status: {inner_e}")

        raise


@celery_app.task(bind=True, base=BacktestTask)
def run_parameter_scan_task(
    self, config_base: Dict[str, Any], param_ranges: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Celery 异步参数扫描任务

    执行参数扫描：
    1. 生成所有参数组合
    2. 对每个组合运行回测
    3. 按优化目标排序
    4. 返回排序结果

    Args:
        config_base: 基础配置
        param_ranges: 参数范围

    Returns:
        扫描结果列表
    """
    task_id = self.request.id
    logger.info(f"run_parameter_scan_task: started task {task_id}")

    try:
        from itertools import product

        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        param_combos = list(product(*param_values))

        logger.info(
            f"run_parameter_scan_task: {len(param_combos)} parameter combinations"
        )

        # 运行回测（简化：串行执行，实际应使用 task chain）
        results = []
        for i, combo in enumerate(param_combos):
            params = dict(zip(param_names, combo))
            config_dict = config_base.copy()
            config_dict.update(params)

            # 运行回测
            config = BacktestConfig(**config_dict)
            engine = BacktestEngine(config)
            import asyncio
            result = asyncio.run(engine.run())

            # 计算指标
            calculator = MetricsCalculator()
            metrics = calculator.calculate(result)

            results.append(
                {
                    "params": params,
                    "metrics": metrics,
                    "result": _result_to_dict(result),
                }
            )

            # 更新进度
            progress = (i + 1) / len(param_combos)
            self.update_state(
                state="PROGRESS",
                meta={"current": i + 1, "total": len(param_combos), "progress": progress},
            )

        # 按夏普比率排序
        results.sort(key=lambda r: r["metrics"].get("sharpe_ratio", 0.0), reverse=True)

        logger.info(f"run_parameter_scan_task: task {task_id} completed")
        return results

    except Exception as e:
        logger.error(f"run_parameter_scan_task: task {task_id} failed: {e}")
        raise


def _result_to_dict(result: BacktestResult) -> Dict[str, Any]:
    """将 BacktestResult 转换为字典

    Args:
        result: 回测结果

    Returns:
        字典
    """
    return {
        "config": {
            "symbol": result.config.symbol,
            "market_type": result.config.market_type,
            "start_date": result.config.start_date,
            "end_date": result.config.end_date,
            "timeframe": result.config.timeframe,
            "initial_cash": result.config.initial_cash,
            "commission_rate": result.config.commission_rate,
            "fusion_strategy": result.config.fusion_strategy,
        },
        "total_return": result.total_return,
        "annual_return": result.annual_return,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "profit_loss_ratio": result.profit_loss_ratio,
        "calmar_ratio": result.calmar_ratio,
        "sortino_ratio": result.sortino_ratio,
        "total_trades": result.total_trades,
        "equity_curve": result.equity_curve,
        "drawdown_curve": result.drawdown_curve,
        "monthly_returns": result.monthly_returns,
        "benchmark_return": result.benchmark_return,
    }


def _trade_to_dict(trade: Any) -> Dict[str, Any]:
    """将 Trade 转换为字典

    Args:
        trade: 交易记录

    Returns:
        字典
    """
    return {
        "symbol": trade.symbol,
        "direction": trade.direction.value if hasattr(trade.direction, "value") else str(trade.direction),
        "open_time": trade.open_time.isoformat() if trade.open_time else None,
        "open_price": trade.open_price,
        "close_time": trade.close_time.isoformat() if trade.close_time else None,
        "close_price": trade.close_price,
        "quantity": trade.quantity,
        "pnl": trade.pnl,
        "pnl_pct": trade.pnl_pct,
        "signal_source": trade.signal_source,
        "theory_name": trade.theory_name,
        "confidence": trade.confidence,
        "exit_reason": trade.exit_reason,
    }
