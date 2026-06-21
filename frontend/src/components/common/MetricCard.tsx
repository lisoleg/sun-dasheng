import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { ThemeMode } from '@/theme';

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;  // 涨跌值
  trend?: 'up' | 'down' | 'flat';
  format?: 'currency' | 'percent' | 'number';
  prefix?: string;  // 前缀（如 ¥, $, USDT）
  suffix?: string;  // 后缀（如 %, 元）
  themeMode?: ThemeMode;
}

/**
 * 数值指标卡
 * 用于仪表盘展示关键指标
 */
const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  trend = 'flat',
  format = 'number',
  prefix = '',
  suffix = '',
  themeMode = 'dark',
}) => {
  const getColor = () => {
    if (trend === 'up') return '#ef4444';  // 涨（红，A股习惯）
    if (trend === 'down') return '#22c55e';  // 跌（绿）
    return themeMode === 'dark' ? '#c9d1d9' : '#1f2328';
  };

  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    switch (format) {
      case 'currency':
        return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      case 'percent':
        return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`;
      case 'number':
      default:
        return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
  };

  const color = getColor();

  return (
    <Card
      sx={{
        height: '100%',
        bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff',
        border: 1,
        borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
        borderRadius: 2,
      }}
    >
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Typography
          variant="caption"
          sx={{ color: themeMode === 'dark' ? '#8b949e' : '#656d76', fontSize: '11px' }}
        >
          {title}
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontFamily: '"JetBrains Mono", "Roboto Mono", monospace',
            color,
            textAlign: 'right',
            fontSize: '1.5rem',
            fontWeight: 700,
            mt: 0.5,
          }}
        >
          {prefix}{formatValue(value)}{suffix}
        </Typography>
        {change !== undefined && (
          <Typography
            variant="caption"
            sx={{
              color: change >= 0 ? '#ef4444' : '#22c55e',
              fontSize: '12px',
              fontWeight: 500,
              mt: 0.5,
              display: 'block',
            }}
          >
            {change >= 0 ? '+' : ''}{change.toFixed(2)}{suffix || ''}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
