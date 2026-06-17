/**
 * Mock数据工具 - 为前端页面提供独立运行的模拟数据
 *
 * 包含：K线数据、信号列表、持仓数据、风控告警、知识图谱节点、回测结果等。
 * 后端API就绪后可逐步替换为真实数据。
 */

import type { Bar, Signal, Position } from "@/types";
import type { RiskAlertData, RiskConfigData } from "@/api/risk";

// ============================================================
// K线 Mock 数据
// ============================================================

/**
 * 生成模拟K线数据
 * @param symbol 标的代码
 * @param count K线数量
 * @param basePrice 基础价格
 * @returns K线数据数组
 */
export function generateMockBars(
  symbol: string = "BTCUSDT",
  count: number = 200,
  basePrice: number = 65000,
): Bar[] {
  const bars: Bar[] = [];
  let price = basePrice;
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  for (let i = count - 1; i >= 0; i--) {
    const timestamp = new Date(now - i * oneDay).toISOString();
    const volatility = basePrice * 0.02;
    const change = (Math.random() - 0.48) * volatility;
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    const volume = Math.floor(Math.random() * 10000 + 5000);

    bars.push({
      symbol,
      market: "crypto",
      timeframe: "1d",
      timestamp,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume,
    });

    price = close;
  }

  return bars;
}

// ============================================================
// 信号 Mock 数据
// ============================================================

const THEORY_NAMES = [
  "太极中心律",
  "螺旋律",
  "波浪理论",
  "斐波那契",
  "DNA29",
  "DNA13",
  "TOMAS终裁",
];

const SOURCE_ENGINES = ["taiji", "spiral", "elliott", "tomas", "fusion"];

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "000001.SZ", "600519.SH"];

/**
 * 生成模拟信号数据
 * @param count 信号数量
 * @returns 信号数组
 */
export function generateMockSignals(count: number = 20): Signal[] {
  const signals: Signal[] = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const direction = (["LONG", "SHORT", "HOLD"] as const)[Math.floor(Math.random() * 3)];
    const symbol = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];
    const theoryIdx = Math.floor(Math.random() * THEORY_NAMES.length);
    const sourceIdx = Math.floor(Math.random() * SOURCE_ENGINES.length);

    signals.push({
      signal_id: `sig_${Date.now()}_${i}`,
      symbol,
      market: symbol.includes(".") ? "a_share" : "crypto",
      direction,
      price: parseFloat((Math.random() * 70000 + 1000).toFixed(2)),
      confidence: parseFloat(Math.random().toFixed(2)),
      source_engine: SOURCE_ENGINES[sourceIdx],
      theory_name: THEORY_NAMES[theoryIdx],
      timestamp: new Date(now - i * 3600000).toISOString(),
      metadata: {
        fib_level: Math.random() > 0.5 ? 0.618 : 0.382,
        wave_label: ["1", "2", "3", "4", "5", "A", "B", "C"][Math.floor(Math.random() * 8)],
        taiji_center: Math.random() > 0.5,
      },
    });
  }

  return signals;
}

// ============================================================
// 持仓 Mock 数据
// ============================================================

/**
 * 生成模拟持仓数据
 * @returns 持仓数组
 */
export function generateMockPositions(): Position[] {
  return [
    {
      position_id: "pos_001",
      symbol: "BTCUSDT",
      market: "crypto",
      quantity: 0.5,
      entry_price: 62000,
      current_price: 65800,
      stop_loss_price: 59000,
      take_profit_price: 70000,
      unrealized_pnl: 1900,
      opened_at: new Date(Date.now() - 3 * 86400000).toISOString(),
    },
    {
      position_id: "pos_002",
      symbol: "ETHUSDT",
      market: "crypto",
      quantity: 5,
      entry_price: 3200,
      current_price: 3050,
      stop_loss_price: 3000,
      take_profit_price: 3600,
      unrealized_pnl: -750,
      opened_at: new Date(Date.now() - 1 * 86400000).toISOString(),
    },
    {
      position_id: "pos_003",
      symbol: "SOLUSDT",
      market: "crypto",
      quantity: 50,
      entry_price: 145,
      current_price: 158,
      stop_loss_price: 135,
      take_profit_price: 170,
      unrealized_pnl: 650,
      opened_at: new Date(Date.now() - 6 * 3600000).toISOString(),
    },
  ];
}

// ============================================================
// 风控告警 Mock 数据
// ============================================================

/**
 * 生成模拟风控告警
 * @returns 告警数组
 */
