import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

interface ConfidenceBarProps {
  value: number;  // 0-1
  height?: number;
  showLabel?: boolean;
}

/**
 * 置信度进度条
 * 颜色：<0.3 灰，0.3-0.6 黄，>0.6 绿
 */
const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ value, height = 6, showLabel = true }) => {
  const getColor = () => {
    if (value < 0.3) return '#6b7280';  // 灰
    if (value < 0.6) return '#f59e0b';  // 黄
    return '#22c55e';  // 绿
  };

  const color = getColor();
  const percentage = Math.min(100, Math.max(0, value * 100));

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, width: '100%' }}>
      <Box
        sx={{
          flex: 1,
          height,
          bgcolor: 'rgba(255,255,255,0.08)',
          borderRadius: height / 2,
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            width: `${percentage}%`,
            height: '100%',
            bgcolor: color,
            borderRadius: height / 2,
            transition: 'width 0.3s ease',
          }}
        />
      </Box>
      {showLabel && (
        <Typography
          variant="caption"
          sx={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: '11px',
            color,
            minWidth: 32,
            textAlign: 'right',
          }}
        >
          {(value * 100).toFixed(0)}%
        </Typography>
      )}
    </Box>
  );
};

export default ConfidenceBar;
