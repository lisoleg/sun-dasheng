"""回测引擎数据模型 — 纯内存对象（不用SQLAlchemy）"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Direction(Enum):
    """交易方向"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """订单类型"""
    MARKET = "MARKET"  # 市价单
    LIMIT = "LIMIT"  # 限价单
    STOP = "STOP"    # 止损单


@dataclass
class Bar:
    """K线数据"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = ""


@dataclass
class Order:
    """订单"""
    id: str
    bar_index: int
    symbol: str
    direction: Direction
    order_type: OrderType = OrderType.MARKET
    price: float = 0.0  # 限价单价格
    quantity: float = 0.0
    signal_source: str = ""
    theory_name: Optional[str] = None
    confidence: float = 0.0


@dataclass
class Fill:
    """成交记录"""
    order_id: str
    bar_index: int
    fill_price: float
    fill_quantity: float
    commission: float
    timestamp: datetime


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: float  # 正=多仓，负=空仓（A股仅正向）
    avg_cost: float
    unrealized_pnl: float = 0.0

    def update_market_value(self, current_price: float) -> None:
        """更新持仓市值和浮动盈亏"""
        self.unrealized_pnl = (current_price - self.avg_cost) * self.quantity


@dataclass
class Portfolio:
    """资金账户"""
    cash: float
    initial_cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    equity: float = 0.0
    max_equity: float = 0.0
    max_drawdown_pct: float = 0.0
    trades: List["Trade"] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        """初始化后计算初始权益"""
        if self.equity == 0.0:
            self.equity = self.cash
        if self.max_equity == 0.0:
            self.max_equity = self.cash

    def mark_to_market(self, current_bars: Dict[str, Bar]) -> None:
        """标记持仓市值"""
        total_position_value = 0.0
        for symbol, position in self.positions.items():
            if symbol in current_bars:
                current_price = current_bars[symbol].close
                position.update_market_value(current_price)
                total_position_value += position.quantity * current_price

        self.equity = self.cash + total_position_value

        # 更新最大权益和回撤
        if self.equity > self.max_equity:
            self.max_equity = self.equity

        if self.max_equity > 0:
            current_drawdown = (self.equity - self.max_equity) / self.max_equity
            if current_drawdown < self.max_drawdown_pct:
                self.max_drawdown_pct = current_drawdown

        # 记录权益曲线
        self.equity_curve.append(self.equity)
        self.drawdown_curve.append(self.max_drawdown_pct)


@dataclass
class Trade:
    """已完成交易"""
    trade_id: str
    symbol: str
    direction: Direction  # 开仓方向
    open_time: datetime
    open_price: float
    close_time: Optional[datetime] = None
    close_price: Optional[float] = None
    quantity: float = 0.0
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    holding_hours: Optional[float] = None
    signal_source: str = ""
    theory_name: Optional[str] = None
    confidence: float = 0.0
    exit_reason: str = ""  # SIGNAL / STOP_LOSS / TAKE_PROFIT / END_OF_DATA


@dataclass
class BacktestConfig:
    """回测配置"""
    symbol: str = ""
    market_type: str = "crypto"  # a-stock / crypto
    start_date: str = ""
    end_date: str = ""
    timeframe: str = "1d"
    initial_cash: float = 100000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_bps: float = 5.0  # 5 bps = 0.05%
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_position_pct: float = 0.3  # 单笔最大仓位30%
    theory_weights: Dict[str, float] = field(default_factory=dict)
    fusion_strategy: str = "weighted"  # weighted / and / or
    position_sizing: str = "fixed_pct"  # fixed_pct / fixed_amount / kelly / risk_parity


@dataclass
class BacktestResult:
    """回测结果"""
    config: BacktestConfig = field(default_factory=BacktestConfig)
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    total_trades: int = 0
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    monthly_returns: Dict[str, float] = field(default_factory=dict)
    benchmark_return: Optional[float] = None
