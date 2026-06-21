import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { usePreferences } from '@/store/preferencesSlice';

/**
 * 底部状态栏（28px）
 * 左侧：WS 连接状态 / Celery 任务状态 / Redis 状态
 * 右侧：当前市场时间 / 系统版本
 */
const StatusBar: React.FC = () => {
  const { themeMode } = usePreferences();

  // 模拟状态（实际应从 wsSlice 获取）
  const wsConnected = true;
  const celeryStatus = 'running' as 'running' | 'stopped' | 'error';
  const redisStatus = 'connected' as 'connected' | 'disconnected';

  const getStatusDot = (isGood: boolean) => (
    <Box
      sx={{
        width: 6,
        height: 6,
        borderRadius: '50%',
        bgcolor: isGood ? '#22c55e' : '#ef4444',
        mr: 0.5,
        flexShrink: 0,
      }}
    />
  );

  return (
    <Box
      component="footer"
      sx={{
        height: 28,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 1.5,
        py: 0,
        bgcolor: themeMode === 'dark' ? '#0d1117' : '#f6f8fa',
        borderTop: 1,
        borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
        fontSize: '11px',
        fontFamily: '"JetBrains Mono", monospace',
        color: themeMode === 'dark' ? '#8b949e' : '#656d76',
        zIndex: (theme) => theme.zIndex.drawer + 2,
      }}
    >
      {/* 左侧状态 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* WS 连接状态 */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {getStatusDot(wsConnected)}
          <Typography variant="caption" sx={{ fontSize: '11px' }}>
            {wsConnected ? '🟢 WS 已连接' : '🔴 WS 断开'}
          </Typography>
        </Box>

        {/* Celery 状态 */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {getStatusDot(celeryStatus === 'running')}
          <Typography variant="caption" sx={{ fontSize: '11px' }}>
            Celery: {celeryStatus}
          </Typography>
        </Box>

        {/* Redis 状态 */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {getStatusDot(redisStatus === 'connected')}
          <Typography variant="caption" sx={{ fontSize: '11px' }}>
            Redis: {redisStatus}
          </Typography>
        </Box>

        {/* 最后更新时间 */}
        <Typography variant="caption" sx={{ fontSize: '11px', ml: 2 }}>
          最后更新: {new Date().toLocaleTimeString('zh-CN')}
        </Typography>
      </Box>

      {/* 右侧信息 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* 市场时间 */}
        <Typography variant="caption" sx={{ fontSize: '11px' }}>
          A股: {isMarketOpen() ? '开市中' : '已收盘'} | 币安: 24h
        </Typography>

        {/* 系统版本 */}
        <Typography variant="caption" sx={{ fontSize: '11px' }}>
          v0.2.0
        </Typography>
      </Box>
    </Box>
  );
};

/** 判断 A股是否开市（09:30-15:00 工作日）*/
const isMarketOpen = (): boolean => {
  const now = new Date();
  const day = now.getDay();
  if (day === 0 || day === 6) return false; // 周末
  const hour = now.getHours();
  const minute = now.getMinutes();
  const time = hour * 60 + minute;
  return (time >= 9 * 60 + 30 && time <= 11 * 60 + 30) || (time >= 13 * 60 && time <= 15 * 60);
};

export default StatusBar;
