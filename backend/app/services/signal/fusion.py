"""信号融合器 - 多源信号加权融合与冲突消解

核心功能：
1. fuse(theory_results, tomas_result): 多源信号加权融合
2. weight_signals(): 根据各理论引擎历史准确率分配权重
3. resolve_conflicts(): 冲突消解——同标的多信号方向相反时，取置信度最高者
4. assign_confidence(): 综合理论置信度和TOMAS终裁置信度

信号生成规则：
- direction = LONG / SHORT / HOLD
- 仅置信度 > 0.3 的信号输出

融合策略选择：
- 支持 weighted（默认）/ and / or 三种策略
- 通过 set_strategy() 或构造参数选择
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.signal.fusion_strategies import (
    FusionStrategy,
    WeightedFusionStrategy,
    AndFusionStrategy,
    OrFusionStrategy,
    create_fusion_strategy,
)
from app.services.signal.base import Signal, SignalHint, TheoryResult
from app.services.tomas.token_bridge import TomasResult


@dataclass
class WeightedSignal:
    """加权信号（中间结果）"""

    signal: Signal = field(default_factory=Signal)
    weight: float = 1.0
    weighted_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal": self.signal.to_dict(),
            "weight": self.weight,
            "weighted_confidence": self.weighted_confidence,
        }


class SignalFusion:
    """信号融合器 - 多源信号加权融合

    将理论引擎信号与TOMAS-AGI推理结果融合，生成最终交易信号。

    融合流程：
    1. 从理论结果中提取原始信号
    2. 使用选择的融合策略融合信号
    3. 综合TOMAS终裁，计算最终置信度
    4. 过滤低置信度信号（>0.3）

    权重分配策略：
    - 初始：各引擎等权 1/N
    - 后续：根据历史准确率动态调整（预留接口）

    融合策略：
    - weighted（默认）：加权平均
    - and：所有引擎一致才输出
    - or：任一引擎信号即输出
    """

    # 信号置信度输出阈值
    CONFIDENCE_THRESHOLD: float = 0.3

    # TOMAS终裁置信度权重
    TOMAS_WEIGHT: float = 0.4

    # 理论信号置信度权重
    THEORY_WEIGHT: float = 0.6

    # 各理论引擎历史准确率（初始等权，后续可动态更新）
    _engine_weights: Dict[str, float] = {}

    def __init__(
        self,
        engine_weights: Optional[Dict[str, float]] = None,
        fusion_strategy: str = "weighted",
    ) -> None:
        """初始化信号融合器

        Args:
            engine_weights: 各理论引擎权重，默认等权
            fusion_strategy: 融合策略 (weighted/and/or)
        """
        self._engine_weights = engine_weights or {}
        self._fusion_strategy_name = fusion_strategy
        self._fusion_strategy = create_fusion_strategy(
            fusion_strategy, engine_weights=engine_weights
        )

    def set_strategy(self, strategy_name: str, **kwargs) -> None:
        """设置融合策略

        Args:
            strategy_name: 策略名称 (weighted/and/or)
            **kwargs: 传递给策略构造函数的参数
        """
        self._fusion_strategy_name = strategy_name
        self._fusion_strategy = create_fusion_strategy(strategy_name, **kwargs)
        logger.info(f"SignalFusion: switched to '{strategy_name}' strategy")

    @property
    def fusion_strategy(self) -> str:
        """当前融合策略名称"""
        return self._fusion_strategy_name

    def fuse(
        self,
        theory_results: List[TheoryResult],
        tomas_result: TomasResult,
    ) -> List[Signal]:
        """多源信号加权融合

        将理论引擎结果与TOMAS终裁融合，生成最终信号列表。

        Args:
            theory_results: 理论引擎结果列表
            tomas_result: TOMAS-AGI推理结果

        Returns:
            List[Signal]: 融合后的信号列表（仅置信度>0.3的信号）
        """
        logger.info(
            f"SignalFusion: fusing {len(theory_results)} theory results "
            f"with TOMAS result (source={tomas_result.source}), "
            f"strategy={self._fusion_strategy_name}"
        )

        # 步骤1：从理论结果提取原始信号
        raw_signals = self._extract_raw_signals(theory_results)
        if not raw_signals:
            logger.info("SignalFusion: no raw signals from theories")
            # 如果没有理论信号，仅依赖TOMAS
            if tomas_result.confidence > self.CONFIDENCE_THRESHOLD:
                return [self._create_tomas_signal(tomas_result)]
            return []

        # 步骤2：使用融合策略融合信号
        fused_results = self._fusion_strategy.fuse(raw_signals, theory_results)

        # 步骤3：转换为Signal列表并综合TOMAS
        final_signals = []
        for fused in fused_results:
            signal = fused.signal

            # 综合TOMAS终裁
            direction_bonus = 0.0
            tomas_direction = self._parse_tomas_direction(tomas_result)
            tomas_confidence = tomas_result.confidence

            if tomas_direction and signal.direction != "HOLD":
                if signal.direction == tomas_direction:
                    direction_bonus = tomas_confidence * 0.2
                else:
                    direction_bonus = -tomas_confidence * 0.3

            theory_component = signal.confidence * self.THEORY_WEIGHT
            tomas_component = tomas_confidence * self.TOMAS_WEIGHT
            final_confidence = theory_component + tomas_component + direction_bonus
            final_confidence = max(0.0, min(1.0, final_confidence))

            signal.confidence = round(final_confidence, 4)
            signal.source_engine = f"fusion_{self._fusion_strategy_name}"
            signal.metadata["fusion_strategy"] = self._fusion_strategy_name
            signal.metadata["tomas_direction"] = tomas_direction
            signal.metadata["tomas_confidence"] = tomas_confidence

            final_signals.append(signal)

        # 步骤4：过滤低置信度信号
        filtered = [s for s in final_signals if s.confidence > self.CONFIDENCE_THRESHOLD]

        logger.info(
            f"SignalFusion: {len(raw_signals)} raw → {len(filtered)} final signals "
            f"(threshold={self.CONFIDENCE_THRESHOLD}, strategy={self._fusion_strategy_name})"
        )

        return filtered

    def weight_signals(self, signals: List[Signal]) -> List[WeightedSignal]:
        """根据各理论引擎历史准确率分配权重

        初始等权1/N，后续可按历史准确率调整。

        Args:
            signals: 原始信号列表

        Returns:
            List[WeightedSignal]: 加权信号列表
        """
        if not signals:
            return []

        # 计算引擎数量
        engine_names = set(s.source_engine for s in signals)
        n_engines = max(len(engine_names), 1)

        # 默认等权
        default_weight = 1.0 / n_engines

        weighted: List[WeightedSignal] = []
        for signal in signals:
            # 查找引擎权重，无则使用默认权重
            weight = self._engine_weights.get(signal.source_engine, default_weight)
            weighted_confidence = signal.confidence * weight

            weighted.append(WeightedSignal(
                signal=signal,
                weight=weight,
                weighted_confidence=weighted_confidence,
            ))

        return weighted

    def resolve_conflicts(self, weighted_signals: List[WeightedSignal]) -> List[Signal]:
        """冲突消解——同标的多信号方向相反时，取置信度最高者

        当同一标的出现多个方向相反的信号时：
        1. 按标的分组
        2. 每组内选择加权置信度最高的信号
        3. 丢弃方向相反的低置信度信号

        Args:
            weighted_signals: 加权信号列表

        Returns:
            List[Signal]: 消解冲突后的信号列表
        """
        if not weighted_signals:
            return []

        # 按标的分组
        by_symbol: Dict[str, List[WeightedSignal]] = {}
        for ws in weighted_signals:
            symbol = ws.signal.symbol or "unknown"
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(ws)

        resolved: List[Signal] = []

        for symbol, ws_list in by_symbol.items():
            if len(ws_list) == 1:
                resolved.append(ws_list[0].signal)
                continue

            # 检查是否有方向冲突
            directions = {ws.signal.direction for ws in ws_list}
            if len(directions) <= 1:
                # 无冲突：保留所有信号
                for ws in ws_list:
                    resolved.append(ws.signal)
            else:
                # 有冲突：选择加权置信度最高的信号
                best_ws = max(ws_list, key=lambda ws: ws.weighted_confidence)
                resolved.append(best_ws.signal)

                # 记录冲突消解
                other_directions = directions - {best_ws.signal.direction}
                logger.info(
                    f"SignalFusion: conflict resolved for {symbol} - "
                    f"chose {best_ws.signal.direction} (conf={best_ws.weighted_confidence:.4f}), "
                    f"discarded {other_directions}"
                )

        return resolved

    def assign_confidence(
        self, signals: List[Signal], tomas_result: TomasResult
    ) -> List[Signal]:
        """综合理论置信度和TOMAS终裁置信度，计算最终信号置信度

        公式：final_confidence = theory_confidence * THEORY_WEIGHT + tomas_confidence * TOMAS_WEIGHT

        TOMAS终裁可以增强或削弱理论信号的置信度：
        - TOMAS方向一致时：增强
        - TOMAS方向相反时：削弱
        - TOMAS无明确方向时：保持不变

        Args:
            signals: 理论信号列表
            tomas_result: TOMAS推理结果

        Returns:
            List[Signal]: 最终信号列表
        """
        # 解析TOMAS方向
        tomas_direction = self._parse_tomas_direction(tomas_result)
        tomas_confidence = tomas_result.confidence

        final_signals: List[Signal] = []

        for signal in signals:
            # 计算TOMAS方向一致性加成/惩罚
            direction_bonus = 0.0
            if tomas_direction and signal.direction != "HOLD":
                if signal.direction == tomas_direction:
                    # 方向一致：增强
                    direction_bonus = tomas_confidence * 0.2
                else:
                    # 方向相反：削弱
                    direction_bonus = -tomas_confidence * 0.3

            # 综合置信度
            theory_component = signal.confidence * self.THEORY_WEIGHT
            tomas_component = tomas_confidence * self.TOMAS_WEIGHT
            final_confidence = theory_component + tomas_component + direction_bonus

            # 限制在[0, 1]范围
            final_confidence = max(0.0, min(1.0, final_confidence))

            # 更新信号
            updated_signal = Signal(
                signal_id=f"sig-{uuid.uuid4().hex[:8]}",
                symbol=signal.symbol,
                market=signal.market,
                direction=signal.direction,
                price=signal.price,
                confidence=round(final_confidence, 4),
                source_engine="fusion",
                theory_name=signal.theory_name,
                metadata={
                    **signal.metadata,
                    "original_confidence": signal.confidence,
                    "tomas_direction": tomas_direction,
                    "tomas_confidence": tomas_confidence,
                    "direction_bonus": direction_bonus,
                    "fusion_source": signal.source_engine,
                },
            )
            final_signals.append(updated_signal)

        return final_signals

    def _extract_raw_signals(self, theory_results: List[TheoryResult]) -> List[Signal]:
        """从理论结果中提取原始信号

        Args:
            theory_results: 理论引擎结果列表

        Returns:
            List[Signal]: 原始信号列表
        """
        signals: List[Signal] = []

        for result in theory_results:
            if result.error:
                continue

            for hint in result.hints:
                signal = Signal(
                    signal_id=f"sig-{uuid.uuid4().hex[:8]}",
                    direction=hint.direction,
                    confidence=hint.confidence,
                    source_engine=self._engine_key_from_name(result.theory_name),
                    theory_name=result.theory_name,
                    price=hint.price_target or 0.0,
                    metadata={
                        "reason": hint.reason,
                        "annotations": result.annotations,
                    },
                )
                signals.append(signal)

        return signals

    def _create_tomas_signal(self, tomas_result: TomasResult) -> Signal:
        """从TOMAS结果创建信号（无理论信号时的备选）

        Args:
            tomas_result: TOMAS推理结果

        Returns:
            Signal: TOMAS信号
        """
        direction = self._parse_tomas_direction(tomas_result)

        return Signal(
            signal_id=f"sig-{uuid.uuid4().hex[:8]}",
            direction=direction or "HOLD",
            confidence=tomas_result.confidence,
            source_engine="tomas",
            theory_name="TOMAS-AGI",
            metadata={
                "tomas_source": tomas_result.source,
                "tomas_answer": tomas_result.answer[:500],
                "tomas_reasoning": tomas_result.reasoning[:500],
            },
        )

    @staticmethod
    def _parse_tomas_direction(tomas_result: TomasResult) -> Optional[str]:
        """解析TOMAS推理结果的交易方向

        Args:
            tomas_result: TOMAS推理结果

        Returns:
            Optional[str]: 交易方向 LONG/SHORT/HOLD，无法解析返回None
        """
        text = tomas_result.answer.upper()

        # 优先从metadata中获取
        if "direction" in tomas_result.metadata:
            direction = tomas_result.metadata["direction"].upper()
            if direction in ("LONG", "SHORT", "HOLD"):
                return direction

        # 从回答文本中解析
        if "LONG" in text or "做多" in tomas_result.answer:
            return "LONG"
        elif "SHORT" in text or "做空" in tomas_result.answer:
            return "SHORT"
        elif "HOLD" in text or "观望" in tomas_result.answer:
            return "HOLD"

        return None

    @staticmethod
    def _engine_key_from_name(theory_name: str) -> str:
        """将理论名称转换为引擎键

        Args:
            theory_name: 理论名称（中文）

        Returns:
            str: 引擎键（英文）
        """
        name_map = {
            "太极中心律": "taiji",
            "螺旋律": "spiral",
            "波浪理论": "elliott",
        }
        return name_map.get(theory_name, theory_name.lower().replace(" ", "_"))

    def update_engine_weight(self, engine_name: str, weight: float) -> None:
        """更新引擎权重

        Args:
            engine_name: 引擎名称
            weight: 新权重值
        """
        self._engine_weights[engine_name] = weight
        logger.info(f"SignalFusion: updated weight for '{engine_name}' to {weight:.4f}")
