/**
 * 默认布局配置（给 react-grid-layout 用）
 * PRD §4.2：6 个默认面板
 */
import type { Layout } from 'react-grid-layout';

export const defaultLayout: Layout[] = [
  { i: 'market-overview', x: 0, y: 0, w: 6, h: 4, minW: 4, minH: 3 },
  { i: 'account-summary', x: 6, y: 0, w: 6, h: 3, minW: 4, minH: 2 },
  { i: 'recent-signals', x: 6, y: 3, w: 6, h: 3, minW: 4, minH: 2 },
  { i: 'pnl-curve', x: 0, y: 4, w: 12, h: 4, minW: 6, minH: 3 },
  { i: 'theory-status', x: 0, y: 8, w: 6, h: 3, minW: 4, minH: 2 },
  { i: 'system-status', x: 6, y: 8, w: 6, h: 3, minW: 4, minH: 2 },
];

export default defaultLayout;
