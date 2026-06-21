import React from 'react';
import Chip from '@mui/material/Chip';

type TheoryName = 'taiji' | 'spiral' | 'elliott' | 'dual' | 'cycle' | 'gann' | 'bg_ma';

interface TheoryTagProps {
  theory: TheoryName;
  showLabel?: boolean;
  size?: 'small' | 'medium';
}

const THEORY_CONFIG: Record<TheoryName, { label: string; color: string }> = {
  taiji: { label: '太极', color: '#ef4444' },
  spiral: { label: '螺旋', color: '#3b82f6' },
  elliott: { label: '波浪', color: '#f59e0b' },
  dual: { label: '对偶', color: '#8b5cf6' },
  cycle: { label: '周期', color: '#ec4899' },
  gann: { label: '江恩', color: '#14b8a6' },
  bg_ma: { label: 'BG均线', color: '#f97316' },
};

/**
 * 理论标签
 * 7种颜色，对应7个理论
 */
const TheoryTag: React.FC<TheoryTagProps> = ({ theory, showLabel = true, size = 'small' }) => {
  const config = THEORY_CONFIG[theory];

  return (
    <Chip
      label={showLabel ? config.label : ''}
      size={size}
      sx={{
        bgcolor: `${config.color}20`,  // 20 = 12% 透明度
        color: config.color,
        border: `1px solid ${config.color}`,
        fontWeight: 500,
        fontSize: '11px',
        height: size === 'small' ? 20 : 28,
        '& .MuiChip-label': { px: 0.75 },
      }}
    />
  );
};

export default TheoryTag;
