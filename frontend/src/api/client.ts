import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

/**
 * API 客户端（axios 实例）
 * 包含所有 API 调用的基础配置
 */

const API_BASE = '/api';

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ========== 请求拦截器 ==========
client.interceptors.request.use(
  (config) => {
    // 可添加 auth token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ========== 响应拦截器 ==========
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // 统一错误处理
    if (error.response) {
      const status = error.response.status;
      if (status === 401) {
        console.error('[API] 未授权，请重新登录');
      } else if (status === 403) {
        console.error('[API] 权限不足');
      } else if (status >= 500) {
        console.error('[API] 服务器错误', status);
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('[API] 请求超时');
    }
    return Promise.reject(error);
  }
);

export default client;

export { API_BASE };
