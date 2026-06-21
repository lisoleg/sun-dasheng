import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { usePreferences } from '@/store/preferencesSlice';

/**
 * 仪表盘首页
 * PRD §4.3.1：6 个默认面板
 * 
 * 布局：使用 Grid（暂不支持拖拽，T12 的 DraggableGrid 待集成）
 * 面板：多市场概览 / 账户总览 / 最近信号 / 盈亏曲线 / 理论状态 / 系统状态
 */
const DashboardPage: React.FC = () => {
  const { themeMode } = usePreferences();

  return (
    <Box sx={{ p: 2, height: 'calc(100vh - 48px - 28px)', overflow: 'auto' }}>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, fontSize: '18px' }}>
        仪表盘
      </Typography>

      {/* 面板网格 */}
      <Grid container spacing={2}>
        {/* 多市场概览 */}
        <Grid item xs={12} md={6}>
          <MarketOverviewPanel themeMode={themeMode} />
        </Grid>

        {/* 账户总览 */}
        <Grid item xs={12} md={6}>
          <AccountSummaryPanel themeMode={themeMode} />
        </Grid>

        {/* 最近信号 */}
        <Grid item xs={12} md={6}>
          <RecentSignalsPanel themeMode={themeMode} />
        </Grid>

        {/* 盈亏曲线 */}
        <Grid item xs={12}>
          <PnLCurvePanel themeMode={themeMode} />
        </Grid>

        {/* 理论引擎状态 */}
        <Grid item xs={12} md={6}>
          <TheoryStatusPanel themeMode={themeMode} />
        </Grid>

        {/* 系统状态 */}
        <Grid item xs={12} md={6}>
          <SystemStatusPanel themeMode={themeMode} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
