import { ThemeOptions } from '@mui/material/styles';
import { semanticColors } from './palette';

/**
 * 浅色主题
 * 参考：GitHub Light, TradingView Light
 */
export const lightTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    background: {
      default: semanticColors.bgLight,       // #ffffff 主背景
      paper: semanticColors.bgLightPanel,    // #f6f8fa 面板背景
    },
    primary: {
      main: '#0969da',                      // 蓝色（链接/按钮）
      light: '#54aeff',
      dark: '#0550ae',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#1a7f37',                     // 绿色（A股跌色）
      light: '#2da44e',
      dark: '#116329',
      contrastText: '#ffffff',
    },
    error: {
      main: '#cf222e',                      // 红色（A股涨色）
      light: '#f85149',
      dark: '#82071e',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#d4a72c',                      // 黄色（警告）
      light: '#eac54f',
      dark: '#9a6700',
      contrastText: '#000000',
    },
    info: {
      main: '#0969da',
      light: '#54aeff',
      dark: '#0550ae',
      contrastText: '#ffffff',
    },
    success: {
      main: '#1a7f37',
      light: '#2da44e',
      dark: '#116329',
      contrastText: '#ffffff',
    },
    text: {
      primary: semanticColors.textLightPrimary,    // #1f2328
      secondary: semanticColors.textLightSecondary,  // #656d76
    },
    divider: semanticColors.borderLight,            // #d0d7de
  },

  shape: {
    borderRadius: 6,
  },

  spacing: 8,

  components: {
    // ========== 全局样式注入 ==========
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: '#a0a0a0 #f0f0f0',
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': { width: 8, height: 8 },
          '&::-webkit-scrollbar-track': { background: '#f0f0f0' },
          '&::-webkit-scrollbar-thumb': { background: '#c0c0c0', borderRadius: 4 },
          '&::-webkit-scrollbar-thumb:hover': { background: '#a0a0a0' },
        },
      },
    },

    // ========== Card ==========
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: semanticColors.bgLight,
          backgroundImage: 'none',
          border: `1px solid ${semanticColors.borderLight}`,
          borderRadius: 6,
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        },
      },
    },

    // ========== Paper ==========
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: semanticColors.bgLight,
          backgroundImage: 'none',
          borderRadius: 6,
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        },
        elevation2: {
          boxShadow: '0 3px 6px rgba(0,0,0,0.12)',
        },
      },
    },

    // ========== AppBar ==========
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#f6f8fa',
          backgroundImage: 'none',
          borderBottom: `1px solid ${semanticColors.borderLight}`,
          boxShadow: 'none',
          color: semanticColors.textLightPrimary,
        },
      },
    },

    // ========== Drawer ==========
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#ffffff',
          borderRight: `1px solid ${semanticColors.borderLight}`,
        },
      },
    },

    // ========== TableCell ==========
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${semanticColors.borderLight}`,
        },
        head: {
          backgroundColor: '#f6f8fa',
          color: semanticColors.textLightSecondary,
          fontWeight: 600,
        },
      },
    },

    // ========== Dialog ==========
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: semanticColors.bgLight,
          border: `1px solid ${semanticColors.borderLight}`,
          boxShadow: '0 8px 24px rgba(0,0,0,0.16)',
          borderRadius: 8,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          backgroundColor: '#f6f8fa',
          borderBottom: `1px solid ${semanticColors.borderLight}`,
          padding: '12px 24px',
        },
      },
    },

    // ========== Button ==========
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 4,
          fontWeight: 500,
        },
      },
    },
  },
};
