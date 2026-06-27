"""对偶律引擎 - 鲁兆理论对偶律

鲁兆理论：相邻K线收盘价对偶关系，上涨对偶下跌，形成阴阳转换点。
- 对偶关系：阳线（收盘价>开盘价）对偶阴线（收盘价<开盘价）
- 阴阳转换点：连续阳线后第一根阴线，或连续阴线后第一根阳线
- 输出：DUAL_BUY（阴转阳）/ DUAL_SELL（阳转阴）/ DUAL_HOLD
- 置信度：基于连续对偶次数（3次以上高置信度）
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult
from app.core.topo_invariants import apply_phase_filter
from app.core.cosmic_algorithm import apply_369_signal_filter

# 对偶置信度阈值
CONFIDENCE_THRESHOLD = 0.3

# 高置信度连续次数
HIGH_CONFIDENCE_STREAK = 3


class DualLawEngine(TheoryEngine):
    """对偶律引擎

    基于鲁兆理论的对偶律分析方法：
    1. 计算相邻K线的阴阳关系
    2. 识别阴阳转换点（连续同方向后的第一次反转）
    3. 根据连续对偶次数计算置信度
    4. 生成买卖信号
    """

    theory_name = "dual_law"

    @property
    def name(self) -> str:
        return "对偶律"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行对偶律分析

        Args:
            bars: K线数据列表

        Returns:
            TheoryResult 包含阴阳转换点和信号提示
        """
        if len(bars) < 5:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 计算阴阳关系
        yin_yang_series = self._calc_yin_yang_series(bars)

        # 识别阴阳转换点
        reversal_points = self._find_reversal_points(bars, yin_yang_series)

        # 计算连续对偶次数
        streak_counts = self._calc_streak_counts(yin_yang_series)

        # 生成信号提示
        hints = self._generate_hints(bars, yin_yang_series, reversal_points, streak_counts)

        # 计算整体置信度
        confidence = self._calc_confidence(reversal_points, streak_counts)

        # [TOMAS v2.0] 相位连续性过滤
        hints, confidence, pcs, is_sing = apply_phase_filter(
            hints, confidence, bars, log_prefix=self.name
        )

        # [宇宙算法] 369振动模态过滤（双重过滤）
        hints, confidence, vibration_score, mode_details = apply_369_signal_filter(
            hints, confidence, bars, log_prefix=self.name
        )

        return TheoryResult(
            theory_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            annotations={
                "yin_yang_series": yin_yang_series,
                "reversal_points": reversal_points,
                "streak_counts": streak_counts,
                "phase_continuity_score": pcs,
                "is_phase_singularity": is_sing,
                "vibration_369": mode_details,
            },
            hints=hints,
            confidence=confidence,
            phase_continuity=pcs,
            is_phase_valid=pcs >= 0.7,
        )

    def get_annotations(self, bars: List[Dict]) -> List[Dict]:
        """获取对偶律图表标注

        返回阴阳转换点标注，用于前端图表绘制。
        """
        if len(bars) < 5:
            return []

        yin_yang_series = self._calc_yin_yang_series(bars)
        reversal_points = self._find_reversal_points(bars, yin_yang_series)

        annotations: List[Dict[str, Any]] = []

        for point in reversal_points:
            idx = point["index"]
            if idx < len(bars):
                direction = point["direction"]
                annotations.append({
                    "type": "dual_reversal",
                    "index": idx,
                    "price": bars[idx].get("close", 0),
                    "direction": direction,
                    "label": f"对偶{'买入' if direction == 'buy' else '卖出'}",
                    "color": "#FF6B6B" if direction == "sell" else "#4ECDC4",
                })

        return annotations

    def _calc_yin_yang_series(self, bars: List[Dict]) -> List[str]:
        """计算阴阳关系序列

        阳线：收盘价 >= 开盘价（或相比前收盘上涨）
        阴线：收盘价 < 开盘价（或相比前收盘下跌）

        Returns:
            阴阳序列列表，每个元素为 "yang" 或 "yin"
        """
        series = []
        for i, bar in enumerate(bars):
            close = float(bar.get("close", 0))
            open_price = float(bar.get("open", 0))

            # 使用收盘价与开盘价的比较来判断阴阳
            if close >= open_price:
                series.append("yang")
            else:
                series.append("yin")

        return series

    def _find_reversal_points(
        self, bars: List[Dict], yin_yang_series: List[str]
    ) -> List[Dict[str, Any]]:
        """识别阴阳转换点

        阴阳转换点定义：
        - 阴转阳：前一根为阴线，当前为阳线 -> 潜在买入点
        - 阳转阴：前一根为阳线，当前为阴线 -> 潜在卖出点

        Args:
            bars: K线数据列表
            yin_yang_series: 阴阳关系序列

        Returns:
            转换点列表，每项包含 index, direction, type
        """
        reversal_points = []

        for i in range(1, len(yin_yang_series)):
            prev = yin_yang_series[i - 1]
            curr = yin_yang_series[i]

            if prev != curr:
                # 发生阴阳转换
                if prev == "yin" and curr == "yang":
                    # 阴转阳 -> 买入信号
                    reversal_points.append({
                        "index": i,
                        "direction": "buy",
                        "type": "yin_to_yang",
                    })
                elif prev == "yang" and curr == "yin":
                    # 阳转阴 -> 卖出信号
                    reversal_points.append({
                        "index": i,
                        "direction": "sell",
                        "type": "yang_to_yin",
                    })

        return reversal_points

    def _calc_streak_counts(self, yin_yang_series: List[str]) -> List[int]:
        """计算连续对偶次数

        遍历阴阳序列，计算当前连续同向的次数。
        用于评估信号的强度：连续次数越多，反转信号越强。

        Returns:
            每个位置对应的连续次数列表
        """
        if not yin_yang_series:
            return []

        streaks = [1]
        for i in range(1, len(yin_yang_series)):
            if yin_yang_series[i] == yin_yang_series[i - 1]:
                streaks.append(streaks[-1] + 1)
            else:
                streaks.append(1)

        return streaks

    def _generate_hints(
        self,
        bars: List[Dict],
        yin_yang_series: List[str],
        reversal_points: List[Dict[str, Any]],
        streak_counts: List[int],
    ) -> List[Dict[str, Any]]:
        """基于阴阳转换生成信号提示

        当识别到阴阳转换点时，根据连续次数生成买卖信号。
        - 连续阴线后转阳：买入信号，连续次数越多置信度越高
        - 连续阳线后转阴：卖出信号，连续次数越多置信度越高
        """
        hints = []
        current_idx = len(bars) - 1

        # 检查最近是否发生阴阳转换
        recent_reversals = [p for p in reversal_points if p["index"] >= current_idx - 3]

        for reversal in recent_reversals:
            idx = reversal["index"]
            streak = streak_counts[idx] if idx < len(streak_counts) else 1

            # 根据连续次数计算置信度
            if streak >= HIGH_CONFIDENCE_STREAK:
                confidence = 0.7
            elif streak >= 2:
                confidence = 0.5
            else:
                confidence = 0.35

            direction = "LONG" if reversal["direction"] == "buy" else "SHORT"

            hints.append({
                "type": "dual_reversal",
                "direction": direction,
                "confidence": confidence,
                "description": (
                    f"对偶律信号：{reversal['type']}，"
                    f"连续{streak}根{'阳' if reversal['type'] == 'yin_to_yang' else '阴'}线后反转"
                ),
                "index": idx,
                "streak": streak,
            })

        # 如果没有近期转换，检查当前是否处于连续状态
        if not recent_reversals and len(streak_counts) > 0:
            current_streak = streak_counts[-1]
            current_yin_yang = yin_yang_series[-1]

            if current_streak >= 5:
                # 连续多根同色K线，预警即将反转
                hints.append({
                    "type": "dual_streak_warning",
                    "direction": "HOLD",
                    "confidence": 0.3,
                    "description": (
                        f"连续{current_streak}根{current_yin_yang}线，"
                        "关注即将可能出现的反转信号"
                    ),
                    "streak": current_streak,
                })

        return hints

    def _calc_confidence(
        self,
        reversal_points: List[Dict[str, Any]],
        streak_counts: List[int],
    ) -> float:
        """计算整体置信度

        基于数据充分性和信号强度综合评估。
        """
        if not reversal_points:
            return 0.0

        # 数据充分性权重
        data_score = min(len(streak_counts) / 20.0, 1.0)

        # 转换点数量权重
        reversal_score = min(len(reversal_points) / 5.0, 1.0)

        # 最大连续次数权重（连续越多，反转信号越强）
        max_streak = max(streak_counts) if streak_counts else 0
        streak_score = min(max_streak / 10.0, 1.0)

        # 近期转换点权重
        recent_reversals = [p for p in reversal_points if True]
        recent_score = min(len(recent_reversals) / 3.0, 1.0) if recent_reversals else 0

        confidence = data_score * 0.2 + reversal_score * 0.3 + streak_score * 0.3 + recent_score * 0.2
        return round(min(confidence, 1.0), 4)
