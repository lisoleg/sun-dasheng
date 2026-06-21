import React from 'react';
import IconButton from '@mui/material/IconButton';
import { usePreferences } from '@/store/preferencesSlice';
import Sun from 'lucide-react/dist/Sun';
import Moon from 'lucide-react/dist/Moon';

interface ThemeToggleProps {
  size?: 'small' | 'medium';
}

/**
 * 主题切换按钮
 * 使用 Sun / Moon 图标
 */
const ThemeToggle: React.FC<ThemeToggleProps> = ({ size = 'medium' }) => {
  const { themeMode, setThemeMode } = usePreferences();

  const toggle = () => {
    setThemeMode(themeMode === 'dark' ? 'light' : 'dark');
  };

  return (
    <IconButton onClick={toggle} size={size} sx={{ p: 0.5 }}>
      {themeMode === 'dark' ? <Sun size={size === 'small' ? 16 : 20} /> : <Moon size={size === 'small' ? 16 : 20} />}
    </IconButton>
  );
};

export default ThemeToggle;
