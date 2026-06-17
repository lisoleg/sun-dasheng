"""EML知识蒸馏器 - 将理论文本蒸馏为EML知识图谱

核心功能：
1. distill(theory_texts): 将理论文本蒸馏为EML知识图谱
2. resolve_conflicts(new_knowledge, existing): 知识冲突处理
3. export_eml(graph): 导出为JSON格式供D3.js渲染

EMLGraph数据结构：
{
    nodes: [{id, label, type, properties}],
    edges: [{source, target, relation, weight}]
}
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


class ConflictStrategy(str, Enum):
    """知识冲突处理策略"""

    KEEP_OLD = "keep_old"  # 保留旧知
    ADOPT_NEW = "adopt_new"  # 采纳新知
    MERGE = "merge"  # 合并
    IGNORE = "ignore"  # 忽略冲突


@dataclass
class EMLGraph:
    """EML知识图谱数据结构

    Attributes:
        nodes: 概念节点列表
        edges: 关系边列表
    """

    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
        }

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取节点

        Args:
            node_id: 节点ID

        Returns:
            Optional[Dict]: 节点数据，不存在则返回None
        """
        for node in self.nodes:
            if node.get("id") == node_id:
                return node
        return None

    def get_edges_for_node(self, node_id: str) -> List[Dict[str, Any]]:
        """获取与指定节点关联的所有边

        Args:
            node_id: 节点ID

        Returns:
            List[Dict]: 关联的边列表
        """
        return [
            edge for edge in self.edges
            if edge.get("source") == node_id or edge.get("target") == node_id
        ]

    def add_node(self, node: Dict[str, Any]) -> None:
        """添加节点

        Args:
            node: 节点数据
        """
        if "id" not in node:
            node["id"] = str(uuid.uuid4())[:8]
        self.nodes.append(node)

    def add_edge(self, edge: Dict[str, Any]) -> None:
        """添加边

        Args:
            edge: 边数据
        """
        self.edges.append(edge)

    @property
    def node_count(self) -> int:
        """节点数量"""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """边数量"""
        return len(self.edges)


@dataclass
class ConflictResolution:
    """冲突解决结果"""

    strategy: ConflictStrategy = ConflictStrategy.IGNORE
    resolved_node: Optional[Dict[str, Any]] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "strategy": self.strategy.value,
            "resolved_node": self.resolved_node,
            "description": self.description,
        }


