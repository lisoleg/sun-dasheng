/**
 * KnowledgeGraph - D3力导向图组件
 *
 * 基于D3.js v7，提供：
 * - 力导向图布局（节点拖拽、缩放）
 * - 节点按类型着色（理论/概念/指标/信号）
 * - 边按关系类型设置线型（实线/虚线/点线）
 * - 鼠标悬停高亮关联节点和边
 * - 点击节点显示详情
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import type {
  KnowledgeNode,
  KnowledgeEdge,
  KnowledgeNodeType,
  KnowledgeEdgeType,
} from "@/utils/mockData";

// ============================================================
// 类型定义
// ============================================================

/** 节点颜色映射 */
const NODE_COLOR_MAP: Record<KnowledgeNodeType, string> = {
  theory: "#2196F3",    // 蓝色
  concept: "#4CAF50",   // 绿色
  indicator: "#FF9800",  // 橙色
  signal: "#F44336",    // 红色
};

/** 边线型映射 */
const EDGE_STROKE_DASH_MAP: Record<KnowledgeEdgeType, string> = {
  derive: "",          // 实线
  contain: "5,5",    // 虚线
  oppose: "2,2",     // 点线
  apply: "10,5",     // 长虚线
};

/** 节点半径 */
const NODE_RADIUS = 20;

/** KnowledgeGraph组件属性 */
export interface KnowledgeGraphProps {
  /** 知识图谱节点 */
  nodes: KnowledgeNode[];
  /** 知识图谱边 */
  edges: KnowledgeEdge[];
  /** 图表宽度 */
  width?: number;
  /** 图表高度 */
  height?: number;
  /** 节点点击回调 */
  onNodeSelect?: (node: KnowledgeNode | null) => void;
}

// ============================================================
// 工具函数
// ============================================================

/**
 * 根据节点类型返回颜色
 */
function getNodeColor(type: KnowledgeNodeType): string {
  return NODE_COLOR_MAP[type] ?? "#999";
}

/**
 * 根据边类型返回线型
 */
function getEdgeStrokeDash(type: KnowledgeEdgeType): string {
  return EDGE_STROKE_DASH_MAP[type] ?? "";
}

// ============================================================
// 组件实现
// ============================================================

/**
 * KnowledgeGraph - D3力导向图组件
 *
 * 使用D3.js v7创建交互式知识图谱可视化
 */
const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  nodes,
  edges,
  width = 800,
  height = 600,
  onNodeSelect,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const simulationRef = useRef<d3.Simulation<d3.SimulationNodeDatum, undefined> | null>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);

  // 初始化图谱
  useEffect(() => {
    if (!containerRef.current) return;

    // 清空容器
    d3.select(containerRef.current).selectAll("svg").remove();

    // 创建SVG
    const svg = d3.select(containerRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .style("background", "#fafafa")
      .style("border", "1px solid #e0e0e0")
      .style("border-radius", "8px");

    svgRef.current = svg.node();

    // 创建缩放行为
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform.toString());
      });

    svg.call(zoom);

    // 创建主分组（用于缩放）
    const g = svg.append("g").attr("class", "main-group");

    // 创建箭头标记
    svg.append("defs")
      .selectAll("marker")
      .data(["arrowhead"])
      .enter()
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 20)
      .attr("refY", 5)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 Z")
      .attr("fill", "#999");

    // 创建力仿真
    const simulation = d3.forceSimulation<KnowledgeNode & d3.SimulationNodeDatum>(nodes as any)
      .force("link", d3.forceLink<KnowledgeEdge & d3.SimulationLinkDatum<KnowledgeNode & d3.SimulationNodeDatum, KnowledgeEdge & d3.SimulationLinkDatum<any, any>>, KnowledgeNode & d3.SimulationNodeDatum>(edges as any)
        .id((d: any) => d.id)
        .distance(100)
      )
      .force("charge", d3.forceManyBody<KnowledgeNode & d3.SimulationNodeDatum>()
        .strength(-300)
      )
      .force("center", d3.forceCenter<KnowledgeNode & d3.SimulationNodeDatum>(width / 2, height / 2))
      .force("collision", d3.forceCollide<KnowledgeNode & d3.SimulationNodeDatum>()
        .radius(NODE_RADIUS + 5)
      );

    simulationRef.current = simulation;

    // 创建边
    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(edges)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", (d) => getEdgeStrokeDash(d.type))
      .attr("marker-end", "url(#arrowhead)");

    // 创建节点分组
    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(d3.drag<SVGGElement, KnowledgeNode & d3.SimulationNodeDatum>()
        .on("start", dragStarted)
        .on("drag", dragging)
        .on("end", dragEnded)
      );

    // 节点圆圈
    node.append("circle")
      .attr("r", NODE_RADIUS)
      .attr("fill", (d) => getNodeColor(d.type))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")
      .on("mouseover", handleMouseOver)
      .on("mouseout", handleMouseOut)
      .on("click", handleNodeClick);

    // 节点标签
    node.append("text")
      .text((d) => d.label)
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("fill", "#fff")
      .attr("font-size", "11px")
      .attr("font-weight", "bold")
      .style("pointer-events", "none");

    // 拖拽事件处理
    function dragStarted(event: d3.D3DragEvent<SVGGElement, KnowledgeNode, unknown>, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragging(event: d3.D3DragEvent<SVGGElement, KnowledgeNode, unknown>, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event: d3.D3DragEvent<SVGGElement, KnowledgeNode, unknown>, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // 鼠标悬停高亮
    function handleMouseOver(event: MouseEvent, d: KnowledgeNode) {
      // 高亮关联节点和边
      const connectedNodeIds = new Set<string>();
      edges.forEach((edge) => {
        if (edge.source === d.id) connectedNodeIds.add(edge.target);
        if (edge.target === d.id) connectedNodeIds.add(edge.source);
      });

      node.select("circle")
        .style("opacity", (n: any) => 
          n.id === d.id || connectedNodeIds.has(n.id) ? 1 : 0.3
        );

      link
        .style("opacity", (e: any) => 
          e.source.id === d.id || e.target.id === d.id ? 1 : 0.1
        );
    }

    function handleMouseOut() {
      node.select("circle").style("opacity", 1);
      link.style("opacity", 1);
    }

    // 节点点击
    function handleNodeClick(event: MouseEvent, d: KnowledgeNode) {
      setSelectedNode(d);
      if (onNodeSelect) onNodeSelect(d);
    }

    // 仿真更新
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d: any) => `translate(${d.x}, ${d.y})`);
    });

    // 清理
    return () => {
      simulation.stop();
      d3.select(containerRef.current).selectAll("svg").remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, width, height]);

  // 节点点击回调
  const handleNodeClick = useCallback((node: KnowledgeNode | null) => {
    setSelectedNode(node);
    if (onNodeSelect) onNodeSelect(node);
  }, [onNodeSelect]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      {selectedNode && (
        <div
          className="absolute top-2 right-2 bg-white p-3 rounded shadow-lg border border-gray-200 max-w-xs"
          style={{ maxHeight: "calc(100% - 16px)", overflow: "auto" }}
        >
          <h4 className="font-bold text-sm mb-2">{selectedNode.label}</h4>
          <p className="text-xs text-gray-600 mb-1">类型: {selectedNode.type}</p>
          <p className="text-xs text-gray-600">{selectedNode.description}</p>
          <button
            className="mt-2 text-xs text-blue-500 hover:text-blue-700"
            onClick={() => handleNodeClick(null)}
          >
            关闭
          </button>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;
