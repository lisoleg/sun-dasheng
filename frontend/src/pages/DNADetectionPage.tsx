/**
 * DNADetectionPage - 鲁兆DNA倍发生成验证页面 (TOMAS v2.0)
 *
 * 展示：
 * - DNA基因卡片（第一浪幅度/时间）
 * - κ-Snap溯因验证结果
 * - 波浪倍数检测结果表
 * - 斐波那契/鲁加斯数验证
 * - 【新增】波浪结构可视化图
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
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
  ComposedChart,
} from "recharts";
import { Dna, CheckCircle2, XCircle, Search } from "lucide-react";

// ── 类型定义 ──
interface DNAGene {
  wave_label: string;
  amplitude: number;
  duration: number;
  start_index: number;
  end_index: number;
}

interface DNADetectionData {
  genes: DNAGene[];
  ksnap_verified: boolean;
  ksnap_score: number;
  fibonacci_verification: {
    valid: boolean;
    match_rate: number;
    details: Array<{
      wave: number;
      actual: number;
      expected: number;
      error: number;
      matches: boolean;
    }>;
  };
  lucas_verification: {
    valid: boolean;
    match_rate: number;
  };
  phase_valid: boolean;
  pcs: number;
  summary: string;
  wave_chart?: Array<{
    bar_index: number;
    price: number;
    wave_label?: string;
    is_swing?: boolean;
  }>;
}

// ── 波浪模拟数据生成 ──
const generateWaveChartData = (genes: DNAGene[]) => {
  const data: Array<{
    bar_index: number;
    price: number;
    wave_label?: string;
    is_swing?: boolean;
  }> = [];
  if (!genes.length) return data;

  const totalBars = Math.max(...genes.map((g) => g.end_index)) + 10;
  let price = 3000;
  const baseIdx = 0;

  // 根据 gene 生成价格走势
  for (const gene of genes) {
    const start = gene.start_index;
    const end = gene.end_index;
    const isUp = gene.wave_label.includes("1") || gene.wave_label.includes("3") || gene.wave_label.includes("5");
    const direction = isUp ? 1 : -1;
    const totalChange = gene.amplitude * direction;

    for (let i = start; i <= end; i++) {
      const progress = (i - start) / (end - start);
      // 模拟波浪形状（加速-减速）
      const shaped = progress < 0.5
        ? 2 * progress * progress
        : 1 - 2 * (1 - progress) * (1 - progress);
      price = (price || 3000) + (totalChange * (shaped - (data[data.length - 1]?.price ? 0 : 0)) / (end - start + 1);
      // 简化：直接用线性+噪声
      const noise = (Math.random() - 0.5) * 10;
      const barPrice = 3000 + (i * 5) + (isUp ? i * 3 : -i * 2) + noise;
      data.push({
        bar_index: i,
        price: Math.round(barPrice * 100) / 100,
        wave_label: i === start ? gene.wave_label : undefined,
        is_swing: i === start || i === end,
      });
    }
  }
  return data;
};

// ── 自定义 Tooltip ──
const WaveTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <Box sx={{ bgcolor: "#161b22", border: "1px solid #30363d", p: 1.5, borderRadius: 1 }}>
      <Typography variant="caption" sx={{ color: "#8b949e" }}>
        Bar #{d.bar_index}
      </Typography>
      <Typography variant="body2" sx={{ color: "#e6edf3", fontWeight: 700 }}>
        价格: {d.price.toFixed(2)}
      </Typography>
      {d.wave_label && (
        <Chip label={d.wave_label} size="small" sx={{ bgcolor: "rgba(88,166,255,0.15)", color: "#58a6ff", mt: 0.5 }} />
      )}
    </Box>
  );
};

// ── 主组件 ──
const DNADetectionPage: React.FC = () => {
  const [symbol, setSymbol] = useState("SH000001");
  const [data, setData] = useState<DNADetectionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetection = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `/api/v1/market/dna-detection?symbol=${symbol}&bars=200`
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      // 后端暂未返回 wave_chart，前端生成模拟数据
      if (!json.wave_chart && json.genes) {
        json.wave_chart = generateWaveChartData(json.genes);
      }
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
      // 降级：模拟数据
      const mockGenes = [
        { wave_label: "浪1", amplitude: 320.5, duration: 13, start_index: 10, end_index: 23 },
        { wave_label: "浪2", amplitude: 198.3, duration: 8, start_index: 23, end_index: 31 },
        { wave_label: "浪3", amplitude: 518.7, duration: 21, start_index: 31, end_index: 52 },
        { wave_label: "浪4", amplitude: 240.1, duration: 13, start_index: 52, end_index: 65 },
        { wave_label: "浪5", amplitude: 345.2, duration: 21, start_index: 65, end_index: 86 },
      ];
      setData({
        genes: mockGenes,
        ksnap_verified: true,
        ksnap_score: 0.78,
        fibonacci_verification: {
          valid: true,
          match_rate: 0.8,
          details: [
            { wave: 1, actual: 320.5, expected: 320.5, error: 0, matches: true },
            { wave: 2, actual: 198.3, expected: 198.7, error: 0.002, matches: true },
            { wave: 3, actual: 518.7, expected: 518.4, error: 0.001, matches: true },
            { wave: 4, actual: 240.1, expected: 310.0, error: 0.225, matches: false },
            { wave: 5, actual: 345.2, expected: 345.7, error: 0.001, matches: true },
          ],
        },
        lucas_verification: { valid: true, match_rate: 0.67 },
        phase_valid: true,
        pcs: 0.75,
        summary: "DNA倍发生成验证通过：80%斐波那契匹配 + κ-Snap验证通过 + 相位连续",
        wave_chart: generateWaveChartData(mockGenes),
      });
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchDetection();
  }, [fetchDetection]);

  // 获取波浪边界用于图表标注
  const waveMarkers = data?.wave_chart
    ?.filter((d) => d.wave_label)
    .map((d) => d.bar_index) ?? [];

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: "auto" }}>
      {/* 标题栏 */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <Dna size={24} color="#58a6ff" />
        <Typography variant="h5" sx={{ fontWeight: 700, color: "#e6edf3" }}>
          鲁兆DNA倍发生成验证
        </Typography>
        <Chip
          label="κ-Snap"
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
          onClick={fetchDetection}
          disabled={loading}
          startIcon={!loading ? <Search size={16} /> : undefined}
          sx={{ bgcolor: "#238636", "&:hover": { bgcolor: "#2ea043" } }}
        >
          {loading ? <CircularProgress size={20} color="inherit" /> : "检测"}
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 2, bgcolor: "rgba(210,153,34,0.1)" }}>
          API 连接失败，已使用模拟数据展示。错误：{error}
        </Alert>
      )}

      {data && (
        <Grid container spacing={3}>
          {/* κ-Snap 验证状态 */}
          <Grid item xs={12} md={4}>
            <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d", height: "100%" }}>
              <CardContent sx={{ textAlign: "center", py: 4 }}>
                <Typography variant="body2" sx={{ color: "#8b949e", mb: 2 }}>
                  κ-Snap 溯因验证
                </Typography>
                {data.ksnap_verified ? (
                  <CheckCircle2 size={80} color="#3fb950" style={{ margin: "0 auto" }} />
                ) : (
                  <XCircle size={80} color="#f85149" style={{ margin: "0 auto" }} />
                )}
                <Typography variant="h4" sx={{ mt: 2, fontWeight: 800, color: data.ksnap_verified ? "#3fb950" : "#f85149" }}>
                  {data.ksnap_score.toFixed(2)}
                </Typography>
                <Typography variant="body2" sx={{ color: "#8b949e", mt: 1 }}>
                  {data.ksnap_verified ? "验证通过" : "验证失败"}
                </Typography>
                <Chip
                  label={data.phase_valid ? "相位连续" : "相位断裂"}
                  size="small"
                  sx={{
                    mt: 2,
                    bgcolor: data.phase_valid ? "rgba(63,185,80,0.15)" : "rgba(248,81,73,0.15)",
                    color: data.phase_valid ? "#3fb950" : "#f85149",
                  }}
                />
              </CardContent>
            </Card>
          </Grid>

          {/* 验证摘要 */}
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              {/* 斐波那契验证 */}
              <Grid item xs={6}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      斐波那契倍数验证
                    </Typography>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      {data.fibonacci_verification.valid ? (
                        <CheckCircle2 size={20} color="#3fb950" />
                      ) : (
                        <XCircle size={20} color="#f85149" />
                      )}
                      <Typography variant="h5" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                        {(data.fibonacci_verification.match_rate * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: "#8b949e" }}>
                      匹配率
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* 鲁加斯验证 */}
              <Grid item xs={6}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      鲁加斯自相似验证
                    </Typography>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      {data.lucas_verification.valid ? (
                        <CheckCircle2 size={20} color="#3fb950" />
                      ) : (
                        <XCircle size={20} color="#f85149" />
                      )}
                      <Typography variant="h5" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                        {(data.lucas_verification.match_rate * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: "#8b949e" }}>
                      隔代自相似匹配率
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* 摘要 */}
              <Grid item xs={12}>
                <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      检测摘要
                    </Typography>
                    <Typography variant="body1" sx={{ color: "#e6edf3" }}>
                      {data.summary}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* ── 新增：波浪结构可视化图 ── */}
          <Grid item xs={12}>
            <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                  <Dna size={18} color="#58a6ff" />
                  <Typography variant="h6" sx={{ color: "#e6edf3" }}>
                    波浪结构可视化
                  </Typography>
                  <Chip label="模拟数据" size="small" sx={{ bgcolor: "rgba(210,153,34,0.15)", color: "#d29922", fontSize: 10 }} />
                </Box>
                <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
                <Box sx={{ width: "100%", height: 320 }}>
                  <ResponsiveContainer>
                    <ComposedChart data={data.wave_chart ?? []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                      <XAxis
                        dataKey="bar_index"
                        stroke="#8b949e"
                        fontSize={11}
                        label={{ value: "K线序号", position: "insideBottom", offset: -5, fill: "#8b949e", fontSize: 11 }}
                      />
                      <YAxis
                        stroke="#8b949e"
                        fontSize={11}
                        label={{ value: "价格", angle: -90, position: "insideLeft", fill: "#8b949e", fontSize: 11 }}
                      />
                      <Tooltip content={<WaveTooltip />} />
                      {/* 价格面积图 */}
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#58a6ff"
                        fill="rgba(88,166,255,0.08)"
                        strokeWidth={2}
                        name="价格"
                      />
                      {/* 波浪边界散点 */}
                      <Scatter
                        dataKey="price"
                        fill="#f0883e"
                        shape="diamond"
                        legendType="none"
                      />
                      {/* 波浪标注线 */}
                      {waveMarkers.map((idx) => {
                        const point = data.wave_chart?.find((d) => d.bar_index === idx);
                        return point ? (
                          <ReferenceLine
                            key={idx}
                            x={idx}
                            stroke="#f0883e"
                            strokeDasharray="3 3"
                            label={{
                              value: point.wave_label,
                              position: "top",
                              fill: "#f0883e",
                              fontSize: 11,
                            }}
                          />
                        ) : null;
                      })}
                    </ComposedChart>
                  </ResponsiveContainer>
                </Box>
                <Typography variant="caption" sx={{ color: "#8b949e", display: "block", mt: 1 }}>
                  📊 面积图展示价格走势 · 🔷 菱形标记波浪起点 · 虚线标注波浪边界
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* DNA基因卡片 */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ color: "#e6edf3", mb: 2 }}>
              DNA基因（波浪信息）
            </Typography>
            <Grid container spacing={2}>
              {data.genes.map((gene) => (
                <Grid item xs={6} md={2.4} key={gene.wave_label}>
                  <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: "#58a6ff", fontWeight: 700, mb: 1 }}>
                        {gene.wave_label}
                      </Typography>
                      <Divider sx={{ mb: 1, borderColor: "#30363d" }} />
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>
                        幅度: <span style={{ color: "#e6edf3", fontWeight: 600 }}>{gene.amplitude.toFixed(1)}</span>
                      </Typography>
                      <Typography variant="body2" sx={{ color: "#8b949e" }}>
                        时间: <span style={{ color: "#e6edf3", fontWeight: 600 }}>{gene.duration} 根</span>
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* 斐波那契倍数验证表 */}
          <Grid item xs={12}>
            <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: "#e6edf3", mb: 2 }}>
                  斐波那契倍数验证明细
                </Typography>
                <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
                <TableContainer component={Paper} sx={{ bgcolor: "transparent" }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ "& th": { color: "#8b949e", borderColor: "#30363d" } }}>
                        <TableCell>浪号</TableCell>
                        <TableCell>实际幅度</TableCell>
                        <TableCell>期望幅度</TableCell>
                        <TableCell>误差</TableCell>
                        <TableCell>匹配</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.fibonacci_verification.details.map((d) => (
                        <TableRow key={d.wave} sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                          <TableCell>浪{d.wave}</TableCell>
                          <TableCell>{d.actual.toFixed(1)}</TableCell>
                          <TableCell>{d.expected.toFixed(1)}</TableCell>
                          <TableCell>{(d.error * 100).toFixed(1)}%</TableCell>
                          <TableCell>
                            {d.matches ? (
                              <CheckCircle2 size={16} color="#3fb950" />
                            ) : (
                              <XCircle size={16} color="#f85149" />
                            )}
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

export default DNADetectionPage;
