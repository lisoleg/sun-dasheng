/**
 * 格式化工具函数
 * 金融数字/百分比/日期格式化
 */

/**
 * 格式化数字（金融）
 * 右对齐 + 等宽字体（在组件中使用）
 */
export function formatNumber(
  num: number,
  options?: {
    decimals?: number;
    compact?: boolean;
    prefix?: string;
    suffix?: string;
  }
): string {
  const { decimals = 2, compact = false, prefix = '', suffix = '' } = options || {};

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
 * 格式化百分比
 */
export function formatPercent(
  value: number,
  decimals = 2,
  includeSign = true
): string {
  const formatted = value.toFixed(decimals);
  return includeSign && value > 0 ? `+${formatted}%` : `${formatted}%`;
}

/**
 * 格式化货币
 */
export function formatCurrency(
  value: number,
  currency = 'CNY',
  decimals = 2
): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * 格式化日期
 */
export function formatDate(
  date: string | Date,
  format: 'short' | 'medium' | 'long' | 'time' = 'short'
): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  switch (format) {
    case 'short':
      return d.toLocaleDateString('zh-CN');
    case 'medium':
      return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    case 'long':
      return d.toLocaleString('zh-CN');
    case 'time':
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    default:
      return d.toLocaleDateString('zh-CN');
  }
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化持续时间（秒 → 可读字符串）
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${Math.round(seconds % 60)}秒`;
  return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`;
}

/**
 * 格式化回测状态
 */
export function formatBacktestStatus(status: string): string {
  const map: Record<string, string> = {
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };
  return map[status] || status;
}
