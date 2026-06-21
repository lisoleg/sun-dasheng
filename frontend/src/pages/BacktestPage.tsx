import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import type { ThemeMode } from '@/theme';
import BacktestConfigForm from '@/components/backtest/BacktestConfigForm';
import EquityCurveChart from '@/components/backtest/EquityCurveChart';

interface BacktestPageProps {
  themeMode?: ThemeMode;
}

/**
 * 回测页
 * PRD §4.3.4：配置 + 结果可视化
 * 
 * 布局：
 * - 左侧：配置面板（300px 固定）
 * - 右侧：结果区（Tab 切换）
 */
const BacktestPage: React.FC<BacktestPageProps> = ({ themeMode = 'dark' }) => {
  const [tab, setTab] = useState(0);
  const [running, setRunning] = useState(false);
  const [hasResult, setHasResult] = useState(false);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };

  const handleRunBacktest = () => {
    setRunning(true);
    // 模拟回测完成
    setTimeout(() => {
      setRunning(false);
      setHasResult(true);
    }, 3000);
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 48px - 28px)', overflow: 'hidden' }}>
      {/* 左侧配置面板 */}
      <Box
        sx={{
          width: 320,
          borderRight: 1,
          borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
          overflow: 'auto',
          p: 2,
        }}
      >
        <BacktestConfigForm onRun={handleRunBacktest} />
      </Box>

      {/* 右侧结果区 */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <Tabs value={tab} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="结果总览" />
          <Tab label="交易明细" />
          <Tab label="参数扫描" />
          <Tab label="导出报告" />
        </Tabs>

        {tab === 0 && (
          <Box>
            {running && (
              <Typography color="primary" sx={{ mb: 2 }}>
                回测运行中...
              </Typography>
            )}
            {hasResult && (
              <Box>
                <PerformanceMetrics themeMode={themeMode} />
                <EquityCurveChart themeMode={themeMode} />
              </Box>
            )}
            {!running && !hasResult && (
              <Typography color="text.secondary">
                请配置回测参数并点击"启动回测"
              </Typography>
            )}
          </Box>
        )}
        {tab === 1 && (
          <Typography color="text.secondary">
            交易明细（Phase 2.1 实现）
          </Typography>
        )}
        {tab === 2 && (
          <Typography color="text.secondary">
            参数扫描（Phase 2.1 实现）
          </Typography>
        )}
        {tab === 3 && (
          <Typography color="text.secondary">
            导出报告（Phase 2.1 实现）
          </Typography>
        )}
      </Box>
    </Box>
  );
};

// ==================== 绩效指标卡片 ===================
function PerformanceMetrics({ themeMode }: { themeMode: ThemeMode }) {
  const metrics = [
    { label: '总收益率', value: '35.0%', color: '#ef4444' },
    { label: '年化收益率', value: '18.2%', color: '#ef4444' },
    { label: '夏普比率', value: '1.85', color: '#58a6ff' },
    { label: '最大回撤', value: '-3.0%', color: '#22c55e' },
    { label: '胜率', value: '58.5%', color: '#58a6ff' },
    { label: '盈亏比', value: '1.65', color: '#58a6ff' },
  ];

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2, mb: 2 }}>
      {metrics.map((m) => (
        <Box
          key={m.label}
          sx={{
            p: 2,
            border: 1,
            borderColor: themeMode === 'dark' ? '#30363d' : '#d0d7de',
            borderRadius: 1,
          }}
        >
          <Typography variant="caption" color="textSecondary">
            {m.label}
          </Typography>
          <Typography variant="h6" sx={{ color: m.color, fontFamily: 'monospace' }}>
            {m.value}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

export default BacktestPage;
