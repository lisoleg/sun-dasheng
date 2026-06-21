import React from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  TextField,
  Button,
  Alert,
  Paper,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SettingsPage() {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        设置
      </Typography>
      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered>
          <Tab label="交易所 API" />
          <Tab label="策略参数" />
          <Tab label="通知设置" />
          <Tab label="系统设置" />
        </Tabs>

        {/* Tab 1: 交易所 API */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            交易所 API 配置
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            API Key 将加密存储在数据库中，请确保环境安全。
          </Alert>
          <TextField
            fullWidth
            label="币安 API Key"
            type="password"
            margin="normal"
          />
          <TextField
            fullWidth
            label="币安 API Secret"
            type="password"
            margin="normal"
          />
          <TextField
            fullWidth
            label="A 股券商 API Key"
            type="password"
            margin="normal"
          />
          <Button variant="contained" startIcon={<SaveIcon />} sx={{ mt: 2 }}>
            保存配置
          </Button>
        </TabPanel>

        {/* Tab 2: 策略参数 */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            策略参数调优
          </Typography>
          <TextField
            fullWidth
            label="太极中心律权重"
            type="number"
            margin="normal"
            defaultValue={1.0}
            inputProps={{ min: 0, max: 2, step: 0.1 }}
          />
          <TextField
            fullWidth
            label="螺旋律权重"
            type="number"
            margin="normal"
            defaultValue={0.8}
          />
          {/* 更多参数... */}
          <Button variant="contained" sx={{ mt: 2 }}>
            保存参数
          </Button>
        </TabPanel>

        {/* Tab 3: 通知设置 */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            通知设置
          </Typography>
          <Alert severity="warning" sx={{ mb: 2 }}>
            通知功能正在开发中，当前仅支持 WebSocket 实时推送。
          </Alert>
          {/* 通知设置表单... */}
        </TabPanel>

        {/* Tab 4: 系统设置 */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            系统设置
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            系统设置正在开发中。
          </Alert>
        </TabPanel>
      </Paper>
    </Box>
  );
}
