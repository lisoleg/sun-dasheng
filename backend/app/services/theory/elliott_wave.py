"""波浪理论引擎 - 鲁兆理论结合艾略特波浪理论的实践应用

鲁兆理论认为波浪理论是描述股市运动形态的重要工具：
- 推动浪（Impulse Waves）：由5个子浪组成（1-2-3-4-5）
  - 上升推动浪：高点递升 + 低点递升
  - 下降推动浪：高点递降 + 低点递降
- 调整浪（Corrective Waves）：由3个子浪组成（A-B-C）
  - 在推动浪之后的三浪回调结构
- 波浪标注：推动浪标注1-5，调整浪标注A-C
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult
from app.core.topo_invariants import apply_phase_filter
from app.core.cosmic_algorithm import apply_369_signal_filter

# ZigZag阈值用于识别极值点
ZIGZAG_THRESHOLD = 0.03  # 3%用于波浪识别（比太极中心律更敏感）


class ElliottWaveEngine(TheoryEngine):
    """波浪理论引擎

    基于鲁兆理论结合艾略特波浪理论的分析方法：
    1. 使用极值点序列识别推动浪（1-5浪）
    2. 在推动浪后识别调整浪（A-B-C）
    3. 为识别到的浪添加标签
    4. 判断当前处于第几浪，并生成信号提示
    """

    @property
    def name(self) -> str:
        return "波浪理论"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行波浪理论分析"""
        if len(bars) < 20:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 识别极值点
        pivots = self._find_pivots(bars)

        if len(pivots) < 5:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                annotations={"pivots": pivots, "current_wave": "unknown"},
                confidence=0.1,
            )

        # 识别推动浪
        impulse_waves = self.detect_impulse_waves(bars, pivots)

        # 识别调整浪
        corrective_waves = self.detect_corrective_waves(bars, pivots, impulse_waves)

        # 标注浪型
        labeled_waves = self.label_waves(impulse_waves, corrective_waves)

        # 判断当前浪位置
        current_wave = self._determine_current_wave(bars, impulse_waves, corrective_waves)

        # 生成信号提示
        hints = self._generate_hints(bars, impulse_waves, corrective_waves, current_wave)

        # 计算置信度
        confidence = self._calc_confidence(bars, impulse_waves, corrective_waves)

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
                "pivots": pivots,
                "impulse_waves": impulse_waves,
                "corrective_waves": corrective_waves,
                "labeled_waves": labeled_waves,
                "current_wave": current_wave,
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
        """获取波浪理论图表标注"""
        if len(bars) < 20:
            return []

        pivots = self._find_pivots(bars)
        impulse_waves = self.detect_impulse_waves(bars, pivots)
        corrective_waves = self.detect_corrective_waves(bars, pivots, impulse_waves)
        labeled_waves = self.label_waves(impulse_waves, corrective_waves)

        annotations: List[Dict[str, Any]] = []

        # 推动浪标注
        for wave in impulse_waves:
            wave_type = wave.get("type", "bullish")
            color = "#4ECDC4" if wave_type == "bullish" else "#FF6B6B"
            for i, point in enumerate(wave.get("points", [])):
                label = str(i + 1) if wave_type == "bullish" else str(i + 1)
                annotations.append({
                    "type": "impulse_wave",
                    "index": point.get("index", 0),
                    "price": point.get("price", 0),
                    "label": label,
                    "wave_type": wave_type,
                    "color": color,
                })

        # 调整浪标注
        for wave in corrective_waves:
            labels = ["A", "B", "C"]
            for i, point in enumerate(wave.get("points", [])):
                label = labels[i] if i < len(labels) else "?"
                annotations.append({
                    "type": "corrective_wave",
                    "index": point.get("index", 0),
                    "price": point.get("price", 0),
                    "label": label,
                    "color": "#95E1D3",
                })

        # 标注波浪连线
        for labeled in labeled_waves:
            annotations.append({
                "type": "wave_label",
                "wave_id": labeled.get("wave_id", ""),
                "label": labeled.get("label", ""),
                "start_index": labeled.get("start_index", 0),
                "end_index": labeled.get("end_index", 0),
                "direction": labeled.get("direction", ""),
            })

        return annotations

    def detect_impulse_waves(
        self, bars: List[Dict], pivots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别推动浪（1-5浪结构）

        上升推动浪判定条件：
        - 由6个极值点构成5浪（低-高-低-高-低-高）
        - 高点依次递升
        - 低点依次递升
        - 第3浪不能是最短的一浪

        下降推动浪判定条件：
        - 由6个极值点构成5浪（高-低-高-低-高-低）
        - 高点依次递降
        - 低点依次递降

        Args:
            bars: K线数据列表
            pivots: 极值点列表

        Returns:
            推动浪列表
        """
        impulse_waves: List[Dict[str, Any]] = []

        if len(pivots) < 6:
            return impulse_waves

        # 滑动窗口检测5浪结构（需要6个极值点）
        for start in range(len(pivots) - 5):
            window = pivots[start:start + 6]
            directions = [p["direction"] for p in window]

            # 检查上升推动浪：低-高-低-高-低-高
            if directions == ["low", "high", "low", "high", "low", "high"]:
                prices = [p["price"] for p in window]
                highs = [prices[1], prices[3], prices[5]]
                lows = [prices[0], prices[2], prices[4]]

                # 高点递升
                if highs[0] < highs[1] < highs[2]:
                    # 低点递升
                    if lows[0] < lows[1] < lows[2]:
                        # 第3浪不能最短
                        wave1_len = highs[0] - lows[0]
                        wave3_len = highs[1] - lows[1]
                        wave5_len = highs[2] - lows[2]
                        if wave3_len >= wave1_len and wave3_len >= wave5_len:
                            # 至少有一半满足
                            pass
                        # 宽松条件：第3浪不是三浪中最短的
                        if not (wave3_len <= wave1_len and wave3_len <= wave5_len):
                            impulse_waves.append({
                                "type": "bullish",
                                "points": window,
                                "wave1_high": highs[0],
                                "wave3_high": highs[1],
                                "wave5_high": highs[2],
                                "wave1_low": lows[0],
                                "wave3_low": lows[1],
                                "wave5_low": lows[2],
                            })

            # 检查下降推动浪：高-低-高-低-高-低
            elif directions == ["high", "low", "high", "low", "high", "low"]:
                prices = [p["price"] for p in window]
                highs = [prices[0], prices[2], prices[4]]
                lows = [prices[1], prices[3], prices[5]]

                # 高点递降
                if highs[0] > highs[1] > highs[2]:
                    # 低点递降
                    if lows[0] > lows[1] > lows[2]:
                        impulse_waves.append({
                            "type": "bearish",
                            "points": window,
                            "wave1_high": highs[0],
                            "wave3_high": highs[1],
                            "wave5_high": highs[2],
                            "wave1_low": lows[0],
                            "wave3_low": lows[1],
                            "wave5_low": lows[2],
                        })

        return impulse_waves

    def detect_corrective_waves(
        self,
        bars: List[Dict],
        pivots: List[Dict[str, Any]],
        impulse_waves: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """识别调整浪（ABC结构）

        在推动浪结束后，市场通常进入ABC三浪调整。
        A浪与趋势方向相反，B浪是反弹，C浪继续调整。

        判定条件：
        - 由3个极值点构成A-B-C
        - 在推动浪之后出现
        - C浪通常超过A浪终点（1:1或0.618关系）

        Args:
            bars: K线数据列表
            pivots: 极值点列表
            impulse_waves: 已识别的推动浪列表

        Returns:
            调整浪列表
        """
        corrective_waves: List[Dict[str, Any]] = []

        if len(pivots) < 3:
            return corrective_waves

        # 获取推动浪结束位置
        impulse_end_indices = set()
        for impulse in impulse_waves:
            if impulse.get("points"):
                last_point = impulse["points"][-1]
                impulse_end_indices.add(last_point["index"])

        # 在极值点序列中寻找ABC结构
        for start in range(len(pivots) - 2):
            window = pivots[start:start + 3]
            directions = [p["direction"] for p in window]

            # 上升趋势后的调整浪：高-低-高（但第二个高点低于第一个）
            if directions == ["high", "low", "high"]:
                prices = [p["price"] for p in window]
                # A浪下跌，B浪反弹不超过A浪起点，C浪可能继续下跌
                if prices[2] < prices[0] and prices[1] < prices[0]:
                    corrective_waves.append({
                        "type": "abc_correction",
                        "parent_direction": "bullish",
                        "points": window,
                        "wave_a_price": prices[0],
                        "wave_b_price": prices[1],
                        "wave_c_price": prices[2],
                    })

            # 下降趋势后的调整浪：低-高-低（但第二个低点高于第一个）
            elif directions == ["low", "high", "low"]:
                prices = [p["price"] for p in window]
                # A浪上涨，B浪回调不低于A浪起点，C浪可能继续上涨
                if prices[2] > prices[0] and prices[1] > prices[0]:
                    corrective_waves.append({
                        "type": "abc_correction",
                        "parent_direction": "bearish",
                        "points": window,
                        "wave_a_price": prices[0],
                        "wave_b_price": prices[1],
                        "wave_c_price": prices[2],
                    })

        return corrective_waves

    def label_waves(
        self,
        impulse_waves: List[Dict[str, Any]],
        corrective_waves: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """为识别到的浪添加标签

        推动浪标注1-5，调整浪标注A-C。

        Args:
            impulse_waves: 推动浪列表
            corrective_waves: 调整浪列表

        Returns:
            标注后的浪列表
        """
        labeled: List[Dict[str, Any]] = []

        # 推动浪标签
        for idx, wave in enumerate(impulse_waves):
            wave_type = wave.get("type", "bullish")
            points = wave.get("points", [])

            # 5浪结构标签
            impulse_labels = [1, 2, 3, 4, 5] if wave_type == "bullish" else [1, 2, 3, 4, 5]
            # 6个点对应5浪，每两个点为一浪
            for i in range(min(5, len(points) - 1)):
                label = str(impulse_labels[i])
                direction = "up" if i % 2 == 0 and wave_type == "bullish" else "down"
                if wave_type == "bearish":
                    direction = "down" if i % 2 == 0 else "up"

                labeled.append({
                    "wave_id": f"impulse-{idx}",
                    "label": label,
                    "start_index": points[i].get("index", 0),
                    "end_index": points[i + 1].get("index", 0) if i + 1 < len(points) else points[i].get("index", 0),
                    "direction": direction,
                    "type": "impulse",
                })

        # 调整浪标签
        for idx, wave in enumerate(corrective_waves):
            points = wave.get("points", [])
            abc_labels = ["A", "B", "C"]

            for i in range(min(3, len(points) - 1)):
                label = abc_labels[i]
                parent_dir = wave.get("parent_direction", "bullish")
                direction = "down" if (i != 1 and parent_dir == "bullish") else "up"
                if parent_dir == "bearish":
                    direction = "up" if (i != 1) else "down"

                labeled.append({
                    "wave_id": f"corrective-{idx}",
                    "label": label,
                    "start_index": points[i].get("index", 0),
                    "end_index": points[i + 1].get("index", 0) if i + 1 < len(points) else points[i].get("index", 0),
                    "direction": direction,
                    "type": "corrective",
                })

        return labeled

    def _find_pivots(
        self, bars: List[Dict], threshold: float = ZIGZAG_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """使用ZigZag方法识别极值点

        与太极中心律类似但阈值更小（3%），用于波浪识别。

        Args:
            bars: K线数据列表
            threshold: 价格变化阈值

        Returns:
            极值点列表
        """
        if len(bars) < 3:
            return []

        pivots: List[Dict[str, Any]] = []
        closes = [float(bar.get("close", 0)) for bar in bars]
        highs = [float(bar.get("high", 0)) for bar in bars]
        lows = [float(bar.get("low", 0)) for bar in bars]

        direction = 0  # 0=未确定, 1=上升, -1=下降
        last_pivot_idx = 0
        last_pivot_price = closes[0]

        for i in range(1, len(closes)):
            current_high = highs[i]
            current_low = lows[i]

            if direction == 0:
                change_pct = (current_high - last_pivot_price) / last_pivot_price if last_pivot_price != 0 else 0
                if change_pct >= threshold:
                    direction = 1
                    pivots.append({
                        "index": last_pivot_idx,
                        "price": lows[last_pivot_idx],
                        "direction": "low",
                    })
                    last_pivot_idx = i
                    last_pivot_price = current_high
                elif change_pct <= -threshold:
                    direction = -1
                    pivots.append({
                        "index": last_pivot_idx,
                        "price": highs[last_pivot_idx],
                        "direction": "high",
                    })
                    last_pivot_idx = i
                    last_pivot_price = current_low

            elif direction == 1:
                if current_high > last_pivot_price:
                    last_pivot_idx = i
                    last_pivot_price = current_high
                else:
                    change_pct = (last_pivot_price - current_low) / last_pivot_price if last_pivot_price != 0 else 0
                    if change_pct >= threshold:
                        pivots.append({
                            "index": last_pivot_idx,
                            "price": highs[last_pivot_idx],
                            "direction": "high",
                        })
                        direction = -1
                        last_pivot_idx = i
                        last_pivot_price = current_low

            elif direction == -1:
                if current_low < last_pivot_price:
                    last_pivot_idx = i
                    last_pivot_price = current_low
                else:
                    change_pct = (current_high - last_pivot_price) / last_pivot_price if last_pivot_price != 0 else 0
                    if change_pct >= threshold:
                        pivots.append({
                            "index": last_pivot_idx,
                            "price": lows[last_pivot_idx],
                            "direction": "low",
                        })
                        direction = 1
                        last_pivot_idx = i
                        last_pivot_price = current_high

        return pivots

    def _determine_current_wave(
        self,
        bars: List[Dict],
        impulse_waves: List[Dict[str, Any]],
        corrective_waves: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """判断当前处于第几浪

        根据最近识别的推动浪/调整浪和当前价格位置，
        判断当前处于波浪结构中的哪个位置。

        Returns:
            当前浪位置信息
        """
        current_idx = len(bars) - 1
        current_price = float(bars[-1].get("close", 0)) if bars else 0

        # 默认未知
        result: Dict[str, Any] = {
            "wave_type": "unknown",
            "wave_number": 0,
            "label": "未识别",
            "description": "无法判断当前浪位置",
        }

        # 查找最近的推动浪
        if impulse_waves:
            latest_impulse = impulse_waves[-1]
            points = latest_impulse.get("points", [])
            if points:
                last_point = points[-1]
                if current_idx > last_point.get("index", 0):
                    # 在推动浪之后，可能在调整浪中
                    result = {
                        "wave_type": "corrective",
                        "wave_number": 0,
                        "label": "调整浪",
                        "description": f"推动浪结束于索引{last_point['index']}，当前处于调整阶段",
                    }
                else:
                    # 在推动浪内部
                    for i in range(len(points) - 1):
                        if points[i].get("index", 0) <= current_idx <= points[i + 1].get("index", 0):
                            wave_num = i + 1
                            label = f"第{wave_num}浪"
                            if latest_impulse.get("type") == "bullish":
                                label += "(上升)" if wave_num % 2 == 1 else "(回调)"
                            else:
                                label += "(下跌)" if wave_num % 2 == 1 else "(反弹)"
                            result = {
                                "wave_type": "impulse",
                                "wave_number": wave_num,
                                "label": label,
                                "description": f"当前处于推动浪{label}",
                            }
                            break

        # 查找最近的调整浪
        if corrective_waves and result["wave_type"] == "unknown":
            latest_corrective = corrective_waves[-1]
            points = latest_corrective.get("points", [])
            if points:
                last_point = points[-1]
                if current_idx > last_point.get("index", 0):
                    result = {
                        "wave_type": "post_correction",
                        "wave_number": 0,
                        "label": "调整浪后",
                        "description": "调整浪结束，等待新的推动浪",
                    }
                else:
                    for i in range(len(points) - 1):
                        if points[i].get("index", 0) <= current_idx <= points[i + 1].get("index", 0):
                            labels = ["A", "B", "C"]
                            label = labels[i] if i < len(labels) else "?"
                            result = {
                                "wave_type": "corrective",
                                "wave_number": i + 1,
                                "label": f"{label}浪",
                                "description": f"当前处于调整浪{label}浪",
                            }
                            break

        return result

    def _generate_hints(
        self,
        bars: List[Dict],
        impulse_waves: List[Dict[str, Any]],
        corrective_waves: List[Dict[str, Any]],
        current_wave: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """基于波浪理论生成信号提示"""
        hints: List[Dict[str, Any]] = []

        wave_type = current_wave.get("wave_type", "unknown")
        wave_number = current_wave.get("wave_number", 0)
        label = current_wave.get("label", "未识别")

        if wave_type == "impulse":
            if wave_number == 1:
                # 第1浪，趋势刚启动
                hints.append({
                    "type": "wave_signal",
                    "direction": "long",
                    "confidence": 0.4,
                    "description": f"当前处于{label}，趋势初现，建议轻仓跟进",
                })
            elif wave_number == 3:
                # 第3浪通常是最强的
                hints.append({
                    "type": "wave_signal",
                    "direction": "long",
                    "confidence": 0.75,
                    "description": f"当前处于{label}，通常是主升浪，趋势最强",
                })
            elif wave_number == 5:
                # 第5浪可能见顶
                hints.append({
                    "type": "wave_signal",
                    "direction": "short",
                    "confidence": 0.5,
                    "description": f"当前处于{label}，推动浪可能接近尾声，注意风险",
                })
            elif wave_number in (2, 4):
                # 第2、4浪是回调
                hints.append({
                    "type": "wave_signal",
                    "direction": "long",
                    "confidence": 0.45,
                    "description": f"当前处于{label}回调中，可能是加仓机会",
                })

        elif wave_type == "corrective":
            abc_label = current_wave.get("label", "")
            if "C" in abc_label:
                # C浪通常是调整的最后一浪
                hints.append({
                    "type": "wave_signal",
                    "direction": "long",
                    "confidence": 0.55,
                    "description": f"当前处于调整浪{abc_label}，调整可能接近尾声",
                })
            elif "A" in abc_label:
                hints.append({
                    "type": "wave_signal",
                    "direction": "short",
                    "confidence": 0.5,
                    "description": f"当前处于调整浪{abc_label}，调整刚开始，注意控制风险",
                })

        elif wave_type == "post_correction":
            hints.append({
                "type": "wave_signal",
                "direction": "long",
                "confidence": 0.5,
                "description": "调整浪结束，新推动浪可能启动",
            })

        return hints

    def _calc_confidence(
        self,
        bars: List[Dict],
        impulse_waves: List[Dict[str, Any]],
        corrective_waves: List[Dict[str, Any]],
    ) -> float:
        """计算整体置信度"""
        if not bars:
            return 0.0

        data_score = min(len(bars) / 50.0, 1.0)

        # 波浪识别权重
        wave_score = 0.0
        if impulse_waves:
            wave_score = min(len(impulse_waves) * 0.3, 0.7)
        if corrective_waves:
            wave_score = min(wave_score + len(corrective_waves) * 0.15, 0.9)

        # 如果同时识别到推动浪和调整浪，置信度更高
        structure_score = 0.0
        if impulse_waves and corrective_waves:
            structure_score = 0.3

        confidence = data_score * 0.3 + wave_score * 0.4 + structure_score * 0.3
        return round(min(confidence, 1.0), 4)
