/** 行情Zustand状态切片 - 管理K线数据、当前标的、周期等状态 */

import { create } from "zustand";
import type { Bar, SymbolInfo, Timeframe, MarketType } from "@/types";
import { getBars, getSymbols } from "@/api/market";

/** 行情状态接口 */
interface MarketSliceState {
  /** K线数据列表 */
  bars: Bar[];
  /** 可用标的列表 */
  symbols: SymbolInfo[];
  /** 当前选中标的 */
  currentSymbol: string;
  /** 当前时间周期 */
  currentTimeframe: Timeframe;
  /** 当前市场类型 */
  currentMarket: MarketType;
  /** 数据加载状态 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 最后更新时间 */
  lastUpdated: string | null;

  /** 设置当前标的 */
  setCurrentSymbol: (symbol: string) => void;
  /** 设置时间周期 */
  setTimeframe: (timeframe: Timeframe) => void;
  /** 设置市场类型 */
  setMarket: (market: MarketType) => void;
  /** 获取K线数据 */
  fetchBars: (symbol?: string, timeframe?: Timeframe, limit?: number) => Promise<void>;
  /** 获取标的列表 */
  fetchSymbols: () => Promise<void>;
  /** 清空错误 */
  clearError: () => void;
}

/**
 * 行情状态Store
 *
 * 管理行情相关的所有状态，包括K线数据、标的列表、
 * 当前选择状态以及数据获取操作。
 */
export const useMarketSlice = create<MarketSliceState>((set, get) => ({
  bars: [],
  symbols: [],
  currentSymbol: "BTCUSDT",
  currentTimeframe: "1d",
  currentMarket: "crypto",
  loading: false,
  error: null,
  lastUpdated: null,

  setCurrentSymbol: (symbol: string) => {
    set({ currentSymbol: symbol });
    // 切换标的后自动获取数据
    const { currentTimeframe } = get();
    get().fetchBars(symbol, currentTimeframe);
  },

  setTimeframe: (timeframe: Timeframe) => {
    set({ currentTimeframe: timeframe });
    const { currentSymbol } = get();
    get().fetchBars(currentSymbol, timeframe);
  },

  setMarket: (market: MarketType) => {
    // 切换市场时设置默认标的
    const defaultSymbol = market === "crypto" ? "BTCUSDT" : "000001.SZ";
    set({ currentMarket: market, currentSymbol: defaultSymbol });
    const { currentTimeframe } = get();
    get().fetchBars(defaultSymbol, currentTimeframe);
  },

  fetchBars: async (symbol?: string, timeframe?: Timeframe, limit: number = 200) => {
    const sym = symbol || get().currentSymbol;
    const tf = timeframe || get().currentTimeframe;
    set({ loading: true, error: null });

    try {
      const data = await getBars(sym, tf, limit);
      set({
        bars: data.items,
        loading: false,
        lastUpdated: new Date().toISOString(),
      });
    } catch (err: any) {
      set({
        loading: false,
        error: err?.message || "获取K线数据失败",
      });
    }
  },

  fetchSymbols: async () => {
    try {
      const data = await getSymbols();
      set({ symbols: data.items });
    } catch (err: any) {
      console.error("[marketSlice] fetchSymbols error:", err);
    }
  },

  clearError: () => set({ error: null }),
}));
