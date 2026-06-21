import React from 'react';
import type { ThemeMode } from '@/theme';

interface CrosshairSyncProps {
  themeMode: ThemeMode;
}

const CrosshairSync: React.FC<CrosshairSyncProps> = ({ themeMode }) => {
  return (
    <div style={{ padding: 16, color: themeMode === 'dark' ? '#8b949e' : '#656d76' }}>
      <p>十字光标联动（T16 实现中）</p>
      <p style={{ fontSize: '12px' }}>副图十字光标同步</p>
    </div>
  );
};

export default CrosshairSync;
