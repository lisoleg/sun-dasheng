"""螺旋律引擎 - 鲁兆理论的螺旋线规律

鲁兆理论：股市运动遵循螺旋线规律，数学基础为斐波那契数列。
- 斐波那契回撤位：0.236, 0.382, 0.5, 0.618, 0.786
- 斐波那契扩展位：1.236, 1.382, 1.618, 2.0, 2.618
- 当价格触及斐波那契回撤/扩展位时标注为螺旋线关键点
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult
from app.core.topo_invariants import apply_phase_filter

# 斐波那契回撤比例
FIBONACCI_RETRACEMENT_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]

# 斐波那契扩展比例
FIBONACCI_EXTENSION_LEVELS = [1.236, 1.382, 1.618, 2.0, 2.618]

# 螺旋点检测容差（百分比）
SPIRAL_TOLERANCE = 0.005  # 0.5%容差


class SpiralEngine(TheoryEngine):
    """螺旋律引擎

    基于鲁兆理论的螺旋线规律分析方法：
    1. 识别趋势的高低点
    2. 计算斐波那契回撤位和扩展位
    3. 在K线数据中检测触及螺旋位的关键点
    4. 生成基于螺旋律的信号提示
    """

    @property
    def name(self) -> str:
        return "螺旋律"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行螺旋律分析"""
        if len(bars) < 10:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 识别趋势高低点
        high_point, low_point = self._find_swing_points(bars)

        # 计算斐波那契回撤位
        retracement_levels = self.calc_fibonacci_retracement(
            high_point["price"], low_point["price"]
        )

        # 计算斐波那契扩展位
        extension_levels = self.calc_fibonacci_extensions(
            high_point["price"], low_point["price"]
        )

        # 检测螺旋线关键点
        spiral_points = self.detect_spiral_points(
            bars, retracement_levels, extension_levels
        )

        # 生成信号提示
        hints = self._generate_hints(
            bars, retracement_levels, extension_levels, spiral_points
        )

        # 计算整体置信度
        confidence = self._calc_confidence(bars, spiral_points)

        # [TOMAS v2.0] 相位连续性过滤
        hints, confidence, pcs, is_sing = apply_phase_filter(
            hints, confidence, bars, log_prefix=self.name
        )

        return TheoryResult(
            theory_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            annotations={
                "high_point": high_point,
                "low_point": low_point,
                "retracement_levels": retracement_levels,
                "extension_levels": extension_levels,
                "spiral_points": spiral_points,
                "phase_continuity_score": pcs,
                "is_phase_singularity": is_sing,
            },
            hints=hints,
            confidence=confidence,
            phase_continuity=pcs,
            is_phase_valid=pcs >= 0.7,
        )

    def get_annotations(self, bars: List[Dict]) -> List[Dict]:
        """获取螺旋律图表标注"""
        if len(bars) < 10:
            return []

        high_point, low_point = self._find_swing_points(bars)
        retracement_levels = self.calc_fibonacci_retracement(
            high_point["price"], low_point["price"]
        )
        extension_levels = self.calc_fibonacci_extensions(
            high_point["price"], low_point["price"]
        )
        spiral_points = self.detect_spiral_points(
            bars, retracement_levels, extension_levels
        )

        annotations: List[Dict[str, Any]] = []

        # 回撤位标注
        for ratio, price in retracement_levels.items():
            annotations.append({
                "type": "fibonacci_retracement",
                "ratio": ratio,
                "price": price,
                "label": f"回撤 {ratio:.3f} = {price:.2f}",
                "color": "#4ECDC4",
            })

        # 扩展位标注
        for ratio, price in extension_levels.items():
            annotations.append({
                "type": "fibonacci_extension",
                "ratio": ratio,
                "price": price,
                "label": f"扩展 {ratio:.3f} = {price:.2f}",
                "color": "#FF6B6B",
            })

        # 螺旋关键点标注
        for point in spiral_points:
            annotations.append({
                "type": "spiral_point",
                "index": point["index"],
                "price": point["price"],
                "level_type": point["level_type"],
                "level_ratio": point["level_ratio"],
                "label": f"螺旋点 {point['level_type']} {point['level_ratio']:.3f}",
                "color": "#FFE66D",
            })

        return annotations

    def calc_fibonacci_retracement(
        self, high: float, low: float
    ) -> Dict[float, float]:
        """计算斐波那契回撤位

        回撤位公式：retracement = high - (high - low) * ratio

        Args:
            high: 趋势最高价
            low: 趋势最低价

        Returns:
            回撤位字典 {比例: 价格}
        """
        diff = high - low
        levels: Dict[float, float] = {}
        for ratio in FIBONACCI_RETRACEMENT_LEVELS:
            levels[ratio] = round(high - diff * ratio, 4)
        return levels

    def calc_fibonacci_extensions(
        self, high: float, low: float
    ) -> Dict[float, float]:
        """计算斐波那契扩展位

        扩展位公式（上升趋势）：extension = low + (high - low) * ratio
        扩展位用于预测突破后的目标位

        Args:
            high: 趋势最高价
            low: 趋势最低价

        Returns:
            扩展位字典 {比例: 价格}
        """
        diff = high - low
        levels: Dict[float, float] = {}
        for ratio in FIBONACCI_EXTENSION_LEVELS:
            levels[ratio] = round(low + diff * ratio, 4)
        return levels

    def detect_spiral_points(
        self,
        bars: List[Dict],
        retracement_levels: Dict[float, float],
        extension_levels: Dict[float, float],
        tolerance: float = SPIRAL_TOLERANCE,
    ) -> List[Dict[str, Any]]:
        """在K线数据中检测螺旋线关键点

        当价格触及斐波那契回撤/扩展位时（在容差范围内），
        标注该K线为螺旋线关键点。

        Args:
            bars: K线数据列表
            retracement_levels: 回撤位字典
            extension_levels: 扩展位字典
            tolerance: 容差比例（默认0.5%）

        Returns:
            螺旋关键点列表
        """
        spiral_points: List[Dict[str, Any]] = []

        for i, bar in enumerate(bars):
            close_price = float(bar.get("close", 0))
            low_price = float(bar.get("low", 0))
            high_price = float(bar.get("high", 0))

            # 检查是否触及回撤位
            for ratio, level_price in retracement_levels.items():
                # 使用最低价和收盘价检查回撤支撑
                if level_price > 0:
                    if (abs(low_price - level_price) / level_price <= tolerance or
                            abs(close_price - level_price) / level_price <= tolerance):
                        spiral_points.append({
                            "index": i,
                            "price": close_price,
                            "level_type": "retracement",
                            "level_ratio": ratio,
                            "level_price": level_price,
                            "direction": "support",
                        })
                        break  # 每根K线只标注最近的一个级别

            # 检查是否触及扩展位
            for ratio, level_price in extension_levels.items():
                # 使用最高价和收盘价检查扩展阻力
                if level_price > 0:
                    if (abs(high_price - level_price) / level_price <= tolerance or
                            abs(close_price - level_price) / level_price <= tolerance):
                        spiral_points.append({
                            "index": i,
                            "price": close_price,
                            "level_type": "extension",
                            "level_ratio": ratio,
                            "level_price": level_price,
                            "direction": "resistance",
                        })
                        break

        return spiral_points

    def _find_swing_points(self, bars: List[Dict]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """识别趋势的高低点

        在K线数据中寻找全局最高价和最低价作为斐波那契计算的基准点。

        Returns:
            (high_point, low_point) 高点和低点信息
        """
        high_price = float("-inf")
        low_price = float("inf")
        high_idx = 0
        low_idx = 0

        for i, bar in enumerate(bars):
            h = float(bar.get("high", 0))
            l = float(bar.get("low", 0))
            if h > high_price:
                high_price = h
                high_idx = i
            if l < low_price:
                low_price = l
                low_idx = i

        high_point = {"index": high_idx, "price": high_price}
        low_point = {"index": low_idx, "price": low_price}
        return high_point, low_point

    def _generate_hints(
        self,
        bars: List[Dict],
        retracement_levels: Dict[float, float],
        extension_levels: Dict[float, float],
        spiral_points: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """基于螺旋律生成信号提示

        当前价格接近回撤位时产生做多信号，
        接近扩展位时产生做空或止盈信号。
        """
        hints: List[Dict[str, Any]] = []

        if not bars:
            return hints

        current_price = float(bars[-1].get("close", 0))

        # 检查当前价格与回撤位的关系
        for ratio, level_price in sorted(retracement_levels.items()):
            if level_price > 0:
                distance_pct = abs(current_price - level_price) / level_price
                if distance_pct <= 0.02:  # 2%范围内
                    # 接近回撤位通常是支撑，倾向做多
                    confidence = 0.6 * (1 - distance_pct / 0.02)
                    hints.append({
                        "type": "spiral_retracement",
                        "direction": "long",
                        "confidence": round(confidence, 4),
                        "description": (
                            f"价格接近斐波那契回撤位 {ratio:.3f} "
                            f"({level_price:.2f})，距离{distance_pct:.2%}"
                        ),
                        "level_ratio": ratio,
                        "level_price": level_price,
                    })

        # 检查当前价格与扩展位的关系
        for ratio, level_price in sorted(extension_levels.items()):
            if level_price > 0:
                distance_pct = abs(current_price - level_price) / level_price
                if distance_pct <= 0.02:
                    # 接近扩展位通常是阻力，倾向做空或止盈
                    confidence = 0.6 * (1 - distance_pct / 0.02)
                    hints.append({
                        "type": "spiral_extension",
                        "direction": "short",
                        "confidence": round(confidence, 4),
                        "description": (
                            f"价格接近斐波那契扩展位 {ratio:.3f} "
                            f"({level_price:.2f})，距离{distance_pct:.2%}"
                        ),
                        "level_ratio": ratio,
                        "level_price": level_price,
                    })

        # 检查最近的螺旋关键点
        recent_spiral = [p for p in spiral_points if p["index"] >= len(bars) - 5]
        if recent_spiral:
            for point in recent_spiral:
                direction = "long" if point["direction"] == "support" else "short"
                hints.append({
                    "type": "spiral_touch",
                    "direction": direction,
                    "confidence": 0.55,
                    "description": (
                        f"近期价格触及螺旋{point['level_type']}位 "
                        f"{point['level_ratio']:.3f} ({point['level_price']:.2f})"
                    ),
                    "level_type": point["level_type"],
                    "level_ratio": point["level_ratio"],
                })

        return hints

    def _calc_confidence(
        self, bars: List[Dict], spiral_points: List[Dict[str, Any]]
    ) -> float:
        """计算整体置信度"""
        if not bars:
            return 0.0

        data_score = min(len(bars) / 30.0, 1.0)

        # 螺旋关键点密度权重
        point_density = len(spiral_points) / len(bars) if bars else 0
        point_score = min(point_density * 10, 1.0)

        # 最近螺旋点权重
        recent_score = 0.0
        recent_points = [p for p in spiral_points if p["index"] >= len(bars) - 10]
        if recent_points:
            recent_score = min(len(recent_points) / 3.0, 1.0)

        confidence = data_score * 0.3 + point_score * 0.3 + recent_score * 0.4
        return round(min(confidence, 1.0), 4)
