/** 信号数据Hook - 封装信号API调用与WebSocket实时更新 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getLatestSignals, getSignals } from "@/api/signal";
import type { Signal, WsMessage } from "@/types";

/** 信号Hook参数 */
interface UseSignalsOptions {
  /** 筛选标的代码 */
  symbol?: string;
  /** 筛选方向 */
  direction?: string;
  /** 自动刷新间隔（毫秒），0表示不自动刷新 */
  refreshInterval?: number;
  /** 是否启用WebSocket实时更新 */
  enableWebSocket?: boolean;
}

/** 信号Hook返回值 */
interface UseSignalsResult {
  /** 信号列表 */
  signals: Signal[];
  /** 最新信号（前N条） */
  latestSignals: Signal[];
  /** 加载状态 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 手动刷新 */
  refresh: () => Promise<void>;
  /** 总数 */
  total: number;
}

/**
 * 信号数据Hook
 *
 * 封装信号API调用，支持分页查询和WebSocket实时更新。
 *
 * @param options Hook配置选项
 * @returns 信号数据与操作方法
 */
export function useSignals(options: UseSignalsOptions = {}): UseSignalsResult {
  const { symbol, direction, refreshInterval = 0, enableWebSocket = true } = options;

  const [signals, setSignals] = useState<Signal[]>([]);
  const [latestSignals, setLatestSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const refreshTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /** 获取信号列表 */
  const fetchSignals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getSignals({
        symbol,
        direction,
        page: 1,
        page_size: 50,
      });
      if (response.code === 0) {
        setSignals(response.data.items);
        setTotal(response.data.total);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "获取信号列表失败";
      setError(message);
      console.error("[useSignals] fetchSignals error:", message);
    } finally {
      setLoading(false);
    }
  }, [symbol, direction]);

  /** 获取最新信号 */
  const fetchLatestSignals = useCallback(async () => {
    try {
      const response = await getLatestSignals(10);
      if (response.code === 0) {
        setLatestSignals(response.data.items);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "获取最新信号失败";
      console.error("[useSignals] fetchLatestSignals error:", message);
    }
  }, []);

  /** 手动刷新 */
  const refresh = useCallback(async () => {
    await Promise.all([fetchSignals(), fetchLatestSignals()]);
  }, [fetchSignals, fetchLatestSignals]);

  /** 初始化：获取数据 */
  useEffect(() => {
    fetchSignals();
    fetchLatestSignals();
  }, [fetchSignals, fetchLatestSignals]);

  /** 自动刷新定时器 */
  useEffect(() => {
    if (refreshInterval > 0) {
      refreshTimerRef.current = setInterval(() => {
        fetchSignals();
        fetchLatestSignals();
      }, refreshInterval);
    }

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [refreshInterval, fetchSignals, fetchLatestSignals]);

  /** WebSocket实时更新 */
  useEffect(() => {
    if (!enableWebSocket) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/signals`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[useSignals] WebSocket connected");
        // 发送订阅消息
        ws.send(JSON.stringify({ type: "subscribe", direction: "all" }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WsMessage = JSON.parse(event.data);
          if (message.type === "signal_generated" && message.payload) {
            const newSignal = message.payload as Signal;
            // 将新信号插入列表头部
            setLatestSignals((prev) => [newSignal, ...prev].slice(0, 10));
            setSignals((prev) => [newSignal, ...prev].slice(0, 50));
            setTotal((prev) => prev + 1);
          }
        } catch (parseErr) {
          console.error("[useSignals] WebSocket message parse error:", parseErr);
        }
      };

      ws.onerror = (event) => {
        console.error("[useSignals] WebSocket error:", event);
      };

      ws.onclose = () => {
        console.log("[useSignals] WebSocket disconnected");
      };
    } catch (wsErr) {
      console.error("[useSignals] WebSocket connection error:", wsErr);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [enableWebSocket]);

  return {
    signals,
    latestSignals,
    loading,
    error,
    refresh,
    total,
  };
}
