/** 风控Zustand状态 - 管理风控配置、告警与监控状态 */

import { create } from "zustand";

/** 风控配置接口 */
interface RiskConfigState {
  id: string;
  name: string;
  symbol: string;
  market: string;
  max_position_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  max_drawdown_pct: number;
  trailing_stop_enabled: boolean;
  trailing_stop_pct: number;
  is_active: boolean;
}

/** 风控告警接口 */
interface RiskAlertState {
  id: string;
  alert_type: "STOP_LOSS" | "TAKE_PROFIT" | "DRAWDOWN" | "POSITION_LIMIT";
  symbol: string;
  message: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  timestamp: string;
  details: Record<string, number>;
}

/** 告警严重级别过滤 */
export type AlertSeverityFilter = "ALL" | "INFO" | "WARNING" | "CRITICAL";

/** 风控状态接口 */
interface RiskState {
  /** 风控配置 */
  config: RiskConfigState | null;
  /** 告警列表 */
  alerts: RiskAlertState[];
  /** 告警总数 */
  alertTotal: number;
  /** 是否显示告警面板 */
  showAlerts: boolean;
  /** 告警过滤级别 */
  alertSeverityFilter: AlertSeverityFilter;
  /** 是否正在加载配置 */
  configLoading: boolean;
  /** 是否正在加载告警 */
  alertsLoading: boolean;
  /** 错误信息 */
  error: string | null;

  /** 设置风控配置 */
  setConfig: (config: RiskConfigState) => void;
  /** 设置告警列表 */
  setAlerts: (alerts: RiskAlertState[], total: number) => void;
  /** 添加新告警（WebSocket推送时使用） */
  addAlert: (alert: RiskAlertState) => void;
  /** 设置是否显示告警面板 */
  setShowAlerts: (show: boolean) => void;
  /** 设置告警过滤级别 */
  setAlertSeverityFilter: (filter: AlertSeverityFilter) => void;
  /** 设置配置加载状态 */
  setConfigLoading: (loading: boolean) => void;
  /** 设置告警加载状态 */
  setAlertsLoading: (loading: boolean) => void;
  /** 设置错误信息 */
  setError: (error: string | null) => void;
  /** 获取过滤后的告警列表 */
  getFilteredAlerts: () => RiskAlertState[];
  /** 获取未读严重告警数量 */
  getCriticalAlertCount: () => number;
}

/** 默认风控配置 */
const DEFAULT_CONFIG: RiskConfigState = {
  id: "",
  name: "default",
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

/**
 * 风控Zustand状态Store
 *
 * 管理风控配置、告警列表和监控状态。
 * 支持：
 * - 风控配置读写
 * - 告警列表CRUD与过滤
 * - WebSocket实时推送告警
 * - 严重级别统计
 */
export const useRiskStore = create<RiskState>((set, get) => ({
  config: DEFAULT_CONFIG,
  alerts: [],
  alertTotal: 0,
  showAlerts: true,
  alertSeverityFilter: "ALL",
  configLoading: false,
  alertsLoading: false,
  error: null,

  setConfig: (config) => set({ config }),

  setAlerts: (alerts, alertTotal) => set({ alerts, alertTotal }),

  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, 100),
      alertTotal: state.alertTotal + 1,
      // CRITICAL级别告警自动弹出
      showAlerts: alert.severity === "CRITICAL" ? true : state.showAlerts,
    })),

  setShowAlerts: (showAlerts) => set({ showAlerts }),

  setAlertSeverityFilter: (alertSeverityFilter) =>
    set({ alertSeverityFilter }),

  setConfigLoading: (configLoading) => set({ configLoading }),

  setAlertsLoading: (alertsLoading) => set({ alertsLoading }),

  setError: (error) => set({ error }),

  getFilteredAlerts: () => {
    const { alerts, alertSeverityFilter } = get();
    if (alertSeverityFilter === "ALL") {
      return alerts;
    }
    return alerts.filter((alert) => alert.severity === alertSeverityFilter);
  },

  getCriticalAlertCount: () => {
    const { alerts } = get();
    return alerts.filter(
      (alert) => alert.severity === "CRITICAL" || alert.severity === "WARNING",
    ).length;
  },
}));
