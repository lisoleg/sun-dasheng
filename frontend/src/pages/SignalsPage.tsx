import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import type { ThemeMode } from '@/theme';
import SignalListView from '@/components/signals/SignalListView';

interface SignalsPageProps {
  themeMode?: ThemeMode;
}

/**
 * 信号中心页
 * PRD §4.3.3：列表/卡片双视图 + 筛选
 * 
 * 布局：
 * - 顶部：视图切换 + 筛选栏
 * - 主区域：信号列表/卡片
 * - 详情弹窗：点击信号打开
 */
const SignalsPage: React.FC<SignalsPageProps> = ({ themeMode = 'dark' }) => {
  const [viewMode, setViewMode] = useState<'list' | 'card'>('list');
  const [filterOpen, setFilterOpen] = useState(false);

  return (
    <Box sx={{ p: 2, height: 'calc(100vh - 48px - 28px)', overflow: 'auto' }}>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, fontSize: '18px' }}>
        信号中心
      </Typography>

      {/* 顶部工具栏 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Button
          variant={viewMode === 'list' ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setViewMode('list')}
        >
          列表
        </Button>
        <Button
          variant={viewMode === 'card' ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setViewMode('card')}
        >
          卡片
        </Button>

        <Box sx={{ flexGrow: 1 }} />

        <Button
          variant="outlined"
          size="small"
          onClick={() => setFilterOpen(!filterOpen)}
        >
          筛选
        </Button>
      </Box>

      {/* 筛选栏 */}
      {filterOpen && (
        <Box sx={{ mb: 2, p: 1, border: 1, borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de', borderRadius: 1 }}>
          <Typography variant="caption">筛选栏（标的/方向/置信度/理论/时间）</Typography>
        </Box>
      )}

      {/* 信号列表/卡片 */}
      <Box sx={{ flex: 1 }}>
        {viewMode === 'list' ? (
          <SignalListView />
        ) : (
          <Box sx={{ color: 'text.secondary' }}>信号卡片视图（Phase 2.1 实现）</Box>
        )}
      </Box>
    </Box>
  );
};

export default SignalsPage;
