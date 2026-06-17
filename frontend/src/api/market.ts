/** 行情API调用模块 - 封装行情相关的HTTP请求 */

import apiClient from "./client";
import type { ApiResponse, Bar, SymbolInfo } from "@/types";

/** K线数据列表响应类型 */
interface BarListData {
  total: number;
  items: Bar[];
}

/** 标的列表响应类型 */
interface SymbolListData {
  total: number;
  items: SymbolInfo[];
}

/**
 * 获取K线数据
 * @param symbol 标的代码，如 BTCUSDT
 * @param timeframe 时间周期，如 1m/5m/1h/1d
 * @param limit 数据条数
 */
export async function getBars(
  symbol: string = "BTCUSDT",
  timeframe: string = "1d",
  limit: number = 100,
): Promise<BarListData> {
  const response = await apiClient.get<ApiResponse<BarListData>>("/market/bars", {
    params: { symbol, timeframe, limit },
  });
  return response.data.data;
}

/**
 * 获取可用标的列表
 */
export async function getSymbols(): Promise<SymbolListData> {
  const response = await apiClient.get<ApiResponse<SymbolListData>>("/market/symbols");
  return response.data.data;
}
