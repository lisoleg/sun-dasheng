import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import { getTheme } from './theme';
import { usePreferences } from './store/preferencesSlice';
import './index.css';

const AppWrapper: React.FC = () => {
  const themeMode = usePreferences((s) => s.themeMode);
  const theme = getTheme(themeMode);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppWrapper />
  </React.StrictMode>,
);
