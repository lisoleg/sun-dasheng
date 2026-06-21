"""BG均线引擎 - 鲁兆神秘四条线

鲁兆理论：4/8/16/32 四条均线，4是短期，32是长期，金叉死叉信号。
- BG均线：4, 8, 16, 32 周期简单移动平均线
- 金叉：短期均线上穿长期均线 -> 买入信号
- 死叉：短期均线下穿长期均线 -> 卖出信号
- 输出：BG_GOLDEN_CROSS / BG_DEATH_CROSS / BG_HOLD
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.services.theory.base import TheoryEngine, TheoryResult

# BG均线周期
BG_PERIODS = [4, 8, 16, 32]

# 金叉死叉检测容差（K线数）
CROSS_TOLERANCE = 3


class BGMovingAverageEngine(TheoryEngine):
    """BG均线引擎

    基于鲁兆神秘四条线的分析方法：
    1. 计算 4/8/16/32 四条均线
    2. 检测金叉死叉信号
    3. 评估均线排列（多头排列/空头排列）
    4. 生成买卖信号
    """

    theory_name = "bg_ma"

    @property
    def name(self) -> str:
        return "BG均线"

    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """执行BG均线分析

        Args:
            bars: K线数据列表

        Returns:
            TheoryResult 包含均线数据和信号提示
        """
        if len(bars) < BG_PERIODS[-1] + 1:
            return TheoryResult(
                theory_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )

        # 计算BG均线
        bg_ma = self._calc_bg_ma(bars)

        # 检测金叉死叉
        crosses = self._detect_crosses(bg_ma)

        # 评估均线排列
        arrangement = self._evaluate_arrangement(bg_ma)

        # 生成信号提示
        hints = self._generate_hints(bars, bg_ma, crosses, arrangement)

        # 计算整体置信度
        confidence = self._calc_confidence(crosses, arrangement)

        return TheoryResult(
            theory_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            annotations={
                "bg_ma": bg_ma,
                "crosses": crosses,
                "arrangement": arrangement,
            },
            hints=hints,
            confidence=confidence,
        )

    def get_annotations(self, bars: List[Dict]) -> List[Dict]:
        """获取BG均线图表标注"""
        if len(bars) < BG_PERIODS[-1] + 1:
            return []

        bg_ma = self._calc_bg_ma(bars)
        crosses = self._detect_crosses(bg_ma)

        annotations: List[Dict[str, Any]] = []

        # 金叉死叉标注
        for cross in crosses:
            idx = cross["index"]
            if idx < len(bars):
                annotations.append({
                    "type": "bg_cross",
                    "index": idx,
                    "price": bars[idx].get("close", 0),
                    "cross_type": cross["type"],
                    "short_period": cross["short_period"],
                    "long_period": cross["long_period"],
                    "label": f"BG{'金叉' if cross['type'] == 'golden' else '死叉'} ({cross['short_period']}/{cross['long_period']})",
                    "color": "#4ECDC4" if cross["type"] == "golden" else "#FF6B6B",
                })

        return annotations

    def _calc_bg_ma(self, bars: List[Dict]) -> Dict[int, List[float]]:
        """计算BG均线（4/8/16/32周期SMA）

        Args:
            bars: K线数据列表

        Returns:
            均线数据字典 {周期: [均线值列表]}
        """
        closes = [float(bar.get("close", 0)) for bar in bars]

        bg_ma = {}
        for period in BG_PERIODS:
            ma_values = []
            for i in range(len(closes)):
                if i < period - 1:
                    ma_values.append(None)
                else:
                    ma = sum(closes[i - period + 1 : i + 1]) / period
                    ma_values.append(ma)
            bg_ma[period] = ma_values

        return bg_ma

    def _detect_crosses(self, bg_ma: Dict[int, List[float]]) -> List[Dict[str, Any]]:
        """检测金叉死叉

        金叉：短期均线上穿长期均线
        死叉：短期均线下穿长期均线

        Returns:
            交叉信号列表
        """
        crosses = []

        # 检查相邻均线的交叉
        for i in range(len(BG_PERIODS) - 1):
            short_period = BG_PERIODS[i]
            long_period = BG_PERIODS[i + 1]

            short_ma = bg_ma[short_period]
            long_ma = bg_ma[long_period]

            for j in range(1, len(short_ma)):
                if short_ma[j] is None or long_ma[j] is None:
                    continue

                prev_diff = (short_ma[j - 1] or 0) - (long_ma[j - 1] or 0)
                curr_diff = short_ma[j] - long_ma[j]

                # 金叉：prev_diff <= 0 and curr_diff > 0
                if prev_diff <= 0 and curr_diff > 0:
                    crosses.append({
                        "index": j,
                        "type": "golden",
                        "short_period": short_period,
                        "long_period": long_period,
                    })

                # 死叉：prev_diff >= 0 and curr_diff < 0
                elif prev_diff >= 0 and curr_diff < 0:
                    crosses.append({
                        "index": j,
                        "type": "death",
                        "short_period": short_period,
                        "long_period": long_period,
                    })

        return crosses

    def _evaluate_arrangement(self, bg_ma: Dict[int, List[float]]) -> Dict[str, Any]:
        """评估均线排列

        多头排列：MA4 > MA8 > MA16 > MA32（短期在上方）
        空头排列：MA4 < MA8 < MA16 < MA32（短期在下方）

        Returns:
            排列信息字典
        """
        if not bg_ma or len(bg_ma[BG_PERIODS[0]]) == 0:
            return {"type": "unknown"}

        current_idx = len(bg_ma[BG_PERIODS[0]]) - 1

        # 获取当前各周期均线值
        current_ma = {}
        for period in BG_PERIODS:
            ma_value = bg_ma[period][current_idx]
            if ma_value is not None:
                current_ma[period] = ma_value

        if len(current_ma) < len(BG_PERIODS):
            return {"type": "unknown"}

        # 检查排列
        ma_values = [current_ma[p] for p in BG_PERIODS]

        # 多头排列：短期 > 长期
        if all(ma_values[i] >= ma_values[i + 1] for i in range(len(ma_values) - 1)):
            arrangement_type = "bullish"  # 多头排列
        # 空头排列：短期 < 长期
        elif all(ma_values[i] <= ma_values[i + 1] for i in range(len(ma_values) - 1)):
            arrangement_type = "bearish"  # 空头排列
        else:
            arrangement_type = "mixed"  # 混乱排列

        return {
            "type": arrangement_type,
            "values": current_ma,
        }

    def _generate_hints(
        self,
        bars: List[Dict],
        bg_ma: Dict[int, List[float]],
        crosses: List[Dict[str, Any]],
        arrangement: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """基于BG均线生成信号提示

        金叉信号：买入
        死叉信号：卖出
        均线排列：辅助判断趋势强度
        """
        hints = []
        current_idx = len(bars) - 1

        # 检查近期金叉死叉
        recent_crosses = [c for c in crosses if current_idx - c["index"] <= CROSS_TOLERANCE]

        for cross in recent_crosses:
            if cross["type"] == "golden":
                hints.append({
                    "type": "bg_golden_cross",
                    "direction": "LONG",
                    "confidence": 0.65,
                    "description": (
                        f"BG均线金叉：{cross['short_period']}周期上穿{cross['long_period']}周期，"
                        f"买入信号"
                    ),
                    "index": cross["index"],
                })
            else:
                hints.append({
                    "type": "bg_death_cross",
                    "direction": "SHORT",
                    "confidence": 0.65,
                    "description": (
                        f"BG均线死叉：{cross['short_period']}周期下穿{cross['long_period']}周期，"
                        f"卖出信号"
                    ),
                    "index": cross["index"],
                })

        # 均线排列提示
        arrangement_type = arrangement.get("type", "unknown")
        if arrangement_type == "bullish":
            hints.append({
                "type": "bg_bullish_arrangement",
                "direction": "LONG",
                "confidence": 0.5,
                "description": "BG均线多头排列（MA4 > MA8 > MA16 > MA32），趋势偏多",
            })
        elif arrangement_type == "bearish":
            hints.append({
                "type": "bg_bearish_arrangement",
                "direction": "SHORT",
                "confidence": 0.5,
                "description": "BG均线空头排列（MA4 < MA8 < MA16 < MA32），趋势偏空",
            })

        # 价格与均线关系
        current_price = float(bars[-1].get("close", 0))
        ma4 = bg_ma[4][current_idx]

        if ma4 is not None:
            if current_price > ma4:
                hints.append({
                    "type": "bg_price_above_ma",
                    "direction": "LONG",
                    "confidence": 0.4,
                    "description": f"价格在MA4({ma4:.2f})上方，短期偏多",
                })
            else:
                hints.append({
                    "type": "bg_price_below_ma",
                    "direction": "SHORT",
                    "confidence": 0.4,
                    "description": f"价格在MA4({ma4:.2f})下方，短期偏空",
                })

        return hints

    def _calc_confidence(
        self,
        crosses: List[Dict[str, Any]],
        arrangement: Dict[str, Any],
    ) -> float:
        """计算整体置信度"""
        # 交叉信号权重
        cross_score = min(len(crosses) / 3.0, 1.0) if crosses else 0.0

        # 排列清晰度权重
        arrangement_type = arrangement.get("type", "unknown")
        if arrangement_type == "bullish" or arrangement_type == "bearish":
            arrangement_score = 0.8
        elif arrangement_type == "mixed":
            arrangement_score = 0.3
        else:
            arrangement_score = 0.0

        # 近期交叉权重
        # (简化：假设有交叉就是1.0)
        recent_score = 1.0 if crosses else 0.0

        confidence = cross_score * 0.4 + arrangement_score * 0.3 + recent_score * 0.3
        return round(min(confidence, 1.0), 4)
