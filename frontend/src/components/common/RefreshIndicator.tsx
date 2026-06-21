import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

interface RefreshIndicatorProps {
  mode: 'real-time' | 'degraded' | 'manual';
  lastUpdate?: string;
}

/**
 * 刷新状态指示器
 * 实时=绿色脉冲 / 降级=黄色 / 手动=灰色
 */
const RefreshIndicator: React.FC<RefreshIndicatorProps> = ({ mode, lastUpdate }) => {
  const getConfig = () => {
    switch (mode) {
      case 'real-time':
        return { dotColor: '#22c55e', label: '实时', pulse: true };
      case 'degraded':
        return { dotColor: '#f59e0b', label: '降级', pulse: false };
      case 'manual':
        return { dotColor: '#6b7280', label: '手动', pulse: false };
    }
  };

  const config = getConfig();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '11px' }}>
      <Box
        sx={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          bgcolor: config.dotColor,
          ...(config.pulse && {
            animation: 'green-pulse 2s infinite',
          }),
        }}
      />
      <Typography variant="caption" sx={{ fontSize: '11px', color: 'text.secondary' }}>
        {config.label}
      </Typography>
      {lastUpdate && (
        <Typography variant="caption" sx={{ fontSize: '11px', color: 'text.muted' }}>
          {lastUpdate}
        </Typography>
      )}
    </Box>
  );
};

export default RefreshIndicator;
