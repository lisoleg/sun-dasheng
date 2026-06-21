/**
 * 语义色板 - 导出给非 MUI 组件使用
 * 遵循 A股习惯：红涨绿跌
 */
export const semanticColors = {
  // 涨跌色（A股习惯）
  up: '#ef4444',           // 涨（红）
  down: '#22c55e',         // 跌（绿）
  flat: '#6b7280',         // 平（灰）

  // 语义色
  warning: '#f59e0b',     // 警告（黄）
  danger: '#dc2626',       // 危险（深红）
  info: '#3b82f6',        // 信息（蓝）
  success: '#22c55e',      // 成功（绿）

  // 背景色（深色主题）
  bgDark: '#0d1117',      // 主背景（GitHub dark 风）
  bgPanel: '#161b22',     // 面板背景
  bgHover: '#1c2128',     // 悬停背景
  bgActive: '#1f2937',    // 激活背景

  // 背景色（浅色主题）
  bgLight: '#ffffff',      // 主背景
  bgLightPanel: '#f6f8fa', // 面板背景
  bgLightHover: '#f3f4f6', // 悬停背景

  // 边框色
  border: '#30363d',      // 深色边框
  borderLight: '#d0d7de', // 浅色边框
  divider: '#30363d',     // 分割线（深色）
  dividerLight: '#d0d7de', // 分割线（浅色）

  // 文本色（深色主题）
  textPrimary: '#c9d1d9',   // 主文本
  textSecondary: '#8b949e', // 次要文本
  textMuted: '#6e7681',     // 静默文本
  textLink: '#58a6ff',       // 链接

  // 文本色（浅色主题）
  textLightPrimary: '#1f2328',
  textLightSecondary: '#656d76',

  // 图表色板（7个理论）
  theoryColors: [
    '#ef4444', // 太极 - 红
    '#3b82f6', // 螺旋 - 蓝
    '#f59e0b', // 波浪 - 黄
    '#8b5cf6', // 对偶 - 紫
    '#ec4899', // 周期 - 粉
    '#14b8a6', // 江恩 - 青
    '#f97316', // BG均线 - 橙
  ],

  // 置信度颜色
  confidenceLow: '#6b7280',    // < 0.3 灰
  confidenceMid: '#f59e0b',   // 0.3-0.6 黄
  confidenceHigh: '#22c55e',  // > 0.6 绿
  confidenceVeryHigh: '#3b82f6', // > 0.8 蓝
} as const;

export type SemanticColorKey = keyof typeof semanticColors;
