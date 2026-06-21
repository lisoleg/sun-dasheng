/**
 * 字体配置
 * 金融数字使用等宽字体对齐
 */
export const fontConfig = {
  // 无衬线字体栈（正文）
  sans: '"Inter", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif',

  // 等宽字体栈（金融数字、代码）
  mono: '"JetBrains Mono", "Roboto Mono", "Fira Code", "Consolas", monospace',

  // 金融数字专用（强制等宽，便于对齐）
  financial: '"JetBrains Mono", "Roboto Mono", monospace',

  // 中文字体回退
  chinese: '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif',

  // 字体大小基准（8px 栅格）
  fontSize: {
    xs: '0.6875rem',   // ~11px
    sm: '0.8125rem',   // ~13px
    base: '0.875rem',  // 14px
    lg: '1rem',         // 16px
    xl: '1.125rem',    // 18px
    '2xl': '1.25rem',  // 20px
    '3xl': '1.5rem',   // 24px
    '4xl': '2rem',      // 32px
  },

  // 字体粗细
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // 行高
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
} as const;
