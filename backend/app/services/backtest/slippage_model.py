"""
滑点模型 — SlippageModel (TOMAS v2.0 升级)

[TOMAS v2.0] 滑点 = 相位失配代价（Phase Misalignment Cost）
- 做市商（Market Maker）维持相位连续性
- LOB 深度不足时，滑点增大
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
import numpy as np


@dataclass
class SlippageModel:
    """滑点模型（扩展版）

    [TOMAS v2.0] 滑点作为相位失配代价：
    - 市价单：成交价格 = 请求价格 × (1 + slippage_rate)
    - 限价单：如果当前价格优于限价，则按限价成交；否则不成交
    - 相位失配代价：当市场处于相变区时，滑点增大

    属性：
        slippage_bps: 基点滑点，默认 5 bps = 0.05%
        phase_sensitivity: 相位敏感度，默认 1.0
        lob_depth_threshold: LOB 深度阈值，低于此值时滑点增大
    """

    slippage_bps: float = 5.0
    phase_sensitivity: float = 1.0
    lob_depth_threshold: float = 1000.0

    def apply(
        self,
        order_price: float,
        direction: str,
        fill_price: Optional[float] = None,
        phase_continuity_score: float = 1.0,
        lob_depth: Optional[float] = None,
    ) -> float:
        """应用滑点（扩展版）

        [TOMAS v2.0] 滑点 = 基础滑点 + 相位失配代价 + LOB 深度调整

        Args:
            order_price: 订单请求价格
            direction: 交易方向 (BUY/SELL)
            fill_price: 实际成交价
            phase_continuity_score: 相位连续性评分 [0, 1]
            lob_depth: LOB 深度

        Returns:
            考虑滑点后的成交价
        """
        # 1. 基础滑点率
        base_slippage_rate = self.slippage_bps / 10000.0

        # 2. [TOMAS v2.0] 相位失配代价
        if phase_continuity_score < 0.3:
            phase_multiplier = 3.0
        elif phase_continuity_score < 0.7:
            phase_multiplier = 1.0 + (0.7 - phase_continuity_score) / 0.7
        else:
            phase_multiplier = 1.0

        # 3. [TOMAS v2.0] LOB 深度调整
        lob_multiplier = 1.0
        if lob_depth is not None and lob_depth > 0:
            if lob_depth < self.lob_depth_threshold:
                lob_multiplier = min(self.lob_depth_threshold / lob_depth, 5.0)

        # 4. 综合滑点率
        adjusted_slippage_rate = (
            base_slippage_rate
            * (1.0 + self.phase_sensitivity * (phase_multiplier - 1.0))
            * lob_multiplier
        )

        if fill_price is None:
            fill_price = order_price

        # 5. 应用滑点
        if direction == "BUY":
            slipped_price = fill_price * (1 + adjusted_slippage_rate)
        elif direction == "SELL":
            slipped_price = fill_price * (1 - adjusted_slippage_rate)
        else:
            slipped_price = fill_price

        return slipped_price

    def calc_commission(
        self, price: float, quantity: float, commission_rate: float
    ) -> float:
        """计算手续费"""
        return price * quantity * commission_rate

    def compute_phase_misalignment_cost(
        self,
        order_price: float,
        fill_price: float,
        phase_continuity_score: float,
    ) -> Dict[str, float]:
        """计算相位失配代价（详细版）

        [TOMAS v2.0] 滑点即做市商收取的相位对齐费（Phase Alignment Toll）

        Returns:
            {"base_slippage", "phase_misalignment_cost", "market_maker_profit"}
        """
        base_slippage = abs(fill_price - order_price)
        phase_misalignment = base_slippage * (2.0 - phase_continuity_score)
        market_maker_profit = base_slippage * 0.3

        return {
            "base_slippage": float(base_slippage),
            "phase_misalignment_cost": float(phase_misalignment),
            "market_maker_profit": float(market_maker_profit),
            "phase_continuity_score": phase_continuity_score,
        }
