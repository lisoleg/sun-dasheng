import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

interface RiskGaugeProps {
  value: number;      // 当前值
  min?: number;      // 最小值
  max?: number;      // 最大值
  threshold?: number; // 阈值（超过显示警告色）
  label?: string;     // 标签
  unit?: string;      // 单位
}

/**
 * 风险仪表
 * 使用 SVG 弧形条展示风险指标
 */
const RiskGauge: React.FC<RiskGaugeProps> = ({
  value,
  min = 0,
  max = 100,
  threshold = 70,
  label = '风险',
  unit = '%',
}) => {
  const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const angle = (percentage / 100) * 180; // 180度半圆

  const getColor = () => {
    if (percentage < 30) return '#22c55e';  // 绿（安全）
    if (percentage < threshold) return '#f59e0b';  // 黄（警告）
    return '#ef4444';  // 红（危险）
  };

  const color = getColor();
  const radius = 60;
  const circumference = Math.PI * radius;
  const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 1 }}>
      <Box sx={{ position: 'relative', width: 140, height: 80 }}>
        {/* SVG 仪表 */}
        <svg width="140" height="80" viewBox="0 0 140 80">
          {/* 背景弧 */}
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke="#30363d"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeLinecap="round"
            transform="rotate(180 70 70)"
          />
          {/* 值弧 */}
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
            transform="rotate(180 70 70)"
            style={{ transition: 'stroke-dasharray 0.5s ease' }}
          />
        </svg>
        {/* 中心数值 */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            textAlign: 'center',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              color,
              fontWeight: 700,
              lineHeight: 1,
            }}
          >
            {value.toFixed(1)}{unit}
          </Typography>
        </Box>
      </Box>
      {label && (
        <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '11px', mt: 0.5 }}>
          {label}
        </Typography>
      )}
    </Box>
  );
};

export default RiskGauge;
