import axios from 'axios';

const API_BASE = '/api';

/**
 * 用户偏好 API
 */
export interface UserPreferences {
  theme_mode: 'dark' | 'light';
  layout_template: string;
  custom_layout?: Record<string, unknown>;
  chart_indicators?: Record<string, boolean>;
  notifications?: Record<string, unknown>;
  refresh_mode?: string;
  shortcuts_enabled?: boolean;
}

/**
 * 获取用户偏好
 */
export async function getPreferences(): Promise<UserPreferences> {
  const { data } = await axios.get(`${API_BASE}/preferences`);
  return data.data || data;
}

/**
 * 更新用户偏好
 */
export async function updatePreferences(prefs: Partial<UserPreferences>): Promise<UserPreferences> {
  const { data } = await axios.put(`${API_BASE}/preferences`, prefs);
  return data.data || data;
}

/**
 * 获取布局模板列表
 */
export async function getLayouts(): Promise<Array<{ id: string; name: string }>> {
  const { data } = await axios.get(`${API_BASE}/preferences/layouts`);
  return data.data || data || [];
}

/**
 * 保存自定义布局
 */
export async function saveLayout(name: string, layout: Record<string, unknown>): Promise<void> {
  await axios.post(`${API_BASE}/preferences/layouts`, { name, layout });
}

/**
 * 删除布局模板
 */
export async function deleteLayout(id: string): Promise<void> {
  await axios.delete(`${API_BASE}/preferences/layouts/${id}`);
}
