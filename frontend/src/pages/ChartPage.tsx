/**
 * ChartPage - K线图表主页面
 *
 * 包含：
 * - 顶部工具栏（周期切换、标的搜索）
 * - K线图表主体（占80vh）
 * - 底部信号列表（最近10条信号）
 */

import React, { useState, useCallback, useMemo } from "react";
import {
  Box,
  Toolbar,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  InputAdornment,
  IconButton,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import RemoveIcon from "@mui/icons-material/Remove";
import { ChartWidget, type TaijiMarker, type FibLevel, type WaveLabel } from "@/components/ChartWidget";
import { generateMockBars, generateMockSignals } from "@/utils/mockData";
import type { Bar, Signal } from "@/types";

// ============================================================
// 类型定义
// ============================================================

/** 时间周期选项 */
const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"] as const;
type Timeframe = (typeof TIMEFRAMES)[number];

// ============================================================
// 工具函数
// ============================================================

/**
 * 从信号数据中提取太极标记
 */
function extractTaijiMarkers(signals: Signal[]): TaijiMarker[] {
  return signals
    .filter((s) => s.metadata?.taiji_center)
    .map((s) => ({
      time: s.timestamp,
      price: s.price,
      isTop: s.direction === "SHORT", // 做空信号通常在顶部
      text: s.direction === "LONG" ? "▲太极底" : "▼太极顶",
    }));
}

/**
 * 从信号数据中提取斐波那契水平线
 */
function extractFibLevels(signals: Signal[]): FibLevel[] {
  const levels: FibLevel[] = [];
  for (const signal of signals) {
    if (signal.metadata?.fib_level) {
      levels.push({
        price: signal.price,
        level: signal.metadata.fib_level,
        color: signal.metadata.fib_level >= 0.618 ? "#F44336" : "#FF9800",
      });
    }
  }
  return levels;
}

/**
 * 从信号数据中提取波浪标签
 */
function extractWaveLabels(signals: Signal[]): WaveLabel[] {
  return signals
    .filter((s) => s.metadata?.wave_label)
    .map((s) => ({
      time: s.timestamp,
      label: s.metadata.wave_label,
      isImpulse: ["1", "2", "3", "4", "5"].includes(s.metadata.wave_label),
    }));
}

// ============================================================
// 主组件
// ============================================================

/**
 * ChartPage - K线图表主页面
 */
const ChartPage: React.FC = () => {
  const [timeframe, setTimeframe] = useState<Timeframe>("1d");
  const [searchSymbol, setSearchSymbol] = useState("");
  const [bars, setBars] = useState<Bar[]>(() => generateMockBars("BTCUSDT", 200));
  const [signals, setSignals] = useState<Signal[]>(() => generateMockSignals(50));

  // 处理周期切换
  const handleTimeframeChange = useCallback(
    (_: React.MouseEvent<HTMLElement>, newTimeframe: Timeframe | null) => {
      if (newTimeframe) {
        setTimeframe(newTimeframe);
        // 切换周期时重新生成mock数据
        setBars(generateMockBars("BTCUSDT", 200));
      }
    },
    [],
  );

  // 处理标的搜索
  const handleSearch = useCallback(() => {
    if (searchSymbol.trim()) {
      setBars(generateMockBars(searchSymbol.trim(), 200));
    }
  }, [searchSymbol]);

  // 提取理论标注数据
  const taijiMarkers = useMemo(() => extractTaijiMarkers(signals), [signals]);
  const fibLevels = useMemo(() => extractFibLevels(signals), [signals]);
  const waveLabels = useMemo(() => extractWaveLabels(signals), [signals]);

  // 最近10条信号
  const recentSignals = useMemo(
    () => signals.slice(0, 10),
    [signals],
  );

  return (
    <Box sx={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column" }}>
      {/* 顶部工具栏 */}
      <Paper
        elevation={1}
        sx={{
          p: 1,
          display: "flex",
          alignItems: "center",
          gap: 2,
          borderRadius: 0,
        }}
      >
        {/* 周期切换 */}
        <ToggleButtonGroup
          value={timeframe}
          exclusive
          onChange={handleTimeframeChange}
          size="small"
        >
          {TIMEFRAMES.map((tf) => (
            <ToggleButton key={tf} value={tf} sx={{ px: 1.5, py: 0.5 }}>
              {tf}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>

        {/* 标的搜索 */}
        <TextField
          size="small"
          placeholder="搜索标的 (如 BTCUSDT)"
          value={searchSymbol}
          onChange={(e) => setSearchSymbol(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <IconButton onClick={handleSearch} size="small">
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ width: 300 }}
        />
      </Paper>

      {/* K线图表主体 */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <ChartWidget
          bars={bars}
          taijiMarkers={taijiMarkers}
          fibLevels={fibLevels}
          waveLabels={waveLabels}
          height="100%"
        />
      </Box>

      {/* 底部信号列表 */}
      <Paper
        elevation={2}
        sx={{
          height: 200,
          overflow: "auto",
          borderRadius: 0,
          borderTop: 1,
          borderColor: "divider",
        }}
      >
        <Typography variant="subtitle2" sx={{ p: 1, pb: 0 }}>
          最近信号
        </Typography>
        <List dense>
          {recentSignals.map((signal) => (
            <ListItem key={signal.signal_id} sx={{ py: 0.5 }}>
              <ListItemIcon sx={{ minWidth: 40 }}>
                {signal.direction === "LONG" ? (
                  <ArrowUpwardIcon sx={{ color: "#ef5350" }} />
                ) : signal.direction === "SHORT" ? (
                  <ArrowDownwardIcon sx={{ color: "#26a69a" }} />
                ) : (
                  <RemoveIcon sx={{ color: "#999" }} />
                )}
              </ListItemIcon>
              <ListItemText
                primary={
                  <span>
                    <Chip
                      label={signal.symbol}
                      size="small"
                      sx={{ mr: 1, height: 20 }}
                    />
                    <span style={{ color: signal.direction === "LONG" ? "#ef5350" : signal.direction === "SHORT" ? "#26a69a" : "#999" }}>
                      {signal.direction}
                    </span>
                  </span>
                }
                secondary={
                  <span>
                    价格: {signal.price.toFixed(2)} | 置信度:
                    <LinearProgress
                      variant="determinate"
                      value={signal.confidence * 100}
                      sx={{
                        width: 60,
                        display: "inline-block",
                        ml: 1,
                        verticalAlign: "middle",
                        "& .MuiLinearProgress-bar": {
                          bgcolor: signal.confidence > 0.7 ? "#4caf50" : signal.confidence > 0.3 ? "#ff9800" : "#f44336",
                        },
                      }}
                    />
                  </span>
                }
              />
              <Chip
                label={signal.theory_name}
                size="small"
                color="primary"
                variant="outlined"
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
};

export default ChartPage;
