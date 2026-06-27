import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import { useNavigate, useLocation } from 'react-router-dom';

// lucide-react 图标
import {
  LayoutDashboard,
  CandlestickChart,
  Bell,
  FlaskConical,
  ShieldAlert,
  Network,
  Settings,
  ChevronRight,
  Activity,
  Dna,
  Orbit,
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
}

const SIDEBAR_WIDTH = 200;
const COLLAPSED_WIDTH = 64;

const NAV_ITEMS = [
  { path: '/', label: '仪表盘', icon: LayoutDashboard },
  { path: '/chart', label: 'K线图表', icon: CandlestickChart },
  { path: '/signals', label: '信号中心', icon: Bell },
  { path: '/backtest', label: '回测', icon: FlaskConical },
  { path: '/risk', label: '风控', icon: ShieldAlert },
  { path: '/knowledge', label: '知识图谱', icon: Network },
  // TOMAS v2.0 新增
  { path: '/phase-analysis', label: '相位分析', icon: Activity },
  { path: '/dna-detection', label: 'DNA检测', icon: Dna },
  // 宇宙算法三重奏
  { path: '/cosmic-algorithm', label: '宇宙算法', icon: Orbit },
];

const Sidebar: React.FC<SidebarProps> = ({ open }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const renderNavItem = (item: typeof NAV_ITEMS[0]) => {
    const active = isActive(item.path);
    const Icon = item.icon;

    const button = (
      <ListItemButton
        onClick={() => navigate(item.path)}
        selected={active}
        sx={{
          minHeight: 44,
          px: open ? 2 : 1.5,
          borderRadius: 1,
          mx: 0.5,
          mb: 0.25,
          justifyContent: open ? 'initial' : 'center',
          ...(active && {
            bgcolor: 'rgba(88, 166, 255, 0.12)',
            '&:hover': { bgcolor: 'rgba(88, 166, 255, 0.18)' },
            '& .MuiListItemIcon-root': { color: '#58a6ff' },
          }),
        }}
      >
        <ListItemIcon
          sx={{
            minWidth: 36,
            color: active ? '#58a6ff' : 'rgba(255,255,255,0.6)',
            justifyContent: 'center',
          }}
        >
          <Icon size={20} />
        </ListItemIcon>
        {open && (
          <ListItemText
            primary={item.label}
            sx={{
              '& .MuiTypography-root': {
                fontSize: '13px',
                fontWeight: active ? 600 : 400,
              },
            }}
          />
        )}
      </ListItemButton>
    );

    return open ? (
      <ListItem key={item.path} disablePadding>
        {button}
      </ListItem>
    ) : (
      <ListItem key={item.path} disablePadding>
        <Tooltip title={item.label} placement="right" arrow>
          {button}
        </Tooltip>
      </ListItem>
    );
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: open ? SIDEBAR_WIDTH : COLLAPSED_WIDTH,
        flexShrink: 0,
        transition: (theme) => theme.transitions.create('width', {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.enteringScreen,
        }),
        '& .MuiDrawer-paper': {
          width: open ? SIDEBAR_WIDTH : COLLAPSED_WIDTH,
          boxSizing: 'border-box',
          top: 48,
          height: 'calc(100vh - 48px - 28px)',
          transition: (theme) => theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          overflowX: 'hidden',
        },
      }}
    >
      <Box sx={{ overflow: 'auto', py: 1 }}>
        <List disablePadding>
          {NAV_ITEMS.map(renderNavItem)}

          <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.08)' }} />

          {/* 设置 */}
          <ListItem disablePadding>
            {open ? (
              <ListItemButton
                onClick={() => setSettingsOpen(!settingsOpen)}
                sx={{ minHeight: 44, px: 2, borderRadius: 1, mx: 0.5, mb: 0.25 }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: 'rgba(255,255,255,0.6)', justifyContent: 'center' }}>
                  <Settings size={20} />
                </ListItemIcon>
                <ListItemText
                  primary="设置"
                  sx={{ '& .MuiTypography-root': { fontSize: '13px' } }}
                />
                <ChevronRight
                  size={14}
                  style={{
                    transform: settingsOpen ? 'rotate(90deg)' : 'none',
                    transition: 'transform 0.2s',
                  }}
                />
              </ListItemButton>
            ) : (
              <Tooltip title="设置" placement="right" arrow>
                <ListItemButton
                  onClick={() => navigate('/settings')}
                  sx={{ minHeight: 44, justifyContent: 'center', borderRadius: 1, mx: 0.5 }}
                >
                  <ListItemIcon sx={{ minWidth: 36, color: 'rgba(255,255,255,0.6)', justifyContent: 'center' }}>
                    <Settings size={20} />
                  </ListItemIcon>
                </ListItemButton>
              </Tooltip>
            )}
          </ListItem>

          {open && settingsOpen && (
            <List disablePadding sx={{ pl: 2 }}>
              {['交易所', '策略参数', '通知', '系统'].map((sub) => (
                <ListItem key={sub} disablePadding>
                  <ListItemButton
                    onClick={() => navigate('/settings')}
                    sx={{ minHeight: 36, px: 2, borderRadius: 1, fontSize: '12px' }}
                  >
                    <ListItemText
                      primary={sub}
                      sx={{ '& .MuiTypography-root': { fontSize: '12px', color: 'rgba(255,255,255,0.5)' } }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
