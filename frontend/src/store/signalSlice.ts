/** 信号Zustand状态 - 管理信号列表、过滤与实时更新 */

import { create } from "zustand";
import type { Signal } from "@/types";

/** 信号方向过滤选项 */
export type SignalDirectionFilter = "ALL" | "LONG" | "SHORT" | "HOLD";

/** 信号源过滤选项 */
export type SignalSourceFilter = "ALL" | "taiji" | "spiral" | "elliott" | "tomas" | "fusion";

/** 信号状态接口 */
interface SignalState {
  /** 信号列表 */
  signals: Signal[];
  /** 最新信号（前10条） */
  latestSignals: Signal[];
  /** 方向过滤 */
  directionFilter: SignalDirectionFilter;
  /** 来源过滤 */
  sourceFilter: SignalSourceFilter;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 总数 */
  total: number;

  /** 设置信号列表 */
  setSignals: (signals: Signal[]) => void;
  /** 设置最新信号 */
  setLatestSignals: (signals: Signal[]) => void;
  /** 添加新信号（WebSocket实时推送时使用） */
  addSignal: (signal: Signal) => void;
  /** 设置方向过滤 */
  setDirectionFilter: (filter: SignalDirectionFilter) => void;
  /** 设置来源过滤 */
  setSourceFilter: (filter: SignalSourceFilter) => void;
  /** 设置加载状态 */
  setLoading: (loading: boolean) => void;
  /** 设置错误信息 */
  setError: (error: string | null) => void;
  /** 设置总数 */
  setTotal: (total: number) => void;
  /** 获取过滤后的信号列表 */
  getFilteredSignals: () => Signal[];
}

/**
 * 信号Zustand状态Store
 *
 * 管理信号列表、过滤条件和实时更新。
 * 支持：
 * - 信号列表CRUD
 * - 方向/来源过滤
 * - WebSocket实时推送新信号
 */
export const useSignalStore = create<SignalState>((set, get) => ({
  signals: [],
  latestSignals: [],
  directionFilter: "ALL",
  sourceFilter: "ALL",
  loading: false,
  error: null,
  total: 0,

  setSignals: (signals) => set({ signals }),

  setLatestSignals: (latestSignals) => set({ latestSignals }),

  addSignal: (signal) =>
    set((state) => ({
      signals: [signal, ...state.signals].slice(0, 100),
      latestSignals: [signal, ...state.latestSignals].slice(0, 10),
      total: state.total + 1,
    })),

  setDirectionFilter: (directionFilter) => set({ directionFilter }),

  setSourceFilter: (sourceFilter) => set({ sourceFilter }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  setTotal: (total) => set({ total }),

  getFilteredSignals: () => {
    const { signals, directionFilter, sourceFilter } = get();
    return signals.filter((signal) => {
      if (directionFilter !== "ALL" && signal.direction !== directionFilter) {
        return false;
      }
      if (sourceFilter !== "ALL" && signal.source_engine !== sourceFilter) {
        return false;
      }
      return true;
    });
  },
}));
