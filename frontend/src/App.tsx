import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Link as RouterLink, useLocation } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  MenuItem,
  Select,
  SelectChangeEvent,
  Divider,
  Container,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import CandlestickChartIcon from "@mui/icons-material/CandlestickChart";
import SignalCellularAltIcon from "@mui/icons-material/SignalCellularAlt";
import AssessmentIcon from "@mui/icons-material/Assessment";
import SecurityIcon from "@mui/icons-material/Security";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import SettingsIcon from "@mui/icons-material/Settings";
import { useMarketStore } from "@/store";
import type { MarketType } from "@/types";

// 页面组件导入
import ChartPage from "@/pages/ChartPage";
import SignalsPage from "@/pages/SignalsPage";
import BacktestPage from "@/pages/BacktestPage";
import RiskMonitorPage from "@/pages/RiskMonitorPage";
import KnowledgePage from "@/pages/KnowledgePage";

const DRAWER_WIDTH = 220;

/** 侧边栏导航项定义 */
const NAV_ITEMS = [
  { path: "/", label: "K线图表", icon: <CandlestickChartIcon /> },
  { path: "/signals", label: "信号面板", icon: <SignalCellularAltIcon /> },
  { path: "/backtest", label: "回测中心", icon: <AssessmentIcon /> },
  { path: "/risk", label: "风控监控", icon: <SecurityIcon /> },
  { path: "/knowledge", label: "知识图谱", icon: <AccountTreeIcon /> },
] as const;

/** 侧边栏导航内容 */
const SidebarNav: React.FC = () => {
  const location = useLocation();

  return (
    <Box sx={{ width: DRAWER_WIDTH, pt: 1 }}>
      <Divider />
      <List>
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                component={RouterLink}
                to={item.path}
                selected={isActive}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  "&.Mui-selected": {
                    bgcolor: "primary.light",
                    color: "primary.contrastText",
                    "& .MuiListItemIcon-root": { color: "primary.contrastText" },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};

/** 顶部导航栏 */
const TopAppBar: React.FC<{ onToggleDrawer: () => void }> = ({ onToggleDrawer }) => {
  const { currentMarket, setMarket, currentSymbol, setSymbol } = useMarketStore();

  const handleMarketChange = (event: SelectChangeEvent<MarketType>) => {
    const market = event.target.value as MarketType;
    setMarket(market);
    // 切换市场时重置默认标的
    if (market === "crypto") {
      setSymbol("BTCUSDT");
    } else {
      setSymbol("000001.SZ");
    }
  };

  return (
    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar sx={{ gap: 1 }}>
        <IconButton color="inherit" edge="start" onClick={onToggleDrawer} sx={{ mr: 1 }}>
          <MenuIcon />
        </IconButton>

        {/* Logo */}
        <Typography variant="h6" noWrap sx={{ fontWeight: 700, mr: 3 }}>
          孙大圣
        </Typography>

        {/* 市场切换 */}
        <Select
          value={currentMarket}
          onChange={handleMarketChange}
          size="small"
          sx={{
            color: "common.white",
            "& .MuiOutlinedInput-notchedOutline": { borderColor: "rgba(255,255,255,0.5)" },
            "& .MuiSvgIcon-root": { color: "common.white" },
            minWidth: 100,
          }}
        >
          <MenuItem value="a_share">A股</MenuItem>
          <MenuItem value="crypto">币安</MenuItem>
        </Select>

        {/* 当前标的 */}
        <Typography variant="body2" sx={{ ml: 2, opacity: 0.85 }}>
          {currentSymbol}
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        {/* 账户 & 设置 */}
        <IconButton color="inherit" aria-label="账户">
          <AccountCircleIcon />
        </IconButton>
        <IconButton color="inherit" aria-label="设置">
          <SettingsIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
};

/** 根组件 - 路由 + 布局 */
const App: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(true);

  const toggleDrawer = () => setDrawerOpen((prev) => !prev);

  return (
    <BrowserRouter>
      <Box sx={{ display: "flex", height: "100vh", bgcolor: "background.default" }}>
        {/* 顶部导航栏 */}
        <TopAppBar onToggleDrawer={toggleDrawer} />

        {/* 侧边栏 */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={drawerOpen}
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: DRAWER_WIDTH,
              boxSizing: "border-box",
              top: 64,
            },
          }}
        >
          <SidebarNav />
        </Drawer>

        {/* 主内容区域 */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            mt: "64px",
            ml: drawerOpen ? `${DRAWER_WIDTH}px` : 0,
            transition: "margin 0.2s",
            overflow: "auto",
          }}
        >
          <Container maxWidth="xl" sx={{ py: 2, height: "calc(100vh - 64px)" }}>
            <Routes>
              <Route path="/" element={<ChartPage />} />
              <Route path="/signals" element={<SignalsPage />} />
              <Route path="/backtest" element={<BacktestPage />} />
              <Route path="/risk" element={<RiskMonitorPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </BrowserRouter>
  );
};

export default App;
