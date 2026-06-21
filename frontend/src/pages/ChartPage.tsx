import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import type { ThemeMode } from '@/theme';

interface ChartPageProps {
  themeMode?: ThemeMode;
}

/**
 * K线图表页
 * PRD §4.3.2：多时间周期 + 技术指标叠加
 * 
 * 布局：
 * - 顶部：标的切换 + 周期切换 + 指标开关
 * - 主图：K线（lightweight-charts）
 * - 副图1：成交量
 * - 副图2：MACD / KDJ / RSI（可选）
 */
const ChartPage: React.FC<ChartPageProps> = ({ themeMode = 'dark' }) => {
  const [timeframe, setTimeframe] = useState('1h');
  const [symbol, setSymbol] = useState('BTCUSDT');

  const timeframes = [
    { value: '1m', label: '1分' },
    { value: '5m', label: '5分' },
    { value: '15m', label: '15分' },
    { value: '1h', label: '1小时' },
    { value: '4h', label: '4小时' },
    { value: '1d', label: '日线' },
    { value: '1w', label: '周线' },
  ];

  return (
    <Box sx={{ p: 2, height: 'calc(100vh - 48px - 28px)', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部工具栏 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexShrink: 0 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '16px' }}>
          K线图表
        </Typography>

        <Select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          size="small"
          sx={{ minWidth: 140, height: 36 }}
        >
          <MenuItem value="BTCUSDT">BTC/USDT</MenuItem>
          <MenuItem value="ETHUSDT">ETH/USDT</MenuItem>
          <MenuItem value="000001.SZ">上证指数</MenuItem>
        </Select>

        <Box sx={{ display: 'flex', gap: 0.5, ml: 2 }}>
          {timeframes.map((tf) => (
            <Button
              key={tf.value}
              variant={timeframe === tf.value ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setTimeframe(tf.value)}
              sx={{ minWidth: 48, height: 32, fontSize: '12px' }}
            >
              {tf.label}
            </Button>
          ))}
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        {/* 指标开关 */}
        <Button variant="outlined" size="small" sx={{ height: 32 }}>
          指标
        </Button>
        <Button variant="outlined" size="small" sx={{ height: 32 }}>
          绘图
        </Button>
      </Box>

      {/* K线主图区域 */}
      <Box sx={{ flex: 1, bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff', border: 1, borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          K线图表区域（T16 实现中，使用 lightweight-charts）
        </Typography>
      </Box>

      {/* 副图：成交量 */}
      <Box sx={{ height: 120, mt: 1, bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff', border: 1, borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          成交量副图
        </Typography>
      </Box>
    </Box>
  );
};

export default ChartPage;
