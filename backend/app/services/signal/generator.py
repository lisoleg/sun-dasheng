"""信号生成器 - 调度核心

编排理论引擎和TOMAS-AGI的运行：
1. 并行运行所有理论引擎 → 汇总theory_results
2. 咨询TOMAS → 获取终裁推理
3. 融合信号 → 生成最终信号列表
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.signal.base import SignalHint, TheoryResult, Signal, TheoryEngine
from app.services.signal.fusion import SignalFusion
from app.services.tomas.token_bridge import TomasBridge, TomasResult


class SignalGenerator:
    """信号生成器 - 调度核心

    编排理论引擎和TOMAS-AGI的运行流程：
    1. 并行运行所有注册的理论引擎
    2. 汇总理论结果，咨询TOMAS推理
    3. 通过信号融合器生成最终信号
    """

    def __init__(
        self,
        tomas_bridge: TomasBridge,
        fusion: Optional[SignalFusion] = None,
        engines: Optional[List[Any]] = None,
    ) -> None:
        """初始化信号生成器

        Args:
            tomas_bridge: TOMAS-AGI推理桥
            fusion: 信号融合器，默认创建新实例
            engines: 理论引擎列表
        """
        self.tomas = tomas_bridge
        self.fusion = fusion or SignalFusion()
        self._engines: List[Any] = engines or []

    def register_engine(self, engine: Any) -> None:
        """注册理论引擎

        Args:
            engine: 实现TheoryEngine协议的引擎实例
        """
        self._engines.append(engine)
        logger.info(f"SignalGenerator: registered engine '{engine.name}'")

    def unregister_engine(self, engine_name: str) -> None:
        """移除理论引擎

        Args:
            engine_name: 引擎名称
        """
        self._engines = [e for e in self._engines if e.name != engine_name]
        logger.info(f"SignalGenerator: unregistered engine '{engine_name}'")

    @property
    def engines(self) -> List[Any]:
        """获取已注册的引擎列表"""
        return self._engines

    async def generate(self, bars: List[Dict[str, Any]]) -> List[Signal]:
        """生成交易信号（主入口方法）

        流程：并行运行理论引擎 → 咨询TOMAS → 融合信号

        Args:
            bars: K线数据列表

        Returns:
            List[Signal]: 交易信号列表
        """
        if not bars:
            logger.warning("SignalGenerator: no bars data, skipping signal generation")
            return []

        logger.info(f"SignalGenerator: generating signals for {len(bars)} bars")

        # 步骤1：并行运行所有理论引擎
        theory_results = await self._run_theories(bars)
        logger.info(f"SignalGenerator: {len(theory_results)} theory results collected")

        # 步骤2：咨询TOMAS-AGI
        tomas_result = await self._consult_tomas(theory_results, bars)
        logger.info(
            f"SignalGenerator: TOMAS result - source={tomas_result.source}, "
            f"confidence={tomas_result.confidence:.4f}"
        )

        # 步骤3：融合信号
        signals = self.fusion.fuse(theory_results, tomas_result)

        # 为信号补充市场信息
        last_bar = bars[-1] if bars else {}
        for signal in signals:
            signal.symbol = last_bar.get("symbol", "")
            signal.market = last_bar.get("market", "crypto")
            signal.price = last_bar.get("close", 0.0)

        logger.info(f"SignalGenerator: generated {len(signals)} signals")
        return signals

    async def _run_theories(self, bars: List[Dict[str, Any]]) -> List[TheoryResult]:
        """并行运行所有理论引擎

        单个引擎异常不影响其他引擎，捕获异常后返回空TheoryResult。

        Args:
            bars: K线数据列表

        Returns:
            List[TheoryResult]: 理论引擎结果列表
        """
        if not self._engines:
            logger.warning("SignalGenerator: no engines registered")
            return []

        # 并行调用所有引擎
        tasks = [self._run_engine_safe(engine, bars) for engine in self._engines]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # 过滤None结果
        valid_results = [r for r in results if r is not None]
        return valid_results

    async def _run_engine_safe(
        self, engine: Any, bars: List[Dict[str, Any]]
    ) -> Optional[TheoryResult]:
        """安全运行单个理论引擎，捕获异常

        Args:
            engine: 理论引擎实例
            bars: K线数据

        Returns:
            Optional[TheoryResult]: 分析结果，异常时返回None
        """
        try:
            result = engine.analyze(bars)
            if hasattr(result, "__await__"):
                result = await result
            logger.debug(f"Engine '{engine.name}' completed: confidence={result.confidence:.4f}")
            return result
        except Exception as e:
            logger.error(f"Engine '{engine.name}' failed: {e}")
            return None

    async def _consult_tomas(
        self,
        results: List[TheoryResult],
        bars: Optional[List[Dict[str, Any]]] = None,
    ) -> TomasResult:
        """将理论结果交给TOMAS推理

        Args:
            results: 理论引擎结果列表
            bars: K线数据（提供上下文）

        Returns:
            TomasResult: TOMAS推理结果
        """
        # 构建查询文本
        query = self._build_tomas_query(results)

        # 构建上下文
        context: Dict[str, Any] = {
            "theory_results": [r.to_dict() for r in results],
        }
        if bars:
            last_bar = bars[-1] if bars else {}
            context["bars_summary"] = {
                "symbol": last_bar.get("symbol", ""),
                "close": last_bar.get("close", 0.0),
                "bar_count": len(bars),
            }

        # 调用TOMAS推理
        tomas_result = await self.tomas.reason(query, context)
        return tomas_result

    def _build_tomas_query(self, results: List[TheoryResult]) -> str:
        """构建TOMAS查询文本

        Args:
            results: 理论引擎结果

        Returns:
            str: 查询文本
        """
        if not results:
            return "请分析当前市场状态并给出交易方向建议"

        parts: List[str] = ["基于以下理论分析结果，请综合判断交易方向："]
        for result in results:
            if result.error:
                parts.append(f"- {result.theory_name}：计算异常（{result.error}）")
            else:
                hint_dirs = [h.direction for h in result.hints] if result.hints else ["HOLD"]
                parts.append(
                    f"- {result.theory_name}：方向={hint_dirs}, 置信度={result.confidence:.2%}"
                )

        parts.append("请给出综合判断。")
        return "\n".join(parts)
