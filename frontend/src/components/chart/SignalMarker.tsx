import React from 'react';
import type { ThemeMode } from '@/theme';

interface SignalMarkerProps {
  themeMode: ThemeMode;
}

const SignalMarker: React.FC<SignalMarkerProps> = ({ themeMode }) => {
  return (
    <div style={{ padding: 16, color: themeMode === 'dark' ? '#8b949e' : '#656d76' }}>
      <p>信号标记（T16 实现中）</p>
      <p style={{ fontSize: '12px' }}>置信度颜色编码</p>
    </div>
  );
};

export default SignalMarker;
