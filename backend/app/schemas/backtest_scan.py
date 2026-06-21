"""参数扫描 Pydantic Schema"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.backtest import BacktestConfigSchema, PerformanceMetricsSchema


class ParameterGridSchema(BaseModel):
    """参数网格定义"""
    grid: Dict[str, List[float]] = Field(..., description="参数网格: {param_name: [values]}")


class ScanRequestSchema(BaseModel):
    """启动参数扫描请求"""
    base_config: BacktestConfigSchema = Field(..., description="基础回测配置")
    grid: Dict[str, List[float]] = Field(..., description="参数网格")


class ScanJobResult(BaseModel):
    """单个参数组合的回测结果"""
    params: Dict[str, float] = Field(..., description="参数组合")
    metrics: Dict[str, float] = Field(default_factory=dict, description="关键指标")


class ScanResultSchema(BaseModel):
    """参数扫描结果"""
    scan_id: str = Field(..., description="扫描ID")
    base_config: BacktestConfigSchema = Field(..., description="基础配置")
    grid: Dict[str, List[float]] = Field(..., description="参数网格")
    status: str = Field(..., description="状态: pending/running/completed/failed/cancelled")
    total_jobs: int = Field(default=0, description="总任务数")
    completed_jobs: int = Field(default=0, description="已完成任务数")
    results: List[ScanJobResult] = Field(default_factory=list, description="扫描结果列表")
    best_params: Optional[Dict[str, float]] = Field(default=None, description="最优参数")
    best_metrics: Optional[Dict[str, float]] = Field(default=None, description="最优指标")
    error_message: Optional[str] = Field(default=None, description="错误信息")
