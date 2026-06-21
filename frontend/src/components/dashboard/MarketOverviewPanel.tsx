import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { LineChart } from 'recharts';
import type { ThemeMode } from '@/theme';

interface MarketOverviewPanelProps {
  themeMode: ThemeMode;
}

/**
 * 多市场概览面板
 * 展示 A股指数 + 币安标的
 */
const MarketOverviewPanel: React.FC<MarketOverviewPanelProps> = ({ themeMode }) => {
  // 模拟数据（实际应从 API 获取）
  const marketData = [
    { name: '上证指数', price: 3245.67, change: 1.23 },
    { name: '深证成指', price: 11234.56, change: -0.45 },
    { name: '创业板', price: 2234.89, change: 2.34 },
    { name: '科创50', price: 987.65, change: 0.78 },
    { name: '沪深300', price: 3876.54, change: 0.92 },
    { name: '中证500', price: 6123.45, change: -0.23 },
    { name: 'BTC/USDT', price: 65432.10, change: 3.45 },
    { name: 'ETH/USDT', price: 3456.78, change: 2.12 },
    { name: 'BNB/USDT', price: 567.89, change: -1.23 },
    { name: 'SOL/USDT', price: 123.45, change: 5.67 },
    { name: 'XRP/USDT', price: 0.5678, change: -2.34 },
    { name: 'ADA/USDT', price: 0.4321, change: 1.89 },
  ];

  return (
    <Card sx={{ height: '100%', bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1, fontSize: '14px', fontWeight: 600 }}>
          多市场概览
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 1 }}>
          {marketData.map((item) => (
            <Box
              key={item.name}
              sx={{
                p: 1,
                border: 1,
                borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
                borderRadius: 1,
                cursor: 'pointer',
                '&:hover': { borderColor: '#58a6ff' },
              }}
            >
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '11px' }}>
                {item.name}
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  fontFamily: '"JetBrains Mono", monospace',
                  textAlign: 'right',
                  color: item.change >= 0 ? '#ef4444' : '#22c55e',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                {item.price.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: item.change >= 0 ? '#ef4444' : '#22c55e',
                  fontSize: '11px',
                  fontWeight: 500,
                }}
              >
                {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)}%
              </Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default MarketOverviewPanel;
