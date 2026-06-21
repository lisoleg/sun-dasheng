import React, { Suspense } from 'react';
import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';

interface LoadingFallbackProps {
  message?: string;
  height?: number | string;
}

/**
 * 加载占位（骨架屏）
 * 用于 Suspense fallback
 */
const LoadingFallback: React.FC<LoadingFallbackProps> = ({
  message = '加载中...',
  height = '100%',
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height,
        p: 2,
      }}
    >
      <Skeleton variant="rectangular" width="80%" height={40} sx={{ mb: 1, borderRadius: 1 }} />
      <Skeleton variant="rectangular" width="60%" height={120} sx={{ mb: 1, borderRadius: 1 }} />
      <Skeleton variant="text" width="40%" sx={{ mb: 2 }} />
      {message && (
        <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '12px' }}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

/**
 * 包装组件：添加 Suspense
 */
export function withSuspense<T>(Component: React.ComponentType<T>, fallback?: React.ReactNode) {
  return (props: T) => (
    <Suspense fallback={fallback || <LoadingFallback />}>
      <Component {...props} />
    </Suspense>
  );
}

export default LoadingFallback;
