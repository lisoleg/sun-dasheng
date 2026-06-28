"""信号融合策略扩展 — 支持 AND / OR / weighted / risk_parity 四种融合策略

基于现有 SignalFusion，新增策略模式：
- AndFusionStrategy: 所有信号一致才发出（高置信度，低频率）
- OrFusionStrategy: 任一信号发出即发出（低置信度，高频率）
- WeightedFusionStrategy: 加权平均，置信度加权（默认）
- RiskParityFusionStrategy: 风险平价加权，各引擎风险贡献均衡（大师共识二）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.services.signal.base import Signal, SignalHint, TheoryResult


@dataclass
class FusedSignal:
    """融合后信号"""

    signal: Signal = field(default_factory=Signal)
    strategy_name: str = ""
    contributor_count: int = 0  # 贡献信号的引擎数量
    weighted_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal": self.signal.to_dict(),
            "strategy_name": self.strategy_name,
            "contributor_count": self.contributor_count,
            "weighted_confidence": self.weighted_confidence,
        }


class FusionStrategy(ABC):
    """融合策略抽象基类

    所有融合策略必须实现 fuse 方法。
    """

    @abstractmethod
    def fuse(self, signals: List[Signal], theory_results: List[TheoryResult]) -> List[FusedSignal]:
        """融合信号

        Args:
            signals: 理论引擎原始信号列表
            theory_results: 理论引擎结果列表

        Returns:
            融合后信号列表
        """
        ...


class AndFusionStrategy(FusionStrategy):
    """AND融合策略：所有信号一致才发出

    高置信度，低频率。
    仅当所有启用的理论引擎都发出同方向信号时，才输出融合信号。

    适用场景：
    - 趋势明确的市场
    - 追求高胜率而非高频交易
    """

    name = "and"

    def fuse(self, signals: List[Signal], theory_results: List[TheoryResult]) -> List[FusedSignal]:
        """AND融合：仅当所有信号方向一致时输出"""
        if not signals or not theory_results:
            return []

        # 按标的分组
        by_symbol: Dict[str, List[Signal]] = {}
        for signal in signals:
            symbol = signal.symbol or "unknown"
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(signal)

        fused = []
        for symbol, symbol_signals in by_symbol.items():
            # 统计各方向信号数
            direction_counts: Dict[str, int] = {}
            for signal in symbol_signals:
                direction = signal.direction
                direction_counts[direction] = direction_counts.get(direction, 0) + 1

            # 找出主要方向（信号数最多的方向）
            if not direction_counts:
                continue

            main_direction = max(direction_counts, key=direction_counts.get)
            total_engines = len(theory_results)
            agreeing_engines = direction_counts.get(main_direction, 0)

            # 仅当所有引擎一致时输出
            if agreeing_engines == total_engines and main_direction != "HOLD":
                # 计算平均置信度
                agreeing_signals = [s for s in symbol_signals if s.direction == main_direction]
                avg_confidence = (
                    sum(s.confidence for s in agreeing_signals) / len(agreeing_signals)
                    if agreeing_signals
                    else 0.0
                )

                # AND策略：置信度加成（因为所有引擎一致）
                boosted_confidence = min(avg_confidence * 1.2, 1.0)

                fused_signal = Signal(
                    signal_id=f"sig-and-{symbol}",
                    symbol=symbol,
                    direction=main_direction,
                    confidence=round(boosted_confidence, 4),
                    source_engine="fusion_and",
                    theory_name="AND Fusion",
                    metadata={
                        "strategy": "and",
                        "agreeing_engines": agreeing_engines,
                        "total_engines": total_engines,
                        "contributors": [s.source_engine for s in agreeing_signals],
                    },
                )

                fused.append(FusedSignal(
                    signal=fused_signal,
                    strategy_name="and",
                    contributor_count=agreeing_engines,
                    weighted_confidence=boosted_confidence,
                ))

                logger.info(
                    f"AndFusion: consensus reached for {symbol} "
                    f"({agreeing_engines}/{total_engines} engines agree)"
                )

        return fused


class OrFusionStrategy(FusionStrategy):
    """OR融合策略：任一信号发出即输出

    低置信度，高频率。
    只要有任一理论引擎发出信号，就输出融合信号。
    置信度取所有信号的最大值。

    适用场景：
    - 震荡市场
    - 追求高频交易信号
    """

    name = "or"

    def fuse(self, signals: List[Signal], theory_results: List[TheoryResult]) -> List[FusedSignal]:
        """OR融合：任一信号即输出"""
        if not signals:
            return []

        # 按标的和方向分组
        by_symbol_direction: Dict[Tuple[str, str], List[Signal]] = {}

        for signal in signals:
            if signal.direction == "HOLD":
                continue
            key = (signal.symbol or "unknown", signal.direction)
            if key not in by_symbol_direction:
                by_symbol_direction[key] = []
            by_symbol_direction[key].append(signal)

        fused = []
        for (symbol, direction), symbol_signals in by_symbol_direction.items():
            # OR策略：置信度取最大值（因为任一信号触发）
            max_confidence = max(s.confidence for s in symbol_signals)

            # OR策略：置信度折扣（因为仅部分引擎同意）
            total_engines = len(theory_results)
            agreeing_engines = len(symbol_signals)
            discount = agreeing_engines / max(total_engines, 1)
            adjusted_confidence = max_confidence * discount

            fused_signal = Signal(
                signal_id=f"sig-or-{symbol}-{direction}",
                symbol=symbol,
                direction=direction,
                confidence=round(adjusted_confidence, 4),
                source_engine="fusion_or",
                theory_name="OR Fusion",
                metadata={
                    "strategy": "or",
                    "agreeing_engines": agreeing_engines,
                    "total_engines": total_engines,
                    "contributors": [s.source_engine for s in symbol_signals],
                },
            )

            fused.append(FusedSignal(
                signal=fused_signal,
                strategy_name="or",
                contributor_count=agreeing_engines,
                weighted_confidence=adjusted_confidence,
            ))

            logger.info(
                f"OrFusion: signal for {symbol} {direction} "
                f"({agreeing_engines}/{total_engines} engines)"
            )

        return fused


class WeightedFusionStrategy(FusionStrategy):
    """加权平均融合策略：置信度加权

    默认策略，平衡胜率和频率。
    根据各理论引擎的历史准确率分配权重，计算加权置信度。

    适用场景：
    - 通用场景
    - 平衡胜率和交易频率
    """

    name = "weighted"

    def __init__(self, engine_weights: Optional[Dict[str, float]] = None) -> None:
        """初始化加权平均融合策略

        Args:
            engine_weights: 各引擎权重，默认等权
        """
        self.engine_weights = engine_weights or {}
        self.default_weight = 1.0

    def fuse(self, signals: List[Signal], theory_results: List[TheoryResult]) -> List[FusedSignal]:
        """加权平均融合"""
        if not signals:
            return []

        # 按标的分组
        by_symbol: Dict[str, List[Signal]] = {}
        for signal in signals:
            symbol = signal.symbol or "unknown"
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(signal)

        # [大师共识四] Dalio象限权重调整
        regime_weights_adjustment: Optional[Dict[str, float]] = None
        if signals and signals[0].metadata.get("prices"):
            from app.core.market_regime import detect_regime, get_regime_theory_weights
            regime_result = detect_regime(
                signals[0].metadata["prices"],
                signals[0].metadata.get("volumes", []),
            )
            regime_weights_adjustment = get_regime_theory_weights(regime_result.regime)
            logger.info(
                f"WeightedFusion: Dalio regime adjustment applied "
                f"regime={regime_result.regime.value}, "
                f"confidence={regime_result.confidence:.4f}"
            )

        fused = []
        for symbol, symbol_signals in by_symbol.items():
            # 按方向分组
            by_direction: Dict[str, List[Signal]] = {}
            for signal in symbol_signals:
                direction = signal.direction
                if direction not in by_direction:
                    by_direction[direction] = []
                by_direction[direction].append(signal)

            # 计算每个方向的加权置信度
            direction_scores: Dict[str, float] = {}
            direction_contributors: Dict[str, List[str]] = {}

            for direction, dir_signals in by_direction.items():
                weighted_sum = 0.0
                weight_sum = 0.0
                contributors = []

                for signal in dir_signals:
                    # 获取引擎权重
                    engine_name = signal.source_engine
                    if regime_weights_adjustment:
                        regime_adj = regime_weights_adjustment.get(engine_name, 1.0)
                        weight = self.engine_weights.get(engine_name, self.default_weight) * regime_adj
                    else:
                        weight = self.engine_weights.get(engine_name, self.default_weight)

                    weighted_sum += signal.confidence * weight
                    weight_sum += weight
                    contributors.append(engine_name)

                if weight_sum > 0:
                    direction_scores[direction] = weighted_sum / weight_sum
                    direction_contributors[direction] = contributors

            # 选择得分最高的方向
            if not direction_scores:
                continue

            best_direction = max(direction_scores, key=direction_scores.get)
            best_score = direction_scores[best_direction]

            # [TOMAS v2.0] 相位连续性过滤
            # 计算平均相位连续性评分
            phase_scores = [
                r.phase_continuity for r in theory_results 
                if hasattr(r, 'phase_continuity')
            ]
            avg_phase = sum(phase_scores) / len(phase_scores) if phase_scores else 1.0
            
            # 相变奇点区：不输出信号
            if avg_phase < 0.3:
                logger.warning(f"Phase singularity: avg_PCS={avg_phase:.3f}, skipping fusion")
                continue
            
            # 过渡区：降低置信度
            if avg_phase < 0.7:
                best_score = best_score * (0.5 + 0.5 * (avg_phase / 0.7))
                logger.info(f"Phase transition: avg_PCS={avg_phase:.3f}, reducing confidence")
            
            # 仅输出置信度超过阈值的信号
            if best_score < 0.3:
                continue
            
            fused_signal = Signal(
                signal_id=f"sig-weighted-{symbol}",
                symbol=symbol,
                direction=best_direction,
                confidence=round(best_score, 4),
                source_engine="fusion_weighted",
                theory_name="Weighted Fusion",
                metadata={
                    "strategy": "weighted",
                    "direction_scores": direction_scores,
                    "contributors": direction_contributors.get(best_direction, []),
                    "phase_continuity": avg_phase,  # [TOMAS v2.0] 记录相位评分
                    "regime_weights_adjustment": regime_weights_adjustment,  # [大师共识四] 记录象限权重调整
                },
            )

            fused.append(FusedSignal(
                signal=fused_signal,
                strategy_name="weighted",
                contributor_count=len(direction_contributors.get(best_direction, [])),
                weighted_confidence=best_score,
            ))

        return fused

    def update_engine_weight(self, engine_name: str, weight: float) -> None:
        """更新引擎权重"""
        self.engine_weights[engine_name] = weight
        logger.info(f"WeightedFusion: updated weight for '{engine_name}' to {weight:.4f}")


class RiskParityFusionStrategy(FusionStrategy):
    """风险平价融合策略 — 各引擎风险贡献均衡

    借鉴Dalio全天候模型的核心思想：分散化是投资的圣杯。

    不按置信度加权（高置信度引擎可能高波动），
    而按风险贡献均衡加权（每个引擎对组合的波动贡献相等）。

    公式：
        weight_i = 1 / (σ_i × N)  其中 σ_i 是引擎i的历史波动率
        然后归一化：weight_i = weight_i / Σ(weight_j)

    对应大师共识二：风控比选股重要 — 风险平价是风控的系统化版本。
    """

    name = "risk_parity"

    def __init__(self, engine_weights: Optional[Dict[str, float]] = None) -> None:
        """初始化风险平价融合策略

        Args:
            engine_weights: 各引擎权重（外部覆盖），默认使用风险平价计算
        """
        self.engine_weights = engine_weights or {}
        # 默认引擎波动率（历史回测统计值，后续可动态更新）
        self.engine_volatility: Dict[str, float] = {
            "taiji": 0.15,      # 太极中心律波动率
            "spiral": 0.12,     # 螺旋律波动率
            "elliott_wave": 0.18,  # 波浪理论波动率（较高）
            "cycle_law": 0.10,  # 周期律波动率（较低）
            "dual_law": 0.14,   # 对偶律波动率
            "gann_angle": 0.16, # Gann角度波动率
            "bg_moving_average": 0.08,  # 均线波动率（最低）
        }

    def fuse(self, signals: List[Signal], theory_results: List[TheoryResult]) -> List[FusedSignal]:
        """风险平价融合"""
        if not signals:
            return []

        # 计算风险平价权重
        risk_parity_weights = self._calculate_risk_parity_weights(signals)

        # 按标的分组
        by_symbol: Dict[str, List[Signal]] = {}
        for signal in signals:
            symbol = signal.symbol or "unknown"
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(signal)

        fused = []
        for symbol, symbol_signals in by_symbol.items():
            by_direction: Dict[str, List[Signal]] = {}
            for signal in symbol_signals:
                direction = signal.direction
                if direction not in by_direction:
                    by_direction[direction] = []
                by_direction[direction].append(signal)

            direction_scores: Dict[str, float] = {}
            for direction, dir_signals in by_direction.items():
                weighted_sum = 0.0
                weight_sum = 0.0
                for signal in dir_signals:
                    engine_name = signal.source_engine
                    weight = risk_parity_weights.get(engine_name, 1.0 / len(signals))
                    weighted_sum += signal.confidence * weight
                    weight_sum += weight
                if weight_sum > 0:
                    direction_scores[direction] = weighted_sum / weight_sum

            if not direction_scores:
                continue

            best_direction = max(direction_scores, key=direction_scores.get)
            best_score = direction_scores[best_direction]

            if best_score < 0.3:
                continue

            # [TOMAS v2.0] PCS过滤（同WeightedFusionStrategy）
            phase_scores = [
                r.phase_continuity for r in theory_results
                if hasattr(r, 'phase_continuity')
            ]
            avg_phase = sum(phase_scores) / len(phase_scores) if phase_scores else 1.0
            if avg_phase < 0.3:
                continue
            if avg_phase < 0.7:
                best_score = best_score * (0.5 + 0.5 * (avg_phase / 0.7))

            fused_signal = Signal(
                signal_id=f"sig-rp-{symbol}",
                symbol=symbol,
                direction=best_direction,
                confidence=round(best_score, 4),
                source_engine="fusion_risk_parity",
                theory_name="Risk Parity Fusion",
                metadata={
                    "strategy": "risk_parity",
                    "risk_parity_weights": risk_parity_weights,
                    "direction_scores": direction_scores,
                    "phase_continuity": avg_phase,
                },
            )

            fused.append(FusedSignal(
                signal=fused_signal,
                strategy_name="risk_parity",
                contributor_count=len(by_direction.get(best_direction, [])),
                weighted_confidence=best_score,
            ))

        return fused

    def _calculate_risk_parity_weights(self, signals: List[Signal]) -> Dict[str, float]:
        """计算风险平价权重

        公式：weight_i = (1/σ_i) / Σ(1/σ_j)
        波动率高的引擎权重低，波动率低的引擎权重高。
        """
        engine_names = set(s.source_engine for s in signals)

        raw_weights: Dict[str, float] = {}
        for engine in engine_names:
            volatility = self.engine_volatility.get(engine, 0.15)  # 默认波动率
            raw_weights[engine] = 1.0 / volatility

        # 归一化
        total = sum(raw_weights.values())
        normalized = {k: v / total for k, v in raw_weights.items()}

        logger.info(f"RiskParity: weights = {normalized}")
        return normalized

    def update_engine_volatility(self, engine_name: str, volatility: float) -> None:
        """更新引擎波动率

        Args:
            engine_name: 引擎名称
            volatility: 新的波动率值
        """
        self.engine_volatility[engine_name] = volatility
        logger.info(f"RiskParity: updated volatility for '{engine_name}' to {volatility:.4f}")


def create_fusion_strategy(strategy_name: str, **kwargs) -> FusionStrategy:
    """创建融合策略实例

    Args:
        strategy_name: 策略名称 (and/or/weighted/risk_parity)
        **kwargs: 传递给策略构造函数的参数

    Returns:
        融合策略实例
    """
    strategy_map = {
        "and": AndFusionStrategy,
        "or": OrFusionStrategy,
        "weighted": WeightedFusionStrategy,
        "risk_parity": RiskParityFusionStrategy,
    }

    strategy_class = strategy_map.get(strategy_name, WeightedFusionStrategy)
    return strategy_class(**kwargs)
