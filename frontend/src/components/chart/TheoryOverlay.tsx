import React from 'react';
import type { ThemeMode } from '@/theme';

interface TheoryOverlayProps {
  themeMode: ThemeMode;
}

const TheoryOverlay: React.FC<TheoryOverlayProps> = ({ themeMode }) => {
  return (
    <div style={{ padding: 16, color: themeMode === 'dark' ? '#8b949e' : '#656d76' }}>
      <p>理论叠加层（T16 实现中）</p>
      <p style={{ fontSize: '12px' }}>7个理论信号标注</p>
    </div>
  );
};

export default TheoryOverlay;
