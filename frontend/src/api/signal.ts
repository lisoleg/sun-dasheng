/** 信号API调用 - getSignals, getLatestSignals */

import apiClient from "./client";
import type { ApiResponse, Signal } from "@/types";

/** 信号列表响应 */
interface SignalListData {
  total: number;
  items: Signal[];
}

/**
 * 获取信号列表（分页）
 * @param params 查询参数
 * @returns 信号列表响应
 */
export async function getSignals(params?: {
  symbol?: string;
  direction?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<SignalListData>> {
  const response = await apiClient.get<ApiResponse<SignalListData>>("/signals", {
    params,
  });
  return response.data;
}

/**
 * 获取最新信号
 * @param limit 返回条数
 * @returns 最新信号列表
 */
export async function getLatestSignals(
  limit: number = 10,
): Promise<ApiResponse<SignalListData>> {
  const response = await apiClient.get<ApiResponse<SignalListData>>(
    "/signals/latest",
    { params: { limit } },
  );
  return response.data;
}
