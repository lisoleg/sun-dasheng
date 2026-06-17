"""作家 - LLM创造性推理引擎

调用LLM（OpenAI API）进行创造性推理，覆盖EML知识图谱之外的领域。
响应时间目标：1-5秒
超时设置：10秒
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from app.config import settings


@dataclass
class WriterResult:
    """作家推理结果"""

    answer: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    model: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "model": self.model,
            "latency_ms": self.latency_ms,
        }


# 默认系统提示词：量化交易分析助手
DEFAULT_SYSTEM_PROMPT = """你是"孙大圣量化交易系统"的TOMAS-AGI作家引擎。
你的职责是基于鲁兆理论（太极中心律、螺旋律、波浪理论）的分析结果，进行深度推理和判断。

你的推理应遵循以下原则：
1. 综合考虑多个理论引擎的分析结果，寻找共振和分歧
2. 对分歧情况给出倾向性判断和理由
3. 评估信号的可靠性和置信度
4. 给出明确的交易方向建议（做多/做空/观望）

输出格式要求：
- 方向判断：LONG（做多）/ SHORT（做空）/ HOLD（观望）
- 置信度：0.0-1.0之间的数值
- 推理过程：简要说明判断依据"""


class Writer:
    """作家 - LLM创造性推理引擎

    当翻译官置信度不足时，作家调用LLM进行创造性推理，
    覆盖EML知识图谱中未收录的场景。

    核心方法：
    - infer(query, context): 调用LLM生成推理结果

    超时策略：10秒超时，超时返回空结果
    配置支持：自定义LLM端点（OPENAI_BASE_URL）
    """

    TIMEOUT_SECONDS: float = 10.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """初始化作家

        Args:
            api_key: OpenAI API密钥，默认从配置读取
            model: LLM模型名称，默认从配置读取
            base_url: LLM API基础URL，默认从配置读取
            system_prompt: 自定义系统提示词
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """获取或创建OpenAI客户端（延迟初始化）

        Returns:
            OpenAI客户端实例
        """
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.TIMEOUT_SECONDS,
                )
                logger.info(f"Writer LLM client initialized: model={self.model}, base_url={self.base_url}")
            except ImportError:
                logger.error("openai package not installed, Writer will not function")
                raise
        return self._client

    async def infer(self, query: str, context: Optional[Dict[str, Any]] = None) -> WriterResult:
        """调用LLM进行创造性推理

        Args:
            query: 推理查询文本
            context: 上下文信息（理论引擎结果等）

        Returns:
            WriterResult: 推理结果
        """
        if context is None:
            context = {}

        start_time = asyncio.get_event_loop().time()

        # 如果API Key未配置，返回模拟结果
        if not self.api_key:
            logger.warning("Writer: OPENAI_API_KEY not configured, returning mock result")
            return self._mock_infer(query, context)

        try:
            client = self._get_client()

            # 构建用户消息
            user_message = self._build_user_message(query, context)

            # 调用LLM
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.3,  # 低温度保证推理稳定性
                    max_tokens=1000,
                ),
                timeout=self.TIMEOUT_SECONDS,
            )

            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            # 解析响应
            answer_text = response.choices[0].message.content or ""
            parsed = self._parse_llm_response(answer_text)

            logger.info(
                f"Writer inferred: model={self.model}, "
                f"direction={parsed.get('direction', 'N/A')}, "
                f"confidence={parsed.get('confidence', 0.0):.4f}, "
                f"latency={latency:.1f}ms"
            )

            return WriterResult(
                answer=parsed.get("answer", answer_text),
                confidence=parsed.get("confidence", 0.5),
                reasoning=parsed.get("reasoning", ""),
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "context_keys": list(context.keys()),
                },
                model=self.model,
                latency_ms=latency,
            )

        except asyncio.TimeoutError:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.warning(f"Writer infer timeout(>{self.TIMEOUT_SECONDS}s)")
            return WriterResult(
                answer="",
                confidence=0.0,
                reasoning="LLM inference timeout",
                metadata={"timeout": True},
                model=self.model,
                latency_ms=latency,
            )

        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"Writer infer error: {e}")
            return WriterResult(
                answer="",
                confidence=0.0,
                reasoning=f"LLM inference error: {str(e)[:200]}",
                metadata={"error": True},
                model=self.model,
                latency_ms=latency,
            )

    def _build_user_message(self, query: str, context: Dict[str, Any]) -> str:
        """构建用户消息，组合查询和上下文

        Args:
            query: 查询文本
            context: 上下文信息

        Returns:
            str: 组合后的用户消息
        """
        parts: list[str] = [f"问题：{query}"]

        # 添加理论引擎结果
        theory_results = context.get("theory_results", [])
        if theory_results:
            parts.append("\n各理论引擎分析结果：")
            for result in theory_results:
                theory_name = result.get("theory_name", "未知")
                confidence = result.get("confidence", 0.0)
                hints = result.get("hints", [])
                parts.append(f"- {theory_name}：置信度={confidence:.2%}，信号={hints}")

        # 添加市场数据摘要
        bars_summary = context.get("bars_summary", {})
        if bars_summary:
            parts.append(f"\n市场数据：{bars_summary}")

        parts.append("\n请给出你的推理判断。")
        return "\n".join(parts)

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM响应文本，提取方向、置信度、推理过程

        Args:
            response_text: LLM原始响应文本

        Returns:
            Dict: 解析结果
        """
        result: Dict[str, Any] = {
            "answer": response_text,
            "direction": "HOLD",
            "confidence": 0.5,
            "reasoning": "",
        }

        text_upper = response_text.upper()

        # 提取方向
        if "LONG" in text_upper or "做多" in response_text:
            result["direction"] = "LONG"
        elif "SHORT" in text_upper or "做空" in response_text:
            result["direction"] = "SHORT"
        else:
            result["direction"] = "HOLD"

        # 提取置信度（寻找0-1之间的小数）
        import re

        confidence_patterns = [
            r"置信度[：:]\s*(\d+\.?\d*)",
            r"confidence[：:]\s*(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*的置信度",
        ]
        for pattern in confidence_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                try:
                    conf = float(match.group(1))
                    if 0.0 <= conf <= 1.0:
                        result["confidence"] = conf
                    elif 0.0 <= conf <= 100.0:
                        result["confidence"] = conf / 100.0
                    break
                except ValueError:
                    continue

        result["reasoning"] = response_text[:500]
        return result

    def _mock_infer(self, query: str, context: Dict[str, Any]) -> WriterResult:
        """模拟推理（API Key未配置时使用）

        Args:
            query: 查询文本
            context: 上下文信息

        Returns:
            WriterResult: 模拟推理结果
        """
        # 基于理论结果生成简单的模拟回答
        theory_results = context.get("theory_results", [])

        if not theory_results:
            return WriterResult(
                answer="HOLD - 缺乏足够信息做出判断",
                confidence=0.3,
                reasoning="Mock: no theory results available",
                metadata={"mock": True},
                model="mock",
            )

        # 统计理论引擎方向倾向
        long_count = 0
        short_count = 0
        for result in theory_results:
            hints = result.get("hints", [])
            for hint in hints:
                direction = hint.get("direction", "HOLD") if isinstance(hint, dict) else "HOLD"
                if direction == "LONG":
                    long_count += 1
                elif direction == "SHORT":
                    short_count += 1

        if long_count > short_count:
            direction = "LONG"
            confidence = min(0.4 + long_count * 0.1, 0.8)
        elif short_count > long_count:
            direction = "SHORT"
            confidence = min(0.4 + short_count * 0.1, 0.8)
        else:
            direction = "HOLD"
            confidence = 0.3

        return WriterResult(
            answer=f"{direction} - Mock推理（API Key未配置）",
            confidence=confidence,
            reasoning=f"Mock: long_count={long_count}, short_count={short_count}",
            metadata={"mock": True},
            model="mock",
        )
