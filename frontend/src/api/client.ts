import axios from "axios";
import type { ApiResponse } from "@/types";

/**
 * Axios实例 - 统一配置基础URL、超时、拦截器
 * 基础URL指向后端API /api前缀，Vite开发代理会转发到 localhost:8000
 */
const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * 响应拦截器 - 统一处理API响应格式 {code, data, message}
 * code !== 0 时视为业务错误，抛出异常
 */
apiClient.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse<unknown>;
    if (data && typeof data.code === "number" && data.code !== 0) {
      const error = new Error(data.message || "请求失败") as Error & { code: number };
      error.code = data.code;
      return Promise.reject(error);
    }
    return response;
  },
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const messages: Record<number, string> = {
        400: "请求参数错误",
        401: "未授权，请登录",
        403: "拒绝访问",
        404: "请求资源不存在",
        500: "服务器内部错误",
      };
      const message = messages[status] || `请求失败 (${status})`;
      console.error(`[API Error] ${status}: ${message}`);
    } else if (error.request) {
      console.error("[API Error] 网络错误，无法连接服务器");
    } else {
      console.error(`[API Error] ${error.message}`);
    }
    return Promise.reject(error);
  },
);

export default apiClient;
