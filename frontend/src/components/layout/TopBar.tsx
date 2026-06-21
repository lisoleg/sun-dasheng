import React, { useState, useCallback, useRef, useEffect } from 'react';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import InputBase from '@mui/material/InputBase';
import Badge from '@mui/material/Badge';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { useNavigate, useLocation } from 'react-router-dom';
import { usePreferences } from '@/store/preferencesSlice';

// lucide-react 图标
import PanelLeftClose from 'lucide-react/dist/PanelLeftClose';
import PanelLeftOpen from 'lucide-react/dist/PanelLeftOpen';
import Search from 'lucide-react/dist/Search';
import Bell from 'lucide-react/dist/Bell';
import Sun from 'lucide-react/dist/Sun';
import Moon from 'lucide-react/dist/Moon';
import User from 'lucide-react/dist/User';
import SunDim from 'lucide-react/dist/SunDim';

interface TopBarProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar, sidebarOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { themeMode, setThemeMode } = usePreferences();
  const [searchOpen, setSearchOpen] = useState(false);
  const [notificationAnchor, setNotificationAnchor] = useState<HTMLElement | null>(null);
  const [accountAnchor, setAccountAnchor] = useState<HTMLElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Ctrl+K 快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
        setTimeout(() => searchInputRef.current?.focus(), 100);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleToggleTheme = useCallback(() => {
    setThemeMode(themeMode === 'dark' ? 'light' : 'dark');
  }, [themeMode, setThemeMode]);

  // 面包屑生成
  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/') return [{ label: '仪表盘', path: '/' }];
    const segments = path.split('/').filter(Boolean);
    const crumbs: Array<{ label: string; path: string }> = [
      { label: '首页', path: '/' },
    ];
    const labelMap: Record<string, string> = {
      'signals': '信号中心',
      'backtest': '回测',
      'risk': '风控',
      'knowledge': '知识图谱',
      'settings': '设置',
      'chart': 'K线图表',
    };
    let currentPath = '';
    segments.forEach((seg) => {
      currentPath += `/${seg}`;
      crumbs.push({
        label: labelMap[seg] || seg,
        path: currentPath,
      });
    });
    return crumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        height: 48,
        justifyContent: 'center',
      }}
    >
      <Toolbar sx={{ minHeight: 48, height: 48, gap: 1 }}>
        {/* 侧边栏切换 */}
        <IconButton
          color="inherit"
          edge="start"
          onClick={onToggleSidebar}
          sx={{ ml: -0.5 }}
        >
          {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
        </IconButton>

        {/* Logo + 标题 */}
        <Box
          sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', mr: 2 }}
          onClick={() => navigate('/')}
        >
          {/* 孙大圣 SVG 图标 */}
          <Box
            sx={{
              width: 28,
              height: 28,
              mr: 1,
              background: 'linear-gradient(135deg, #f97316, #ef4444)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              color: '#fff',
              fontWeight: 'bold',
            }}
          >
            圣
          </Box>
          <Typography
            variant="subtitle1"
            noWrap
            sx={{ fontWeight: 700, fontSize: '15px', display: { xs: 'none', sm: 'block' } }}
          >
            孙大圣
          </Typography>
        </Box>

        {/* 面包屑 */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1, flex: 1, overflow: 'hidden' }}>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={crumb.path}>
              {idx > 0 && (
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', mx: 0.5 }}>
                  /
                </Typography>
              )}
              <Typography
                variant="caption"
                sx={{
                  color: idx === breadcrumbs.length - 1 ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.6)',
                  cursor: idx < breadcrumbs.length - 1 ? 'pointer' : 'default',
                  '&:hover': idx < breadcrumbs.length - 1 ? { textDecoration: 'underline' } : {},
                  whiteSpace: 'nowrap',
                }}
                onClick={() => idx < breadcrumbs.length - 1 && navigate(crumb.path)}
              >
                {crumb.label}
              </Typography>
            </React.Fragment>
          ))}
        </Box>

        {/* 全局搜索框 */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            bgcolor: 'rgba(255,255,255,0.08)',
            borderRadius: 1,
            px: 1.5,
            py: 0.5,
            minWidth: searchOpen ? 240 : 180,
            transition: 'min-width 0.2s',
            cursor: 'pointer',
          }}
          onClick={() => {
            setSearchOpen(true);
            setTimeout(() => searchInputRef.current?.focus(), 100);
          }}
        >
          <Search size={16} color="rgba(255,255,255,0.5)" />
          {searchOpen ? (
            <InputBase
              inputRef={searchInputRef}
              placeholder="搜索标的、信号、策略..."
              sx={{
                ml: 1,
                flex: 1,
                color: '#fff',
                fontSize: '13px',
                '&::placeholder': { color: 'rgba(255,255,255,0.4)' },
              }}
              onBlur={() => setSearchOpen(false)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setSearchOpen(false);
                }
              }}
            />
          ) : (
            <Typography variant="caption" sx={{ ml: 1, color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
              Ctrl+K 搜索
            </Typography>
          )}
        </Box>

        {/* 通知铃铛 */}
        <IconButton
          color="inherit"
          onClick={(e) => setNotificationAnchor(e.currentTarget)}
          sx={{ ml: 1 }}
        >
          <Badge badgeContent={3} color="error">
            <Bell size={20} />
          </Badge>
        </IconButton>

        {/* 主题切换 */}
        <IconButton color="inherit" onClick={handleToggleTheme}>
          {themeMode === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </IconButton>

        {/* 账户头像 */}
        <IconButton
          color="inherit"
          onClick={(e) => setAccountAnchor(e.currentTarget)}
        >
          <User size={20} />
        </IconButton>

        {/* 通知菜单 */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={() => setNotificationAnchor(null)}
          PaperProps={{ sx: { mt: 1, minWidth: 300, maxHeight: 400 } }}
        >
          <MenuItem onClick={() => setNotificationAnchor(null)}>
            <Typography variant="body2">新的信号：BTCUSDT 买入 (92%)</Typography>
          </MenuItem>
          <MenuItem onClick={() => setNotificationAnchor(null)}>
            <Typography variant="body2">回测完成：ETHUSDT 夏普 1.8</Typography>
          </MenuItem>
          <MenuItem onClick={() => setNotificationAnchor(null)}>
            <Typography variant="body2">风险预警：SOLUSDT 跌幅 -3%</Typography>
          </MenuItem>
        </Menu>

        {/* 账户菜单 */}
        <Menu
          anchorEl={accountAnchor}
          open={Boolean(accountAnchor)}
          onClose={() => setAccountAnchor(null)}
          PaperProps={{ sx: { mt: 1 } }}
        >
          <MenuItem onClick={() => { setAccountAnchor(null); navigate('/settings'); }}>
            <Typography variant="body2">设置</Typography>
          </MenuItem>
          <MenuItem onClick={() => setAccountAnchor(null)}>
            <Typography variant="body2">退出登录</Typography>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;
