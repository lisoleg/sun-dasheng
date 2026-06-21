import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { ThemeMode } from '@/theme';

interface TheoryStatusPanelProps {
  themeMode: ThemeMode;
}

const TheoryStatusPanel: React.FC<TheoryStatusPanelProps> = ({ themeMode }) => {
  const theories = [
    { name: '太极', enabled: true, signals: 12, confidence: 0.85 },
    { name: '螺旋', enabled: true, signals: 8, confidence: 0.72 },
    { name: '波浪', enabled: true, signals: 5, confidence: 0.68 },
    { name: '对偶', enabled: false, signals: 0, confidence: 0 },
    { name: '周期', enabled: false, signals: 0, confidence: 0 },
    { name: '江恩', enabled: false, signals: 0, confidence: 0 },
    { name: 'BG均线', enabled: true, signals: 15, confidence: 0.78 },
  ];

  return (
    <Card sx={{ height: '100%', bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1, fontSize: '14px', fontWeight: 600 }}>
          理论引擎状态
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {theories.map((t) => (
            <Box
              key={t.name}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 0.5,
                opacity: t.enabled ? 1 : 0.5,
              }}
            >
              <Typography variant="caption" sx={{ fontSize: '12px' }}>
                {t.name}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '11px', color: 'text.secondary' }}>
                  {t.signals} 信号
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '11px' }}>
                  {(t.confidence * 100).toFixed(0)}%
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default TheoryStatusPanel;
