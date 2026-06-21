import React from 'react';
import type { ThemeMode } from '@/theme';

interface IndicatorPanelProps {
  themeMode: ThemeMode;
}

const IndicatorPanel: React.FC<IndicatorPanelProps> = ({ themeMode }) => {
  return (
    <div style={{ padding: 16, color: themeMode === 'dark' ? '#8b949e' : '#656d76' }}>
      <p>指标图层开关（T16 实现中）</p>
      <p style={{ fontSize: '12px' }}>BG均线 / 江恩 / 斐波那契</p>
    </div>
  );
};

export default IndicatorPanel;
