import { createTheme, ThemeOptions } from '@mui/material/styles';
import { semanticColors } from './palette';
import { fontConfig } from './typography';

/**
 * Bloomberg 风深色主题
 * 参考：GitHub Dark, TradingView Dark
 */
export const darkTheme: ThemeOptions = {
  palette: {
    mode: 'dark',
    background: {
      default: semanticColors.bgDark,      // #0d1117 主背景
      paper: semanticColors.bgPanel,       // #161b22 面板背景
    },
    primary: {
      main: '#58a6ff',                      // 蓝色（链接/按钮）
      light: '#79c0ff',
      dark: '#388bf2',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#3fb950',                      // 绿色（涨/盈利）
      light: '#56d364',
      dark: '#2ea043',
      contrastText: '#ffffff',
    },
    error: {
      main: '#ef4444',                      // 红色（跌/亏损/A股涨色）
      light: '#f87171',
      dark: '#dc2626',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#f59e0b',                      // 黄色（警告）
      light: '#fbbf24',
      dark: '#d97706',
      contrastText: '#000000',
    },
    info: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#2563eb',
      contrastText: '#ffffff',
    },
    success: {
      main: '#22c55e',
      light: '#4ade80',
      dark: '#16a34a',
      contrastText: '#ffffff',
    },
    text: {
      primary: semanticColors.textPrimary,    // #c9d1d9
      secondary: semanticColors.textSecondary,  // #8b949e
      disabled: semanticColors.textMuted,      // #6e7681
    },
    divider: semanticColors.border,            // #30363d
    action: {
      active: '#58a6ff',
      hover: 'rgba(88, 166, 255, 0.08)',
      selected: 'rgba(88, 166, 255, 0.12)',
      disabled: 'rgba(139, 148, 158, 0.38)',
      disabledBackground: 'rgba(139, 148, 158, 0.12)',
    },
  },

  typography: {
    fontFamily: fontConfig.sans,
    fontFamilyMonospace: fontConfig.mono,
    h1: { fontSize: fontConfig.fontSize['4xl'], fontWeight: fontConfig.fontWeight.bold },
    h2: { fontSize: fontConfig.fontSize['3xl'], fontWeight: fontConfig.fontWeight.bold },
    h3: { fontSize: fontConfig.fontSize['2xl'], fontWeight: fontConfig.fontWeight.semibold },
    h4: { fontSize: fontConfig.fontSize.xl, fontWeight: fontConfig.fontWeight.semibold },
    h5: { fontSize: fontConfig.fontSize.lg, fontWeight: fontConfig.fontWeight.semibold },
    h6: { fontSize: fontConfig.fontSize.base, fontWeight: fontConfig.fontWeight.semibold },
    body1: { fontSize: fontConfig.fontSize.base, lineHeight: fontConfig.lineHeight.normal },
    body2: { fontSize: fontConfig.fontSize.sm, lineHeight: fontConfig.lineHeight.normal },
    caption: { fontSize: fontConfig.fontSize.xs, lineHeight: fontConfig.lineHeight.normal },
    button: { fontSize: fontConfig.fontSize.sm, fontWeight: fontConfig.fontWeight.medium, fontFamily: fontConfig.sans },
    overline: { fontSize: fontConfig.fontSize.xs, fontWeight: fontConfig.fontWeight.medium },
  },

  shape: {
    borderRadius: 6,    // 卡片/按钮圆角（PRD 要求 6px）
  },

  spacing: 8,    // 8px 基准栅格

  components: {
    // ========== 全局样式注入 ==========
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: '#6b6b6b #0d1117',
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': { width: 8, height: 8 },
          '&::-webkit-scrollbar-track': { background: '#0d1117' },
          '&::-webkit-scrollbar-thumb': { background: '#30363d', borderRadius: 4 },
          '&::-webkit-scrollbar-thumb:hover': { background: '#484f58' },
          // 金融数字等宽
          '.financial-number': {
            fontFamily: fontConfig.mono,
            textAlign: 'right',
          },
        },
        // 代码块等宽
        'code, pre': {
          fontFamily: fontConfig.mono,
        },
      },
    },

    // ========== Card ==========
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: semanticColors.bgPanel,
          backgroundImage: 'none',
          border: `1px solid ${semanticColors.border}`,
          borderRadius: 6,
          '&:hover': {
            borderColor: '#484f58',
          },
        },
      },
    },

    // ========== Paper ==========
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: semanticColors.bgPanel,
          backgroundImage: 'none',
          borderRadius: 6,
        },
      },
    },

    // ========== AppBar ==========
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#161b22',
          backgroundImage: 'none',
          borderBottom: `1px solid ${semanticColors.border}`,
          boxShadow: 'none',
        },
      },
    },

    // ========== Drawer ==========
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#0d1117',
          borderRight: `1px solid ${semanticColors.border}`,
        },
      },
    },

    // ========== ListItem ==========
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          '&.Mui-selected': {
            backgroundColor: 'rgba(88, 166, 255, 0.12)',
            '&:hover': { backgroundColor: 'rgba(88, 166, 255, 0.18)' },
          },
        },
      },
    },

    // ========== Button ==========
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',    // 不自动大写
          borderRadius: 4,
          fontWeight: fontConfig.fontWeight.medium,
        },
        containedPrimary: {
          backgroundColor: '#58a6ff',
          '&:hover': { backgroundColor: '#79c0ff' },
        },
      },
    },

    // ========== Table ==========
    MuiTable: {
      styleOverrides: {
        root: {
          fontFamily: fontConfig.mono,    // 表格数字等宽
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${semanticColors.border}`,
          fontFamily: fontConfig.mono,    // 数字等宽
          fontSize: fontConfig.fontSize.sm,
        },
        head: {
          backgroundColor: '#1c2128',
          color: semanticColors.textSecondary,
          fontWeight: fontConfig.fontWeight.medium,
        },
      },
    },

    // ========== Chip ==========
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
      },
    },

    // ========== Tooltip ==========
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#1c2128',
          border: `1px solid ${semanticColors.border}`,
          fontSize: fontConfig.fontSize.xs,
          fontFamily: fontConfig.sans,
        },
      },
    },

    // ========== LinearProgress ==========
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: '#21262d',
          borderRadius: 4,
          height: 6,
        },
        bar: {
          borderRadius: 4,
        },
      },
    },

    // ========== Tabs ==========
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: fontConfig.fontWeight.medium,
        },
      },
    },

    // ========== Select ==========
    MuiSelect: {
      styleOverrides: {
        select: {
          fontFamily: fontConfig.sans,
        },
      },
    },

    // ========== Input ==========
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          fontFamily: fontConfig.sans,
          fontSize: fontConfig.fontSize.sm,
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: semanticColors.border,
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#484f58',
          },
        },
      },
    },

    // ========== Dialog ==========
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: semanticColors.bgPanel,
          border: `1px solid ${semanticColors.border}`,
          borderRadius: 8,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          backgroundColor: '#1c2128',
          borderBottom: `1px solid ${semanticColors.border}`,
          padding: '12px 24px',
        },
      },
    },

    // ========== Menu ==========
    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundColor: semanticColors.bgPanel,
          border: `1px solid ${semanticColors.border}`,
          marginTop: 4,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontFamily: fontConfig.sans,
          fontSize: fontConfig.fontSize.sm,
          '&:hover': {
            backgroundColor: 'rgba(88, 166, 255, 0.08)',
          },
        },
      },
    },

    // ========== Badge ==========
    MuiBadge: {
      styleOverrides: {
        badge: {
          fontSize: fontConfig.fontSize.xs,
          fontWeight: fontConfig.fontWeight.medium,
          minWidth: 16,
          height: 16,
          padding: '0 4px',
        },
      },
    },

    // ========== Snackbar ==========
    MuiSnackbarContent: {
      styleOverrides: {
        root: {
          fontFamily: fontConfig.sans,
          fontSize: fontConfig.fontSize.sm,
        },
      },
    },

    // ========== Accordion ==========
    MuiAccordion: {
      styleOverrides: {
        root: {
          backgroundColor: semanticColors.bgPanel,
          border: `1px solid ${semanticColors.border}`,
          '&:before': { display: 'none' },    // 去掉默认阴影线
          '&.Mui-expanded': {
            margin: 0,
          },
        },
      },
    },
    MuiAccordionSummary: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${semanticColors.border}`,
          minHeight: 40,
        },
      },
    },
  },
};

export default createTheme(darkTheme);
