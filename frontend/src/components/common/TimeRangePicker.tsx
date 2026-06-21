import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';

interface TimeRangePickerProps {
  value: string;
  onChange: (range: string) => void;
}

const PRESETS = [
  { label: '今日', value: 'today' },
  { label: '7日', value: '7d' },
  { label: '30日', value: '30d' },
  { label: '90日', value: '90d' },
  { label: '自定义', value: 'custom' },
];

/**
 * 时间范围选择器
 * 快捷选项：今日 / 7日 / 30日 / 90日 / 自定义
 */
const TimeRangePicker: React.FC<TimeRangePickerProps> = ({ value, onChange }) => {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchor(event.currentTarget);
  };

  const handleClose = () => {
    setAnchor(null);
  };

  const handleSelect = (val: string) => {
    onChange(val);
    setAnchor(null);
  };

  const currentLabel = PRESETS.find((p) => p.value === value)?.label || '自定义';

  return (
    <Box>
      <Button
        size="small"
        variant="outlined"
        onClick={handleClick}
        sx={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '12px',
          textTransform: 'none',
          minWidth: 80,
        }}
      >
        {currentLabel}
      </Button>
      <Menu
        anchorEl={anchor}
        open={Boolean(anchor)}
        onClose={handleClose}
        PaperProps={{ sx: { mt: 0.5, minWidth: 120 } }}
      >
        {PRESETS.map((preset) => (
          <MenuItem
            key={preset.value}
            selected={value === preset.value}
            onClick={() => handleSelect(preset.value)}
            sx={{ fontSize: '13px' }}
          >
            {preset.label}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default TimeRangePicker;
