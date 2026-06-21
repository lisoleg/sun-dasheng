import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import type { ThemeMode } from '@/theme';

interface BacktestConfigFormProps {
  themeMode?: ThemeMode;
  onRun: () => void;
}

/**
 * 回测配置表单
 * T18 实现（骨架）
 */
const BacktestConfigForm: React.FC<BacktestConfigFormProps> = ({ themeMode = 'dark', onRun }) => {
  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2, fontSize: '14px', fontWeight: 600 }}>
        回测配置
      </Typography>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        T18 实现中：表单字段（标的/时间范围/初始资金/手续费/理论模块开关）
      </Typography>
      <Button variant="contained" onClick={onRun} sx={{ mt: 2 }}>
        开始回测
      </Button>
    </Box>
  );
};

export default BacktestConfigForm;
