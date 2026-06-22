/**
 * DNADetectionPage - 鲁兆DNA倍发生成验证页面 (TOMAS v2.0)
 *
 * 展示：
 * - DNA基因卡片（第一浪幅度/时间）
 * - κ-Snap溯因验证结果
 * - 波浪倍数检测结果表
 * - 斐波那契/鲁加斯数验证
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
}

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
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
      // 降级：模拟数据
      setData({
        genes: [
          { wave_label: "浪1", amplitude: 320.5, duration: 13, start_index: 10, end_index: 23 },
          { wave_label: "浪2", amplitude: 198.3, duration: 8, start_index: 23, end_index: 31 },
          { wave_label: "浪3", amplitude: 518.7, duration: 21, start_index: 31, end_index: 52 },
          { wave_label: "浪4", amplitude: 240.1, duration: 13, start_index: 52, end_index: 65 },
          { wave_label: "浪5", amplitude: 345.2, duration: 21, start_index: 65, end_index: 86 },
        ],
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
      });
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchDetection();
  }, [fetchDetection]);

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: "auto" }}>
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
