import { create } from "zustand";
import type { MarketType, Timeframe } from "@/types";

/** 市场状态Store - 管理当前市场、标的、周期等全局状态 */
interface MarketState {
  currentMarket: MarketType;
  currentSymbol: string;
  currentTimeframe: Timeframe;
  setMarket: (market: MarketType) => void;
  setSymbol: (symbol: string) => void;
  setTimeframe: (timeframe: Timeframe) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  currentMarket: "crypto",
  currentSymbol: "BTCUSDT",
  currentTimeframe: "1d",
  setMarket: (market) => set({ currentMarket: market }),
  setSymbol: (symbol) => set({ currentSymbol: symbol }),
  setTimeframe: (timeframe) => set({ currentTimeframe: timeframe }),
}));

// 信号状态Store - 从signalSlice导出（完整版，含信号列表、过滤、WebSocket实时更新）
export { useSignalStore } from "./signalSlice";

// 风控状态Store - 从riskSlice导出（完整版，含风控配置、告警、监控）
export { useRiskStore } from "./riskSlice";
