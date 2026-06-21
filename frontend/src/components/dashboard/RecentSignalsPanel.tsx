import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { ThemeMode } from '@/theme';

interface RecentSignalsPanelProps {
  themeMode: ThemeMode;
}

/**
 * 最近信号面板
 * 显示最近 10 条信号
 */
const RecentSignalsPanel: React.FC<RecentSignalsPanelProps> = ({ themeMode }) => {
  // 模拟数据
  const signals = [
    { id: 1, time: '12:34:56', symbol: 'BTCUSDT', direction: 'BUY', confidence: 0.92 },
    { id: 2, time: '12:30:12', symbol: 'ETHUSDT', direction: 'SELL', confidence: 0.78 },
    { id: 3, time: '12:25:44', symbol: '000001.SZ', direction: 'BUY', confidence: 0.56 },
  ];

  return (
    <Card sx={{ height: '100%', bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1, fontSize: '14px', fontWeight: 600 }}>
          最近信号
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {signals.map((signal) => (
            <Box
              key={signal.id}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 0.5,
                borderBottom: 1,
                borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
              }}
            >
              <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '11px' }}>
                {signal.time}
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '12px' }}>
                {signal.symbol}
              </Typography>
              <Box
                sx={{
                  bgcolor: signal.direction === 'BUY' ? '#ef4444' : '#22c55e',
                  color: '#fff',
                  px: 0.5,
                  borderRadius: 0.5,
                  fontSize: '10px',
                }}
              >
                {signal.direction === 'BUY' ? '买入' : '卖出'}
              </Box>
              <Typography variant="caption" sx={{ fontSize: '11px' }}>
                {(signal.confidence * 100).toFixed(0)}%
              </Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default RecentSignalsPanel;