class EMLDistiller:
    """EML知识蒸馏器

    将鲁兆理论文本蒸馏为结构化的EML知识图谱，
    支持知识冲突处理和D3.js渲染格式导出。

    蒸馏流程：
    1. 文本预处理：清洗、分段
    2. 概念提取：识别理论中的关键概念节点（entity）
    3. 关系提取：识别概念间的关系边（relation）
    4. 冲突处理：与已有知识图谱合并时处理冲突
    5. 图谱构建：生成EMLGraph数据结构

    冲突处理四种策略：
    - KEEP_OLD: 保留旧知识，忽略新知识
    - ADOPT_NEW: 采纳新知识，替换旧知识
    - MERGE: 合并新旧知识（保留两者的属性）
    - IGNORE: 忽略冲突，两者共存
    """

    # 鲁兆理论常见概念关键词
    THEORY_ENTITY_PATTERNS: Dict[str, str] = {
        r"太极中心律": "taiji_center",
        r"太极中心": "taiji_center",
        r"DNA29": "dna29",
        r"DNA13": "dna13",
        r"螺旋律": "spiral",
        r"斐波那契": "fibonacci",
        r"波浪理论": "elliott_wave",
        r"五浪": "impulse_wave",
        r"三浪": "corrective_wave",
        r"A浪": "wave_a",
        r"B浪": "wave_b",
        r"C浪": "wave_c",
        r"回撤": "retracement",
        r"扩展": "extension",
        r"支撑位": "support",
        r"阻力位": "resistance",
        r"趋势": "trend",
        r"反转": "reversal",
        r"突破": "breakout",
        r"时间窗口": "time_window",
        r"周期": "cycle",
    }

    # 关系关键词
    RELATION_PATTERNS: Dict[str, str] = {
        r"导致": "causes",
        r"引发": "triggers",
        r"预测": "predicts",
        r"确认": "confirms",
        r"否定": "negates",
        r"相关": "correlates_with",
        r"属于": "belongs_to",
        r"包含": "contains",
        r"形成": "forms",
        r"突破": "breaks",
        r"回踩": "retests",
    }

    def distill(self, theory_texts: List[str]) -> EMLGraph:
        """将理论文本蒸馏为EML知识图谱

        解析文本提取概念节点(entity)和关系边(relation)，
        构建结构化的知识图谱。

        Args:
            theory_texts: 理论文本列表

        Returns:
            EMLGraph: 蒸馏生成的知识图谱
        """
        logger.info(f"EMLDistiller: distilling {len(theory_texts)} theory texts")

        graph = EMLGraph()
        all_entities: Dict[str, Dict[str, Any]] = {}
        all_edges: List[Dict[str, Any]] = []

        for text_idx, text in enumerate(theory_texts):
            # 步骤1：提取概念节点
            entities = self._extract_entities(text, text_idx)
            all_entities.update(entities)

            # 步骤2：提取关系边
            edges = self._extract_edges(text, entities, text_idx)
            all_edges.extend(edges)

        # 构建图谱
        graph.nodes = list(all_entities.values())
        graph.edges = self._deduplicate_edges(all_edges)

        logger.info(
            f"EMLDistiller: distilled {graph.node_count} nodes, "
            f"{graph.edge_count} edges from {len(theory_texts)} texts"
        )

        return graph

    def resolve_conflicts(
        self,
        new_knowledge: EMLGraph,
        existing: EMLGraph,
        strategy: ConflictStrategy = ConflictStrategy.MERGE,
    ) -> EMLGraph:
        """知识冲突处理

        将新蒸馏的知识图谱与已有图谱合并，处理概念冲突。

        Args:
            new_knowledge: 新蒸馏的知识图谱
            existing: 已有的知识图谱
            strategy: 冲突处理策略

        Returns:
            EMLGraph: 合并后的知识图谱
        """
        logger.info(
            f"EMLDistiller: resolving conflicts, "
            f"new={new_knowledge.node_count} nodes, "
            f"existing={existing.node_count} nodes, "
            f"strategy={strategy.value}"
        )

        merged = EMLGraph(
            nodes=list(existing.nodes),
            edges=list(existing.edges),
        )

        # 构建已有节点索引（按label去重）
        existing_labels: Dict[str, Dict[str, Any]] = {}
        for node in existing.nodes:
            label = node.get("label", "").lower()
            if label:
                existing_labels[label] = node

        # 处理新节点
        for new_node in new_knowledge.nodes:
            label = new_node.get("label", "").lower()
            existing_node = existing_labels.get(label)

            if existing_node is None:
                # 无冲突：直接添加
                merged.nodes.append(new_node)
                existing_labels[label] = new_node
            else:
                # 有冲突：按策略处理
                resolution = self._resolve_node_conflict(
                    new_node, existing_node, strategy
                )
                if resolution.resolved_node is not None:
                    # 移除旧节点，添加解决后的节点
                    if resolution.strategy != ConflictStrategy.KEEP_OLD:
                        merged.nodes = [
                            n for n in merged.nodes
                            if n.get("id") != existing_node.get("id")
                        ]
                        merged.nodes.append(resolution.resolved_node)
                        existing_labels[label] = resolution.resolved_node

                logger.debug(
                    f"Conflict resolved: label={label}, "
                    f"strategy={resolution.strategy.value}, "
                    f"desc={resolution.description[:100]}"
                )

        # 添加新边（去重）
        existing_edge_keys = set()
        for edge in merged.edges:
            key = f"{edge.get('source')}->{edge.get('relation')}->{edge.get('target')}"
            existing_edge_keys.add(key)

        for new_edge in new_knowledge.edges:
            key = f"{new_edge.get('source')}->{new_edge.get('relation')}->{new_edge.get('target')}"
            if key not in existing_edge_keys:
                merged.edges.append(new_edge)
                existing_edge_keys.add(key)

        logger.info(
            f"EMLDistiller: merged graph has {merged.node_count} nodes, "
            f"{merged.edge_count} edges"
        )

        return merged

    def export_eml(self, graph: EMLGraph) -> Dict[str, Any]:
        """导出为JSON格式供D3.js渲染

        Args:
            graph: EML知识图谱

        Returns:
            Dict: D3.js力导向图兼容的JSON数据
        """
        export_data = {
            "nodes": [
                {
                    "id": node.get("id", ""),
                    "label": node.get("label", ""),
                    "type": node.get("type", "concept"),
                    "properties": node.get("properties", {}),
                    # D3.js力导向图额外字段
                    "group": self._get_node_group(node.get("type", "concept")),
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.get("source", ""),
                    "target": edge.get("target", ""),
                    "relation": edge.get("relation", ""),
                    "weight": edge.get("weight", 1.0),
                    # D3.js兼容字段
                    "value": edge.get("weight", 1.0),
                }
                for edge in graph.edges
            ],
            "metadata": {
                "node_count": graph.node_count,
                "edge_count": graph.edge_count,
                "export_time": self._current_timestamp(),
            },
        }

        logger.info(
            f"EMLDistiller: exported graph with {graph.node_count} nodes, "
            f"{graph.edge_count} edges for D3.js rendering"
        )

        return export_data

    def _extract_entities(self, text: str, text_idx: int = 0) -> Dict[str, Dict[str, Any]]:
        """从文本中提取概念节点

        Args:
            text: 输入文本
            text_idx: 文本索引

        Returns:
            Dict[str, Dict]: 概念ID -> 概念节点数据
        """
        entities: Dict[str, Dict[str, Any]] = {}

        for pattern, entity_type in self.THEORY_ENTITY_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                label = match.group()
                entity_id = f"{entity_type}_{text_idx}_{match.start()}"

                if label not in {e.get("label") for e in entities.values()}:
                    entities[entity_id] = {
                        "id": entity_id,
                        "label": label,
                        "type": self._classify_entity_type(entity_type),
                        "properties": {
                            "entity_key": entity_type,
                            "source_text_idx": text_idx,
                            "position": match.start(),
                        },
                    }

        # 提取数字相关概念（时间窗口、价格水平等）
        number_patterns = re.finditer(r"(\d+)\s*(天|周|月|日|点|%)", text)
        for match in number_patterns:
            value = match.group(1)
            unit = match.group(2)
            label = f"{value}{unit}"
            entity_id = f"numeric_{text_idx}_{match.start()}"

            if label not in {e.get("label") for e in entities.values()}:
                entities[entity_id] = {
                    "id": entity_id,
                    "label": label,
                    "type": "numeric",
                    "properties": {
                        "value": int(value),
                        "unit": unit,
                        "source_text_idx": text_idx,
                    },
                }

        return entities

    def _extract_edges(
        self, text: str, entities: Dict[str, Dict[str, Any]], text_idx: int = 0
    ) -> List[Dict[str, Any]]:
        """从文本中提取关系边

        Args:
            text: 输入文本
            entities: 已提取的概念节点
            text_idx: 文本索引

        Returns:
            List[Dict]: 关系边列表
        """
        edges: List[Dict[str, Any]] = []
        entity_list = list(entities.values())

        if len(entity_list) < 2:
            return edges

        # 基于文本距离和关系关键词推断边
        for pattern, relation_type in self.RELATION_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                match_pos = match.start()

                # 寻找匹配位置前后的实体
                before_entity = self._find_nearest_entity(
                    entity_list, match_pos, before=True
                )
                after_entity = self._find_nearest_entity(
                    entity_list, match_pos, before=False
                )

                if before_entity and after_entity:
                    edges.append({
                        "source": before_entity["id"],
                        "target": after_entity["id"],
                        "relation": relation_type,
                        "weight": self._calculate_edge_weight(
                            before_entity, after_entity, match_pos, len(text)
                        ),
                    })

        # 相邻实体默认关联
        for i in range(len(entity_list) - 1):
            source = entity_list[i]
            target = entity_list[i + 1]
            edge_key = f"{source['id']}->relates_to->{target['id']}"
            existing_keys = {f"{e.get('source')}->{e.get('relation')}->{e.get('target')}" for e in edges}
            if edge_key not in existing_keys:
                edges.append({
                    "source": source["id"],
                    "target": target["id"],
                    "relation": "relates_to",
                    "weight": 0.5,
                })

        return edges

    def _resolve_node_conflict(
        self,
        new_node: Dict[str, Any],
        existing_node: Dict[str, Any],
        strategy: ConflictStrategy,
    ) -> ConflictResolution:
        """解决单个节点的冲突

        Args:
            new_node: 新节点数据
            existing_node: 已有节点数据
            strategy: 冲突处理策略

        Returns:
            ConflictResolution: 冲突解决结果
        """
        if strategy == ConflictStrategy.KEEP_OLD:
            return ConflictResolution(
                strategy=strategy,
                resolved_node=existing_node,
                description=f"Kept existing node: {existing_node.get('label')}",
            )

        elif strategy == ConflictStrategy.ADOPT_NEW:
            return ConflictResolution(
                strategy=strategy,
                resolved_node=new_node,
                description=f"Adopted new node: {new_node.get('label')}",
            )

        elif strategy == ConflictStrategy.MERGE:
            merged_node = {**existing_node}
            new_props = new_node.get("properties", {})
            existing_props = merged_node.get("properties", {})
            # 合并属性：新属性覆盖旧属性，旧属性保留
            merged_props = {**existing_props, **new_props}
            merged_node["properties"] = merged_props
            return ConflictResolution(
                strategy=strategy,
                resolved_node=merged_node,
                description=f"Merged node: {merged_node.get('label')}, "
                f"properties={len(merged_props)}",
            )

        else:  # IGNORE
            return ConflictResolution(
                strategy=strategy,
                resolved_node=None,
                description=f"Ignored conflict for: {new_node.get('label')}",
            )

    def _find_nearest_entity(
        self,
        entities: List[Dict[str, Any]],
        position: int,
        before: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """找到距离指定位置最近的实体

        Args:
            entities: 实体列表
            position: 文本位置
            before: True找之前的实体，False找之后的

        Returns:
            Optional[Dict]: 最近的实体，未找到返回None
        """
        best_entity: Optional[Dict[str, Any]] = None
        best_distance = float("inf")

        for entity in entities:
            entity_pos = entity.get("properties", {}).get("position", 0)
            if before:
                if entity_pos < position:
                    distance = position - entity_pos
                    if distance < best_distance:
                        best_distance = distance
                        best_entity = entity
            else:
                if entity_pos > position:
                    distance = entity_pos - position
                    if distance < best_distance:
                        best_distance = distance
                        best_entity = entity

        return best_entity

    def _calculate_edge_weight(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        match_pos: int,
        text_length: int,
    ) -> float:
        """计算关系边的权重

        基于实体间距离和关系强度计算权重。

        Args:
            source: 源节点
            target: 目标节点
            match_pos: 关系关键词位置
            text_length: 文本总长度

        Returns:
            float: 边权重 (0.1-1.0)
        """
        source_pos = source.get("properties", {}).get("position", 0)
        target_pos = target.get("properties", {}).get("position", 0)

        distance = abs(target_pos - source_pos)
        if text_length > 0:
            normalized_distance = distance / text_length
        else:
            normalized_distance = 1.0

        # 距离越近，权重越高
        weight = max(0.1, min(1.0, 1.0 - normalized_distance * 0.8))
        return round(weight, 2)

    @staticmethod
    def _classify_entity_type(entity_key: str) -> str:
        """根据实体键分类实体类型

        Args:
            entity_key: 实体键

        Returns:
            str: 实体类型
        """
        theory_types = {"taiji_center", "dna29", "dna13"}
        pattern_types = {"spiral", "fibonacci", "elliott_wave", "impulse_wave", "corrective_wave"}
        level_types = {"support", "resistance", "retracement", "extension"}

        if entity_key in theory_types:
            return "theory"
        elif entity_key in pattern_types:
            return "pattern"
        elif entity_key in level_types:
            return "level"
        else:
            return "concept"

    @staticmethod
    def _get_node_group(node_type: str) -> int:
        """根据节点类型分配D3.js分组编号（用于着色）

        Args:
            node_type: 节点类型

        Returns:
            int: 分组编号
        """
        group_map = {
            "theory": 1,
            "pattern": 2,
            "level": 3,
            "concept": 4,
            "numeric": 5,
        }
        return group_map.get(node_type, 0)

    @staticmethod
    def _deduplicate_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重边

        Args:
            edges: 原始边列表

        Returns:
            List[Dict]: 去重后的边列表
        """
        seen: set = set()
        unique_edges: List[Dict[str, Any]] = []
        for edge in edges:
            key = f"{edge.get('source')}->{edge.get('relation')}->{edge.get('target')}"
            if key not in seen:
                seen.add(key)
                unique_edges.append(edge)
        return unique_edges

    @staticmethod
    def _current_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
