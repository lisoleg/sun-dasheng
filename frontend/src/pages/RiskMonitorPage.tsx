/**
 * RiskMonitorPage - 风控监控页面
 *
 * 包含：
 * - 顶部风控配置卡片（最大仓位、止损、止盈、最大回撤）
 * - 中部持仓监控表格
 * - 底部风控告警列表
 */

import React, { useState, useMemo } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Slider,
  Button,
  Alert,
  Chip,
  LinearProgress,
} from "@mui/material";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import InfoIcon from "@mui/icons-material/Info";
import {
  generateMockPositions,
  generateMockAlerts,
  DEFAULT_RISK_CONFIG,
  type RiskAlertData,
} from "@/utils/mockData";
import type { Position } from "@/types";

// ============================================================
// 主组件
// ============================================================

/**
 * RiskMonitorPage - 风控监控页面
 */
const RiskMonitorPage: React.FC = () => {
  const [config, setConfig] = useState({
    maxPositionPct: DEFAULT_RISK_CONFIG.max_position_pct * 100,
    stopLossPct: DEFAULT_RISK_CONFIG.stop_loss_pct * 100,
    takeProfitPct: DEFAULT_RISK_CONFIG.take_profit_pct * 100,
    maxDrawdownPct: DEFAULT_RISK_CONFIG.max_drawdown_pct * 100,
  });
  const [positions] = useState<Position[]>(() => generateMockPositions());
  const [alerts] = useState<RiskAlertData[]>(() => generateMockAlerts());
  const [saved, setSaved] = useState(false);

  // 保存配置
  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // 未处理告警
  const unhandledAlerts = useMemo(
    () => alerts.filter((a) => a.severity !== "INFO"),
    [alerts],
  );

  return (
    <Box sx={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column", p: 2, gap: 2 }}>
      {/* 顶部风控配置 */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          风控配置
        </Typography>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <Typography gutterBottom>最大仓位比例 ({config.maxPositionPct}%)</Typography>
            <Slider
              value={config.maxPositionPct}
              onChange={(_, value) => setConfig({ ...config, maxPositionPct: value as number })}
              min={1}
              max={30}
              step={1}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography gutterBottom>止损比例 ({config.stopLossPct}%)</Typography>
            <Slider
              value={config.stopLossPct}
              onChange={(_, value) => setConfig({ ...config, stopLossPct: value as number })}
              min={1}
              max={20}
              step={1}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography gutterBottom>止盈比例 ({config.takeProfitPct}%)</Typography>
            <Slider
              value={config.takeProfitPct}
              onChange={(_, value) => setConfig({ ...config, takeProfitPct: value as number })}
              min={1}
              max={50}
              step={1}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Typography gutterBottom>最大回撤 ({config.maxDrawdownPct}%)</Typography>
            <Slider
              value={config.maxDrawdownPct}
              onChange={(_, value) => setConfig({ ...config, maxDrawdownPct: value as number })}
              min={5}
              max={30}
              step={1}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={1}>
            <Button
              fullWidth
              variant="contained"
              onClick={handleSave}
              color={saved ? "success" : "primary"}
            >
              {saved ? "已保存" : "保存"}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* 持仓监控表格 */}
      <Paper sx={{ p: 2, flex: 1, overflow: "auto" }}>
        <Typography variant="h6" gutterBottom>
          持仓监控
        </Typography>
        <TableContainer sx={{ maxHeight: 300 }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>标的</TableCell>
                <TableCell>方向</TableCell>
                <TableCell>数量</TableCell>
                <TableCell>入场价</TableCell>
                <TableCell>当前价</TableCell>
                <TableCell>浮盈亏</TableCell>
                <TableCell>止损价</TableCell>
                <TableCell>止盈价</TableCell>
                <TableCell>止损距离%</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {positions.map((pos) => {
                const pnlColor = pos.unrealized_pnl >= 0 ? "#ef5350" : "#26a69a";
                const stopDistance = ((pos.current_price - pos.stop_loss_price) / pos.current_price * 100).toFixed(2);
                return (
                  <TableRow key={pos.position_id} hover>
                    <TableCell>
                      <Chip label={pos.symbol} size="small" />
                    </TableCell>
                    <TableCell>
                      <span style={{ color: pos.quantity > 0 ? "#ef5350" : "#26a69a" }}>
                        {pos.quantity > 0 ? "LONG" : "SHORT"}
                      </span>
                    </TableCell>
                    <TableCell>{pos.quantity}</TableCell>
                    <TableCell>{pos.entry_price.toFixed(2)}</TableCell>
                    <TableCell>{pos.current_price.toFixed(2)}</TableCell>
                    <TableCell>
                      <span style={{ color: pnlColor, fontWeight: "bold" }}>
                        {pos.unrealized_pnl >= 0 ? "+" : ""}{pos.unrealized_pnl.toFixed(2)}
                      </span>
                    </TableCell>
                    <TableCell>{pos.stop_loss_price.toFixed(2)}</TableCell>
                    <TableCell>{pos.take_profit_price.toFixed(2)}</TableCell>
                    <TableCell>
                      <span style={{ color: parseFloat(stopDistance) < 2 ? "#f44336" : "#4caf50" }}>
                        {stopDistance}%
                      </span>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* 风控告警列表 */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          风控告警 ({unhandledAlerts.length} 条未处理)
        </Typography>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1, maxHeight: 250, overflow: "auto" }}>
          {alerts.map((alert) => {
            const severity = alert.severity === "CRITICAL" ? "error" 
              : alert.severity === "WARNING" ? "warning" 
              : "info";
            const Icon = alert.severity === "CRITICAL" ? ErrorIcon 
              : alert.severity === "WARNING" ? WarningIcon 
              : InfoIcon;
            return (
              <Alert
                key={alert.id}
                severity={severity}
                icon={<Icon />}
                sx={{ alignItems: "center" }}
              >
                <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
                  <span>
                    [{alert.symbol}] {alert.message}
                  </span>
                  <span style={{ fontSize: "0.8rem", opacity: 0.7 }}>
                    {new Date(alert.timestamp).toLocaleString()}
                  </span>
                </Box>
              </Alert>
            );
          })}
        </Box>
      </Paper>
    </Box>
  );
};

export default RiskMonitorPage;
