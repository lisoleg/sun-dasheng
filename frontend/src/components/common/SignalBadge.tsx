import React from 'react';
import Chip from '@mui/material/Chip';
import type { ThemeMode } from '@/theme';

interface SignalBadgeProps {
  direction: 'BUY' | 'SELL' | 'HOLD';
  size?: 'small' | 'medium';
  themeMode?: ThemeMode;
}

/**
 * 信号方向徽章
 * BUY（红底白字）/ SELL（绿底白字）/ HOLD（灰底）
 */
const SignalBadge: React.FC<SignalBadgeProps> = ({ direction, size = 'small', themeMode = 'dark' }) => {
  const getConfig = () => {
    switch (direction) {
      case 'BUY':
        return {
          label: '买入',
          bgcolor: '#ef4444',  // 红（A股涨色）
          color: '#ffffff',
        };
      case 'SELL':
        return {
          label: '卖出',
          bgcolor: '#22c55e',  // 绿（A股跌色）
          color: '#ffffff',
        };
      case 'HOLD':
      default:
        return {
          label: '持有',
          bgcolor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
          color: themeMode === 'dark' ? '#c9d1d9' : '#1f2328',
        };
    }
  };

  const config = getConfig();

  return (
    <Chip
      label={config.label}
      size={size}
      sx={{
        bgcolor: config.bgcolor,
        color: config.color,
        fontWeight: 600,
        fontSize: '11px',
        height: size === 'small' ? 20 : 28,
        '& .MuiChip-label': { px: 1 },
      }}
    />
  );
};

export default SignalBadge;
