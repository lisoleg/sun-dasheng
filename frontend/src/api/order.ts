/** 订单API调用 - createOrder, getOrders, cancelOrder */

import apiClient from "./client";
import type { ApiResponse, Order } from "@/types";

/** 订单创建参数 */
interface OrderCreateParams {
  symbol: string;
  market?: string;
  side: "BUY" | "SELL";
  type?: "MARKET" | "LIMIT";
  price?: number;
  quantity: number;
}

/** 订单列表响应 */
interface OrderListData {
  total: number;
  items: Order[];
}

/**
 * 创建订单（手动下单）
 * @param data 订单参数
 * @returns 创建的订单
 */
export async function createOrder(
  data: OrderCreateParams,
): Promise<ApiResponse<Order>> {
  const response = await apiClient.post<ApiResponse<Order>>("/orders", data);
  return response.data;
}

/**
 * 获取订单列表（分页）
 * @param params 查询参数
 * @returns 订单列表响应
 */
export async function getOrders(params?: {
  symbol?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<OrderListData>> {
  const response = await apiClient.get<ApiResponse<OrderListData>>("/orders", {
    params,
  });
  return response.data;
}

/**
 * 获取订单详情
 * @param orderId 订单ID
 * @returns 订单详情
 */
export async function getOrder(
  orderId: string,
): Promise<ApiResponse<Order>> {
  const response = await apiClient.get<ApiResponse<Order>>(
    `/orders/${orderId}`,
  );
  return response.data;
}

/**
 * 取消订单
 * @param orderId 订单ID
 * @returns 取消后的订单状态
 */
export async function cancelOrder(
  orderId: string,
): Promise<ApiResponse<Order>> {
  const response = await apiClient.delete<ApiResponse<Order>>(
    `/orders/${orderId}`,
  );
  return response.data;
}
