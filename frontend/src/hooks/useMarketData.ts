/** 行情数据Hook - 封装行情数据的获取、缓存和自动刷新逻辑 */

import { useState, useEffect, useCallback, useRef } from "react";
import { getBars, getSymbols } from "@/api/market";
import type { Bar, SymbolInfo, Timeframe } from "@/types";
import { useMarketStore } from "@/store";

/** 行情数据Hook返回类型 */
interface UseMarketDataResult {
  /** K线数据列表 */
  bars: Bar[];
  /** 可用标的列表 */
  symbols: SymbolInfo[];
  /** 数据加载中 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 手动刷新K线数据 */
  refreshBars: () => Promise<void>;
  /** 手动刷新标的列表 */
  refreshSymbols: () => Promise<void>;
}

/**
 * 行情数据Hook
 *
 * 自动根据store中的currentSymbol和currentTimeframe获取K线数据，
 * 支持定时自动刷新和手动刷新。
 *
 * @param autoRefreshInterval 自动刷新间隔（毫秒），默认60000ms，设为0关闭自动刷新
 */
export function useMarketData(autoRefreshInterval: number = 60000): UseMarketDataResult {
  const { currentSymbol, currentTimeframe } = useMarketStore();
  const [bars, setBars] = useState<Bar[]>([]);
  const [symbols, setSymbols] = useState<SymbolInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /** 获取K线数据 */
  const refreshBars = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getBars(currentSymbol, currentTimeframe as Timeframe, 200);
      setBars(data.items);
    } catch (err: any) {
      const message = err?.message || "获取K线数据失败";
      setError(message);
      console.error("[useMarketData] refreshBars error:", err);
    } finally {
      setLoading(false);
    }
  }, [currentSymbol, currentTimeframe]);

  /** 获取标的列表 */
  const refreshSymbols = useCallback(async () => {
    try {
      const data = await getSymbols();
      setSymbols(data.items);
    } catch (err: any) {
      console.error("[useMarketData] refreshSymbols error:", err);
    }
  }, []);

  // 标的或周期变化时自动刷新K线
  useEffect(() => {
    refreshBars();
  }, [refreshBars]);

  // 初始化时获取标的列表
  useEffect(() => {
    refreshSymbols();
  }, [refreshSymbols]);

  // 定时自动刷新
  useEffect(() => {
    if (autoRefreshInterval <= 0) return;

    timerRef.current = setInterval(() => {
      refreshBars();
    }, autoRefreshInterval);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [autoRefreshInterval, refreshBars]);

  return {
    bars,
    symbols,
    loading,
    error,
    refreshBars,
    refreshSymbols,
  };
}
