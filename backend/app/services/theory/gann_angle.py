"""江恩角度线引擎 - 鲁兆理论江恩角度线

鲁兆理论：价格与时间的平方根关系，1x1线是最重要支撑/阻力。
- 江恩角度线：价格与时间的比例关系，关键角度为 1x1, 1x2, 2x1
- 1x1线：价格变化等于时间变化（45度角），最重要的支撑/阻力
- 输出：GANN_SUPPORT / GANN_RESISTANCE / GANN_HOLD
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult
from app.core.topo_invariants import apply_phase_filter
from app.core.cosmic_algorithm import apply_369_signal_filter

# 江恩关键角度
GANN_ANGLES = [
    (1, 1),  # 1x1 - 45度，最重要
    (1, 2),  # 1x2 - 26.25度
    (2, 1),  # 2x1 - 63.75度
    (1, 4),  # 1x4 - 14度
    (4, 1),  # 4x1 - 76度
]

# 角度线容差（价格百分比）
GANN_TOLERANCE = 0.01  # 1%容差


class GannAngleEngine(TheoryEngine):
    """江恩角度线引擎

    基于江恩角度线的分析方法：
    1. 寻找显著起点（重要高低点）
    2. 从起点绘制江恩角度线
    3. 判断当前价格与角度线的关系
    4. 生成支撑/阻力信号
    """

    theory_name = "gann_angle"

    @property
    def name(self) -> str:
        return "江恩角度线"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行江恩角度线分析

        Args:
            bars: K线数据列表

        Returns:
            TheoryResult 包含角度线和信号提示
        """
        if len(bars) < 20:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 寻找角度线起点（最近的重要高低点）
        start_point = self._find_start_point(bars)

        if not start_point:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 计算江恩角度线
        gann_lines = self._calc_gann_lines(bars, start_point)

        # 判断当前价格位置
        price_position = self._analyze_price_position(bars, gann_lines)

        # 生成信号提示
        hints = self._generate_hints(bars, gann_lines, price_position)

        # 计算整体置信度
        confidence = self._calc_confidence(gann_lines, price_position)

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
                "start_point": start_point,
                "gann_lines": gann_lines,
                "price_position": price_position,
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
        """获取江恩角度线图表标注"""
        if len(bars) < 20:
            return []

        start_point = self._find_start_point(bars)
        if not start_point:
            return []

        gann_lines = self._calc_gann_lines(bars, start_point)

        annotations: List[Dict[str, Any]] = []

        # 起点标注
        start_idx = start_point["index"]
        if start_idx < len(bars):
            annotations.append({
                "type": "gann_start",
                "index": start_idx,
                "price": start_point["price"],
                "direction": start_point["direction"],
                "label": f"江恩起点 ({start_point['direction']})",
                "color": "#FF6B6B" if start_point["direction"] == "high" else "#4ECDC4",
            })

        # 角度线标注
        current_idx = len(bars) - 1
        for line in gann_lines:
            angle_name = line["name"]
            current_price = line["prices"].get(current_idx, None)
            if current_price:
                annotations.append({
                    "type": "gann_line",
                    "angle_name": angle_name,
                    "current_price": current_price,
                    "label": f"江恩{angle_name}: {current_price:.2f}",
                    "color": "#FFE66D" if "1x1" in angle_name else "#95E1D3",
                })

        return annotations

    def _find_start_point(self, bars: List[Dict]) -> Dict[str, Any]:
        """寻找江恩角度线的起点

        江恩角度线通常从重要高低点出发。
        选择最近的重要高低点作为起点。

        Returns:
            起点信息字典，包含 index, price, direction
        """
        if len(bars) < 10:
            return {}

        closes = [float(bar.get("close", 0)) for bar in bars]
        highs = [float(bar.get("high", 0)) for bar in bars]
        lows = [float(bar.get("low", 0)) for bar in bars]

        # 寻找最近20根K线内的最高点和最低点
        recent_start = max(0, len(bars) - 20)
        recent_high = max(range(recent_start, len(highs)), key=lambda i: highs[i])
        recent_low = min(range(recent_start, len(lows)), key=lambda i: lows[i])

        # 选择离当前更近的高低点
        high_distance = len(bars) - 1 - recent_high
        low_distance = len(bars) - 1 - recent_low

        # 优先选择距离适中的点（不要太近也不要太远）
        if high_distance <= 10 and (high_distance <= low_distance or low_distance > 15):
            return {
                "index": recent_high,
                "price": highs[recent_high],
                "direction": "high",
            }
        else:
            return {
                "index": recent_low,
                "price": lows[recent_low],
                "direction": "low",
            }

    def _calc_gann_lines(
        self, bars: List[Dict], start_point: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """计算江恩角度线价格序列

        江恩角度线公式：price = start_price + slope * (index - start_index)
        其中 slope 由角度决定。

        Args:
            bars: K线数据列表
            start_point: 起点信息

        Returns:
            角度线列表，每条线包含 name, prices(dict)
        """
        start_idx = start_point["index"]
        start_price = start_point["price"]
        direction = start_point["direction"]

        gann_lines = []
        total_bars = len(bars)

        for numer, denom in GANN_ANGLES:
            # 计算斜率
            # 江恩角度线：价格变化 = (numer/denom) * 时间变化 * 价格单位
            # 简化：使用价格波动的平均值作为价格单位
            closes = [float(bar.get("close", 0)) for bar in bars]
            price_unit = (max(closes) - min(closes)) / len(closes) if len(closes) > 1 else 1.0

            slope = (numer / denom) * price_unit

            # 如果起点是高点，角度线向下；如果是低点，向上
            if direction == "high":
                slope = -slope

            # 计算该角度线的价格序列
            prices = {}
            for i in range(start_idx, total_bars):
                bar_diff = i - start_idx
                price = start_price + slope * bar_diff
                if price > 0:
                    prices[i] = price

            gann_lines.append({
                "name": f"{numer}x{denom}",
                "slope": slope,
                "prices": prices,
            })

        return gann_lines

    def _analyze_price_position(
        self, bars: List[Dict], gann_lines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析当前价格与江恩角度线的关系

        Returns:
            位置信息字典，包含 nearest_line, distance, position_type
        """
        if not bars or not gann_lines:
            return {}

        current_idx = len(bars) - 1
        current_close = float(bars[-1].get("close", 0))

        nearest_line = None
        nearest_distance = float("inf")
        position_type = "unknown"

        for line in gann_lines:
            prices = line["prices"]
            if current_idx in prices:
                line_price = prices[current_idx]
                distance = abs(current_close - line_price) / line_price

                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_line = line["name"]

                    # 判断位置类型
                    if current_close > line_price:
                        position_type = "above"
                    elif current_close < line_price:
                        position_type = "below"
                    else:
                        position_type = "on"

        return {
            "current_price": current_close,
            "nearest_line": nearest_line,
            "nearest_distance_pct": nearest_distance if nearest_distance != float("inf") else None,
            "position_type": position_type,
        }

    def _generate_hints(
        self,
        bars: List[Dict],
        gann_lines: List[Dict[str, Any]],
        price_position: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """基于江恩角度线生成信号提示

        当价格接近或触及江恩角度线时产生信号。
        - 1x1线是最重要的支撑/阻力
        - 价格在角度线上方为强势，下方为弱势
        """
        hints = []

        if not price_position:
            return hints

        nearest_line = price_position.get("nearest_line")
        distance_pct = price_position.get("nearest_distance_pct")
        position_type = price_position.get("position_type")
        current_price = price_position.get("current_price", 0)

        # 如果接近某条角度线
        if nearest_line and distance_pct is not None and distance_pct <= GANN_TOLERANCE:
            # 判断信号方向
            # 从低点出发的角度线，价格在线附近为支撑（买入）
            # 从高点出发的角度线，价格在线附近为阻力（卖出）
            start_point = self._find_start_point(bars)
            direction = "HOLD"

            if start_point:
                if start_point["direction"] == "low" and position_type in ("on", "above"):
                    direction = "LONG"
                elif start_point["direction"] == "high" and position_type in ("on", "below"):
                    direction = "SHORT"

            # 1x1线权重最高
            confidence = 0.7 if "1x1" in nearest_line else 0.5
            confidence *= (1 - distance_pct / GANN_TOLERANCE)

            hints.append({
                "type": "gann_touch",
                "direction": direction,
                "confidence": round(confidence, 4),
                "description": (
                    f"价格接近江恩{nearest_line}线"
                    f"（距离{distance_pct:.2%}），"
                    f"{'支撑' if direction == 'LONG' else '阻力'}信号"
                ),
                "line": nearest_line,
                "distance_pct": distance_pct,
            })

        # 判断趋势强度
        if position_type == "above" and nearest_line:
            hints.append({
                "type": "gann_trend_strength",
                "direction": "LONG",
                "confidence": 0.4,
                "description": f"价格在江恩{nearest_line}线上方，趋势偏强",
            })
        elif position_type == "below" and nearest_line:
            hints.append({
                "type": "gann_trend_weakness",
                "direction": "SHORT",
                "confidence": 0.4,
                "description": f"价格在江恩{nearest_line}线下方，趋势偏弱",
            })

        return hints

    def _calc_confidence(
        self,
        gann_lines: List[Dict[str, Any]],
        price_position: Dict[str, Any],
    ) -> float:
        """计算整体置信度"""
        if not gann_lines or not price_position:
            return 0.0

        # 数据充分性权重
        data_score = 0.5

        # 角度线数量权重
        line_score = min(len(gann_lines) / 5.0, 1.0)

        # 距离权重（越接近角度线置信度越高）
        distance_pct = price_position.get("nearest_distance_pct")
        if distance_pct is not None:
            distance_score = max(0, 1 - distance_pct / GANN_TOLERANCE)
        else:
            distance_score = 0.0

        # 1x1线权重（如果存在1x1线，增加置信度）
        has_1x1 = any("1x1" in line["name"] for line in gann_lines)
        gann_score = 0.3 if has_1x1 else 0.0

        confidence = data_score * 0.2 + line_score * 0.2 + distance_score * 0.4 + gann_score * 0.2
        return round(min(confidence, 1.0), 4)
