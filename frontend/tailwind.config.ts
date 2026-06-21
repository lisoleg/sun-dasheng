import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // ========== 主题色（映射 semanticColors）==========
      colors: {
        // 主色
        primary: {
          50: '#e3f2fd',
          100: '#bbdefb',
          200: '#90caf9',
          300: '#64b5f6',
          400: '#42a5f5',
          500: '#1976d2',    // MUI 默认
          600: '#1565c0',
          700: '#0d47a1',
          800: '#0a3d91',
          900: '#062b6e',
          DEFAULT: '#1976d2',
        },

        // 涨跌色（A股习惯：红涨绿跌）
        up: '#ef4444',        // 涨（红）
        down: '#22c55e',      // 跌（绿）
        flat: '#6b7280',      // 平（灰）

        // 语义色
        warning: '#f59e0b',
        danger: '#dc2626',
        info: '#3b82f6',
        success: '#22c55e',

        // 背景色（深色主题）
        'bg-dark': '#0d1117',
        'bg-panel': '#161b22',
        'bg-hover': '#1c2128',
        'bg-active': '#1f2937',

        // 背景色（浅色主题）
        'bg-light': '#ffffff',
        'bg-light-panel': '#f6f8fa',
        'bg-light-hover': '#f3f4f6',

        // 边框色
        border: '#30363d',
        'border-light': '#d0d7de',

        // 文本色（深色主题）
        'text-primary': '#c9d1d9',
        'text-secondary': '#8b949e',
        'text-muted': '#6e7681',
        'text-link': '#58a6ff',

        // 文本色（浅色主题）
        'text-light-primary': '#1f2328',
        'text-light-secondary': '#656d76',

        // 理论颜色（7个）
        theory: {
          0: '#ef4444',  // 太极 - 红
          1: '#3b82f6',  // 螺旋 - 蓝
          2: '#f59e0b',  // 波浪 - 黄
          3: '#8b5cf6',  // 对偶 - 紫
          4: '#ec4899',  // 周期 - 粉
          5: '#14b8a6',  // 江恩 - 青
          6: '#f97316',  // BG均线 - 橙
        },

        // 置信度颜色
        'confidence-low': '#6b7280',
        'confidence-mid': '#f59e0b',
        'confidence-high': '#22c55e',
        'confidence-very-high': '#3b82f6',
      },

      // ========== 字体族 ==========
      fontFamily: {
        sans: ['"Inter"', '"PingFang SC"', '"Microsoft YaHei"', '"Helvetica Neue"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Roboto Mono"', '"Fira Code"', '"Consolas"', 'monospace'],
        financial: ['"JetBrains Mono"', '"Roboto Mono"', 'monospace'],
      },

      // ========== 圆角 ==========
      borderRadius: {
        'btn': '4px',
        'card': '6px',
        'dialog': '8px',
      },

      // ========== 间距（8px 栅格）==========
      spacing: {
        '0': '0px',
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
      },

      // ========== 动画 ==========
      animation: {
        'pulse-green': 'green-pulse 2s infinite',
        'blink-red': 'red-blink 1s infinite',
      },

      keyframes: {
        'green-pulse': {
          '0%': { boxShadow: '0 0 0 0 rgba(34, 197, 94, 0.7)' },
          '70%': { boxShadow: '0 0 0 6px rgba(34, 197, 94, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(34, 197, 94, 0)' },
        },
        'red-blink': {
          '0%, 49%': { opacity: '1' },
          '50%, 100%': { opacity: '0.3' },
        },
      },
    },
  },
  plugins: [],
  // 避免与 MUI 样式冲突
  corePlugins: {
    preflight: false,
  },
};

export default config;
