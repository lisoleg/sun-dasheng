import React, { Component, ErrorInfo, ReactNode } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

/**
 * React 错误边界
 * componentDidCatch
 */
class ErrorBoundaryClass extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }

      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            p: 3,
          }}
        >
          <Alert severity="error" sx={{ mb: 2, maxWidth: 600 }}>
            <Typography variant="h6" gutterBottom>
              组件渲染错误
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '12px' }}>
              {this.state.error.message}
            </Typography>
          </Alert>
          <Button variant="contained" onClick={this.reset} sx={{ mt: 2 }}>
            重试
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

/**
 * 函数组件包装器
 */
const ErrorBoundary: React.FC<ErrorBoundaryProps> = ({ children, fallback }) => {
  return <ErrorBoundaryClass fallback={fallback}>{children}</ErrorBoundaryClass>;
};

export default ErrorBoundary;
