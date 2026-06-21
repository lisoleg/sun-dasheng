/**
 * 颜色工具函数
 * 涨跌颜色、置信度颜色
 */

import type { ThemeMode } from '@/theme';

/**
 * 获取涨跌颜色（A股习惯：红涨绿跌）
 */
export function getChangeColor(value: number, themeMode: ThemeMode = 'dark'): string {
  if (value > 0) return themeMode === 'dark' ? '#ef4444' : '#cf222e';  // 涨=红
  if (value < 0) return themeMode === 'dark' ? '#22c55e' : '#1a7f37';  // 跌=绿
  return themeMode === 'dark' ? '#8b949e' : '#656d76';  // 平=灰
}

/**
 * 获取涨跌背景色（淡色）
 */
export function getChangeBgColor(value: number, themeMode: ThemeMode = 'dark'): string {
  if (value > 0) return themeMode === 'dark' ? 'rgba(239,68,68,0.12)' : 'rgba(207,34,46,0.08)';
  if (value < 0) return themeMode === 'dark' ? 'rgba(34,197,94,0.12)' : 'rgba(26,127,55,0.08)';
  return 'transparent';
}

/**
 * 格式化金融数字
 * 右对齐 + 等宽字体
 */
export function formatFinancialNumber(
  num: number,
  options?: {
    decimals?: number;
    prefix?: string;
    suffix?: string;
    compact?: boolean;  // K/M 单位
  }
): string {
  const { decimals = 2, prefix = '', suffix = '', compact = false } = options || {};

  let formatted: string;
  if (compact && Math.abs(num) >= 1e6) {
    formatted = `${(num / 1e6).toFixed(decimals)}M`;
  } else if (compact && Math.abs(num) >= 1e3) {
    formatted = `${(num / 1e3).toFixed(decimals)}K`;
  } else {
    formatted = num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  return `${prefix}${formatted}${suffix}`;
}

/**
 * 获取置信度颜色
 * <0.3 灰，0.3-0.6 黄，>0.6 绿
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence < 0.3) return '#6b7280';
  if (confidence < 0.6) return '#f59e0b';
  return '#22c55e';
}

/**
 * 获取理论颜色（7个理论）
 */
export function getTheoryColor(theory: string): string {
  const colorMap: Record<string, string> = {
    taiji: '#ef4444',
    spiral: '#3b82f6',
    elliott: '#f59e0b',
    dual: '#8b5cf6',
    cycle: '#ec4899',
    gann: '#14b8a6',
    bg_ma: '#f97316',
  };
  return colorMap[theory] || '#6b7280';
}
