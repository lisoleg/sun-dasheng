import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import ChartPage from '@/pages/ChartPage';
import SignalsPage from '@/pages/SignalsPage';
import BacktestPage from '@/pages/BacktestPage';
import RiskMonitorPage from '@/pages/RiskMonitorPage';
import KnowledgePage from '@/pages/KnowledgePage';
import PhaseAnalysisPage from '@/pages/PhaseAnalysisPage';
import DNADetectionPage from '@/pages/DNADetectionPage';
import CosmicAlgorithmPage from '@/pages/CosmicAlgorithmPage';

// 临时占位（T15 会创建真正的 DashboardPage）
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage').catch(() => ({
  default: () => (
    <div style={{ padding: 24, textAlign: 'center', color: '#8b949e' }}>
      <h2>仪表盘加载中...</h2>
      <p>请先完成 T15 任务</p>
    </div>
  ),
})));

/**
 * 根组件 - 使用 AppLayout + 路由
 * T12 重写：外层包裹 AppLayout，内嵌路由
 * TOMAS v2.0: 新增相位分析 + DNA检测路由
 */
const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* 所有页面共享 AppLayout */}
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/chart" element={<ChartPage />} />
          <Route path="/signals" element={<SignalsPage />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="/risk" element={<RiskMonitorPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          {/* TOMAS v2.0 新增 */}
          <Route path="/phase-analysis" element={<PhaseAnalysisPage />} />
          <Route path="/dna-detection" element={<DNADetectionPage />} />
          {/* 宇宙算法三重奏 */}
          <Route path="/cosmic-algorithm" element={<CosmicAlgorithmPage />} />
          {/* T23 设置页 */}
          <Route path="/settings" element={<div>设置页（T23 实现中）</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
