import React, { useRef, useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import * as d3 from 'd3';

interface Node {
  id: string;
  label: string;
  type: 'theory' | 'concept' | 'dna';
  x?: number;
  y?: number;
}

interface Link {
  source: string;
  target: string;
  relation: string;
}

const mockNodes: Node[] = [
  { id: '1', label: '太极中心律', type: 'theory' },
  { id: '2', label: 'DNA29', type: 'dna' },
  { id: '3', label: 'DNA13', type: 'dna' },
  { id: '4', label: '螺旋律', type: 'theory' },
  { id: '5', label: '斐波那契', type: 'concept' },
  { id: '6', label: '波浪理论', type: 'theory' },
  { id: '7', label: '艾略特波浪', type: 'concept' },
];

const mockLinks: Link[] = [
  { source: '1', target: '2', relation: '派生' },
  { source: '1', target: '3', relation: '派生' },
  { source: '4', target: '5', relation: '相关' },
  { source: '6', target: '7', relation: '等价' },
];

export default function KnowledgeGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>('all');

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 800;
    const height = 600;

    // 清空 SVG
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // 创建力导向模拟
    const simulation = d3
      .forceSimulation(mockNodes as any)
      .force(
        'link',
        d3
          .forceLink(mockLinks)
          .id((d: any) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // 绘制连线
    const link = svg
      .append('g')
      .selectAll('line')
      .data(mockLinks)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2);

    // 绘制节点
    const node = svg
      .append('g')
      .selectAll('circle')
      .data(mockNodes)
      .enter()
      .append('circle')
      .attr('r', 20)
      .attr('fill', (d: any) => {
        switch (d.type) {
          case 'theory':
            return '#58a6ff';
          case 'concept':
            return '#3fb950';
          case 'dna':
            return '#f59e0b';
          default:
            return '#8b949e';
        }
      })
      .call(d3.drag<SVGCircleElement, Node>().on('start', dragstarted).on('drag', dragged).on('end', dragended) as any);

    // 节点标签
    const label = svg
      .append('g')
      .selectAll('text')
      .data(mockNodes)
      .enter()
      .append('text')
      .text((d: any) => d.label)
      .attr('font-size', 12)
      .attr('fill', '#c9d1d9')
      .attr('text-anchor', 'middle')
      .attr('dy', 30);

    // 力导向更新
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);

      label.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);
    });

    // 拖拽函数
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }, [nodeTypeFilter]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        鲁兆理论知识图谱
      </Typography>
      <Box sx={{ mb: 2 }}>
        <FormControl size="small">
          <InputLabel>筛选节点类型</InputLabel>
          <Select
            value={nodeTypeFilter}
            onChange={(e) => setNodeTypeFilter(e.target.value)}
            label="筛选节点类型"
          >
            <MenuItem value="all">全部</MenuItem>
            <MenuItem value="theory">理论</MenuItem>
            <MenuItem value="concept">概念</MenuItem>
            <MenuItem value="dna">DNA</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Paper sx={{ p: 2, bgcolor: 'background.paper', height: 600 }}>
        <svg ref={svgRef} width="100%" height="100%" />
      </Paper>
    </Box>
  );
}