export function generateMockAlerts(): RiskAlertData[] {
  return [
    {
      id: "alert_001",
      alert_type: "STOP_LOSS",
      symbol: "ETHUSDT",
      message: "ETHUSDT 价格触及止损线 (3000)，建议立即平仓",
      severity: "CRITICAL",
      timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
      details: { current_price: 3050, stop_loss_price: 3000, drawdown: 4.7 },
    },
    {
      id: "alert_002",
      alert_type: "DRAWDOWN",
      symbol: "BTCUSDT",
      message: "BTCUSDT 当前回撤 8.2%，接近最大回撤阈值 (10%)",
      severity: "WARNING",
      timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
      details: { current_drawdown: 8.2, max_drawdown: 10 },
    },
    {
      id: "alert_003",
      alert_type: "POSITION_LIMIT",
      symbol: "*",
      message: "总仓位占比 28%，接近最大仓位比例限制 (30%)",
      severity: "WARNING",
      timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
      details: { current_pct: 28, max_pct: 30 },
    },
    {
      id: "alert_004",
      alert_type: "TAKE_PROFIT",
      symbol: "SOLUSDT",
      message: "SOLUSDT 已达到止盈目标 (170)，建议分批平仓",
      severity: "INFO",
      timestamp: new Date(Date.now() - 8 * 3600000).toISOString(),
      details: { current_price: 158, take_profit_price: 170 },
    },
    {
      id: "alert_005",
      alert_type: "STOP_LOSS",
      symbol: "BNBUSDT",
      message: "BNBUSDT 止损触发，自动平仓已执行",
      severity: "CRITICAL",
      timestamp: new Date(Date.now() - 24 * 3600000).toISOString(),
      details: { exit_price: 580, stop_loss_price: 585, loss_pct: 3.5 },
    },
  ];
}

// ============================================================
// 风控配置 Mock 数据
// ============================================================

/**
 * 默认风控配置
 */
export const DEFAULT_RISK_CONFIG: RiskConfigData = {
  id: "config_default",
  name: "默认风控配置",
  symbol: "*",
  market: "*",
  max_position_pct: 0.1,
  stop_loss_pct: 0.05,
  take_profit_pct: 0.1,
  max_drawdown_pct: 0.2,
  trailing_stop_enabled: true,
  trailing_stop_pct: 0.03,
  is_active: true,
};

// ============================================================
// 知识图谱 Mock 数据
// ============================================================

/** 知识图谱节点类型 */
export type KnowledgeNodeType = "theory" | "concept" | "indicator" | "signal";

/** 知识图谱节点 */
export interface KnowledgeNode {
  id: string;
  label: string;
  type: KnowledgeNodeType;
  description: string;
}

/** 知识图谱边的关系类型 */
export type KnowledgeEdgeType = "derive" | "contain" | "oppose" | "apply";

/** 知识图谱边 */
export interface KnowledgeEdge {
  source: string;
  target: string;
  type: KnowledgeEdgeType;
  label: string;
}

/**
 * 鲁兆理论知识图谱Mock数据 - 节点
 */
export const MOCK_KNOWLEDGE_NODES: KnowledgeNode[] = [
  { id: "taiji", label: "太极中心律", type: "theory", description: "鲁兆理论核心，以太极阴阳平衡为基础，寻找价格运动的中心点。" },
  { id: "spiral", label: "螺旋律", type: "theory", description: "基于斐波那契螺旋的比例关系，分析价格波动的时空共振。" },
  { id: "elliott", label: "波浪理论", type: "theory", description: "艾略特波浪理论，识别5浪推动+3浪修正的市场结构。" },
  { id: "tomas", label: "TOMAS终裁", type: "theory", description: "Tomas方法论，将多理论信号融合为最终交易决策的裁判系统。" },
  { id: "dna29", label: "DNA29", type: "concept", description: "29个核心基因序列，描述市场周期性运动的基本DNA结构。" },
  { id: "dna13", label: "DNA13", type: "concept", description: "13个辅助基因序列，与DNA29组合形成完整的市场DNA图谱。" },
  { id: "fib", label: "斐波那契", type: "indicator", description: "黄金分割比例0.236/0.382/0.5/0.618/0.786，用于回撤与扩展分析。" },
  { id: "wave_label", label: "波浪标签", type: "indicator", description: "1-2-3-4-5-A-B-C波浪结构标注，标识市场运动阶段。" },
  { id: "taiji_center", label: "太极中心点", type: "signal", description: "价格运动的核心平衡点，多空力量转换的关键位置。" },
  { id: "fib_retrace", label: "斐波那契回撤", type: "signal", description: "价格回撤至关键斐波那契水平时的支撑/阻力信号。" },
  { id: "wave_3", label: "第三浪", type: "signal", description: "波浪理论中最强的推动浪，通常为最佳交易机会。" },
  { id: "spiral_resonance", label: "螺旋共振", type: "signal", description: "多个斐波那契比例在时空上重合时产生的强信号。" },
  { id: "tomas_decision", label: "TOMAS决策", type: "signal", description: "多理论融合后的最终交易决策信号，含方向、置信度与理由。" },
];

