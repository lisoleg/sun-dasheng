import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import { useLocation, Link as RouterLink } from 'react-router-dom';

/**
 * 面包屑导航
 * 使用 MUI Breadcrumbs
 */
const Breadcrumb: React.FC = () => {
  const location = useLocation();

  const getBreadcrumbs = () => {
    const segments = location.pathname.split('/').filter(Boolean);
    const crumbs: Array<{ label: string; path: string }> = [];

    const labelMap: Record<string, string> = {
      '': '首页',
      'signals': '信号中心',
      'backtest': '回测',
      'risk': '风控监控',
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

  if (breadcrumbs.length === 0) return null;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 0.5 }}>
      {breadcrumbs.map((crumb, idx) => (
        <React.Fragment key={crumb.path}>
          {idx > 0 && (
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              /
            </Typography>
          )}
          {idx < breadcrumbs.length - 1 ? (
            <Link
              component={RouterLink}
              to={crumb.path}
              variant="caption"
              sx={{
                color: 'text.secondary',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              {crumb.label}
            </Link>
          ) : (
            <Typography variant="caption" sx={{ color: 'text.primary', fontWeight: 600 }}>
              {crumb.label}
            </Typography>
          )}
        </React.Fragment>
      ))}
    </Box>
  );
};

export default Breadcrumb;
