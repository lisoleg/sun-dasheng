import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import type { ThemeMode } from '@/theme';

interface BacktestHistoryListProps {
  themeMode?: ThemeMode;
}

const BacktestHistoryList: React.FC<BacktestHistoryListProps> = ({ themeMode = 'dark' }) => {
  const mockHistory = [
    { id: 'bt-001', date: '2026-06-17', symbol: 'BTCUSDT', return: '25.43%', sharpe: '1.82' },
    { id: 'bt-002', date: '2026-06-16', symbol: 'ETHUSDT', return: '-8.5%', sharpe: '0.45' },
  ];

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontSize: '14px', fontWeight: 600 }}>
        回测历史
      </Typography>
      <List>
        {mockHistory.map((item) => (
          <ListItem key={item.id} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <ListItemText
              primary={item.symbol}
              secondary={`${item.date} | 收益率: ${item.return} | 夏普: ${item.sharpe}`}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default BacktestHistoryList;
