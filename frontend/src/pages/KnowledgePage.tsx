/**
 * KnowledgePage - 知识图谱页面
 *
 * 包含：
 * - 顶部操作栏（蒸馏按钮、搜索框）
 * - 主体：D3力导向图（占70%宽度）
 * - 右侧详情面板（30%）：选中节点的属性和关联关系
 */

import React, { useState, useMemo } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import PsychologyIcon from "@mui/icons-material/Psychology";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import {
  MOCK_KNOWLEDGE_NODES,
  MOCK_KNOWLEDGE_EDGES,
  type KnowledgeNode,
  type KnowledgeEdge,
} from "@/utils/mockData";

// ============================================================
// 主组件
// ============================================================

/**
 * KnowledgePage - 知识图谱页面
 */
const KnowledgePage: React.FC = () => {
  const [search, setSearch] = useState("");
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);
  const [distilling, setDistilling] = useState(false);

  // 搜索过滤
  const filteredNodes = useMemo(() => {
    if (!search.trim()) return MOCK_KNOWLEDGE_NODES;
    return MOCK_KNOWLEDGE_NODES.filter((n) =>
      n.label.toLowerCase().includes(search.toLowerCase()) ||
      n.description.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  // 获取选中节点的关联边
  const relatedEdges = useMemo(() => {
    if (!selectedNode) return [];
    return MOCK_KNOWLEDGE_EDGES.filter(
      (e) => e.source === selectedNode.id || e.target === selectedNode.id
    );
  }, [selectedNode]);

  // 获取关联节点
  const relatedNodes = useMemo(() => {
    if (!selectedNode) return [];
    const relatedIds = new Set<string>();
    relatedEdges.forEach((e) => {
      if (e.source === selectedNode.id) relatedIds.add(e.target);
      else relatedIds.add(e.source);
    });
    return MOCK_KNOWLEDGE_NODES.filter((n) => relatedIds.has(n.id));
  }, [selectedNode, relatedEdges]);

  // 蒸馏按钮点击
  const handleDistill = () => {
    setDistilling(true);
    // 模拟蒸馏过程
    setTimeout(() => {
      setDistilling(false);
      alert("EML知识蒸馏完成！共处理 128 条理论文本，生成 45 个概念节点，78 条关系边。");
    }, 2000);
  };

  return (
    <Box sx={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column", p: 2, gap: 2 }}>
      {/* 顶部操作栏 */}
      <Paper sx={{ p: 2, display: "flex", alignItems: "center", gap: 2, borderRadius: 0 }}>
        <Button
          variant="contained"
          startIcon={<PsychologyIcon />}
          onClick={handleDistill}
          disabled={distilling}
        >
          {distilling ? "蒸馏中..." : "EML蒸馏"}
        </Button>
        <TextField
          fullWidth
          size="small"
          placeholder="搜索知识节点 (如 太极、螺旋、波浪)"
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
      </Paper>

      {/* 主体区域：图谱 + 详情面板 */}
      <Box sx={{ flex: 1, display: "flex", gap: 2, minHeight: 0 }}>
        {/* 知识图谱 */}
        <Paper sx={{ flex: 1, overflow: "hidden", borderRadius: 1 }}>
          <KnowledgeGraph
            nodes={filteredNodes}
            edges={MOCK_KNOWLEDGE_EDGES}
            width={800}
            height={600}
            onNodeSelect={setSelectedNode}
          />
        </Paper>

        {/* 右侧详情面板 */}
        <Paper
          sx={{
            width: 320,
            overflow: "auto",
            p: 2,
            borderRadius: 1,
            display: selectedNode ? "block" : "flex",
            alignItems: selectedNode ? undefined : "center",
            justifyContent: selectedNode ? undefined : "center",
          }}
        >
          {selectedNode ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                节点详情
              </Typography>
              <Chip
                label={selectedNode.type}
                color={
                  selectedNode.type === "theory" ? "primary"
                  : selectedNode.type === "concept" ? "success"
                  : selectedNode.type === "indicator" ? "warning"
                  : "error"
                }
                sx={{ mb: 2 }}
              />
              <Typography variant="subtitle1" fontWeight="bold">
                {selectedNode.label}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
                {selectedNode.description}
              </Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                关联关系 ({relatedEdges.length})
              </Typography>
              <List dense>
                {relatedEdges.map((edge, idx) => {
                  const isSource = edge.source === selectedNode.id;
                  const otherNode = isSource
                    ? MOCK_KNOWLEDGE_NODES.find((n) => n.id === edge.target)
                    : MOCK_KNOWLEDGE_NODES.find((n) => n.id === edge.source);
                  return (
                    <ListItem key={idx} sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <span>
                            <Chip label={edge.type} size="small" sx={{ mr: 1 }} />
                            {otherNode?.label ?? edge.target}
                          </span>
                        }
                        secondary={edge.label}
                      />
                    </ListItem>
                  );
                })}
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                关联节点 ({relatedNodes.length})
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                {relatedNodes.map((node) => (
                  <Chip
                    key={node.id}
                    label={node.label}
                    size="small"
                    onClick={() => setSelectedNode(node)}
                    sx={{ cursor: "pointer" }}
                  />
                ))}
              </Box>
            </Box>
          ) : (
            <Typography color="text.secondary">
              点击图谱中的节点查看详情
            </Typography>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default KnowledgePage;
