"""回测 Pydantic Schema — BacktestConfig / Result / Trade / Progress"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestConfigSchema(BaseModel):
    """回测配置 Schema（对齐 PRD §5.2）"""
    market: str = Field(..., description="市场: a-stock / binance")
    symbol: str = Field(..., description="标的代码: BTCUSDT / 000001.SZ")
    timeframe: str = Field(..., description="周期: 1m/5m/15m/30m/1h/4h/1d/1w")
    start_date: str = Field(..., description="开始日期 ISO 8601")
    end_date: str = Field(..., description="结束日期 ISO 8601")
    initial_capital: float = Field(..., gt=0, description="初始资金")
    commission_rate: float = Field(default=0.001, ge=0, description="手续费率")
    slippage_rate: float = Field(default=0.0005, ge=0, description="滑点率")
    position_sizing: str = Field(default="fixed_pct", description="仓位规则: fixed_pct/fixed_amount/kelly/risk_parity")
    position_value: float = Field(default=0.1, gt=0, description="仓位大小")
    max_position_pct: float = Field(default=0.3, ge=0, le=1, description="单笔最大仓位")
    enabled_theories: List[str] = Field(default_factory=lambda: ["taiji", "spiral", "elliott"], description="启用的理论模块")
    signal_fusion: str = Field(default="weighted", description="信号融合策略: AND/OR/weighted")
    theory_weights: Optional[Dict[str, float]] = Field(default=None, description="各理论权重")
    benchmark: str = Field(default="btc", description="基准: csi300/btc/eth/none")
    stop_loss_pct: Optional[float] = Field(default=None, ge=0, description="固定止损比例")
    take_profit_pct: Optional[float] = Field(default=None, ge=0, description="固定止盈比例")
    trailing_stop_pct: Optional[float] = Field(default=None, ge=0, description="追踪止损比例")
    allow_short: bool = Field(default=False, description="是否允许做空")
    reinvest_profits: bool = Field(default=True, description="盈利再投资")
    parameter_grid: Optional[Dict[str, List[float]]] = Field(default=None, description="参数网格")


class PerformanceMetricsSchema(BaseModel):
    """绩效指标 Schema（16项，对齐 PRD §5.3）"""
    total_return: float = Field(default=0.0, description="总收益率")
    annualized_return: float = Field(default=0.0, description="年化收益率")
    sharpe_ratio: float = Field(default=0.0, description="夏普比率")
    sortino_ratio: float = Field(default=0.0, description="索提诺比率")
    calmar_ratio: float = Field(default=0.0, description="卡尔玛比率")
    max_drawdown: float = Field(default=0.0, description="最大回撤（负数）")
    max_drawdown_duration_days: int = Field(default=0, description="最大回撤持续天数")
    win_rate: float = Field(default=0.0, description="胜率")
    profit_factor: float = Field(default=0.0, description="盈亏比")
    total_trades: int = Field(default=0, description="总交易次数")
    avg_trade_return: float = Field(default=0.0, description="平均每笔收益")
    avg_holding_period_hours: float = Field(default=0.0, description="平均持仓时长")
    volatility: float = Field(default=0.0, description="年化波动率")
    var_95: float = Field(default=0.0, description="95% VaR")
    cvar_95: float = Field(default=0.0, description="95% CVaR")
    benchmark_return: Optional[float] = Field(default=None, description="基准收益率")


class EquityPointSchema(BaseModel):
    """权益曲线数据点"""
    timestamp: str = Field(..., description="时间戳 ISO 8601")
    equity: float = Field(..., description="总资产")
    benchmark_equity: float = Field(default=0.0, description="基准资产")
    drawdown: float = Field(default=0.0, description="回撤")


class MonthlyReturnSchema(BaseModel):
    """月度收益率"""
    year: int = Field(..., description="年份")
    month: int = Field(..., ge=1, le=12, description="月份")
    return_value: float = Field(default=0.0, alias="return", description="收益率")


class BacktestTradeSchema(BaseModel):
    """回测交易明细 Schema"""
    trade_id: str = Field(..., description="交易ID")
    backtest_id: str = Field(..., description="回测ID")
    symbol: str = Field(..., description="标的")
    side: str = Field(..., description="方向: BUY/SELL")
    open_time: str = Field(..., description="开仓时间 ISO 8601")
    open_price: float = Field(..., description="开仓价格")
    close_time: Optional[str] = Field(default=None, description="平仓时间 ISO 8601")
    close_price: Optional[float] = Field(default=None, description="平仓价格")
    quantity: float = Field(..., description="数量")
    pnl: Optional[float] = Field(default=None, description="盈亏绝对值")
    pnl_pct: Optional[float] = Field(default=None, description="盈亏百分比")
    holding_hours: Optional[float] = Field(default=None, description="持仓时长")
    theory_tags: List[str] = Field(default_factory=list, description="触发的理论模块")
    confidence: float = Field(default=0.0, description="信号置信度")
    exit_reason: Optional[str] = Field(default=None, description="平仓原因")


class TheoryContributionSchema(BaseModel):
    """理论贡献度"""
    theory_name: str = Field(..., description="理论名称")
    signal_count: int = Field(default=0, description="触发信号数")
    winning_trades: int = Field(default=0, description="盈利交易数")
    contribution_pct: float = Field(default=0.0, description="贡献占比")


class BacktestResultSchema(BaseModel):
    """回测结果完整 Schema"""
    backtest_id: str = Field(..., description="回测ID")
    config: BacktestConfigSchema = Field(..., description="回测配置")
    status: str = Field(..., description="状态: pending/running/completed/failed/cancelled")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    finished_at: Optional[str] = Field(default=None, description="完成时间")
    duration_seconds: Optional[float] = Field(default=None, description="运行时长")
    progress: Optional[float] = Field(default=None, description="进度 0-100")
    current_stage: Optional[str] = Field(default=None, description="当前阶段")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    metrics: Optional[PerformanceMetricsSchema] = Field(default=None, description="绩效指标")
    equity_curve: List[EquityPointSchema] = Field(default_factory=list, description="权益曲线")
    monthly_returns: List[MonthlyReturnSchema] = Field(default_factory=list, description="月度收益")
    trades: List[BacktestTradeSchema] = Field(default_factory=list, description="交易明细")
    theory_contribution: List[TheoryContributionSchema] = Field(default_factory=list, description="理论贡献")


class BacktestProgressSchema(BaseModel):
    """回测进度 Schema（WebSocket 推送）"""
    backtest_id: str = Field(..., description="回测ID")
    task_id: Optional[str] = Field(default=None, description="Celery任务ID")
    status: str = Field(..., description="状态")
    progress: float = Field(default=0.0, description="进度 0-100")
    stage: str = Field(default="initializing", description="当前阶段")
    message: Optional[str] = Field(default=None, description="进度消息")
    current_bar: Optional[int] = Field(default=None, description="当前K线索引")
    total_bars: Optional[int] = Field(default=None, description="总K线数")


class BacktestRunRequest(BaseModel):
    """启动回测请求"""
    config: BacktestConfigSchema = Field(..., description="回测配置")


class BacktestHistoryResponse(BaseModel):
    """回测历史列表项"""
    backtest_id: str
    symbol: str
    market: str
    timeframe: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None


class BacktestCompareRequest(BaseModel):
    """回测对比请求"""
    backtest_ids: List[str] = Field(..., min_length=2, max_length=4, description="2-4个回测ID")


class BacktestTemplateSchema(BaseModel):
    """回测模板 Schema"""
    template_id: str = Field(default="", description="模板ID")
    name: str = Field(..., description="模板名称")
    config: BacktestConfigSchema = Field(..., description="回测配置")
    created_at: Optional[str] = None
