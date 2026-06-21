import React, { useEffect, useRef } from 'react';
import type { ThemeMode } from '@/theme';

interface KlineChartProps {
  symbol: string;
  timeFrame: string;
  themeMode: ThemeMode;
  onSignalClick?: (signal: unknown) => void;
}

/**
 * K线主图组件
 * 使用 lightweight-charts v4.2
 * T16 实现（骨架）
 */
const KlineChartComponent: React.FC<KlineChartProps> = ({
  symbol,
  timeFrame,
  themeMode,
  onSignalClick,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // TODO: T16 实现 lightweight-charts 集成
    console.log('[KlineChart] 加载', { symbol, timeFrame });
  }, [symbol, timeFrame]);

  return (
    <div
      ref={chartRef}
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: themeMode === 'dark' ? '#8b949e' : '#656d76',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <p>K线图表（T16 实现中）</p>
        <p style={{ fontSize: '12px' }}>{symbol} | {timeFrame}</p>
      </div>
    </div>
  );
};

export default KlineChartComponent;
