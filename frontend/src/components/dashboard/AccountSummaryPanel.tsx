import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { ThemeMode } from '@/theme';

interface AccountSummaryPanelProps {
  themeMode: ThemeMode;
}

/**
 * 账户总览面板
 * 总资产 / 日盈亏 / 总收益率 / 可用资金
 */
const AccountSummaryPanel: React.FC<AccountSummaryPanelProps> = ({ themeMode }) => {
  // 模拟数据
  const account = {
    totalEquity: 125430.56,
    dailyPnL: 3456.78,
    totalReturn: 25.43,
    availableCash: 45210.00,
    positionValue: 80220.56,
    riskExposure: 0.64,
  };

  return (
    <Card sx={{ height: '100%', bgcolor: themeMode === 'dark' ? '#161b22' : '#ffffff' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1, fontSize: '14px', fontWeight: 600 }}>
          账户总览
        </Typography>
        <Box sx={{ display: 'grid', gap: 1 }}>
          <MetricRow label="总资产" value={account.totalEquity} themeMode={themeMode} />
          <MetricRow label="日盈亏" value={account.dailyPnL} isPnL themeMode={themeMode} />
          <MetricRow label="总收益率" value={account.totalReturn} suffix="%" themeMode={themeMode} />
          <MetricRow label="可用资金" value={account.availableCash} themeMode={themeMode} />
          <MetricRow label="持仓市值" value={account.positionValue} themeMode={themeMode} />
          <MetricRow label="风险敞口" value={account.riskExposure} suffix="x" themeMode={themeMode} />
        </Box>
      </CardContent>
    </Card>
  );
};

const MetricRow: React.FC<{
  label: string;
  value: number;
  suffix?: string;
  isPnL?: boolean;
  themeMode: ThemeMode;
}> = ({ label, value, suffix = '', isPnL, themeMode }) => {
  const color = isPnL
    ? value >= 0 ? '#ef4444' : '#22c55e'
    : themeMode === 'dark' ? '#c9d1d9' : '#1f2328';

  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '11px' }}>
        {label}
      </Typography>
      <Typography
        variant="body2"
        sx={{
          fontFamily: '"JetBrains Mono", "Roboto Mono", monospace',
          color,
          fontWeight: 600,
          fontSize: '13px',
        }}
      >
        {value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{suffix}
      </Typography>
    </Box>
  );
};

export default AccountSummaryPanel;
