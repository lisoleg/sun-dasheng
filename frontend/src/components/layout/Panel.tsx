import React from 'react';
import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import { MoreHorizontal } from 'lucide-react';
import type { ThemeMode } from '@/theme';

interface PanelProps {
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  themeMode?: ThemeMode;
  onMore?: () => void;
}

/**
 * 可拖拽面板容器
 * 标题栏可作为拖拽手柄（drag-handle class）
 */
const Panel: React.FC<PanelProps> = ({ title, children, actions, themeMode = 'dark', onMore }) => {
  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff',
        border: 1,
        borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <CardHeader
        title={
          <Typography variant="subtitle2" sx={{ fontSize: '13px', fontWeight: 600 }}>
            {title}
          </Typography>
        }
        action={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {actions}
            {onMore && (
              <IconButton size="small" onClick={onMore} sx={{ p: 0.5 }}>
                <MoreHorizontal size={14} />
              </IconButton>
            )}
          </Box>
        }
        className="drag-handle"
        sx={{
          cursor: 'move',
          p: 1,
          pb: 0.5,
          '& .MuiCardHeader-content': { overflow: 'hidden' },
        }}
      />
      <CardContent
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 1,
          pt: 0.5,
          '&:last-child': { pb: 1 },
        }}
      >
        {children}
      </CardContent>
    </Card>
  );
};

export default Panel;
