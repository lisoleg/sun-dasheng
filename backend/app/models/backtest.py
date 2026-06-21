"""回测配置与结果数据库模型 — BacktestRun / BacktestScan"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import Base, BaseMixin


class BacktestStatus(str, enum.Enum):
    """回测任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanStatus(str, enum.Enum):
    """参数扫描任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestRun(Base, BaseMixin):
    """回测任务记录表

    Attributes:
        backtest_id: 回测唯一标识(UUID)
        config: 完整回测配置(JSON)
        status: 任务状态
        progress: 进度百分比 0-100
        current_stage: 当前阶段
        started_at: 开始时间
        finished_at: 完成时间
        duration_seconds: 运行时长
        error_message: 错误信息
        result_summary: 结果摘要(JSON: metrics, equity_curve, trades_count)
        report_path: 报告文件路径
        csv_path: CSV交易明细路径
    """
    __tablename__ = "backtest_runs"

    backtest_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4())
    )
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[BacktestStatus] = mapped_column(
        SAEnum(BacktestStatus), default=BacktestStatus.PENDING, nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    report_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    csv_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class BacktestScan(Base, BaseMixin):
    """参数扫描任务记录表

    Attributes:
        scan_id: 扫描唯一标识(UUID)
        base_config: 基础回测配置(JSON)
        grid: 参数网格定义(JSON)
        total_jobs: 总任务数
        completed_jobs: 已完成任务数
        status: 任务状态
        best_params: 最优参数组合
        best_metrics: 最优参数对应的指标
        results: 扫描结果列表(JSON)
        started_at: 开始时间
        finished_at: 完成时间
    """
    __tablename__ = "backtest_scans"

    scan_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4())
    )
    base_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    grid: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ScanStatus] = mapped_column(
        SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False
    )
    best_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    best_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
