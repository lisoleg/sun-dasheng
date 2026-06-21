import React, { useMemo, useCallback } from 'react';
import GridLayout, { Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

interface DraggableGridProps {
  children: React.ReactNode;
  layout: Layout[];
  onLayoutChange?: (layout: Layout[]) => void;
  cols?: number;
  rowHeight?: number;
  containerPadding?: [number, number];
  isDraggable?: boolean;
  isResizable?: boolean;
}

/**
 * react-grid-layout 包装器
 * 提供可拖拽、可调整大小的面板布局
 */
const DraggableGrid: React.FC<DraggableGridProps> = ({
  children,
  layout,
  onLayoutChange,
  cols = 12,
  rowHeight = 80,
  containerPadding = [8, 8],
  isDraggable = true,
  isResizable = true,
}) => {
  const handleLayoutChange = useCallback(
    (newLayout: Layout[]) => {
      if (onLayoutChange) {
        onLayoutChange(newLayout);
      }
    },
    [onLayoutChange],
  );

  const childArray = React.Children.toArray(children);

  return (
    <GridLayout
      className="layout"
      layout={layout}
      cols={cols}
      rowHeight={rowHeight}
      width={1200}  // 会被容器宽度覆盖
      containerPadding={containerPadding}
      isDraggable={isDraggable}
      isResizable={isResizable}
      draggableHandle=".drag-handle"
      onLayoutChange={handleLayoutChange}
      margin={[8, 8]}
      useCSSTransforms={true}
      preventCollision={false}
    >
      {childArray.map((child, idx) => {
        const key = layout[idx]?.i || `item-${idx}`;
        return (
          <div key={key}>
            {child}
          </div>
        );
      })}
    </GridLayout>
  );
};

export default DraggableGrid;
