import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import type { ThemeMode } from '@/theme';

interface PerformanceMetricsProps {
  themeMode?: ThemeMode;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ themeMode = 'dark' }) => {
  const metrics = [
    { label: '总收益率', value: '25.43%' },
    { label: '年化收益率', value: '18.67%' },
    { label: '夏普比率', value: '1.82' },
    { label: '最大回撤', value: '-8.5%' },
    { label: '胜率', value: '58.3%' },
    { label: '盈亏比', value: '1.45' },
    { label: '卡尔玛比率', value: '1.23' },
    { label: '索提诺比率', value: '1.67' },
  ];

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontSize: '14px', fontWeight: 600 }}>
        绩效指标
      </Typography>
      <Grid container spacing={2}>
        {metrics.map((m) => (
          <Grid item xs={6} sm={4} md={3} key={m.label}>
            <Box
              sx={{
                p: 1.5,
                border: 1,
                borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
                borderRadius: 2,
              }}
            >
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '11px' }}>
                {m.label}
              </Typography>
              <Typography variant="h6" sx={{ fontSize: '1.25rem', fontWeight: 700 }}>
                {m.value}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default PerformanceMetrics;
