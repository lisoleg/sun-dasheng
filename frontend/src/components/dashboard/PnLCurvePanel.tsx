import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { ThemeMode } from '@/theme';

interface PnLCurvePanelProps {
  themeMode: ThemeMode;
}

const PnLCurvePanel: React.FC<PnLCurvePanelProps> = ({ themeMode }) => {
  return (
    <Card sx={{ height: '100%', bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1, fontSize: '14px', fontWeight: 600 }}>
          盈亏曲线
        </Typography>
        <Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Chart placeholder (recharts 实现）
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PnLCurvePanel;
