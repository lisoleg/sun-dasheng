import { createTheme, ThemeOptions } from '@mui/material/styles';
import { darkTheme } from './darkTheme';
import { lightTheme } from './lightTheme';

export const getTheme = (mode: 'dark' | 'light') =>
  createTheme(mode === 'dark' ? darkTheme : lightTheme);

export type ThemeMode = 'dark' | 'light';

export { darkTheme, lightTheme };
