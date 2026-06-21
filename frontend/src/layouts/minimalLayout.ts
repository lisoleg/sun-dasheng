/**
 * 极简布局（1个全宽面板）
 * 用于快速查看单个指标
 */
import type { Layout } from 'react-grid-layout';

const minimalLayout: Layout[] = [
  { i: 'market-overview', x: 0, y: 0, w: 12, h: 8, minW: 6, minH: 4 },
];

export default minimalLayout;
