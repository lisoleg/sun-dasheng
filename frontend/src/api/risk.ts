/** 风控API调用 - getRiskConfig, updateRiskConfig, getRiskAlerts */

import apiClient from "./client";
import type { ApiResponse } from "@/types";

/** 风控配置数据 */
interface RiskConfigData {
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

/** 风控配置更新参数 */
interface RiskConfigUpdateParams {
  name?: string;
  max_position_pct?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  max_drawdown_pct?: number;
  trailing_stop_enabled?: boolean;
  trailing_stop_pct?: number;
  is_active?: boolean;
}

/** 风控告警数据 */
interface RiskAlertData {
  id: string;
  alert_type: "STOP_LOSS" | "TAKE_PROFIT" | "DRAWDOWN" | "POSITION_LIMIT";
  symbol: string;
  message: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  timestamp: string;
  details: Record<string, number>;
}

/** 风控告警列表响应 */
interface RiskAlertListData {
  total: number;
  items: RiskAlertData[];
}

/**
 * 获取风控配置
 * @returns 风控配置
 */
export async function getRiskConfig(): Promise<ApiResponse<RiskConfigData>> {
  const response = await apiClient.get<ApiResponse<RiskConfigData>>(
    "/risk/config",
  );
  return response.data;
}

/**
 * 更新风控配置
 * @param data 配置更新参数
 * @returns 更新后的风控配置
 */
export async function updateRiskConfig(
  data: RiskConfigUpdateParams,
): Promise<ApiResponse<RiskConfigData>> {
  const response = await apiClient.put<ApiResponse<RiskConfigData>>(
    "/risk/config",
    data,
  );
  return response.data;
}

/**
 * 获取风控告警列表
 * @param params 查询参数
 * @returns 告警列表
 */
export async function getRiskAlerts(params?: {
  severity?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<RiskAlertListData>> {
  const response = await apiClient.get<ApiResponse<RiskAlertListData>>(
    "/risk/alerts",
    { params },
  );
  return response.data;
}

export type {
  RiskConfigData,
  RiskConfigUpdateParams,
  RiskAlertData,
  RiskAlertListData,
};