/**
 * 鲁兆理论知识图谱Mock数据 - 边
 */
export const MOCK_KNOWLEDGE_EDGES: KnowledgeEdge[] = [
  { source: "taiji", target: "taiji_center", type: "derive", label: "推导出" },
  { source: "taiji", target: "dna29", type: "contain", label: "包含" },
  { source: "taiji", target: "dna13", type: "contain", label: "包含" },
  { source: "spiral", target: "fib", type: "derive", label: "推导出" },
  { source: "spiral", target: "spiral_resonance", type: "derive", label: "推导出" },
  { source: "elliott", target: "wave_label", type: "derive", label: "推导出" },
  { source: "elliott", target: "wave_3", type: "derive", label: "推导出" },
  { source: "fib", target: "fib_retrace", type: "apply", label: "应用于" },
  { source: "dna29", target: "taiji_center", type: "apply", label: "应用于" },
  { source: "dna13", target: "spiral_resonance", type: "apply", label: "应用于" },
  { source: "taiji", target: "tomas", type: "apply", label: "输入" },
  { source: "spiral", target: "tomas", type: "apply", label: "输入" },
  { source: "elliott", target: "tomas", type: "apply", label: "输入" },
  { source: "taiji_center", target: "tomas_decision", type: "apply", label: "输入" },
  { source: "fib_retrace", target: "tomas_decision", type: "apply", label: "输入" },
  { source: "wave_3", target: "tomas_decision", type: "apply", label: "输入" },
  { source: "spiral_resonance", target: "tomas_decision", type: "apply", label: "输入" },
  { source: "dna29", target: "dna13", type: "oppose", label: "互补" },
];

// ============================================================
// 回测 Mock 数据
// ============================================================

/** 回测统计指标 */
export interface BacktestStats {
  total_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_loss_ratio: number;
  trade_count: number;
}

/** 回测交易记录 */
export interface BacktestTrade {
  trade_id: string;
  symbol: string;
  direction: "LONG" | "SHORT";
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
}

/** 回测权益曲线点 */
export interface EquityPoint {
  timestamp: string;
  equity: number;
  benchmark: number;
}

/**
 * 生成模拟回测权益曲线
 * @param days 天数
 * @param initialCapital 初始资金
 */
export function generateMockEquityCurve(
  days: number = 90,
  initialCapital: number = 100000,
): EquityPoint[] {
  const points: EquityPoint[] = [];
  let equity = initialCapital;
  let benchmark = initialCapital;
  const now = Date.now();

  for (let i = days; i >= 0; i--) {
    const timestamp = new Date(now - i * 86400000).toISOString();
    const stratReturn = (Math.random() - 0.45) * 0.02;
    const benchReturn = (Math.random() - 0.5) * 0.015;
    equity = equity * (1 + stratReturn);
    benchmark = benchmark * (1 + benchReturn);
    points.push({
      timestamp,
      equity: parseFloat(equity.toFixed(2)),
      benchmark: parseFloat(benchmark.toFixed(2)),
    });
  }

  return points;
}

/**
 * 生成模拟回测交易记录
 */
export function generateMockTrades(): BacktestTrade[] {
  const trades: BacktestTrade[] = [];
  const symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"];
  const now = Date.now();

  for (let i = 0; i < 15; i++) {
    const direction: "LONG" | "SHORT" = Math.random() > 0.5 ? "LONG" : "SHORT";
    const entryPrice = parseFloat((Math.random() * 60000 + 1000).toFixed(2));
    const exitPrice = parseFloat((entryPrice * (1 + (Math.random() - 0.45) * 0.1)).toFixed(2));
    const pnl = direction === "LONG"
      ? (exitPrice - entryPrice) * 0.5
      : (entryPrice - exitPrice) * 0.5;
    const pnlPct = ((exitPrice - entryPrice) / entryPrice) * 100 * (direction === "LONG" ? 1 : -1);

    trades.push({
      trade_id: `trade_${i + 1}`,
      symbol: symbols[i % symbols.length],
      direction,
      entry_time: new Date(now - (15 - i) * 2 * 86400000).toISOString(),
      entry_price: entryPrice,
      exit_time: new Date(now - (15 - i) * 2 * 86400000 + 86400000).toISOString(),
      exit_price: exitPrice,
      pnl: parseFloat(pnl.toFixed(2)),
      pnl_pct: parseFloat(pnlPct.toFixed(2)),
    });
  }

  return trades;
}

/**
 * 模拟回测统计指标
 */
export const MOCK_BACKTEST_STATS: BacktestStats = {
  total_return: 0.237,
  max_drawdown: -0.082,
  sharpe_ratio: 1.85,
  win_rate: 0.62,
  profit_loss_ratio: 2.1,
  trade_count: 48,
};
