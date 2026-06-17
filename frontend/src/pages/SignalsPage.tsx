/**
 * SignalsPage - 信号面板页面
 *
 * 包含：
 * - 顶部统计卡片（今日信号总数、多头信号、空头信号、平均置信度）
 * - 筛选区（市场、方向、来源理论、置信度范围）
 * - 信号表格（MUI Table）
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
  TablePagination,
  Chip,
  LinearProgress,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  InputAdornment,
  IconButton,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import RemoveIcon from "@mui/icons-material/Remove";
import { generateMockSignals } from "@/utils/mockData";
import type { Signal } from "@/types";

// ============================================================
// 类型定义
// ============================================================

type MarketFilter = "all" | "a_share" | "crypto";
type DirectionFilter = "all" | "LONG" | "SHORT" | "HOLD";

// ============================================================
// 主组件
// ============================================================

/**
 * SignalsPage - 信号面板页面
 */
const SignalsPage: React.FC = () => {
  const [signals] = useState<Signal[]>(() => generateMockSignals(100));
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [marketFilter, setMarketFilter] = useState<MarketFilter>("all");
  const [directionFilter, setDirectionFilter] = useState<DirectionFilter>("all");
  const [confidenceRange, setConfidenceRange] = useState<[number, number]>([0, 1]);
  const [search, setSearch] = useState("");

  // 筛选信号
  const filteredSignals = useMemo(() => {
    return signals.filter((s) => {
      if (marketFilter !== "all" && s.market !== marketFilter) return false;
      if (directionFilter !== "all" && s.direction !== directionFilter) return false;
      if (s.confidence < confidenceRange[0] || s.confidence > confidenceRange[1]) return false;
      if (search && !s.symbol.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [signals, marketFilter, directionFilter, confidenceRange, search]);

  // 统计信息
  const stats = useMemo(() => {
    const today = new Date().toISOString().split("T")[0];
    const todaySignals = signals.filter((s) => s.timestamp.startsWith(today));
    return {
      total: todaySignals.length,
      long: todaySignals.filter((s) => s.direction === "LONG").length,
      short: todaySignals.filter((s) => s.direction === "SHORT").length,
      avgConfidence: todaySignals.length > 0
        ? todaySignals.reduce((sum, s) => sum + s.confidence, 0) / todaySignals.length
        : 0,
    };
  }, [signals]);

  // 分页处理
  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Box sx={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column", p: 2, gap: 2 }}>
      {/* 顶部统计卡片 */}
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                今日信号总数
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                多头信号
              </Typography>
              <Typography variant="h4" sx={{ color: "#ef5350" }}>
                {stats.long}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                空头信号
              </Typography>
              <Typography variant="h4" sx={{ color: "#26a69a" }}>
                {stats.short}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                平均置信度
              </Typography>
              <Typography variant="h4">
                {(stats.avgConfidence * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 筛选区 */}
      <Paper sx={{ p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>市场</InputLabel>
              <Select
                value={marketFilter}
                onChange={(e) => setMarketFilter(e.target.value as MarketFilter)}
                label="市场"
              >
                <MenuItem value="all">全部</MenuItem>
                <MenuItem value="a_share">A股</MenuItem>
                <MenuItem value="crypto">币安</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>方向</InputLabel>
              <Select
                value={directionFilter}
                onChange={(e) => setDirectionFilter(e.target.value as DirectionFilter)}
                label="方向"
              >
                <MenuItem value="all">全部</MenuItem>
                <MenuItem value="LONG">多头</MenuItem>
                <MenuItem value="SHORT">空头</MenuItem>
                <MenuItem value="HOLD">持有</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography gutterBottom>置信度范围</Typography>
            <Slider
              value={confidenceRange}
              onChange={(_, newValue) => setConfidenceRange(newValue as [number, number])}
              valueLabelDisplay="auto"
              min={0}
              max={1}
              step={0.1}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              placeholder="搜索标的"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* 信号表格 */}
      <Paper sx={{ flex: 1, overflow: "auto" }}>
        <TableContainer sx={{ maxHeight: "calc(100vh - 400px)" }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>时间</TableCell>
                <TableCell>标的</TableCell>
                <TableCell>方向</TableCell>
                <TableCell>价格</TableCell>
                <TableCell>置信度</TableCell>
                <TableCell>来源理论</TableCell>
                <TableCell>引擎</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSignals
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((signal) => (
                  <TableRow key={signal.signal_id} hover>
                    <TableCell>
                      {new Date(signal.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Chip label={signal.symbol} size="small" />
                    </TableCell>
                    <TableCell>
                      {signal.direction === "LONG" ? (
                        <Chip
                          icon={<ArrowUpwardIcon />}
                          label="LONG"
                          size="small"
                          sx={{ bgcolor: "#ef5350", color: "white" }}
                        />
                      ) : signal.direction === "SHORT" ? (
                        <Chip
                          icon={<ArrowDownwardIcon />}
                          label="SHORT"
                          size="small"
                          sx={{ bgcolor: "#26a69a", color: "white" }}
                        />
                      ) : (
                        <Chip
                          icon={<RemoveIcon />}
                          label="HOLD"
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                    <TableCell>{signal.price.toFixed(2)}</TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={signal.confidence * 100}
                          sx={{
                            width: 80,
                            "& .MuiLinearProgress-bar": {
                              bgcolor: signal.confidence > 0.7 ? "#4caf50" : signal.confidence > 0.3 ? "#ff9800" : "#f44336",
                            },
                          }}
                        />
                        <Typography variant="body2">
                          {(signal.confidence * 100).toFixed(0)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={signal.theory_name} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={signal.source_engine}
                        size="small"
                        color={signal.source_engine === "tomas" ? "secondary" : "default"}
                      />
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[10, 25, 50]}
          component="div"
          count={filteredSignals.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
};

export default SignalsPage;
