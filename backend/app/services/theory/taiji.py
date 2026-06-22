"""太极中心律引擎 - 鲁兆理论核心

鲁兆理论核心思想：太极是股市生命运动的中心主宰。
- 太极中心点：趋势的极值点（最高或最低），该点对后续时空产生控制作用
- DNA29主宰数字：从重要高低点出发，每29个交易日为一个关键时间窗口
- DNA13次级数字：从太极中心点出发，每13个交易日为次级窗口
- ZigZag方法识别显著转折点，标注为太极中心点
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult

# DNA主宰数字常量
DNA_29 = 29  # 主宰数字29，鲁兆理论中的核心周期
DNA_13 = 13  # 次级数字13

# ZigZag默认阈值（价格变化百分比）
ZIGZAG_THRESHOLD = 0.05  # 5%


class TaijiEngine(TheoryEngine):
    """太极中心律引擎

    基于鲁兆理论的太极中心律分析方法：
    1. 寻找太极中心点（趋势极值点）
    2. 计算DNA29主宰数字时间窗口
    3. 计算DNA13次级时间窗口
    4. 判断当前价格位置是否处于关键时间窗口
    """

    @property
    def name(self) -> str:
        return "太极中心律"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行太极中心律分析

        Args:
            bars: K线数据列表

        Returns:
            TheoryResult 包含太极中心点、DNA窗口和信号提示
        """
        if len(bars) < 10:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 寻找太极中心点
        taiji_centers = self.find_taiji_centers(bars)

        # 计算DNA29时间窗口
        dna29_windows = self.calc_dna29_windows(bars, taiji_centers)

        # 计算DNA13时间窗口
        dna13_windows = self.calc_dna13_windows(bars, taiji_centers)

        # 生成信号提示
        hints = self._generate_hints(bars, taiji_centers, dna29_windows, dna13_windows)

        # 计算整体置信度
        confidence = self._calc_confidence(bars, taiji_centers, dna29_windows, dna13_windows)

        # [TOMAS v2.0] 相位连续性过滤
        from app.core.topo_invariants import phase_continuity_score, detect_phase_singularity
        import numpy as np
        
        closes = np.array([float(bar.get("close", 0)) for bar in bars])
        pcs = phase_continuity_score(closes, window=30)
        singularity = detect_phase_singularity(closes)
        
        # 根据相位连续性调整信号
        if pcs < 0.3 or singularity.get("is_singularity", False):
            # 相变奇点区：清空信号，强制熔断
            hints = []
            confidence = confidence * 0.1  # 大幅降低置信度
            logger.warning(f"Phase singularity detected: PCS={pcs:.3f}, clearing all hints")
        elif pcs < 0.7:
            # 过渡区：降低置信度
            confidence = confidence * 0.5
            for hint in hints:
                hint["confidence"] *= 0.5
            logger.info(f"Phase transition zone: PCS={pcs:.3f}, reducing confidence")
        
        return TheoryResult(
            theory_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            annotations={
                "taiji_centers": taiji_centers,
                "dna29_windows": dna29_windows,
                "dna13_windows": dna13_windows,
                "phase_continuity_score": pcs,
                "is_phase_singularity": singularity.get("is_singularity", False),
            },
            hints=hints,
            confidence=confidence,
            phase_continuity=pcs,
            is_phase_valid=pcs >= 0.7,
        )

    def get_annotations(self, bars: List[Dict]) -> List[Dict]:
        """获取太极中心律图表标注

        返回太极中心点标注和DNA时间窗口标注，用于前端图表绘制。
        """
        if len(bars) < 10:
            return []

        taiji_centers = self.find_taiji_centers(bars)
        dna29_windows = self.calc_dna29_windows(bars, taiji_centers)
        dna13_windows = self.calc_dna13_windows(bars, taiji_centers)

        annotations: List[Dict[str, Any]] = []

        # 太极中心点标注
        for center in taiji_centers:
            idx = center["index"]
            if idx < len(bars):
                annotations.append({
                    "type": "taiji_center",
                    "index": idx,
                    "price": center["price"],
                    "direction": center["direction"],
                    "label": f"太极中心 ({center['direction']})",
                    "color": "#FF6B6B" if center["direction"] == "high" else "#4ECDC4",
                })

        # DNA29时间窗口标注
        for window in dna29_windows:
            idx = window["index"]
            if idx < len(bars):
                annotations.append({
                    "type": "dna29_window",
                    "index": idx,
                    "price": bars[idx].get("high", 0) if isinstance(bars[idx], dict) else 0,
                    "label": f"DNA29 (第{window['window_num']}窗)",
                    "color": "#FFE66D",
                })

        # DNA13时间窗口标注
        for window in dna13_windows:
            idx = window["index"]
            if idx < len(bars):
                annotations.append({
                    "type": "dna13_window",
                    "index": idx,
                    "price": bars[idx].get("low", 0) if isinstance(bars[idx], dict) else 0,
                    "label": f"DNA13 (第{window['window_num']}窗)",
                    "color": "#95E1D3",
                })

        return annotations

    def find_taiji_centers(
        self, bars: List[Dict], threshold: float = ZIGZAG_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """寻找太极中心点 - 使用ZigZag方法识别显著转折点

        算法原理：
        1. 从第一个K线开始，寻找价格上涨超过阈值的高点
        2. 从高点开始，寻找价格下跌超过阈值的低点
        3. 交替寻找高点和低点，形成ZigZag走势
        4. 每个转折点即为太极中心点

        Args:
            bars: K线数据列表
            threshold: ZigZag阈值（价格变化百分比），默认5%

        Returns:
            太极中心点列表，每项包含 index, price, direction
        """
        if len(bars) < 3:
            return []

        centers: List[Dict[str, Any]] = []

        # 提取收盘价序列
        closes = [float(bar.get("close", 0)) for bar in bars]
        highs = [float(bar.get("high", 0)) for bar in bars]
        lows = [float(bar.get("low", 0)) for bar in bars]

        # ZigZag算法
        direction = 0  # 0=未确定, 1=上升, -1=下降
        last_pivot_idx = 0
        last_pivot_price = closes[0]

        for i in range(1, len(closes)):
            current_high = highs[i]
            current_low = lows[i]

            if direction == 0:
                # 尚未确定方向，等待突破
                change_pct = (current_high - last_pivot_price) / last_pivot_price if last_pivot_price != 0 else 0
                if change_pct >= threshold:
                    direction = 1
                    centers.append({
                        "index": last_pivot_idx,
                        "price": lows[last_pivot_idx],
                        "direction": "low",
                    })
                    last_pivot_idx = i
                    last_pivot_price = current_high
                elif change_pct <= -threshold:
                    direction = -1
                    centers.append({
                        "index": last_pivot_idx,
                        "price": highs[last_pivot_idx],
                        "direction": "high",
                    })
                    last_pivot_idx = i
                    last_pivot_price = current_low

            elif direction == 1:
                # 上升趋势中，寻找高点
                if current_high > last_pivot_price:
                    last_pivot_idx = i
                    last_pivot_price = current_high
                else:
                    change_pct = (last_pivot_price - current_low) / last_pivot_price if last_pivot_price != 0 else 0
                    if change_pct >= threshold:
                        # 趋势转折，记录高点
                        centers.append({
                            "index": last_pivot_idx,
                            "price": highs[last_pivot_idx],
                            "direction": "high",
                        })
                        direction = -1
                        last_pivot_idx = i
                        last_pivot_price = current_low

            elif direction == -1:
                # 下降趋势中，寻找低点
                if current_low < last_pivot_price:
                    last_pivot_idx = i
                    last_pivot_price = current_low
                else:
                    change_pct = (current_high - last_pivot_price) / last_pivot_price if last_pivot_price != 0 else 0
                    if change_pct >= threshold:
                        # 趋势转折，记录低点
                        centers.append({
                            "index": last_pivot_idx,
                            "price": lows[last_pivot_idx],
                            "direction": "low",
                        })
                        direction = 1
                        last_pivot_idx = i
                        last_pivot_price = current_high

        return centers

    def calc_dna29_windows(
        self, bars: List[Dict], taiji_centers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """计算DNA29主宰数字时间窗口

        鲁兆理论：DNA29是主宰数字，从重要高低点出发，
        每经过29个交易日形成一个关键时间窗口。
        在这些窗口位置，市场出现转折的概率显著增加。

        Args:
            bars: K线数据列表
            taiji_centers: 太极中心点列表

        Returns:
            DNA29时间窗口列表，每项包含 index, center_index, window_num
        """
        windows: List[Dict[str, Any]] = []
        total_bars = len(bars)

        for center in taiji_centers:
            center_idx = center["index"]
            # 从太极中心点出发，每DNA_29个交易日为一个窗口
            window_num = 1
            idx = center_idx + DNA_29
            while idx < total_bars:
                windows.append({
                    "index": idx,
                    "center_index": center_idx,
                    "window_num": window_num,
                    "dna_number": DNA_29,
                })
                window_num += 1
                idx = center_idx + DNA_29 * window_num

        return windows

    def calc_dna13_windows(
        self, bars: List[Dict], taiji_centers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """计算DNA13次级时间窗口

        鲁兆理论：DNA13是次级数字，从太极中心点出发，
        每经过13个交易日形成一个次级窗口。
        在这些位置可能出现次级转折。

        Args:
            bars: K线数据列表
            taiji_centers: 太极中心点列表

        Returns:
            DNA13时间窗口列表
        """
        windows: List[Dict[str, Any]] = []
        total_bars = len(bars)

        for center in taiji_centers:
            center_idx = center["index"]
            window_num = 1
            idx = center_idx + DNA_13
            while idx < total_bars:
                windows.append({
                    "index": idx,
                    "center_index": center_idx,
                    "window_num": window_num,
                    "dna_number": DNA_13,
                })
                window_num += 1
                idx = center_idx + DNA_13 * window_num

        return windows

    def _generate_hints(
        self,
        bars: List[Dict],
        taiji_centers: List[Dict[str, Any]],
        dna29_windows: List[Dict[str, Any]],
        dna13_windows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """基于时间窗口生成信号提示

        当当前K线位置接近DNA窗口时，产生买卖提示：
        - DNA29窗口：强信号（置信度较高）
        - DNA13窗口：弱信号（置信度较低）
        """
        hints: List[Dict[str, Any]] = []
        current_idx = len(bars) - 1

        # 检查当前是否处于DNA29窗口附近（±2个交易日）
        for window in dna29_windows:
            distance = abs(current_idx - window["index"])
            if distance <= 2:
                # 判断最近太极中心方向来决定信号方向
                center_direction = "hold"
                for center in taiji_centers:
                    if center["index"] == window["center_index"]:
                        if center["direction"] == "high":
                            center_direction = "short"  # 高点之后的DNA窗口倾向下跌
                        else:
                            center_direction = "long"  # 低点之后的DNA窗口倾向上涨
                        break

                confidence = 0.7 if distance == 0 else (0.5 if distance == 1 else 0.35)
                hints.append({
                    "type": "dna29_signal",
                    "direction": center_direction,
                    "confidence": confidence,
                    "description": (
                        f"DNA29时间窗口（第{window['window_num']}窗），"
                        f"距窗口中心{distance}个交易日"
                    ),
                    "window_index": window["index"],
                })

        # 检查当前是否处于DNA13窗口附近
        for window in dna13_windows:
            distance = abs(current_idx - window["index"])
            if distance <= 1:
                center_direction = "hold"
                for center in taiji_centers:
                    if center["index"] == window["center_index"]:
                        if center["direction"] == "high":
                            center_direction = "short"
                        else:
                            center_direction = "long"
                        break

                confidence = 0.5 if distance == 0 else 0.3
                hints.append({
                    "type": "dna13_signal",
                    "direction": center_direction,
                    "confidence": confidence,
                    "description": (
                        f"DNA13时间窗口（第{window['window_num']}窗），"
                        f"距窗口中心{distance}个交易日"
                    ),
                    "window_index": window["index"],
                })

        return hints

    def _calc_confidence(
        self,
        bars: List[Dict],
        taiji_centers: List[Dict[str, Any]],
        dna29_windows: List[Dict[str, Any]],
        dna13_windows: List[Dict[str, Any]],
    ) -> float:
        """计算整体置信度

        基于数据充分性和信号强度综合评估。
        """
        if not bars:
            return 0.0

        # 数据充分性权重（至少30条数据为1.0）
        data_score = min(len(bars) / 30.0, 1.0)

        # 太极中心点数量权重（至少3个为1.0）
        center_score = min(len(taiji_centers) / 3.0, 1.0)

        # 信号强度权重
        signal_score = 0.0
        if dna29_windows or dna13_windows:
            current_idx = len(bars) - 1
            for w in dna29_windows:
                if abs(current_idx - w["index"]) <= 2:
                    signal_score = max(signal_score, 0.8)
            for w in dna13_windows:
                if abs(current_idx - w["index"]) <= 1:
                    signal_score = max(signal_score, 0.5)

        confidence = data_score * 0.3 + center_score * 0.3 + signal_score * 0.4
        return round(min(confidence, 1.0), 4)
