"""翻译官 - EML知识检索引擎

在EML知识图谱中进行精确检索，快速返回匹配的知识节点和关系。
响应时间目标：<100ms（纯内存检索）
超时设置：2秒
"""

import asyncio
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from app.services.tomas.eml_distiller import EMLDistiller, EMLGraph


@dataclass
class EMLResult:
    """EML知识检索结果"""

    answer: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    matched_nodes: List[Dict[str, Any]] = field(default_factory=list)
    matched_edges: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "matched_nodes": self.matched_nodes,
            "matched_edges": self.matched_edges,
            "metadata": self.metadata,
            "latency_ms": self.latency_ms,
        }


class EMLStore:
    """EML知识图谱存储与索引

    内存中维护EML知识图谱，构建倒排索引支持快速检索。
    """

    def __init__(self) -> None:
        self.graph: EMLGraph = EMLGraph(nodes=[], edges=[])
        self._node_index: Dict[str, Dict[str, Any]] = {}  # id -> node
        self._keyword_index: Dict[str, Set[str]] = {}  # keyword -> set of node_ids
        self._label_index: Dict[str, Set[str]] = {}  # label -> set of node_ids

    def load_graph(self, graph: EMLGraph) -> None:
        """加载EML知识图谱并构建索引

        Args:
            graph: EML知识图谱
        """
        self.graph = graph
        self._node_index = {}
        self._keyword_index = {}
        self._label_index = {}

        for node in graph.nodes:
            self._node_index[node["id"]] = node

            # 标签索引
            label = node.get("label", "").lower()
            if label:
                if label not in self._label_index:
                    self._label_index[label] = set()
                self._label_index[label].add(node["id"])

            # 关键词索引：对标签和属性进行分词
            tokens = self._tokenize(label)
            for token in tokens:
                if token not in self._keyword_index:
                    self._keyword_index[token] = set()
                self._keyword_index[token].add(node["id"])

            # 属性关键词
            properties = node.get("properties", {})
            for value in properties.values():
                if isinstance(value, str):
                    for token in self._tokenize(value):
                        if token not in self._keyword_index:
                            self._keyword_index[token] = set()
                        self._keyword_index[token].add(node["id"])

        logger.info(
            f"EMLStore loaded: {len(graph.nodes)} nodes, {len(graph.edges)} edges, "
            f"{len(self._keyword_index)} keyword entries"
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """基于关键词的快速检索

        Args:
            query: 查询文本
            top_k: 返回前K个结果

        Returns:
            List[Dict]: 匹配的节点列表，带相似度分数
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 统计每个节点被匹配的关键词数
        node_scores: Counter = Counter()
        for token in query_tokens:
            matched_ids = self._keyword_index.get(token, set())
            for node_id in matched_ids:
                node_scores[node_id] += 1

        # 计算TF-IDF风格相似度
        results: List[Dict[str, Any]] = []
        for node_id, score in node_scores.most_common(top_k):
            node = self._node_index.get(node_id)
            if node:
                # 归一化分数：匹配关键词数 / 查询关键词数
                similarity = score / len(query_tokens)
                results.append({
                    **node,
                    "similarity": min(similarity, 1.0),
                })

        return results

    def get_related_edges(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        """获取与指定节点相关的关系边

        Args:
            node_ids: 节点ID列表

        Returns:
            List[Dict]: 关联的关系边列表
        """
        node_id_set = set(node_ids)
        related = []
        for edge in self.graph.edges:
            if edge.get("source") in node_id_set or edge.get("target") in node_id_set:
                related.append(edge)
        return related

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单分词：中文按字切分，英文按空格切分

        Args:
            text: 输入文本

        Returns:
            List[str]: 分词结果
        """
        if not text:
            return []

        tokens: List[str] = []

        # 英文单词
        english_words = re.findall(r"[a-zA-Z]+", text.lower())
        tokens.extend(english_words)

        # 中文字符（2-gram）
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        for ch in chinese_chars:
            tokens.append(ch)
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i + 1])

        # 数字
        numbers = re.findall(r"\d+", text)
        tokens.extend(numbers)

        return tokens

    @property
    def node_count(self) -> int:
        """节点数量"""
        return len(self.graph.nodes)

    @property
    def edge_count(self) -> int:
        """边数量"""
        return len(self.graph.edges)


