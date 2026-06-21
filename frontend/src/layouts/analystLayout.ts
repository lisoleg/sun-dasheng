/**
 * 分析师布局（K线全宽 + 信号侧边）
 * 适合深度分析场景
 */
import type { Layout } from 'react-grid-layout';

const analystLayout: Layout[] = [
  { i: 'kline-chart', x: 0, y: 0, w: 8, h: 8, minW: 6, minH: 4 },
  { i: 'signal-detail', x: 8, y: 0, w: 4, h: 8, minW: 3, minH: 4 },
  { i: 'theory-overlay', x: 0, y: 8, w: 12, h: 3, minW: 6, minH: 2 },
];

export default analystLayout;
