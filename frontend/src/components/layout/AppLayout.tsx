import React, { useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import StatusBar from './StatusBar';
import { Outlet } from 'react-router-dom';
import { usePreferences } from '@/store/preferencesSlice';

/**
 * 主布局组件
 * 结构：TopBar (48px) + [Sidebar + Main] + StatusBar (28px)
 */
const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { layoutTemplate } = usePreferences();

  const handleToggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* 顶栏 48px */}
      <TopBar
        onToggleSidebar={handleToggleSidebar}
        sidebarOpen={sidebarOpen}
      />

      {/* 中间区域：侧边栏 + 主内容 */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* 侧边栏 200px / 64px */}
        <Sidebar open={sidebarOpen} />

        {/* 主内容区域 */}
        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            ml: sidebarOpen ? 0 : 0,  // Sidebar 内部处理宽度
            transition: (theme) => theme.transitions.create('margin', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          }}
        >
          <Outlet />
        </Box>
      </Box>

      {/* 状态栏 28px */}
      <StatusBar />
    </Box>
  );
};

export default AppLayout;
