import { create } from 'zustand';

/**
 * 用户偏好 Store（主题/布局）
 * T12 会扩展此文件
 */
export type ThemeMode = 'dark' | 'light';
export type LayoutTemplate = 'default' | 'minimal' | 'analyst' | 'custom';

interface PreferencesState {
  themeMode: ThemeMode;
  layoutTemplate: LayoutTemplate;
  setThemeMode: (mode: ThemeMode) => void;
  setLayoutTemplate: (template: LayoutTemplate) => void;
}

const storedTheme = localStorage.getItem('theme_mode') as ThemeMode | null;

export const usePreferences = create<PreferencesState>()((set) => ({
  themeMode: storedTheme || 'dark',
  layoutTemplate: 'default',

  setThemeMode: (mode) => {
    localStorage.setItem('theme_mode', mode);
    set({ themeMode: mode });
  },

  setLayoutTemplate: (template) => {
    localStorage.setItem('layout_template', template);
    set({ layoutTemplate: template });
  },
}));
