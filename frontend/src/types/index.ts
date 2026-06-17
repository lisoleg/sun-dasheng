/** K线数据 */
export interface Bar {
  symbol: string;
  market: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** 交易信号 */
export interface Signal {
  signal_id: string;
  symbol: string;
  market: string;
  direction: "LONG" | "SHORT" | "HOLD";
  price: number;
  confidence: number;
  source_engine: string;
  theory_name: string;
  timestamp: string;
  metadata: Record<string, any>;
}

/** 订单 */
export interface Order {
  order_id: string;
  symbol: string;
  market: string;
  side: "BUY" | "SELL";
  type: "MARKET" | "LIMIT";
  price: number;
  quantity: number;
  status: "PENDING" | "FILLED" | "CANCELLED" | "FAILED";
  created_at: string;
  updated_at: string;
}

/** 持仓 */
export interface Position {
  position_id: string;
  symbol: string;
  market: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  stop_loss_price: number;
  take_profit_price: number;
  unrealized_pnl: number;
  opened_at: string;
}

/** 风控配置 */
export interface RiskConfig {
  max_position_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  max_drawdown_pct: number;
}

/** 统一API响应格式 */
export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

/** WebSocket消息 */
export interface WsMessage {
  type: "bar_update" | "signal_generated" | "order_update" | "risk_alert" | "position_update";
  payload: any;
}

/** 标的信息 */
export interface SymbolInfo {
  symbol: string;
  market: string;
  name: string;
  status: string;
}

/** 市场类型 */
export type MarketType = "a_share" | "crypto";

/** 时间周期 */
export type Timeframe = "1m" | "5m" | "15m" | "1h" | "4h" | "1d";
