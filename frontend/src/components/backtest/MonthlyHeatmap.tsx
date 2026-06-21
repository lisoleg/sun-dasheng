import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { ThemeMode } from '@/theme';

interface MonthlyHeatmapProps {
  themeMode?: ThemeMode;
}

const MonthlyHeatmap: React.FC<MonthlyHeatmapProps> = ({ themeMode = 'dark' }) => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontSize: '14px', fontWeight: 600 }}>
        月度收益热力图
      </Typography>
      <Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          月度收益热力图（T18 实现中，使用 recharts）
        </Typography>
      </Box>
    </Box>
  );
};

export default MonthlyHeatmap;
