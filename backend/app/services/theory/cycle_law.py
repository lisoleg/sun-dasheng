"""周期律引擎 - 鲁兆理论周期律

鲁兆理论：高低点周期重复，识别最近3个周期长度，预测下一个转折点。
- 周期识别：从高低点序列计算周期长度
- 周期预测：基于最近N个周期长度的平均值预测下一个转折点
- 输出：CYCLE_TOP / CYCLE_BOTTOM / CYCLE_HOLD
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult
from app.core.topo_invariants import apply_phase_filter

# 最小周期长度（K线数）
MIN_CYCLE_LENGTH = 5

# 最大周期长度（K线数）
MAX_CYCLE_LENGTH = 100

# 周期预测容差（K线数）
CYCLE_TOLERANCE = 3


class CycleLawEngine(TheoryEngine):
    """周期律引擎

    基于鲁兆理论的周期律分析方法：
    1. 识别显著高低点
    2. 计算周期长度序列
    3. 预测下一个转折点
    4. 生成买卖信号
    """

    theory_name = "cycle_law"

    @property
    def name(self) -> str:
        return "周期律"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行周期律分析

        Args:
            bars: K线数据列表

        Returns:
            TheoryResult 包含周期长度和转折点预测
        """
        if len(bars) < 20:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 识别显著高低点
        swing_points = self._find_swing_points(bars)

        # 计算周期长度
        cycle_lengths = self._calc_cycle_lengths(swing_points)

        # 预测下一个转折点
        next_turn = self._predict_next_turn(bars, swing_points, cycle_lengths)

        # 生成信号提示
        hints = self._generate_hints(bars, swing_points, cycle_lengths, next_turn)

        # 计算整体置信度
        confidence = self._calc_confidence(cycle_lengths, next_turn)

        # [TOMAS v2.0] 相位连续性过滤
        hints, confidence, pcs, is_sing = apply_phase_filter(
            hints, confidence, bars, log_prefix=self.name
        )

        return TheoryResult(
            theory_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            annotations={
                "swing_points": swing_points,
                "cycle_lengths": cycle_lengths,
                "next_turn": next_turn,
                "phase_continuity_score": pcs,
                "is_phase_singularity": is_sing,
            },
            hints=hints,
            confidence=confidence,
            phase_continuity=pcs,
            is_phase_valid=pcs >= 0.7,
        )

    def get_annotations(self, bars: List[Dict]) -> List[Dict]:
        """获取周期律图表标注"""
        if len(bars) < 20:
            return []

        swing_points = self._find_swing_points(bars)
        cycle_lengths = self._calc_cycle_lengths(swing_points)
        next_turn = self._predict_next_turn(bars, swing_points, cycle_lengths)

        annotations: List[Dict[str, Any]] = []

        # 高低点标注
        for point in swing_points:
            idx = point["index"]
            if idx < len(bars):
                annotations.append({
                    "type": "cycle_swing",
                    "index": idx,
                    "price": point["price"],
                    "direction": point["direction"],
                    "label": f"周期{'高点' if point['direction'] == 'high' else '低点'}",
                    "color": "#FF6B6B" if point["direction"] == "high" else "#4ECDC4",
                })

        # 预测转折点标注
        if next_turn and "index" in next_turn:
            idx = next_turn["index"]
            if 0 <= idx < len(bars):
                annotations.append({
                    "type": "cycle_prediction",
                    "index": idx,
                    "price": bars[idx].get("close", 0) if idx < len(bars) else 0,
                    "direction": next_turn["direction"],
                    "label": f"预测转折 ({next_turn['direction']})",
                    "color": "#FFE66D",
                })

        return annotations

    def _find_swing_points(self, bars: List[Dict]) -> List[Dict[str, Any]]:
        """识别显著高低点

        使用ZigZag类似方法识别显著的高低点。
        与太极中心律不同，周期律关注所有显著高低点（不只太极中心）。

        Returns:
            高低点列表，按index排序
        """
        if len(bars) < 10:
            return []

        swings = []
        closes = [float(bar.get("close", 0)) for bar in bars]
        highs = [float(bar.get("high", 0)) for bar in bars]
        lows = [float(bar.get("low", 0)) for bar in bars]

        # 使用简单方法：寻找局部高低点
        for i in range(2, len(closes) - 2):
            # 局部高点：中间K线的最高价高于两侧
            if (highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and
                highs[i] > highs[i + 1] and highs[i] > highs[i + 2]):
                swings.append({
                    "index": i,
                    "price": highs[i],
                    "direction": "high",
                })
            # 局部低点：中间K线的最低价低于两侧
            elif (lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and
                  lows[i] < lows[i + 1] and lows[i] < lows[i + 2]):
                swings.append({
                    "index": i,
                    "price": lows[i],
                    "direction": "low",
                })

        return sorted(swings, key=lambda x: x["index"])

    def _calc_cycle_lengths(self, swing_points: List[Dict[str, Any]]) -> List[int]:
        """计算周期长度

        周期长度定义：相邻同方向高低点之间的K线数。
        例如：两个相邻低点之间的K线数构成一个周期。

        Returns:
            周期长度列表
        """
        if len(swing_points) < 2:
            return []

        # 按方向分组
        high_points = [p for p in swing_points if p["direction"] == "high"]
        low_points = [p for p in swing_points if p["direction"] == "low"]

        cycle_lengths = []

        # 计算高点之间的周期
        for i in range(1, len(high_points)):
            length = high_points[i]["index"] - high_points[i - 1]["index"]
            if MIN_CYCLE_LENGTH <= length <= MAX_CYCLE_LENGTH:
                cycle_lengths.append(length)

        # 计算低点之间的周期
        for i in range(1, len(low_points)):
            length = low_points[i]["index"] - low_points[i - 1]["index"]
            if MIN_CYCLE_LENGTH <= length <= MAX_CYCLE_LENGTH:
                cycle_lengths.append(length)

        return cycle_lengths

    def _predict_next_turn(
        self,
        bars: List[Dict],
        swing_points: List[Dict[str, Any]],
        cycle_lengths: List[int],
    ) -> Dict[str, Any]:
        """预测下一个转折点

        基于最近N个周期长度的平均值，预测下一个转折点的位置。
        使用指数移动平均给近期周期更高权重。

        Returns:
            预测结果字典，包含 index, direction, confidence
        """
        if not cycle_lengths or not swing_points:
            return {}

        # 计算平均周期长度（使用最近3个周期）
        recent_cycles = cycle_lengths[-3:]
        avg_cycle = sum(recent_cycles) / len(recent_cycles)

        # 最后一个高低点
        last_swing = swing_points[-1]
        last_idx = last_swing["index"]

        # 预测下一个转折点位置
        predicted_idx = int(last_idx + avg_cycle)

        # 判断方向（与最后一个高低点相反）
        predicted_direction = "high" if last_swing["direction"] == "low" else "low"

        # 检查预测位置是否在合理范围内
        if predicted_idx < len(bars):
            # 已经过去的预测，不发出信号
            return {}

        # 计算距离（还有多少K线到达预测位置）
        distance = predicted_idx - len(bars)

        return {
            "index": predicted_idx,
            "direction": "LONG" if predicted_direction == "low" else "SHORT",
            "avg_cycle": avg_cycle,
            "distance": distance,
            "last_swing_index": last_idx,
            "last_swing_direction": last_swing["direction"],
        }

    def _generate_hints(
        self,
        bars: List[Dict],
        swing_points: List[Dict[str, Any]],
        cycle_lengths: List[int],
        next_turn: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """基于周期律生成信号提示

        当接近预测转折点时产生买卖信号。
        """
        hints = []
        current_idx = len(bars) - 1

        if not next_turn:
            return hints

        distance = next_turn.get("distance", float("inf"))

        # 如果距离预测转折点较近（在容差范围内）
        if 0 <= distance <= CYCLE_TOLERANCE:
            confidence = 0.6 * (1 - distance / CYCLE_TOLERANCE)
            direction = next_turn["direction"]

            hints.append({
                "type": "cycle_turn_prediction",
                "direction": direction,
                "confidence": round(confidence, 4),
                "description": (
                    f"周期律预测：接近{'低点买入' if direction == 'LONG' else '高点卖出'}窗口，"
                    f"平均周期{next_turn.get('avg_cycle', 0):.1f}根K线"
                ),
                "distance": distance,
                "avg_cycle": next_turn.get("avg_cycle", 0),
            })

        # 如果刚经过一个高低点
        recent_swings = [p for p in swing_points if current_idx - p["index"] <= 5]
        for swing in recent_swings:
            direction = "LONG" if swing["direction"] == "low" else "SHORT"
            hints.append({
                "type": "cycle_recent_swing",
                "direction": direction,
                "confidence": 0.4,
                "description": (
                    f"近期出现周期{swing['direction']}点，"
                    f"预计{next_turn.get('avg_cycle', 0):.0f}根K线后转折"
                ),
                "index": swing["index"],
            })

        return hints

    def _calc_confidence(
        self,
        cycle_lengths: List[int],
        next_turn: Dict[str, Any],
    ) -> float:
        """计算整体置信度"""
        if not cycle_lengths:
            return 0.0

        # 周期稳定性权重（周期长度变化越小越稳定）
        if len(cycle_lengths) >= 2:
            import statistics
            try:
                stdev = statistics.stdev(cycle_lengths)
                mean = statistics.mean(cycle_lengths)
                stability = 1 - min(stdev / mean, 1.0) if mean > 0 else 0
            except statistics.StatisticsError:
                stability = 0.5
        else:
            stability = 0.3

        # 周期数量权重
        count_score = min(len(cycle_lengths) / 5.0, 1.0)

        # 预测距离权重（越接近预测点置信度越高）
        distance = next_turn.get("distance", float("inf")) if next_turn else float("inf")
        if distance <= CYCLE_TOLERANCE:
            distance_score = 1 - distance / CYCLE_TOLERANCE
        else:
            distance_score = 0.0

        confidence = stability * 0.4 + count_score * 0.3 + distance_score * 0.3
        return round(min(confidence, 1.0), 4)
