/**
 * PhaseAnalysisPage - 相位连续性分析页面 (TOMAS v2.0)
 *
 * 展示：
 * - 相位连续性评分 (PCS) 大表盘
 * - 市场状态判定（相位连续区 / 过渡区 / 相变奇点区）
 * - LOB 深度熵指标
 * - ENPV 决策建议
 * - 操作建议（买入/观望/熔断）
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
import { Activity, Zap, ShieldAlert, TrendingUp } from "lucide-react";

// ── 类型定义 ──
interface PhaseAnalysisData {
  pcs: number;
  market_state: string;
  is_singularity: boolean;
  lob_depth_entropy: number;
  enpv: number;
  recommendation: string;
  volatility: number;
  volume_z_score: number;
  invariant_detections: Array<{
    invariant: number;
    detected_period: number;
    power: number;
  }>;
}

// ── 辅助函数 ──
const getStateColor = (pcs: number): string => {
  if (pcs >= 0.7) return "#3fb950"; // 绿色 — 相位连续
  if (pcs >= 0.3) return "#d29922"; // 黄色 — 过渡区
  return "#f85149"; // 红色 — 相变奇点
};

const getStateLabel = (pcs: number): string => {
  if (pcs >= 0.7) return "相位连续区";
  if (pcs >= 0.3) return "过渡区";
  return "相变奇点区";
};

const getRecommendationColor = (rec: string): string => {
  if (rec.includes("正常") || rec.includes("买入")) return "#3fb950";
  if (rec.includes("谨慎") || rec.includes("降仓")) return "#d29922";
  return "#f85149";
};

// ── 主组件 ──
const PhaseAnalysisPage: React.FC = () => {
  const [symbol, setSymbol] = useState("SH000001");
  const [data, setData] = useState<PhaseAnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `/api/v1/market/phase-analysis?symbol=${symbol}&bars=120`
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
      // 降级：使用模拟数据
      setData({
        pcs: 0.72,
        market_state: "相位连续区",
        is_singularity: false,
        lob_depth_entropy: 1.85,
        enpv: 0.034,
        recommendation: "正常交易：相位连续，拓扑不变量有效",
        volatility: 0.018,
        volume_z_score: 0.6,
        invariant_detections: [
          { invariant: 13, detected_period: 13.1, power: 0.82 },
          { invariant: 21, detected_period: 20.8, power: 0.65 },
          { invariant: 29, detected_period: 29.3, power: 0.71 },
          { invariant: 34, detected_period: 33.9, power: 0.55 },
          { invariant: 55, detected_period: 55.2, power: 0.43 },
        ],
      });
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const pcs = data?.pcs ?? 0;
  const stateColor = getStateColor(pcs);

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: "auto" }}>
      {/* 标题栏 */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <Activity size={24} color="#58a6ff" />
        <Typography variant="h5" sx={{ fontWeight: 700, color: "#e6edf3" }}>
          相位连续性分析
        </Typography>
        <Chip
          label="TOMAS v2.0"
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

      {data && (
        <Grid container spacing={3}>
          {/* PCS 大表盘 */}
          <Grid item xs={12} md={4}>
            <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d", height: "100%" }}>
              <CardContent sx={{ textAlign: "center", py: 4 }}>
                <Typography variant="body2" sx={{ color: "#8b949e", mb: 2 }}>
                  相位连续性评分 (PCS)
                </Typography>
                <Box sx={{ position: "relative", display: "inline-flex" }}>
                  <CircularProgress
                    variant="determinate"
                    value={pcs * 100}
                    size={140}
                    thickness={8}
                    sx={{ color: stateColor }}
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
                    <Typography variant="h3" sx={{ fontWeight: 800, color: stateColor }}>
                      {pcs.toFixed(3)}
                    </Typography>
                  </Box>
                </Box>
                <Chip
                  label={getStateLabel(pcs)}
                  sx={{
                    mt: 2,
                    bgcolor: `${stateColor}22`,
                    color: stateColor,
                    fontWeight: 600,
                  }}
                />
                {data.is_singularity && (
                  <Alert severity="error" sx={{ mt: 2, bgcolor: "rgba(248,81,73,0.1)" }}>
                    <ShieldAlert size={16} style={{ verticalAlign: "middle", marginRight: 6 }} />
                    相变奇点！拓扑不变量失效
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* 指标卡片 */}
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              {/* LOB深度熵 */}
              <Grid item xs={6} md={3}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      LOB 深度熵
                    </Typography>
                    <Typography variant="h5" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                      {data.lob_depth_entropy.toFixed(3)}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(data.lob_depth_entropy * 40, 100)}
                      sx={{ mt: 1, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: "#58a6ff" } }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* ENPV */}
              <Grid item xs={6} md={3}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      ENPV 决策值
                    </Typography>
                    <Typography
                      variant="h5"
                      sx={{
                        fontWeight: 700,
                        color: data.enpv >= 0 ? "#3fb950" : "#f85149",
                      }}
                    >
                      {data.enpv >= 0 ? "+" : ""}
                      {data.enpv.toFixed(4)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "#8b949e" }}>
                      {data.enpv >= 0 ? "可追单" : "放弃追单"}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* 波动率 */}
              <Grid item xs={6} md={3}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      波动率
                    </Typography>
                    <Typography variant="h5" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                      {(data.volatility * 100).toFixed(2)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(data.volatility * 2000, 100)}
                      sx={{
                        mt: 1,
                        bgcolor: "#21262d",
                        "& .MuiLinearProgress-bar": { bgcolor: data.volatility > 0.03 ? "#f85149" : "#3fb950" },
                      }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* 成交量Z分数 */}
              <Grid item xs={6} md={3}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      成交量 Z-Score
                    </Typography>
                    <Typography
                      variant="h5"
                      sx={{
                        fontWeight: 700,
                        color: Math.abs(data.volume_z_score) > 2 ? "#f85149" : "#e6edf3",
                      }}
                    >
                      {data.volume_z_score.toFixed(2)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "#8b949e" }}>
                      {Math.abs(data.volume_z_score) > 2 ? "异常" : "正常"}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* 操作建议 */}
              <Grid item xs={12}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                      <TrendingUp size={18} color={getRecommendationColor(data.recommendation)} />
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>
                        操作建议
                      </Typography>
                    </Box>
                    <Typography
                      variant="h6"
                      sx={{ color: getRecommendationColor(data.recommendation), fontWeight: 600 }}
                    >
                      {data.recommendation}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* 拓扑不变量周期检测表 */}
          <Grid item xs={12}>
            <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                  <Zap size={18} color="#58a6ff" />
                  <Typography variant="h6" sx={{ color: "#e6edf3" }}>
                    拓扑不变量周期检测
                  </Typography>
                </Box>
                <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
                <TableContainer component={Paper} sx={{ bgcolor: "transparent" }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ "& th": { color: "#8b949e", borderColor: "#30363d" } }}>
                        <TableCell>不变量</TableCell>
                        <TableCell>检测周期</TableCell>
                        <TableCell>功率</TableCell>
                        <TableCell>强度</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.invariant_detections.map((inv) => (
                        <TableRow key={inv.invariant} sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                          <TableCell>
                            <Chip
                              label={inv.invariant}
                              size="small"
                              sx={{ bgcolor: "rgba(88,166,255,0.12)", color: "#58a6ff" }}
                            />
                          </TableCell>
                          <TableCell>{inv.detected_period.toFixed(1)}</TableCell>
                          <TableCell>{inv.power.toFixed(3)}</TableCell>
                          <TableCell>
                            <LinearProgress
                              variant="determinate"
                              value={inv.power * 100}
                              sx={{ width: 100, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: "#58a6ff" } }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default PhaseAnalysisPage;