class Translator:
    """翻译官 - EML知识图谱检索引擎

    在EML知识图谱中搜索相关概念和关系，为TOMAS-AGI提供快速精确的检索能力。
    核心方法：
    - retrieve(query): 在EML知识图谱中搜索相关概念和关系
    - get_confidence(query): 计算查询与EML图谱的匹配置信度

    超时策略：2秒超时，超时返回低置信度
    """

    # 置信度阈值：相似度高于此值才认为有有效匹配
    MIN_SIMILARITY_THRESHOLD: float = 0.3
    # 超时设置（秒）
    TIMEOUT_SECONDS: float = 2.0

    def __init__(self, eml_store: Optional[EMLStore] = None) -> None:
        """初始化翻译官

        Args:
            eml_store: EML知识图谱存储实例，为None时创建空实例
        """
        self.eml_store = eml_store or EMLStore()
        self._distiller = EMLDistiller()

    def load_eml_graph(self, graph: EMLGraph) -> None:
        """加载EML知识图谱

        Args:
            graph: EML知识图谱数据
        """
        self.eml_store.load_graph(graph)
        logger.info(f"Translator loaded EML graph: {self.eml_store.node_count} nodes")

    async def retrieve(self, query: str) -> EMLResult:
        """在EML知识图谱中检索相关概念和关系

        Args:
            query: 查询文本

        Returns:
            EMLResult: 检索结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # 检索匹配节点
            matched_nodes = self.eml_store.search(query, top_k=5)

            if not matched_nodes:
                latency = (asyncio.get_event_loop().time() - start_time) * 1000
                return EMLResult(
                    answer="EML知识图谱中未找到匹配的概念",
                    confidence=0.0,
                    reasoning="No matching nodes found in EML graph",
                    latency_ms=latency,
                )

            # 获取关联边
            node_ids = [n["id"] for n in matched_nodes]
            matched_edges = self.eml_store.get_related_edges(node_ids)

            # 构建回答文本
            answer = self._build_answer(matched_nodes, matched_edges)

            # 计算综合置信度（取最高相似度）
            max_similarity = max(n.get("similarity", 0.0) for n in matched_nodes)
            confidence = min(max_similarity, 1.0)

            # 构建推理说明
            reasoning = self._build_reasoning(matched_nodes, matched_edges)

            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.info(
                f"Translator retrieved: {len(matched_nodes)} nodes, "
                f"{len(matched_edges)} edges, confidence={confidence:.4f}, "
                f"latency={latency:.1f}ms"
            )

            return EMLResult(
                answer=answer,
                confidence=confidence,
                reasoning=reasoning,
                matched_nodes=matched_nodes,
                matched_edges=matched_edges,
                metadata={
                    "node_count": len(matched_nodes),
                    "edge_count": len(matched_edges),
                    "max_similarity": max_similarity,
                },
                latency_ms=latency,
            )

        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"Translator retrieve error: {e}")
            return EMLResult(
                answer="",
                confidence=0.0,
                reasoning=f"Retrieval error: {str(e)[:200]}",
                latency_ms=latency,
            )

    async def get_confidence(self, query: str) -> float:
        """计算查询与EML图谱的匹配置信度

        基于关键词匹配和相似度评分，判断EML知识图谱是否有足够覆盖。

        Args:
            query: 查询文本

        Returns:
            float: 置信度分数 (0.0-1.0)
        """
        try:
            matched_nodes = self.eml_store.search(query, top_k=3)

            if not matched_nodes:
                logger.debug(f"Translator confidence=0.0 (no matches for: {query[:50]})")
                return 0.0

            # 取最高相似度作为置信度
            max_similarity = max(n.get("similarity", 0.0) for n in matched_nodes)

            # 如果图谱为空，返回0
            if self.eml_store.node_count == 0:
                return 0.0

            # 图谱覆盖率加成：匹配节点数占图谱总节点数的比例
            coverage_bonus = min(len(matched_nodes) / max(self.eml_store.node_count, 1), 0.2)
            confidence = min(max_similarity + coverage_bonus, 1.0)

            logger.debug(
                f"Translator confidence={confidence:.4f} "
                f"(similarity={max_similarity:.4f}, coverage_bonus={coverage_bonus:.4f})"
            )
            return confidence

        except Exception as e:
            logger.error(f"Translator get_confidence error: {e}")
            return 0.0

    def _build_answer(
        self, matched_nodes: List[Dict[str, Any]], matched_edges: List[Dict[str, Any]]
    ) -> str:
        """基于匹配结果构建回答文本

        Args:
            matched_nodes: 匹配的节点列表
            matched_edges: 匹配的边列表

        Returns:
            str: 回答文本
        """
        if not matched_nodes:
            return "未找到相关知识"

        parts: List[str] = []

        # 添加节点信息
        for node in matched_nodes[:3]:
            label = node.get("label", "未知")
            node_type = node.get("type", "概念")
            similarity = node.get("similarity", 0.0)
            parts.append(f"[{node_type}]{label}(匹配度:{similarity:.0%})")

        # 添加关系信息
        for edge in matched_edges[:3]:
            source = edge.get("source", "?")
            target = edge.get("target", "?")
            relation = edge.get("relation", "相关")
            weight = edge.get("weight", 0.0)
            parts.append(f"{source} -[{relation}(权重:{weight:.2f})]-> {target}")

        return "；".join(parts)

    def _build_reasoning(
        self, matched_nodes: List[Dict[str, Any]], matched_edges: List[Dict[str, Any]]
    ) -> str:
        """构建推理说明

        Args:
            matched_nodes: 匹配的节点列表
            matched_edges: 匹配的边列表

        Returns:
            str: 推理说明
        """
        node_labels = [n.get("label", "?") for n in matched_nodes[:3]]
        return f"EML检索匹配到{len(matched_nodes)}个概念节点({', '.join(node_labels)})和{len(matched_edges)}条关系边"
