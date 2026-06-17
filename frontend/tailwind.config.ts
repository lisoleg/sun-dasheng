import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e3f2fd',
          100: '#bbdefb',
          200: '#90caf9',
          300: '#64b5f6',
          400: '#42a5f5',
          500: '#1976d2',
          600: '#1565c0',
          700: '#0d47a1',
          800: '#0a3d91',
          900: '#062b6e',
        },
        long: '#f44336',
        short: '#4caf50',
        hold: '#ff9800',
      },
      fontFamily: {
        sans: ['"Roboto"', '"Helvetica"', '"Arial"', 'sans-serif'],
        mono: ['"Roboto Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
  // 避免与MUI样式冲突
  corePlugins: {
    preflight: false,
  },
};

export default config;
