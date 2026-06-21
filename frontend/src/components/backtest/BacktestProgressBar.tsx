import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import type { ThemeMode } from '@/theme';

interface BacktestProgressBarProps {
  themeMode?: ThemeMode;
}

const BacktestProgressBar: React.FC<BacktestProgressBarProps> = ({ themeMode = 'dark' }) => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontSize: '14px', fontWeight: 600 }}>
        回测进度
      </Typography>
      <LinearProgress variant="indeterminate" sx={{ mb: 1 }} />
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        T18 实现中：进度条（WS 实时更新）
      </Typography>
    </Box>
  );
};

export default BacktestProgressBar;
