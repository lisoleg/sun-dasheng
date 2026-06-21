import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { ThemeMode } from '@/theme';

interface TradeTableProps {
  themeMode?: ThemeMode;
}

const TradeTable: React.FC<TradeTableProps> = ({ themeMode = 'dark' }) => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontSize: '14px', fontWeight: 600 }}>
        交易明细
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          交易明细表（T18 实现中，使用 @mui/x-data-grid）
        </Typography>
      </Box>
    </Box>
  );
};

export default TradeTable;
