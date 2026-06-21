import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { ThemeMode } from '@/theme';

interface SystemStatusPanelProps {
  themeMode: ThemeMode;
}

const SystemStatusPanel: React.FC<SystemStatusPanelProps> = ({ themeMode }) => {
  const services = [
    { name: 'WS 连接', status: 'connected' as 'connected' | 'disconnected' },
    { name: '风控引擎', status: 'connected' as 'connected' | 'disconnected' },
    { name: 'Celery Worker', status: 'connected' as 'connected' | 'disconnected' },
    { name: 'Redis', status: 'connected' as 'connected' | 'disconnected' },
  ];

  return (
    <Card sx={{ height: '100%', bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1, fontSize: '14px', fontWeight: 600 }}>
          系统状态
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {services.map((s) => (
            <Box
              key={s.name}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 0.5,
              }}
            >
              <Typography variant="caption" sx={{ fontSize: '12px' }}>
                {s.name}
              </Typography>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: s.status === 'connected' ? '#22c55e' : '#ef4444',
                }}
              />
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemStatusPanel;
