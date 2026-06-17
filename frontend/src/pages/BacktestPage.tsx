/**
 * BacktestPage - 回测中心页面
 *
 * 包含：
 * - 配置区（策略选择、时间范围、初始资金、标的）
 * - 收益曲线图（策略收益 vs 基准收益）
 * - 统计指标卡片（总收益率、最大回撤、夏普比率等）
 * - 交易明细表格
 */

import React, { useState } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Checkbox,
  FormControlLabel,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import {
  generateMockEquityCurve,
  generateMockTrades,
  MOCK_BACKTEST_STATS,
  type EquityPoint,
  type BacktestTrade,
  type BacktestStats,
} from "@/utils/mockData";

// ============================================================
// 主组件
// ============================================================

/**
 * BacktestPage - 回测中心页面
 */
const BacktestPage: React.FC = () => {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stats, setStats] = useState<BacktestStats | null>(null);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [trades, setTrades] = useState<BacktestTrade[]>([]);
  const [strategies, setStrategies] = useState({
    taiji: true,
    spiral: true,
    elliott: true,
    tomas: false,
  });

  // 运行回测
  const handleRunBacktest = () => {
    setRunning(true);
    setProgress(0);

    // 模拟回测进度
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setRunning(false);
          setStats(MOCK_BACKTEST_STATS);
          setEquityCurve(generateMockEquityCurve(90, 100000));
          setTrades(generateMockTrades());
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  return (
    <Box sx={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column", p: 2, gap: 2 }}>
      {/* 配置区 */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          回测配置
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <Typography gutterBottom>策略选择</Typography>
            <FormControlLabel
              control={
                <Checkbox
                  checked={strategies.taiji}
                  onChange={(e) => setStrategies({ ...strategies, taiji: e.target.checked })}
                />
              }
              label="太极中心律"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={strategies.spiral}
                  onChange={(e) => setStrategies({ ...strategies, spiral: e.target.checked })}
                />
              }
              label="螺旋律"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={strategies.elliott}
                  onChange={(e) => setStrategies({ ...strategies, elliott: e.target.checked })}
                />
              }
              label="波浪理论"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={strategies.tomas}
                  onChange={(e) => setStrategies({ ...strategies, tomas: e.target.checked })}
                />
              }
              label="TOMAS终裁"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="开始日期"
              type="date"
              defaultValue="2024-01-01"
              InputLabelProps={{ shrink: true }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="结束日期"
              type="date"
              defaultValue="2024-03-31"
              InputLabelProps={{ shrink: true }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              label="初始资金"
              defaultValue="100000"
              size="small"
              InputProps={{
                startAdornment: <span>¥</span>,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={1}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={handleRunBacktest}
              disabled={running}
            >
              运行
            </Button>
          </Grid>
        </Grid>
        {running && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              回测进度: {progress}%
            </Typography>
          </Box>
        )}
      </Paper>

      {/* 收益曲线图（Mock） */}
      {stats && (
        <Paper sx={{ p: 2, flex: 1, overflow: "auto" }}>
          <Typography variant="h6" gutterBottom>
            收益曲线
          </Typography>
          <Box
            sx={{
              height: 300,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "#f5f5f5",
              borderRadius: 1,
            }}
          >
            <Typography color="text.secondary">
              收益曲线图（使用 lightweight-charts 渲染）
              <br />
              策略收益: +23.7% | 基准收益: +12.3%
            </Typography>
          </Box>
        </Paper>
      )}

      {/* 统计指标 */}
      {stats && (
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4} md={2}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  总收益率
                </Typography>
                <Typography variant="h5" sx={{ color: stats.total_return > 0 ? "#ef5350" : "#26a69a" }}>
                  {(stats.total_return * 100).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  最大回撤
                </Typography>
                <Typography variant="h5" sx={{ color: "#f44336" }}>
                  {(stats.max_drawdown * 100).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  夏普比率
                </Typography>
                <Typography variant="h5">{stats.sharpe_ratio.toFixed(2)}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  胜率
                </Typography>
                <Typography variant="h5" sx={{ color: "#4caf50" }}>
                  {(stats.win_rate * 100).toFixed(0)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  盈亏比
                </Typography>
                <Typography variant="h5">{stats.profit_loss_ratio.toFixed(1)}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  交易次数
                </Typography>
                <Typography variant="h5">{stats.trade_count}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 交易明细 */}
      {trades.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            交易明细
          </Typography>
          <TableContainer sx={{ maxHeight: 300 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>交易ID</TableCell>
                  <TableCell>标的</TableCell>
                  <TableCell>方向</TableCell>
                  <TableCell>入场价</TableCell>
                  <TableCell>出场价</TableCell>
                  <TableCell>盈亏</TableCell>
                  <TableCell>盈亏%</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trades.map((trade) => (
                  <TableRow key={trade.trade_id} hover>
                    <TableCell>{trade.trade_id}</TableCell>
                    <TableCell>{trade.symbol}</TableCell>
                    <TableCell>
                      <span style={{ color: trade.direction === "LONG" ? "#ef5350" : "#26a69a" }}>
                        {trade.direction}
                      </span>
                    </TableCell>
                    <TableCell>{trade.entry_price.toFixed(2)}</TableCell>
                    <TableCell>{trade.exit_price.toFixed(2)}</TableCell>
                    <TableCell>
                      <span style={{ color: trade.pnl >= 0 ? "#ef5350" : "#26a69a" }}>
                        {trade.pnl >= 0 ? "+" : ""}{trade.pnl.toFixed(2)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span style={{ color: trade.pnl_pct >= 0 ? "#ef5350" : "#26a69a" }}>
                        {trade.pnl_pct >= 0 ? "+" : ""}{trade.pnl_pct.toFixed(2)}%
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {!stats && !running && (
        <Alert severity="info">
          请选择策略并点击"运行"按钮开始回测
        </Alert>
      )}
    </Box>
  );
};

export default BacktestPage;
