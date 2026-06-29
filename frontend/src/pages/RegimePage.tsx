/**
 * RegimePage - 经济象限检测（Dalio象限 + TDA拓扑预警）
 *
 * 展示：
 * - Dalio 2x2象限矩阵（REFLATION/EXPANSION/DEFLATION/STAGFLATION）
 * - TDA拓扑预警卡片（β₀连通分量 + β₁环形结构 + persistence_score）
 * - 增长/通胀信号仪表盘
 * - 推荐资产权重雷达图
 * - 理论引擎权重调整表
 * - 象限历史模拟走势图
 * - 交易建议卡片
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Legend,
} from "recharts";
import { Grid2X2 } from "lucide-react";

// ── 类型定义 ──
interface RegimeData {
  regime: string;
  confidence: number;
  growth_signal: number;
  inflation_signal: number;
  description: string;
  asset_weights: Record<string, number>;
  betti_0: number;
  betti_1: number;
  persistence_score: number;
  tda_warning: string;
  tda_confidence: number;
  theory_weights_adjustment: Record<string, number>;
}

// ── 辅助函数 ──
const getRegimeLabel = (regime: string): string => {
  const labelMap: Record<string, string> = {
    expansion: "扩张期",
    reflation: "再膨胀期",
    stagflation: "滞胀期",
    deflation: "通缩期",
  };
  return labelMap[regime] || regime;
};

const getRegimeColor = (regime: string): string => {
  const colorMap: Record<string, string> = {
    expansion: "#3fb950",   // 绿色 — 增长↑通胀↑
    reflation: "#58a6ff",   // 蓝色 — 增长↑通胀↓
    stagflation: "#f85149", // 红色 — 增长↓通胀↑
    deflation: "#bc8cff",   // 紫色 — 增长↓通胀↓
  };
  return colorMap[regime] || "#8b949e";
};

const getRegimeBgColor = (regime: string): string => {
  const colorMap: Record<string, string> = {
    expansion: "rgba(63,185,80,0.08)",
    reflation: "rgba(88,166,255,0.08)",
    stagflation: "rgba(248,81,73,0.08)",
    deflation: "rgba(188,140,255,0.08)",
  };
  return colorMap[regime] || "rgba(139,148,158,0.08)";
};

const getTDAWarningLabel = (warning: string): string => {
  const labelMap: Record<string, string> = {
    normal: "正常",
    fragmenting: "碎片化⚠️",
    loop_transition: "环形过渡⚠️",
    critical_transition: "临界过渡🔴",
  };
  return labelMap[warning] || warning;
};

const getTDAWarningColor = (warning: string): string => {
  if (warning === "critical_transition") return "#f85149";
  if (warning === "fragmenting") return "#d29922";
  if (warning === "loop_transition") return "#58a6ff";
  return "#3fb950";
};

const getPersistenceColor = (score: number): string => {
  if (score >= 0.5) return "#3fb950"; // 稳定
  if (score >= 0.3) return "#d29922"; // 中等
  return "#f85149"; // 脆弱
};

const getAssetName = (key: string): string => {
  const nameMap: Record<string, string> = {
    equity: "股票",
    commodity: "商品",
    bond: "债券",
    gold: "黄金",
    cash: "现金",
  };
  return nameMap[key] || key;
};

// ── 象限配置 ──
const QUADRANTS = [
  { id: "reflation", label: "再膨胀期", sub: "增长↑通胀↓", color: "#58a6ff", bgColor: "rgba(88,166,255,0.12)", x: 0, y: 0, assets: "股票50% 债券25%" },
  { id: "expansion", label: "扩张期", sub: "增长↑通胀↑", color: "#3fb950", bgColor: "rgba(63,185,80,0.12)", x: 1, y: 0, assets: "股票40% 商品25%" },
  { id: "deflation", label: "通缩期", sub: "增长↓通胀↓", color: "#bc8cff", bgColor: "rgba(188,140,255,0.12)", x: 0, y: 1, assets: "债券50% 现金20%" },
  { id: "stagflation", label: "滞胀期", sub: "增长↓通胀↑", color: "#f85149", bgColor: "rgba(248,81,73,0.12)", x: 1, y: 1, assets: "商品40% 黄金30%" },
];

// ── 历史模拟数据 ──
const generateRegimeHistory = (currentData: RegimeData, bars: number = 60) => {
  const history: Array<{
    bar_index: number;
    growth_signal: number;
    inflation_signal: number;
    confidence: number;
    betti_0: number;
    betti_1: number;
    persistence_score: number;
  }> = [];
  let g = currentData.growth_signal;
  let i = currentData.inflation_signal;
  let c = currentData.confidence;
  let b0 = currentData.betti_0;
  let b1 = currentData.betti_1;
  let ps = currentData.persistence_score;

  for (let idx = 0; idx < bars; idx++) {
    g += (Math.random() - 0.5) * 2;
    i += (Math.random() - 0.5) * 2;
    c += (Math.random() - 0.48) * 0.05;
    b0 = Math.max(1, b0 + Math.round((Math.random() - 0.6) * 1));
    b1 = Math.max(0, b1 + Math.round((Math.random() - 0.7) * 1));
    ps += (Math.random() - 0.48) * 0.04;
    c = Math.max(0, Math.min(1, c));
    ps = Math.max(0.05, Math.min(1, ps));
    history.push({
      bar_index: idx,
      growth_signal: Math.round(g * 100) / 100,
      inflation_signal: Math.round(i * 100) / 100,
      confidence: Math.round(c * 1000) / 1000,
      betti_0: b0,
      betti_1: b1,
      persistence_score: Math.round(ps * 1000) / 1000,
    });
  }

  // 最后5根让数据接近当前值
  for (let idx = Math.max(0, bars - 5); idx < bars; idx++) {
    history[idx].growth_signal = Math.round((history[idx].growth_signal * 0.3 + currentData.growth_signal * 0.7) * 100) / 100;
    history[idx].inflation_signal = Math.round((history[idx].inflation_signal * 0.3 + currentData.inflation_signal * 0.7) * 100) / 100;
    history[idx].betti_0 = currentData.betti_0;
    history[idx].betti_1 = currentData.betti_1;
    history[idx].persistence_score = Math.round((history[idx].persistence_score * 0.3 + currentData.persistence_score * 0.7) * 1000) / 1000;
  }

  return history;
};

// ── Mock数据 ──
const MOCK_DATA: RegimeData = {
  regime: "expansion",
  confidence: 0.65,
  growth_signal: 3.5,
  inflation_signal: 2.8,
  description: "增长↑通胀↑ — 扩张期，股票和商品利好",
  asset_weights: { equity: 0.40, commodity: 0.25, bond: 0.15, gold: 0.10, cash: 0.10 },
  betti_0: 1,
  betti_1: 0,
  persistence_score: 0.72,
  tda_warning: "normal",
  tda_confidence: 0.58,
  theory_weights_adjustment: {
    taiji: 1.2, spiral: 1.2, elliott_wave: 1.1,
    cycle_law: 1.0, dual_law: 1.0,
    gann_angle: 0.9, bg_moving_average: 0.8,
  },
};

// ── 自定义 Tooltip ──
const RegimeTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <Box sx={{ bgcolor: "#161b22", border: "1px solid #30363d", p: 1.5, borderRadius: 1 }}>
      <Typography variant="caption" sx={{ color: "#8b949e" }}>
        Bar #{d.bar_index}
      </Typography>
      <Typography variant="body2" sx={{ color: "#58a6ff" }}>
        增长: {d.growth_signal?.toFixed(2)}
      </Typography>
      <Typography variant="body2" sx={{ color: "#d29922" }}>
        通胀: {d.inflation_signal?.toFixed(2)}
      </Typography>
      <Typography variant="body2" sx={{ color: "#3fb950" }}>
        置信度: {d.confidence?.toFixed(3)}
      </Typography>
      <Typography variant="body2" sx={{ color: "#f0883e" }}>
        β₀: {d.betti_0} | β₁: {d.betti_1}
      </Typography>
      <Typography variant="body2" sx={{ color: getPersistenceColor(d.persistence_score) }}>
        Persistence: {d.persistence_score?.toFixed(3)}
      </Typography>
    </Box>
  );
};

// ── 主组件 ──
const RegimePage: React.FC = () => {
  const [symbol, setSymbol] = useState("SH000001");
  const [timeframe, setTimeframe] = useState("1d");
  const [data, setData] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [regimeHistory, setRegimeHistory] = useState<any[]>([]);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `/api/v1/market/regime?symbol=${symbol}&timeframe=${timeframe}&limit=200`
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      if (json.code !== 0 || !json.data) throw new Error(json.message || "数据异常");
      setData(json.data);
      setRegimeHistory(generateRegimeHistory(json.data));
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
      setData(MOCK_DATA);
      setRegimeHistory(generateRegimeHistory(MOCK_DATA));
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

  const regimeColor = getRegimeColor(data.regime);
  const tdaWarningColor = getTDAWarningColor(data.tda_warning);
  const persistenceColor = getPersistenceColor(data.persistence_score);

  // 资产权重雷达图数据
  const radarData = Object.entries(data.asset_weights).map(([key, val]) => ({
    asset: getAssetName(key),
    weight: Math.round(val * 100),
  }));

  // 理论引擎权重表数据
  const theoryData = Object.entries(data.theory_weights_adjustment).map(([key, val]) => ({
    engine: key,
    weight: val,
    adjusted: val > 1 ? "↑" : val < 1 ? "↓" : "—",
  }));

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: "auto" }}>
      {/* 标题栏 */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <Grid2X2 size={24} color="#58a6ff" />
        <Typography variant="h5" sx={{ fontWeight: 700, color: "#e6edf3" }}>
          经济象限检测
        </Typography>
        <Chip
          label="Dalio+TDA"
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
          {loading ? <CircularProgress size={20} color="inherit" /> : "检测"}
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 2, bgcolor: "rgba(210,153,34,0.1)" }}>
          API 连接失败，已使用模拟数据展示。错误：{error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* ── Dalio 2x2象限矩阵 ── */}
        <Grid item xs={12} md={5}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d", height: "100%" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                  Dalio 四象限矩阵
                </Typography>
                <Chip label="增长×通胀" size="small" sx={{ bgcolor: "rgba(139,148,158,0.12)", color: "#8b949e", fontSize: 10 }} />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />

              {/* SVG 象限图 */}
              <Box sx={{ width: "100%", position: "relative" }}>
                <svg viewBox="0 0 400 400" width="100%" style={{ maxHeight: 380 }}>
                  {/* 轴标签 */}
                  <text x="50" y="15" fill="#8b949e" fontSize="11" textAnchor="start">增长↑</text>
                  <text x="50" y="385" fill="#8b949e" fontSize="11" textAnchor="start">增长↓</text>
                  <text x="385" y="195" fill="#8b949e" fontSize="11" textAnchor="end">通胀↑</text>
                  <text x="5" y="195" fill="#8b949e" fontSize="11" textAnchor="start">通胀↓</text>

                  {/* 象限背景 */}
                  {QUADRANTS.map((q) => (
                    <g key={q.id}>
                      <rect
                        x={q.x === 0 ? 50 : 200}
                        y={q.y === 0 ? 20 : 200}
                        width={150}
                        height={180}
                        fill={q.bgColor}
                        stroke={data.regime === q.id ? q.color : "#30363d"}
                        strokeWidth={data.regime === q.id ? 3 : 1}
                        rx={8}
                        style={{
                          transition: "stroke 0.3s, fill 0.3s",
                        }}
                      />
                      {/* 象限名称 */}
                      <text
                        x={q.x === 0 ? 125 : 275}
                        y={q.y === 0 ? 80 : 260}
                        fill={data.regime === q.id ? q.color : "#8b949e"}
                        fontSize="16"
                        fontWeight="bold"
                        textAnchor="middle"
                      >
                        {q.label}
                      </text>
                      {/* 象限子描述 */}
                      <text
                        x={q.x === 0 ? 125 : 275}
                        y={q.y === 0 ? 105 : 285}
                        fill="#8b949e"
                        fontSize="10"
                        textAnchor="middle"
                      >
                        {q.sub}
                      </text>
                      {/* 推荐资产 */}
                      <text
                        x={q.x === 0 ? 125 : 275}
                        y={q.y === 0 ? 145 : 325}
                        fill="#8b949e"
                        fontSize="9"
                        textAnchor="middle"
                      >
                        {q.assets}
                      </text>
                      {/* 当前象限高亮脉冲 */}
                      {data.regime === q.id && (
                        <>
                          <circle
                            cx={q.x === 0 ? 125 : 275}
                            cy={q.y === 0 ? 65 : 245}
                            r={8}
                            fill={q.color}
                            opacity={0.8}
                          >
                            <animate
                              attributeName="r"
                              values="8;14;8"
                              dur="2s"
                              repeatCount="indefinite"
                            />
                            <animate
                              attributeName="opacity"
                              values="0.8;0.3;0.8"
                              dur="2s"
                              repeatCount="indefinite"
                            />
                          </circle>
                          {/* 当前值标注 */}
                          <text
                            x={q.x === 0 ? 125 : 275}
                            y={q.y === 0 ? 170 : 350}
                            fill={q.color}
                            fontSize="9"
                            fontWeight="bold"
                            textAnchor="middle"
                          >
                            当前: 置信度 {data.confidence.toFixed(2)}
                          </text>
                        </>
                      )}
                    </g>
                  ))}

                  {/* 分隔线 */}
                  <line x1="50" y1="200" x2="350" y2="200" stroke="#30363d" strokeWidth="1" strokeDasharray="5,5" />
                  <line x1="200" y1="20" x2="200" y2="380" stroke="#30363d" strokeWidth="1" strokeDasharray="5,5" />

                  {/* 信号指示点（增长/通胀的当前位置） */}
                  <circle
                    cx={200 + (data.inflation_signal > 0 ? Math.min(data.inflation_signal * 10, 140) : Math.max(data.inflation_signal * 10, -140))}
                    cy={200 - (data.growth_signal > 0 ? Math.min(data.growth_signal * 10, 160) : Math.max(data.growth_signal * 10, -160))}
                    r={6}
                    fill={regimeColor}
                    stroke="#e6edf3"
                    strokeWidth={2}
                  />
                </svg>
              </Box>

              {/* 象限信息 */}
              <Box sx={{ mt: 2, textAlign: "center" }}>
                <Typography variant="body2" sx={{ color: regimeColor, fontWeight: 600 }}>
                  {data.description}
                </Typography>
                <Chip
                  label={getRegimeLabel(data.regime)}
                  sx={{ mt: 1, bgcolor: `${regimeColor}22`, color: regimeColor, fontWeight: 600 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ── TDA拓扑预警卡片 ── */}
        <Grid item xs={12} md={7}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                  TDA拓扑预警
                </Typography>
                <Chip
                  label={getTDAWarningLabel(data.tda_warning)}
                  size="small"
                  sx={{
                    bgcolor: `${tdaWarningColor}22`,
                    color: tdaWarningColor,
                    fontWeight: 600,
                  }}
                />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Grid container spacing={2}>
                {/* β₀ 连通分量 */}
                <Grid item xs={4}>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      β₀ 连通分量数
                    </Typography>
                    <Typography variant="h4" sx={{ color: data.betti_0 > 2 ? "#d29922" : "#58a6ff", fontWeight: 800 }}>
                      {data.betti_0}
                    </Typography>
                    {data.betti_0 > 2 && (
                      <Typography variant="caption" sx={{ color: "#d29922", mt: 0.5 }}>
                        市场碎片化 ↑
                      </Typography>
                    )}
                    {data.betti_0 === 1 && (
                      <Typography variant="caption" sx={{ color: "#3fb950", mt: 0.5 }}>
                        市场整体连通 ✓
                      </Typography>
                    )}
                    {/* β₀ 小趋势图 */}
                    <Box sx={{ width: "100%", height: 40, mt: 1 }}>
                      <ResponsiveContainer>
                        <LineChart data={regimeHistory.slice(-20)}>
                          <Line type="monotone" dataKey="betti_0" stroke={data.betti_0 > 2 ? "#d29922" : "#58a6ff"} strokeWidth={1.5} dot={false} />
                          <YAxis domain={[0, "dataMax + 1"]} hide />
                          <XAxis dataKey="bar_index" hide />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </Box>
                </Grid>

                {/* β₁ 环形结构 */}
                <Grid item xs={4}>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      β₁ 环形结构数
                    </Typography>
                    <Typography variant="h4" sx={{ color: data.betti_1 >= 2 ? "#58a6ff" : "#8b949e", fontWeight: 800 }}>
                      {data.betti_1}
                    </Typography>
                    {data.betti_1 >= 2 && (
                      <Typography variant="caption" sx={{ color: "#58a6ff", mt: 0.5 }}>
                        环形过渡信号 ↑
                      </Typography>
                    )}
                    {data.betti_1 === 0 && (
                      <Typography variant="caption" sx={{ color: "#8b949e", mt: 0.5 }}>
                        无循环结构
                      </Typography>
                    )}
                    {/* β₁ 小趋势图 */}
                    <Box sx={{ width: "100%", height: 40, mt: 1 }}>
                      <ResponsiveContainer>
                        <LineChart data={regimeHistory.slice(-20)}>
                          <Line type="monotone" dataKey="betti_1" stroke={data.betti_1 >= 2 ? "#58a6ff" : "#8b949e"} strokeWidth={1.5} dot={false} />
                          <YAxis domain={[0, "dataMax + 1"]} hide />
                          <XAxis dataKey="bar_index" hide />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </Box>
                </Grid>

                {/* Persistence Score 表盘 */}
                <Grid item xs={4}>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      拓扑持久度
                    </Typography>
                    <Box sx={{ position: "relative", display: "inline-flex" }}>
                      <CircularProgress
                        variant="determinate"
                        value={data.persistence_score * 100}
                        size={80}
                        thickness={6}
                        sx={{ color: persistenceColor }}
                      />
                      <Box
                        sx={{
                          position: "absolute",
                          top: 0,
                          left: 0,
                          bottom: 0,
                          right: 0,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <Typography variant="h6" sx={{ color: persistenceColor, fontWeight: 800 }}>
                          {data.persistence_score.toFixed(2)}
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="caption" sx={{ color: persistenceColor, mt: 0.5 }}>
                      {data.persistence_score >= 0.5 ? "结构稳健 ✓" : "结构脆弱 ⚠️"}
                    </Typography>
                    {/* persistence 小趋势图 */}
                    <Box sx={{ width: "100%", height: 40, mt: 1 }}>
                      <ResponsiveContainer>
                        <LineChart data={regimeHistory.slice(-20)}>
                          <Line type="monotone" dataKey="persistence_score" stroke={persistenceColor} strokeWidth={1.5} dot={false} />
                          <YAxis domain={[0, 1]} hide />
                          <XAxis dataKey="bar_index" hide />
                          <ReferenceLine y={0.3} stroke="#d29922" strokeDasharray="2 2" strokeOpacity={0.5} />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </Box>
                </Grid>
              </Grid>

              {/* TDA预警置信度 */}
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" sx={{ color: "#8b949e" }}>TDA预警置信度</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={data.tda_confidence * 100}
                      sx={{ mt: 1, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: tdaWarningColor } }}
                    />
                    <Typography variant="caption" sx={{ color: tdaWarningColor, mt: 0.5 }}>
                      {data.tda_confidence.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" sx={{ color: "#8b949e" }}>Dalio象限置信度（TDA调整后）</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={data.confidence * 100}
                      sx={{ mt: 1, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: regimeColor } }}
                    />
                    <Typography variant="caption" sx={{ color: regimeColor, mt: 0.5 }}>
                      {data.confidence.toFixed(2)}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>

              {/* TDA预警规则说明 */}
              <Box sx={{ mt: 2, p: 1.5, bgcolor: "rgba(139,148,158,0.05)", borderRadius: 1 }}>
                <Typography variant="caption" sx={{ color: "#8b949e", lineHeight: 1.6 }}>
                  TDA预警规则：β₀>2 → 碎片化（市场分裂为多个独立价格簇）| β₁≥2 → 环形过渡（新循环结构出现）| persistence&lt;0.3 → 临界相变（拓扑结构脆弱）
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ── 增长/通胀信号仪表盘 ── */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700, mb: 1 }}>
                增长 / 通胀 信号仪表盘
              </Typography>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Grid container spacing={3}>
                {/* 增长信号 */}
                <Grid item xs={6}>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      增长信号 (Growth)
                    </Typography>
                    <Box sx={{ position: "relative", display: "inline-flex" }}>
                      <CircularProgress
                        variant="determinate"
                        value={Math.min(Math.abs(data.growth_signal) * 10, 100)}
                        size={120}
                        thickness={8}
                        sx={{ color: data.growth_signal > 0 ? "#3fb950" : "#f85149" }}
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
                        <Typography variant="h4" sx={{ color: data.growth_signal > 0 ? "#3fb950" : "#f85149", fontWeight: 800 }}>
                          {data.growth_signal.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "#8b949e" }}>
                          {data.growth_signal > 0 ? "增长↑" : "增长↓"}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* 通胀信号 */}
                <Grid item xs={6}>
                  <Box sx={{ textAlign: "center" }}>
                    <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                      通胀信号 (Inflation)
                    </Typography>
                    <Box sx={{ position: "relative", display: "inline-flex" }}>
                      <CircularProgress
                        variant="determinate"
                        value={Math.min(Math.abs(data.inflation_signal) * 10, 100)}
                        size={120}
                        thickness={8}
                        sx={{ color: data.inflation_signal > 0 ? "#d29922" : "#bc8cff" }}
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
                        <Typography variant="h4" sx={{ color: data.inflation_signal > 0 ? "#d29922" : "#bc8cff", fontWeight: 800 }}>
                          {data.inflation_signal.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "#8b949e" }}>
                          {data.inflation_signal > 0 ? "通胀↑" : "通胀↓"}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* ── 推荐资产权重雷达图 ── */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                  推荐资产权重
                </Typography>
                <Chip label={getRegimeLabel(data.regime)} size="small" sx={{ bgcolor: `${regimeColor}22`, color: regimeColor }} />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Box sx={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="80%">
                    <PolarGrid stroke="#30363d" />
                    <PolarAngleAxis dataKey="asset" tick={{ fill: "#8b949e", fontSize: 12 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 60]} tick={{ fill: "#8b949e", fontSize: 10 }} />
                    <Radar
                      name="权重%"
                      dataKey="weight"
                      stroke={regimeColor}
                      fill={regimeColor}
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </Box>
              {/* 资产权重明细 */}
              <Box sx={{ mt: 1 }}>
                <Grid container spacing={1}>
                  {Object.entries(data.asset_weights).map(([key, val]) => (
                    <Grid item xs={2.4} key={key} sx={{ textAlign: "center" }}>
                      <Typography variant="caption" sx={{ color: "#8b949e" }}>
                        {getAssetName(key)}
                      </Typography>
                      <Typography variant="body2" sx={{ color: regimeColor, fontWeight: 700 }}>
                        {Math.round(val * 100)}%
                      </Typography>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ── 理论引擎权重调整表 ── */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                  理论引擎权重调整
                </Typography>
                <Chip label={getRegimeLabel(data.regime)} size="small" sx={{ bgcolor: `${regimeColor}22`, color: regimeColor }} />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <TableContainer component={Paper} sx={{ bgcolor: "transparent" }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ "& th": { color: "#8b949e", borderColor: "#30363d" } }}>
                      <TableCell>理论引擎</TableCell>
                      <TableCell>权重系数</TableCell>
                      <TableCell>调整方向</TableCell>
                      <TableCell>可视化</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {theoryData.map((row) => (
                      <TableRow key={row.engine} sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                        <TableCell>
                          <Chip label={row.engine} size="small" sx={{ bgcolor: "rgba(88,166,255,0.08)", color: "#58a6ff", fontSize: 10 }} />
                        </TableCell>
                        <TableCell>
                          <Typography sx={{ color: row.weight > 1 ? "#3fb950" : row.weight < 1 ? "#f85149" : "#e6edf3", fontWeight: 700 }}>
                            {row.weight.toFixed(1)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography sx={{ color: row.weight > 1 ? "#3fb950" : row.weight < 1 ? "#f85149" : "#8b949e" }}>
                            {row.adjusted}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <LinearProgress
                            variant="determinate"
                            value={row.weight * 50}
                            sx={{ width: 100, bgcolor: "#21262d", "& .MuiLinearProgress-bar": { bgcolor: row.weight > 1 ? "#3fb950" : row.weight < 1 ? "#f85149" : "#8b949e" } }}
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

        {/* ── 象限历史模拟走势图 ── */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <Grid2X2 size={18} color="#58a6ff" />
                <Typography variant="h6" sx={{ color: "#e6edf3" }}>
                  象限指标走势
                </Typography>
                <Chip label="模拟数据" size="small" sx={{ bgcolor: "rgba(210,153,34,0.15)", color: "#d29922", fontSize: 10 }} />
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Box sx={{ width: "100%", height: 280 }}>
                <ResponsiveContainer>
                  <ComposedChart data={regimeHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                    <XAxis dataKey="bar_index" stroke="#8b949e" fontSize={11} />
                    <YAxis stroke="#8b949e" fontSize={11} domain={[-10, 10]} />
                    <Tooltip content={<RegimeTooltip />} />
                    {/* 增长信号零线 */}
                    <ReferenceLine y={0} stroke="#30363d" />
                    <ReferenceArea y1={0} y2={10} fill="#3fb950" fillOpacity={0.03} />
                    <ReferenceArea y1={-10} y2={0} fill="#f85149" fillOpacity={0.03} />
                    {/* 增长信号面积图 */}
                    <Area
                      type="monotone"
                      dataKey="growth_signal"
                      stroke="#58a6ff"
                      fill="rgba(88,166,255,0.08)"
                      strokeWidth={2}
                      name="增长信号"
                    />
                    {/* 通胀信号折线 */}
                    <Line type="monotone" dataKey="inflation_signal" stroke="#d29922" strokeWidth={1.5} dot={false} name="通胀信号" />
                    <Legend wrapperStyle={{ fontSize: 11, color: "#8b949e" }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ── 交易建议卡片 ── */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: "#161b22", border: "1px solid #30363d" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ color: "#e6edf3", fontWeight: 700 }}>
                  交易建议
                </Typography>
                <Chip label={getRegimeLabel(data.regime)} sx={{ bgcolor: `${regimeColor}22`, color: regimeColor }} />
                {data.tda_warning !== "normal" && (
                  <Chip label={getTDAWarningLabel(data.tda_warning)} sx={{ bgcolor: `${tdaWarningColor}22`, color: tdaWarningColor }} />
                )}
              </Box>
              <Divider sx={{ mb: 2, borderColor: "#30363d" }} />
              <Grid container spacing={3}>
                {/* Dalio象限建议 */}
                <Grid item xs={6}>
                  <Typography variant="body1" sx={{ color: regimeColor, fontWeight: 600, mb: 2 }}>
                    {data.description}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "#8b949e", mb: 1 }}>
                    推荐配置:
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                    {Object.entries(data.asset_weights).map(([key, val]) => (
                      <Chip
                        key={key}
                        label={`${getAssetName(key)} ${Math.round(val * 100)}%`}
                        size="small"
                        sx={{ bgcolor: "rgba(88,166,255,0.08)", color: "#e6edf3", fontSize: 11 }}
                      />
                    ))}
                  </Box>
                </Grid>

                {/* TDA预警建议 */}
                <Grid item xs={6}>
                  <Typography variant="body1" sx={{ color: tdaWarningColor, fontWeight: 600, mb: 2 }}>
                    {data.tda_warning === "normal"
                      ? "拓扑结构正常，Dalio象限判断可信"
                      : data.tda_warning === "fragmenting"
                        ? "市场碎片化预警！价格分散为多个独立簇，建议分散持仓+降低仓位"
                        : data.tda_warning === "loop_transition"
                          ? "环形过渡信号！新循环结构出现，象限可能切换，建议动态调整配置"
                          : "临界相变预警！拓扑结构脆弱，象限即将切换，建议防御配置+硬止损"
                    }
                  </Typography>
                  <TableContainer component={Paper} sx={{ bgcolor: "transparent" }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ "& th": { color: "#8b949e", borderColor: "#30363d" } }}>
                          <TableCell>预警指标</TableCell>
                          <TableCell>数值</TableCell>
                          <TableCell>状态</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                          <TableCell>β₀(连通分量)</TableCell>
                          <TableCell>{data.betti_0}</TableCell>
                          <TableCell>
                            <Chip label={data.betti_0 > 2 ? "碎片化" : "正常"} size="small" sx={{ bgcolor: data.betti_0 > 2 ? "rgba(210,153,34,0.15)" : "rgba(63,185,80,0.15)", color: data.betti_0 > 2 ? "#d29922" : "#3fb950" }} />
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                          <TableCell>β₁(环形结构)</TableCell>
                          <TableCell>{data.betti_1}</TableCell>
                          <TableCell>
                            <Chip label={data.betti_1 >= 2 ? "过渡信号" : "正常"} size="small" sx={{ bgcolor: data.betti_1 >= 2 ? "rgba(88,166,255,0.15)" : "rgba(63,185,80,0.15)", color: data.betti_1 >= 2 ? "#58a6ff" : "#3fb950" }} />
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                          <TableCell>持久度评分</TableCell>
                          <TableCell>{data.persistence_score.toFixed(3)}</TableCell>
                          <TableCell>
                            <Chip label={data.persistence_score < 0.3 ? "脆弱" : data.persistence_score < 0.5 ? "中等" : "稳健"} size="small" sx={{ bgcolor: `${persistenceColor}15`, color: persistenceColor }} />
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ "& td": { color: "#e6edf3", borderColor: "#30363d" } }}>
                          <TableCell>TDA置信度</TableCell>
                          <TableCell>{data.tda_confidence.toFixed(2)}</TableCell>
                          <TableCell>
                            <Chip label={data.tda_confidence > 0.6 ? "高" : data.tda_confidence > 0.3 ? "中" : "低"} size="small" sx={{ bgcolor: "rgba(88,166,255,0.08)", color: "#58a6ff" }} />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RegimePage;
