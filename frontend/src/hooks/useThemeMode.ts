import { useCallback } from 'react';
import { usePreferences } from '@/store/preferencesSlice';

/**
 * 主题切换 Hook
 */
export function useThemeMode() {
  const { themeMode, setThemeMode } = usePreferences();

  const toggleTheme = useCallback(() => {
    setThemeMode(themeMode === 'dark' ? 'light' : 'dark');
  }, [themeMode, setThemeMode]);

  const setDark = useCallback(() => {
    setThemeMode('dark');
  }, [setThemeMode]);

  const setLight = useCallback(() => {
    setThemeMode('light');
  }, [setThemeMode]);

  return {
    themeMode,
    toggleTheme,
    setDark,
    setLight,
    setThemeMode,
  };
}
