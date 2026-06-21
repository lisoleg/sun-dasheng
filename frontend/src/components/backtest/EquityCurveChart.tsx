import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Mock 数据（权益曲线）
const mockEquityData = [
  { date: '2024-01-01', equity: 10000, drawdown: 0 },
  { date: '2024-02-01', equity: 10500, drawdown: 0 },
  { date: '2024-03-01', equity: 10200, drawdown: -0.03 },
  { date: '2024-04-01', equity: 11000, drawdown: 0 },
  { date: '2024-05-01', equity: 10800, drawdown: -0.02 },
  { date: '2024-06-01', equity: 11500, drawdown: 0 },
  { date: '2024-07-01', equity: 12000, drawdown: 0 },
  { date: '2024-08-01', equity: 11800, drawdown: -0.02 },
  { date: '2024-09-01', equity: 12500, drawdown: 0 },
  { date: '2024-10-01', equity: 13000, drawdown: 0 },
  { date: '2024-11-01', equity: 12800, drawdown: -0.015 },
  { date: '2024-12-01', equity: 13500, drawdown: 0 },
];

interface EquityCurveChartProps {
  themeMode?: 'dark' | 'light';
}

export default function EquityCurveChart({ themeMode = 'dark' }: EquityCurveChartProps) {
  const textColor = themeMode === 'dark' ? '#c9d1d9' : '#1f2937';
  const gridColor = themeMode === 'dark' ? '#30363d' : '#e5e7eb';

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        权益曲线
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={mockEquityData}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis dataKey="date" tick={{ fill: textColor, fontSize: 12 }} />
          <YAxis tick={{ fill: textColor, fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: themeMode === 'dark' ? '#161b22' : '#ffffff',
              border: `1px solid ${gridColor}`,
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#58a6ff"
            strokeWidth={2}
            dot={false}
            name="权益"
          />
          <Line
            type="monotone"
            dataKey="drawdown"
            stroke="#ef4444"
            strokeWidth={1}
            dot={false}
            name="回撤"
          />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
}
