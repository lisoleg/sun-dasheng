"""回测 API 路由 — 启动/查询/历史/删除回测，参数扫描"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.backtest import BacktestRun, BacktestScan
from app.schemas.backtest import (
    BacktestConfigSchema,
    BacktestResultSchema,
    BacktestRunRequest,
    BacktestHistoryResponse,
    BacktestProgressSchema,
)
from app.schemas.backtest_scan import ScanRequestSchema, ScanResultSchema

router = APIRouter()


@router.post("/run", response_model=Dict[str, Any], tags=["回测"])
async def start_backtest(
    request: BacktestRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """启动回测（异步）

    创建回测任务并记录到数据库，返回 backtest_id。
    实际回测在后台任务中执行。
    """
    backtest_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    run = BacktestRun(
        backtest_id=backtest_id,
        config=request.config.model_dump(),
        status="pending",
        progress=0.0,
        started_at=now,
    )
    db.add(run)
    await db.commit()

    # 启动后台回测任务
    background_tasks.add_task(_run_backtest_task, backtest_id, request.config.model_dump())

    return {
        "code": 0,
        "data": {"backtest_id": backtest_id, "status": "pending"},
        "message": "回测任务已创建",
    }


@router.get("/{backtest_id}", response_model=Dict[str, Any], tags=["回测"])
async def get_backtest_result(
    backtest_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取回测结果"""
    result = await db.get(BacktestRun, backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    return {
        "code": 0,
        "data": {
            "backtest_id": result.backtest_id,
            "status": result.status,
            "progress": result.progress,
            "current_stage": result.current_stage,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "finished_at": result.finished_at.isoformat() if result.finished_at else None,
            "duration_seconds": result.duration_seconds,
            "error_message": result.error_message,
            "result_summary": result.result_summary,
            "report_path": result.report_path,
            "csv_path": result.csv_path,
        },
        "message": "ok",
    }


@router.get("/{backtest_id}/progress", response_model=Dict[str, Any], tags=["回测"])
async def get_backtest_progress(
    backtest_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取回测进度"""
    result = await db.get(BacktestRun, backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    return {
        "code": 0,
        "data": {
            "backtest_id": result.backtest_id,
            "status": result.status,
            "progress": result.progress,
            "current_stage": result.current_stage or "initializing",
        },
        "message": "ok",
    }


@router.get("/history", response_model=Dict[str, Any], tags=["回测"])
async def list_backtest_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取回测历史列表"""
    from sqlalchemy import select, func

    offset = (page - 1) * page_size
    stmt = (
        select(BacktestRun)
        .order_by(BacktestRun.started_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    runs = result.scalars().all()

    count_stmt = select(func.count()).select_from(BacktestRun)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    items = [
        {
            "backtest_id": r.backtest_id,
            "symbol": r.config.get("symbol", ""),
            "market": r.config.get("market", ""),
            "timeframe": r.config.get("timeframe", ""),
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "status": r.status,
            "total_return": r.result_summary.get("total_return") if r.result_summary else None,
            "sharpe_ratio": r.result_summary.get("sharpe_ratio") if r.result_summary else None,
            "max_drawdown": r.result_summary.get("max_drawdown") if r.result_summary else None,
            "total_trades": r.result_summary.get("total_trades") if r.result_summary else None,
        }
        for r in runs
    ]

    return {
        "code": 0,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": "ok",
    }


@router.delete("/{backtest_id}", response_model=Dict[str, Any], tags=["回测"])
async def delete_backtest_run(
    backtest_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """删除回测任务"""
    result = await db.get(BacktestRun, backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    await db.delete(result)
    await db.commit()

    return {
        "code": 0,
        "data": {"backtest_id": backtest_id},
        "message": "回测任务已删除",
    }


@router.post("/scan", response_model=Dict[str, Any], tags=["参数扫描"])
async def start_parameter_scan(
    request: ScanRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """启动参数扫描（异步）

    对参数网格进行批量回测，找出最优参数组合。
    """
    scan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # 计算总任务数
    import math
    from itertools import product

    grid = request.grid
    total_jobs = 1
    for values in grid.values():
        total_jobs *= len(values)

    scan = BacktestScan(
        scan_id=scan_id,
        base_config=request.base_config.model_dump(),
        grid=grid,
        total_jobs=total_jobs,
        completed_jobs=0,
        status="pending",
        started_at=now,
    )
    db.add(scan)
    await db.commit()

    # 启动后台扫描任务
    background_tasks.add_task(
        _run_scan_task, scan_id, request.base_config.model_dump(), grid
    )

    return {
        "code": 0,
        "data": {"scan_id": scan_id, "status": "pending", "total_jobs": total_jobs},
        "message": "参数扫描任务已创建",
    }


@router.get("/scan/{scan_id}", response_model=Dict[str, Any], tags=["参数扫描"])
async def get_scan_result(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取参数扫描结果"""
    result = await db.get(BacktestScan, scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="扫描任务不存在")

    return {
        "code": 0,
        "data": {
            "scan_id": result.scan_id,
            "status": result.status,
            "total_jobs": result.total_jobs,
            "completed_jobs": result.completed_jobs,
            "progress": result.completed_jobs / max(result.total_jobs, 1) * 100,
            "best_params": result.best_params,
            "best_metrics": result.best_metrics,
            "results": result.results,
            "error_message": result.error_message,
        },
        "message": "ok",
    }


# ============ 后台任务 ============


async def _run_backtest_task(backtest_id: str, config_dict: Dict[str, Any]) -> None:
    """后台回测任务

    简化实现：直接更新状态为 completed，生成模拟结果。
    完整实现需要调用 BacktestEngine。
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        run = await db.get(BacktestRun, backtest_id)
        if not run:
            return

        try:
            # 更新状态为运行中
            run.status = "running"
            run.current_stage = "computing_signals"
            run.progress = 10.0
            await db.commit()

            # TODO: 调用完整回测引擎
            # from app.services.backtest.engine import BacktestEngine
            # engine = BacktestEngine(BacktestConfigSchema(**config_dict))
            # result = await engine.run()

            # 模拟回测过程
            import asyncio

            await asyncio.sleep(1)

            run.current_stage = "calculating_metrics"
            run.progress = 80.0
            await db.commit()

            await asyncio.sleep(0.5)

            # 更新完成状态
            run.status = "completed"
            run.progress = 100.0
            run.current_stage = "finished"
            run.finished_at = datetime.now(timezone.utc)
            run.result_summary = {
                "total_return": 0.25,
                "annualized_return": 0.12,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.08,
                "win_rate": 0.58,
                "total_trades": 42,
            }
            await db.commit()

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            await db.commit()
        finally:
            await engine.dispose()


async def _run_scan_task(
    scan_id: str, base_config: Dict[str, Any], grid: Dict[str, List[float]]
) -> None:
    """后台参数扫描任务

    简化实现：生成模拟扫描结果。
    完整实现需要调用 ParameterOptimizer。
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.config import settings
    import asyncio

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        scan = await db.get(BacktestScan, scan_id)
        if not scan:
            return

        try:
            scan.status = "running"
            await db.commit()

            # 模拟扫描过程
            import itertools

            param_names = list(grid.keys())
            param_values = list(grid.values())
            combinations = list(itertools.product(*param_values))

            results = []
            for i, combo in enumerate(combinations):
                params = dict(zip(param_names, combo))
                # 模拟每次回测结果
                import random

                metrics = {
                    "sharpe_ratio": random.uniform(0.5, 2.5),
                    "total_return": random.uniform(-0.1, 0.5),
                }
                results.append({"params": params, "metrics": metrics})
                scan.completed_jobs = i + 1
                scan.progress = (i + 1) / len(combinations) * 100
                await db.commit()
                await asyncio.sleep(0.1)

            # 找出最优参数
            best = max(results, key=lambda x: x["metrics"].get("sharpe_ratio", 0))
            scan.best_params = best["params"]
            scan.best_metrics = best["metrics"]
            scan.results = {"items": results[:100]}  # 限制返回数量
            scan.status = "completed"
            scan.finished_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            await db.commit()
        finally:
            await engine.dispose()
