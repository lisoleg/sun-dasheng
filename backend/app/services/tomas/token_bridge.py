"""Token Bridge推理引擎 - 置信度路由器

TOMAS-AGI的核心组件，实现"翻译官+作家"双引擎混合推理架构：
- 置信度 >= 0.5：走翻译官(EML精确检索)，响应时间 < 100ms
- 置信度 < 0.5：走作家(LLM创造性推理)，响应时间 1-5s
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from app.services.tomas.translator import Translator
from app.services.tomas.writer import Writer


@dataclass
class TomasResult:
    """TOMAS推理结果"""

    answer: str = ""
    confidence: float = 0.0
    source: str = "none"  # "translator" | "writer" | "fallback"
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "source": self.source,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class TomasBridge:
    """Token Bridge推理引擎 - 置信度路由器

    根据查询与EML知识图谱的匹配置信度，自动选择翻译官或作家进行推理：
    - 高置信度(>=0.5)：翻译官在EML知识图谱中精确检索，响应迅速
    - 低置信度(<0.5)：作家调用LLM进行创造性推理，覆盖面广

    异常降级策略：
    - 翻译官超时(>2s)：降级为作家路由
    - 作家超时(>10s)：返回空结果，依赖纯理论信号
    """

    CONFIDENCE_THRESHOLD: float = 0.5

    def __init__(self, translator: Translator, writer: Writer) -> None:
        """初始化Token Bridge

        Args:
            translator: 翻译官实例，负责EML知识检索
            writer: 作家实例，负责LLM创造性推理
        """
        self.translator = translator
        self.writer = writer

    async def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> TomasResult:
        """主推理方法：根据置信度选择翻译官或作家

        Args:
            query: 推理查询文本
            context: 上下文信息（理论引擎结果等）

        Returns:
            TomasResult: 推理结果
        """
        if context is None:
            context = {}

        logger.info(f"TomasBridge reasoning: query={query[:80]}...")

        # 步骤1：计算翻译官置信度
        confidence = await self._get_confidence_safe(query)
        logger.info(f"TomasBridge confidence={confidence:.4f}, threshold={self.CONFIDENCE_THRESHOLD}")

        # 步骤2：根据置信度路由到对应引擎
        if confidence >= self.CONFIDENCE_THRESHOLD:
            result = await self._route_translator(query, confidence)
        else:
            result = await self._route_writer(query, context, confidence)

        return result

    async def _get_confidence_safe(self, query: str) -> float:
        """安全获取翻译官置信度，超时降级为低置信度

        Args:
            query: 查询文本

        Returns:
            float: 置信度分数，超时时返回0.0
        """
        try:
            confidence = await asyncio.wait_for(
                self.translator.get_confidence(query),
                timeout=2.0,
            )
            return float(confidence)
        except asyncio.TimeoutError:
            logger.warning("Translator get_confidence timeout(>2s), degrading to writer route")
            return 0.0
        except Exception as e:
            logger.error(f"Translator get_confidence error: {e}, degrading to writer route")
            return 0.0

    async def _route_translator(self, query: str, confidence: float) -> TomasResult:
        """路由到翻译官：EML精确检索

        Args:
            query: 查询文本
            confidence: 置信度

        Returns:
            TomasResult: 翻译官检索结果
        """
        try:
            eml_result = await asyncio.wait_for(
                self.translator.retrieve(query),
                timeout=2.0,
            )
            return TomasResult(
                answer=eml_result.answer,
                confidence=confidence,
                source="translator",
                reasoning=eml_result.reasoning,
                metadata=eml_result.metadata,
            )
        except asyncio.TimeoutError:
            logger.warning("Translator retrieve timeout(>2s), falling back to writer")
            return await self._route_writer(query, {}, confidence)
        except Exception as e:
            logger.error(f"Translator retrieve error: {e}, falling back to writer")
            return await self._route_writer(query, {}, confidence)

    async def _route_writer(
        self,
        query: str,
        context: Dict[str, Any],
        confidence: float,
    ) -> TomasResult:
        """路由到作家：LLM创造性推理

        Args:
            query: 查询文本
            context: 上下文信息
            confidence: 原始置信度

        Returns:
            TomasResult: 作家推理结果
        """
        try:
            writer_result = await asyncio.wait_for(
                self.writer.infer(query, context),
                timeout=10.0,
            )
            return TomasResult(
                answer=writer_result.answer,
                confidence=writer_result.confidence,
                source="writer",
                reasoning=writer_result.reasoning,
                metadata=writer_result.metadata,
            )
        except asyncio.TimeoutError:
            logger.warning("Writer infer timeout(>10s), returning fallback result")
            return TomasResult(
                answer="",
                confidence=confidence,
                source="fallback",
                reasoning="Writer timeout, falling back to pure theory signals",
                metadata={"timeout": True},
            )
        except Exception as e:
            logger.error(f"Writer infer error: {e}, returning fallback result")
            return TomasResult(
                answer="",
                confidence=0.0,
                source="fallback",
                reasoning=f"Writer error: {str(e)[:200]}",
                metadata={"error": True},
            )

    def _route_by_confidence(self, confidence: float) -> str:
        """根据置信度确定路由目标

        Args:
            confidence: 置信度分数

        Returns:
            str: "translator" 或 "writer"
        """
        return "translator" if confidence >= self.CONFIDENCE_THRESHOLD else "writer"
