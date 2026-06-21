import { useState, useCallback } from 'react';
import type { Layout } from 'react-grid-layout';

/**
 * 布局模板保存/加载（localStorage）
 */
export function useLayoutTemplate() {
  const saveTemplate = useCallback((name: string, layout: Layout[]) => {
    localStorage.setItem(`layout_${name}`, JSON.stringify(layout));
  }, []);

  const loadTemplate = useCallback((name: string): Layout[] => {
    const data = localStorage.getItem(`layout_${name}`);
    if (data) {
      try {
        return JSON.parse(data) as Layout[];
      } catch {
        return getDefaultLayout(name);
      }
    }
    return getDefaultLayout(name);
  }, []);

  const getAvailableTemplates = useCallback((): Array<{ name: string; label: string }> => {
    return [
      { name: 'default', label: '默认布局' },
      { name: 'minimal', label: '极简布局' },
      { name: 'analyst', label: '分析师布局' },
    ];
  }, []);

  return { saveTemplate, loadTemplate, getAvailableTemplates };
}

function getDefaultLayout(name: string): Layout[] {
  // 硬编码默认布局（避免循环依赖）
  const defaultLayouts: Record<string, Layout[]> = {
    default: [
      { i: 'market-overview', x: 0, y: 0, w: 6, h: 4 },
      { i: 'account-summary', x: 6, y: 0, w: 6, h: 3 },
      { i: 'recent-signals', x: 6, y: 3, w: 6, h: 3 },
    ],
    minimal: [
      { i: 'market-overview', x: 0, y: 0, w: 12, h: 4 },
    ],
    analyst: [
      { i: 'kline-chart', x: 0, y: 0, w: 12, h: 6 },
      { i: 'signals', x: 0, y: 6, w: 6, h: 4 },
    ],
  };
  return defaultLayouts[name] || defaultLayouts['default'];
}
