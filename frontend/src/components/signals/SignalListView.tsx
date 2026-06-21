import React from 'react';
import { useState } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Visibility as VisibilityIcon } from '@mui/icons-material';

interface Signal {
  id: string;
  timestamp: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  price: number;
  confidence: number;
  theory: string;
  status: 'pending' | 'executed' | 'stopped';
}

const mockSignals: Signal[] = [
  {
    id: '1',
    timestamp: '2026-06-17 14:30:00',
    symbol: 'BTCUSDT',
    direction: 'BUY',
    price: 65000,
    confidence: 0.85,
    theory: 'taiji',
    status: 'executed',
  },
  {
    id: '2',
    timestamp: '2026-06-17 14:25:00',
    symbol: '000001.SZ',
    direction: 'SELL',
    price: 12.5,
    confidence: 0.72,
    theory: 'spiral',
    status: 'pending',
  },
  // 更多 Mock 数据...
];

export default function SignalListView() {
  const [signals] = useState<Signal[]>(mockSignals);

  const getDirectionColor = (direction: string) => {
    return direction === 'BUY' ? 'error' : 'success'; // 红涨绿跌
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'executed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'stopped':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        信号列表
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>时间</TableCell>
              <TableCell>标的</TableCell>
              <TableCell>方向</TableCell>
              <TableCell>价格</TableCell>
              <TableCell>置信度</TableCell>
              <TableCell>理论</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {signals.map((signal) => (
              <TableRow key={signal.id}>
                <TableCell>{signal.timestamp}</TableCell>
                <TableCell>{signal.symbol}</TableCell>
                <TableCell>
                  <Chip
                    label={signal.direction}
                    color={getDirectionColor(signal.direction) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                  {signal.price.toLocaleString()}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 60,
                        height: 8,
                        borderRadius: 4,
                        bgcolor: 'divider',
                        position: 'relative',
                        overflow: 'hidden',
                      }}
                    >
                      <Box
                        sx={{
                          width: `${signal.confidence * 100}%`,
                          height: '100%',
                          bgcolor:
                            signal.confidence >= 0.7
                              ? 'success.main'
                              : signal.confidence >= 0.4
                              ? 'warning.main'
                              : 'error.main',
                          borderRadius: 4,
                        }}
                      />
                    </Box>
                    <Typography variant="caption">
                      {(signal.confidence * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip label={signal.theory} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Chip
                    label={signal.status}
                    color={getStatusColor(signal.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title="查看详情">
                    <IconButton size="small">
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
