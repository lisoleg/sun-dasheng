/**
 * CosmicAlgorithmPage - 宇宙算法三重奏 (7-139-369) 实时评分页面
 *
 * 展示：
 * - 三重奏综合评分大表盘
 * - 369振动模态分数 + 模态标签 + 三阶段频率
 * - 139相变评分 + regime标签 + 方差/自相关/恢复速率
 * - 7闭合评分 + 循环群检测 + FFT功率
 * - 369数字根分布条形图
 * - 三重奏综合时间序列图
 * - 交易含义 + 风控建议
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Area,
  ReferenceLine,
  ReferenceArea,
  Legend,
} from "recharts";
import { Orbit } from "lucide-react";

// ── 类型定义 ──
interface CosmicAlgorithmData {
  trio_score: number;
  trio_label: string;
  trading_implication: string;
  risk_control: {
    should_reduce_position: boolean;
    should_hard_stop: boolean;
    volatility_warning: boolean;
  };
  vibration_369: {
    vibration_score: number;
    trigger_freq: number;
    resonance_freq: number;
    closure_freq: number;
    root_distribution: Record<number, number>;
    is_strong: boolean;
    is_noise: boolean;
    mode_label: string;
  };
  critical_139: {
    is_critical: boolean;
    variance_ratio: number;
    autocorrelation: number;
    recovery_rate: number;
    critical_score: number;
    regime: string;
  };
  cycle_7: {
    has_7_cycle: boolean;
    closure_score: number;
    dominant_period: number;
    fft_power_at_7: number;
  };
  vibration_score: number;
  critical_score_normalized: number;
  closure_score: number;
}

// ── 辅助函数 ──
const getTrioColor = (score: number): string => {
  if (score >= 0.6) return "#3fb950"; // 绿色 — 三重奏共振强
  if (score >= 0.3) return "#d29922"; // 黄色 — 部分共振
  return "#f85149"; // 红色 — 三重奏失效
};

const getTrioLabel = (label: string): string => {
  const labelMap: Record<string, string> = {
    strong: "三重奏共振强",
    moderate: "部分共振",
    weak: "三重奏失效",
  };
  return labelMap[label] || label;
};

const getRegimeLabel = (regime: string): string => {
  const regimeMap: Record<string, string> = {
    critical_slowing: "临界慢化",
    transitioning: "过渡区",
    stable: "稳定态",
    insufficient_data: "数据不足",
  };
  return regimeMap[regime] || regime;
};

const getRegimeColor = (regime: string): string => {
  if (regime === "critical_slowing") return "#f85149";
  if (regime === "transitioning") return "#d29922";
  if (regime === "stable") return "#3fb950";
  return "#8b949e";
};

const getModeColor = (label: string): string => {
  if (label === "strong") return "#3fb950";
  if (label === "moderate") return "#d29922";
  if (label === "noise") return "#f85149";
  return "#8b949e";
};

// ── 三重奏历史模拟数据 ──
const generateTrioHistory = (currentData: CosmicAlgorithmData, bars: number = 60) => {
  const history: Array<{
    bar_index: number;
    trio_score: number;
    vibration_score: number;
    critical_score: number;
    closure_score: number;
  }> = [];
  let trio = 0.45;
  let vib = 0.4;
  let crit = 0.35;
  let clos = 0.3;
  for (let i = 0; i < bars; i++) {
    trio += (Math.random() - 0.48) * 0.04;
    vib += (Math.random() - 0.48) * 0.05;
    crit += (Math.random() - 0.48) * 0.04;
    clos += (Math.random() - 0.48) * 0.03;
    trio = Math.max(0.05, Math.min(0.95, trio));
    vib = Math.max(0.05, Math.min(0.95, vib));
    crit = Math.max(0.05, Math.min(0.95, crit));
    clos = Math.max(0.05, Math.min(0.95, clos));
    history.push({
      bar_index: i,
      trio_score: Math.round(trio * 1000) / 1000,
      vibration_score: Math.round(vib * 1000) / 1000,
      critical_score: Math.round(crit * 1000) / 1000,
      closure_score: Math.round(clos * 1000) / 1000,
    });
  }
  // 最后5根让分数接近当前值
  const currentTrio = currentData.trio_score;
  const currentVib = currentData.vibration_score;
  const currentCrit = currentData.critical_score_normalized;
  const currentClos = currentData.closure_score;
  for (let i = Math.max(0, bars - 5); i < bars; i++) {
    history[i].trio_score = Math.round((history[i].trio_score * 0.3 + currentTrio * 0.7) * 1000) / 1000;
    history[i].vibration_score = Math.round((history[i].vibration_score * 0.3 + currentVib * 0.7) * 1000) / 1000;
    history[i].critical_score = Math.round((history[i].critical_score * 0.3 + currentCrit * 0.7) * 1000) / 1000;
    history[i].closure_score = Math.round((history[i].closure_score * 0.3 + currentClos * 0.7) * 1000) / 1000;
  }
  return history;
};

// ── 自定义 Tooltip ──
const TrioTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <Box sx={{ bgcolor: "#161b22", border: "1px solid #30363d", p: 1.5, borderRadius: 1 }}>
      <Typography variant="caption" sx={{ color: "#8b949e" }}>
        Bar #{d.bar_index}
      </Typography>
      <Typography variant="body2" sx={{ color: getTrioColor(d.trio_score), fontWeight: 700 }}>
        三重奏: {d.trio_score?.toFixed(3)}
      </Typography>
      <Typography variant="body2" sx={{ color: "#58a6ff" }}>
        369振动: {d.vibration_score?.toFixed(3)}
      </Typography>
      <Typography variant="body2" sx={{ color: "#d29922" }}>
        139相变: {d.critical_score?.toFixed(3)}
      </Typography>
      <Typography variant="body2" sx={{ color: "#f0883e" }}>
        7闭合: {d.closure_score?.toFixed(3)}
      </Typography>
    </Box>
  );
};

// ── 主组件 ──
const CosmicAlgorithmPage: React.FC = () => {
  const [symbol, setSymbol] = useState("SH000001");
  const [timeframe, setTimeframe] = useState("1d");
  const [data, setData] = useState<CosmicAlgorithmData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trioHistory, setTrioHistory] = useState<any[]>([]);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `/api/v1/market/cosmic-algorithm?symbol=${symbol}&timeframe=${timeframe}&limit=200`
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      setData(json);
      setTrioHistory(generateTrioHistory(json));
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
      // 降级：使用模拟数据
      const mockData: CosmicAlgorithmData = {
        trio_score: 0.645,
        trio_label: "strong",
        trading_implication: "三重奏共振强，市场结构清晰，信号高度可信，可正常交易",
        risk_control: {
          should_reduce_position: false,
          should_hard_stop: false,
          volatility_warning: false,
        },
        vibration_369: {
          vibration_score: 0.65,
          trigger_freq: 0.15,
          resonance_freq: 0.25,
          closure_freq: 0.25,
          root_distribution: { 1: 5, 2: 3, 3: 6, 4: 4, 5: 2, 6: 5, 7: 3, 8: 2, 9: 5 },
          is_strong: true,
          is_noise: false,
          mode_label: "strong",
        },
        critical_139: {
          is_critical: false,
          variance_ratio: 1.2,
          autocorrelation: 0.15,
          recovery_rate: 0.8,
          critical_score: 1.0,
          regime: "transitioning",
        },
        cycle_7: {
          has_7_cycle: true,
          closure_score: 0.45,
          dominant_period: 7,
          fft_power_at_7: 0.003,
        },
        vibration_score: 0.65,
        critical_score_normalized: 0.333,
        closure_score: 0.45,
      };
      setData(mockData);
      setTrioHistory(generateTrioHistory(mockData));
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  if (!data) {
    return (
      <Box sx={{ p: 3, maxWidth: 1400, mx: "auto", textAlign: "center" }}>
        {loading ? (
          <CircularProgress size={60} sx={{ color: "#58a6ff" }} />
        ) : (
          <Typography sx={{ color: "#8b949e" }}>加载中...</Typography>
        )}
      </Box>
    );
  }

  const trioScore = data.trio_score ?? 0;
  const trioColor = getTrioColor(trioScore);

  // 数字根分布条形图数据
  const rootDistData = Object.entries(data.vibration_369.root_distribution || {}).map(
    ([root, count]) => ({
      root: `数字根${root}`,
      count,
      rootNum: Number(root),
      is369: Number(root) === 3 || Number(root) === 6 || Number(root) === 9,
    })
  );

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: "auto" }}>
      {/* 标题栏 */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <Orbit size={24} color="#58a6ff" />
        <Typography variant="h5" sx={{ fontWeight: 700, color: "#e6edf3" }}>
          宇宙算法三重奏
        </Typography>
        <Chip
          label="7-139-369"
          size="small"
          sx={{ bgcolor: "rgba(88,166,255,0.15)", color: "#58a6ff", fontSize: 11 }}
        />
      </Box>

      {/* 搜索栏 */}
      <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
        <TextField
          size="small"
          label="股票代码"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          sx={{ width: 200, input: { color: "#e6edf3" }, label: { color: "#8b949e" } }}
        />
        <TextField
          size="small"
          label="时间周期"
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          sx={{ width: 120, input: { color: "#e6edf3" }, label: { color: "#8b949e" } }}
        />
        <Button
          variant="contained"
          onClick={fetchAnalysis}
          disabled={loading}
          sx={{ bgcolor: "#238636", "&:hover": { bgcolor: "#2ea043" } }}
        >
          {loading ? <CircularProgress size={20} color="inherit" /> : "分析"}
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 2, bgcolor: "rgba(210,153,34,0.1)" }}>
          API 连接失败，已使用模拟数据展示。错误：{error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Trio Score 大表盘 */}
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d", height: "100%" }}>
            <CardContent sx={{ textAlign: "center", py: 4 }}>
              <Typography variant="body2" sx={{ color: "#8b949e", mb: 2 }}>
                三重奏综合评分 (7-139-369)
              </Typography>
              <Box sx={{ position: "relative", display: "inline-flex" }}>
                <CircularProgress
                  variant="determinate"
                  value={trioScore * 100}
                  size={160}
                  thickness={8}
                  sx={{ color: trioColor }}
                />
                <Box
                  sx={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    bottom: 0,
                    right: 0,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, color: trioColor }}>
                    {trioScore.toFixed(3)}
                  </Typography>
                  <Typography variant="caption" sx={{ color: "#8b949e", mt: 0.5 }}>
                    Trio Score
                  </Typography>
                </Box>
              </Box>
              <Chip
                label={getTrioLabel(data.trio_label)}
                sx={{
                  mt: 2,
                  bgcolor: `${trioColor}22`,
                  color: trioColor,
                  fontWeight: 600,
                }}
              />
              {/* 三层分数子表盘 */}
              <Box sx={{ mt: 3 }}>
                <Grid container spacing={1}>
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: "center" }}>
                      <CircularProgress
                        variant="determinate"
                        value={data.vibration_score * 100}
                        size={50}
                        thickness={4}
                        sx={{ color: "#58a6ff" }}
                      />
                      <Typography variant="caption" sx={{ color: "#58a6ff", mt: 0.5, display: "block" }}>
                        369: {data.vibration_score.toFixed(2)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: "center" }}>
                      <CircularProgress
                        variant="determinate"
                        value={data.critical_score_normalized * 100}
                        size={50}
                        thickness={4}
                        sx={{ color: "#d29922" }}
                      />
                      <Typography variant="caption" sx={{ color: "#d29922", mt: 0.5, display: "block" }}>
                        139: {data.critical_score_normalized.toFixed(2)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: "center" }}>
                      <CircularProgress
                        variant="determinate"
                        value={data.closure_score * 100}
                        size={50}
                        thickness={4}
                        sx={{ color: "#f0883e" }}
                      />
                      <Typography variant="caption" sx={{ color: "#f0883e", mt: 0.5, display: "block" }}>
                        7: {data.closure_score.toFixed(2)}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 三层评分卡片 */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            {/* 369 振动模态 */}
            <Grid item xs={12}>
              <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <Typography variant="h6" sx={{ color: "#58a6ff", fontWeight: 700 }}>
                      369 振动模态
                    </Typography>
                    <Chip
                      label={data.vibration_369.mode_label}
                      size="small"
                      sx={{ bgcolor: `${getModeColor(data.vibration_369.mode_label)}22`, color: getModeColor(data.vibration_369.mode_label) }}
                    />
                  </Box>
                  <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>振动模态分数</Typography>
                      <Typography variant="h5" sx={{ color: "#58a6ff", fontWeight: 700 }}>
                        {data.vibration_369.vibration_score.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>触发频率 (数字根=3)</Typography>
                      <Typography variant="h5" sx={{ color: "#3fb950", fontWeight: 700 }}>
                        {data.vibration_369.trigger_freq.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>共振频率 (数字根=6)</Typography>
                      <Typography variant="h5" sx={{ color: "#d29922", fontWeight: 700 }}>
                        {data.vibration_369.resonance_freq.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>归整频率 (数字根=9)</Typography>
                      <Typography variant="h5" sx={{ color: "#f0883e", fontWeight: 700 }}>
                        {data.vibration_369.closure_freq.toFixed(3)}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 139 相变评分 */}
            <Grid item xs={12}>
              <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <Typography variant="h6" sx={{ color: "#d29922", fontWeight: 700 }}>
                      139 临界演化
                    </Typography>
                    <Chip
                      label={getRegimeLabel(data.critical_139.regime)}
                      size="small"
                      sx={{ bgcolor: `${getRegimeColor(data.critical_139.regime)}22`, color: getRegimeColor(data.critical_139.regime) }}
                    />
                    {data.critical_139.is_critical && (
                      <Chip label="临界慢化" size="small" sx={{ bgcolor: "rgba(248,81,73,0.15)", color: "#f85149" }} />
                    )}
                  </Box>
                  <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>相变评分（归一化）</Typography>
                      <Typography variant="h5" sx={{ color: "#d29922", fontWeight: 700 }}>
                        {data.critical_score_normalized.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>方差比值</Typography>
                      <Typography variant="h5" sx={{ color: data.critical_139.variance_ratio > 1.5 ? "#f85149" : "#e6edf3", fontWeight: 700 }}>
                        {data.critical_139.variance_ratio.toFixed(2)}
                      </Typography>
                      {data.critical_139.variance_ratio > 1.5 && (
                        <Typography variant="caption" sx={{ color: "#f85149" }}>↑ 方差上升</Typography>
                      )}
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>自相关系数</Typography>
                      <Typography variant="h5" sx={{ color: Math.abs(data.critical_139.autocorrelation) > 0.3 ? "#f85149" : "#e6edf3", fontWeight: 700 }}>
                        {data.critical_139.autocorrelation.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>恢复速率</Typography>
                      <Typography variant="h5" sx={{ color: data.critical_139.recovery_rate > 0.5 ? "#d29922" : "#3fb950", fontWeight: 700 }}>
                        {data.critical_139.recovery_rate.toFixed(3)}
                      </Typography>
                      {data.critical_139.recovery_rate > 0.5 && (
                        <Typography variant="caption" sx={{ color: "#d29922" }}>↓ 恢复慢化</Typography>
                      )}
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 7 闭合评分 */}
            <Grid item xs={12}>
              <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <Typography variant="h6" sx={{ color: "#f0883e", fontWeight: 700 }}>
                      7 结构自指
                    </Typography>
                    <Chip
                      label={data.cycle_7.has_7_cycle ? "Z₇闭合" : "无循环群"}
                      size="small"
                      sx={{ bgcolor: data.cycle_7.has_7_cycle ? "rgba(63,185,80,0.15)" : "rgba(139,148,158,0.15)", color: data.cycle_7.has_7_cycle ? "#3fb950" : "#8b949e" }}
                    />
                  </Box>
                  <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>闭合度评分</Typography>
                      <Typography variant="h5" sx={{ color: "#f0883e", fontWeight: 700 }}>
                        {data.cycle_7.closure_score.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>主周期</Typography>
                      <Typography variant="h5" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                        {data.cycle_7.dominant_period}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>FFT功率(1/7)</Typography>
                      <Typography variant="h5" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                        {data.cycle_7.fft_power_at_7.toFixed(4)}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>循环节 142857</Typography>
                      <Typography variant="h5" sx={{ color: "#8b949e", fontWeight: 700, fontSize: "14px" }}>
                        1/7 = 0.142857...
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* 369 数字根分布条形图 */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <Orbit size={18} color="#58a6ff" />
                <Typography variant="h6" sx={{ color: "#e6edf3" }}>
                  369 数字根分布
                </Typography>
                <Chip label="模9群 Z₉" size="small" sx={{ bgcolor: "rgba(88,166,255,0.15)", color: "#58a6ff", fontSize: 10 }} />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Box sx={{ width: "100%", height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={rootDistData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                    <XAxis
                      dataKey="root"
                      stroke="#8b949e"
                      fontSize={11}
                    />
                    <YAxis
                      stroke="#8b949e"
                      fontSize={11}
                    />
                    <Tooltip
                      contentStyle={{ bgcolor: "#161b22", border: "1px solid #30363d", borderRadius: 4 }}
                      itemStyle={{ color: "#e6edf3" }}
                      labelStyle={{ color: "#8b949e" }}
                    />
                    <Bar
                      dataKey="count"
                      radius={[4, 4, 0, 0]}
                      fill="#58a6ff"
                    >
                      {/* 369数字根高亮 */}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
              <Box sx={{ display: "flex", gap: 3, mt: 1, justifyContent: "center" }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 8, bgcolor: "#3fb950", borderRadius: 0.5 }} />
                  <Typography variant="caption" sx={{ color: "#8b949e" }}>触发模态(3)</Typography>
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 8, bgcolor: "#d29922", borderRadius: 0.5 }} />
                  <Typography variant="caption" sx={{ color: "#8b949e" }}>共振模态(6)</Typography>
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 8, bgcolor: "#f0883e", borderRadius: 0.5 }} />
                  <Typography variant="caption" sx={{ color: "#8b949e" }}>归整模态(9)</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 三重奏综合时间序列图 */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <Orbit size={18} color="#58a6ff" />
                <Typography variant="h6" sx={{ color: "#e6edf3" }}>
                  三重奏综合走势
                </Typography>
                <Chip label="模拟数据" size="small" sx={{ bgcolor: "rgba(210,153,34,0.15)", color: "#d29922", fontSize: 10 }} />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Box sx={{ width: "100%", height: 280 }}>
                <ResponsiveContainer>
                  <ComposedChart data={trioHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                    <XAxis dataKey="bar_index" stroke="#8b949e" fontSize={11} />
                    <YAxis stroke="#8b949e" fontSize={11} domain={[0, 1]} />
                    <Tooltip content={<TrioTooltip />} />
                    {/* 区域标注 */}
                    <ReferenceArea y1={0.6} y2={1.0} fill="#3fb950" fillOpacity={0.04} />
                    <ReferenceArea y1={0.3} y2={0.6} fill="#d29922" fillOpacity={0.04} />
                    <ReferenceArea y1={0} y2={0.3} fill="#f85149" fillOpacity={0.04} />
                    <ReferenceLine y={0.6} stroke="#3fb950" strokeDasharray="3 3" />
                    <ReferenceLine y={0.3} stroke="#d29922" strokeDasharray="3 3" />
                    {/* 三重奏面积图 */}
                    <Area
                      type="monotone"
                      dataKey="trio_score"
                      stroke={trioColor}
                      fill={`${trioColor}15`}
                      strokeWidth={2}
                      name="三重奏"
                    />
                    {/* 各层折线 */}
                    <Line type="monotone" dataKey="vibration_score" stroke="#58a6ff" strokeWidth={1.5} dot={false} name="369振动" />
                    <Line type="monotone" dataKey="critical_score" stroke="#d29922" strokeWidth={1.5} dot={false} name="139相变" />
                    <Line type="monotone" dataKey="closure_score" stroke="#f0883e" strokeWidth={1.5} dot={false} name="7闭合" />
                    <Legend
                      wrapperStyle={{ fontSize: 11, color: "#8b949e" }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 交易含义 + 风控建议 */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                  交易含义
                </Typography>
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Typography variant="body1" sx={{ color: trioColor, fontWeight: 600, mb: 2 }}>
                {data.trading_implication}
              </Typography>
              <TableContainer component={Paper} sx={{ bgcolor: "transparent" }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ "& th": { color: "#8b949e", borderColor: "#30363d" } }}>
                      <TableCell>风控指标</TableCell>
                      <TableCell>状态</TableCell>
                      <TableCell>说明</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                      <TableCell>139缩仓</TableCell>
                      <TableCell>
                        <Chip
                          label={data.risk_control.should_reduce_position ? "触发" : "安全"}
                          size="small"
                          sx={{
                            bgcolor: data.risk_control.should_reduce_position ? "rgba(248,81,73,0.15)" : "rgba(63,185,80,0.15)",
                            color: data.risk_control.should_reduce_position ? "#f85149" : "#3fb950",
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: "#8b949e" }}>
                        {data.risk_control.should_reduce_position ? "临界慢化 → 建议减仓50%" : "市场稳定 → 正常仓位"}
                      </TableCell>
                    </TableRow>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                      <TableCell>σ硬止损</TableCell>
                      <TableCell>
                        <Chip
                          label={data.risk_control.should_hard_stop ? "触发" : "安全"}
                          size="small"
                          sx={{
                            bgcolor: data.risk_control.should_hard_stop ? "rgba(248,81,73,0.15)" : "rgba(63,185,80,0.15)",
                            color: data.risk_control.should_hard_stop ? "#f85149" : "#3fb950",
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: "#8b949e" }}>
                        {data.risk_control.should_hard_stop ? "critical_score≥3 → 必须立即止损退出" : "波动率正常 → 无需硬止损"}
                      </TableCell>
                    </TableRow>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                      <TableCell>波动率警告</TableCell>
                      <TableCell>
                        <Chip
                          label={data.risk_control.volatility_warning ? "警告" : "正常"}
                          size="small"
                          sx={{
                            bgcolor: data.risk_control.volatility_warning ? "rgba(210,153,34,0.15)" : "rgba(63,185,80,0.15)",
                            color: data.risk_control.volatility_warning ? "#d29922" : "#3fb950",
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: "#8b949e" }}>
                        {data.risk_control.volatility_warning ? "方差比值>2 → 波动异常，谨慎操作" : "方差比值正常"}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* 三层评分对比表 */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700, mb: 1 }}>
                三层评分详情
              </Typography>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <TableContainer component={Paper} sx={{ bgcolor: "transparent" }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ "& th": { color: "#8b949e", borderColor: "#30363d" } }}>
                      <TableCell>层级</TableCell>
                      <TableCell>分数</TableCell>
                      <TableCell>标签</TableCell>
                      <TableCell>阈值判定</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                      <TableCell>
                        <Chip label="369" size="small" sx={{ bgcolor: "rgba(88,166,255,0.12)", color: "#58a6ff" }} />
                      </TableCell>
                      <TableCell>
                        <Typography sx={{ color: "#58a6ff", fontWeight: 700 }}>
                          {data.vibration_score.toFixed(3)}
                        </Typography>
                      </TableCell>
                      <TableCell>{data.vibration_369.mode_label}</TableCell>
                      <TableCell>
                        <LinearProgress
                          variant="determinate"
                          value={data.vibration_score * 100}
                          sx={{ width: 120, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: "#58a6ff" } }}
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                      <TableCell>
                        <Chip label="139" size="small" sx={{ bgcolor: "rgba(210,153,34,0.12)", color: "#d29922" }} />
                      </TableCell>
                      <TableCell>
                        <Typography sx={{ color: "#d29922", fontWeight: 700 }}>
                          {data.critical_score_normalized.toFixed(3)}
                        </Typography>
                      </TableCell>
                      <TableCell>{getRegimeLabel(data.critical_139.regime)}</TableCell>
                      <TableCell>
                        <LinearProgress
                          variant="determinate"
                          value={data.critical_score_normalized * 100}
                          sx={{ width: 120, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: "#d29922" } }}
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                      <TableCell>
                        <Chip label="7" size="small" sx={{ bgcolor: "rgba(240,136,62,0.12)", color: "#f0883e" }} />
                      </TableCell>
                      <TableCell>
                        <Typography sx={{ color: "#f0883e", fontWeight: 700 }}>
                          {data.closure_score.toFixed(3)}
                        </Typography>
                      </TableCell>
                      <TableCell>{data.cycle_7.has_7_cycle ? "Z₇闭合" : "无循环群"}</TableCell>
                      <TableCell>
                        <LinearProgress
                          variant="determinate"
                          value={data.closure_score * 100}
                          sx={{ width: 120, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: "#f0883e" } }}
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d", fontWeight: 700 } }}>
                      <TableCell>
                        <Chip label="三重奏" size="small" sx={{ bgcolor: `${trioColor}22`, color: trioColor }} />
                      </TableCell>
                      <TableCell>
                        <Typography sx={{ color: trioColor, fontWeight: 800 }}>
                          {data.trio_score.toFixed(3)}
                        </Typography>
                      </TableCell>
                      <TableCell>{getTrioLabel(data.trio_label)}</TableCell>
                      <TableCell>
                        <LinearProgress
                          variant="determinate"
                          value={data.trio_score * 100}
                          sx={{ width: 120, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: trioColor } }}
                        />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CosmicAlgorithmPage;
