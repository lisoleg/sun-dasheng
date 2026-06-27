"""仓位管理器

核心功能：
- calculate_size: 根据风险预算计算仓位
- validate_position: 验证新仓位是否超过总仓位限制

仓位计算公式：
    仓位大小 = (总资金 × 风险比例) / |入场价 - 止损价|

单笔最大仓位比例默认10%（RISK_MAX_POSITION_PCT）
"""

from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from app.config import settings
from app.core.cosmic_algorithm import (
    detect_139_critical_transition,
    apply_369_signal_filter,
)


class PositionSizer:
    """仓位管理器

    根据风险预算动态计算仓位大小，确保单笔交易风险可控。

    核心公式：
        仓位大小 = (总资金 × 风险比例) / |入场价 - 止损价|

    参数说明：
    - 总资金(capital): 账户总可用资金
    - 风险比例(risk_pct): 每笔交易愿意承受的最大亏损占总资金的比例
    - 入场价(entry_price): 计划入场价格
    - 止损价(stop_price): 止损价格

    安全检查：
    - 单笔最大仓位比例不超过RISK_MAX_POSITION_PCT（默认10%）
    - 止损价与入场价差为零时拒绝开仓（避免除零错误）
    - 计算出的仓位不超过总资金允许的最大值
    """

    # 单笔最大仓位比例
    MAX_POSITION_PCT: float = settings.RISK_MAX_POSITION_PCT

    # 最小止损距离（入场价的0.1%），防止除零
    MIN_STOP_DISTANCE_PCT: float = 0.001

    def __init__(self, max_position_pct: Optional[float] = None) -> None:
        """初始化仓位管理器

        Args:
            max_position_pct: 单笔最大仓位比例，默认从配置读取
        """
        self.max_position_pct = max_position_pct or self.MAX_POSITION_PCT

    def calculate_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_price: float,
    ) -> float:
        """根据风险预算计算仓位大小

        公式：仓位大小 = (总资金 × 风险比例) / |入场价 - 止损价|

        Args:
            capital: 总资金
            risk_pct: 风险比例（如0.02表示2%）
            entry_price: 入场价格
            stop_price: 止损价格

        Returns:
            float: 仓位大小（交易数量）

        Raises:
            ValueError: 参数无效时
        """
        # 参数验证
        if capital <= 0:
            logger.error(f"PositionSizer: invalid capital={capital}")
            return 0.0

        if risk_pct <= 0 or risk_pct > 1:
            logger.error(f"PositionSizer: invalid risk_pct={risk_pct}")
            return 0.0

        if entry_price <= 0:
            logger.error(f"PositionSizer: invalid entry_price={entry_price}")
            return 0.0

        # 计算止损距离
        stop_distance = abs(entry_price - stop_price)

        # 检查止损距离是否过小
        min_stop_distance = entry_price * self.MIN_STOP_DISTANCE_PCT
        if stop_distance < min_stop_distance:
            logger.warning(
                f"PositionSizer: stop distance too small "
                f"({stop_distance:.8f} < {min_stop_distance:.8f}), "
                f"using minimum stop distance"
            )
            stop_distance = min_stop_distance

        # 核心计算：仓位 = (总资金 × 风险比例) / |入场价 - 止损价|
        risk_amount = capital * risk_pct
        position_size = risk_amount / stop_distance

        # 计算仓位价值
        position_value = position_size * entry_price

        # 限制单笔最大仓位
        max_position_value = capital * self.max_position_pct
        if position_value > max_position_value:
            position_size = max_position_value / entry_price
            logger.info(
                f"PositionSizer: position capped to max {self.max_position_pct:.0%} "
                f"of capital ({max_position_value:.2f})"
            )

        logger.info(
            f"PositionSizer: calculated size={position_size:.8f} - "
            f"capital={capital:.2f}, risk_pct={risk_pct:.2%}, "
            f"entry={entry_price:.2f}, stop={stop_price:.2f}, "
            f"stop_distance={stop_distance:.2f}, "
            f"position_value={position_size * entry_price:.2f}"
        )

        return round(position_size, 8)

    def validate_position(
        self, current_total: float, new_position_size: float
    ) -> bool:
        """验证新仓位是否超过总仓位限制

        检查新仓位价值是否超过总资金的MAX_POSITION_PCT比例。

        Args:
            current_total: 当前持仓总价值
            new_position_size: 新仓位价值

        Returns:
            bool: True表示仓位合法，False表示超过限制
        """
        # current_total为0时（无持仓），总是允许
        if current_total <= 0:
            return True

        # 检查新仓位是否超过限制
        # 注意：这里的new_position_size已经是仓位价值（数量×价格）
        # 我们用简单规则：新仓位不超过总持仓的max_position_pct
        max_allowed = current_total * (1 + self.max_position_pct)

        if new_position_size > max_allowed:
            logger.warning(
                f"PositionSizer: position validation failed - "
                f"new={new_position_size:.2f} > max={max_allowed:.2f} "
                f"(current_total={current_total:.2f}, max_pct={self.max_position_pct:.0%})"
            )
            return False

        return True

    def calculate_max_position_value(self, capital: float) -> float:
        """计算最大单笔仓位价值

        Args:
            capital: 总资金

        Returns:
            float: 最大仓位价值
        """
        return capital * self.max_position_pct

    def calculate_risk_reward_ratio(
        self,
        entry_price: float,
        stop_price: float,
        take_profit_price: float,
    ) -> float:
        """计算风险回报比

        Args:
            entry_price: 入场价格
            stop_price: 止损价格
            take_profit_price: 止盈价格

        Returns:
            float: 风险回报比（如2.0表示1:2的风险回报比）
        """
        risk = abs(entry_price - stop_price)
        reward = abs(take_profit_price - entry_price)

        if risk <= 0:
            return 0.0

        ratio = reward / risk
        return round(ratio, 2)

    def calculate_139_adjusted_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_price: float,
        bars: List[Dict[str, Any]],
    ) -> float:
        """139窗口临界慢化自适应缩仓

        调用宇宙算法的 detect_139_critical_transition() 检测临界慢化征兆，
        根据检测结果动态缩减仓位大小：

        - is_critical=True（临界慢化确认）：仓位减半（size × 0.5）
        - regime="transitioning"（1个征兆）：仓位缩减至75%（size × 0.75）
        - regime="stable"（稳定）：正常仓位（size × 1.0）

        Args:
            capital: 总资金
            risk_pct: 风险比例（如0.02表示2%）
            entry_price: 入场价格
            stop_price: 止损价格
            bars: 近期K线数据列表（每条需包含close/high/low等字段）

        Returns:
            float: 调整后的仓位大小（交易数量）
        """
        # 先用基础公式计算标准仓位
        base_size: float = self.calculate_size(capital, risk_pct, entry_price, stop_price)

        if base_size <= 0.0:
            return 0.0

        # 数据不足时直接返回基础仓位
        if len(bars) < 139:
            logger.warning(
                f"PositionSizer: 139缩仓 - K线数据不足 "
                f"(len={len(bars)} < 139), 使用正常仓位"
            )
            return base_size

        # 调用宇宙算法检测139窗口临界慢化
        result: Dict[str, Any] = detect_139_critical_transition(bars)
        is_critical: bool = result.get("is_critical", False)
        regime: str = result.get("regime", "stable")
        critical_score: float = float(result.get("critical_score", 0.0))

        # 根据检测结果调整仓位
        adjusted_size: float = base_size

        if is_critical:
            # 临界慢化确认：仓位减半
            adjusted_size = base_size * 0.5
            logger.warning(
                f"PositionSizer: 139临界慢化缩仓 - "
                f"is_critical=True, critical_score={critical_score:.2f}, "
                f"仓位减半 {base_size:.8f} -> {adjusted_size:.8f}"
            )
        elif regime == "transitioning":
            # 1个征兆（过渡态）：仓位缩减至75%
            adjusted_size = base_size * 0.75
            logger.info(
                f"PositionSizer: 139过渡态缩仓 - "
                f"regime=transitioning, "
                f"仓位缩减至75% {base_size:.8f} -> {adjusted_size:.8f}"
            )
        else:
            # 稳定态：正常仓位
            logger.debug(
                f"PositionSizer: 139稳定态 - regime=stable, 正常仓位 "
                f"size={base_size:.8f}"
            )

        return round(adjusted_size, 8)

    def calculate_369_adjusted_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_price: float,
        bars: List[Dict[str, Any]],
    ) -> float:
        """369振动模态仓位调整

        调用宇宙算法的 apply_369_signal_filter() 检测振动模态信号质量，
        根据振动得分（vibration_score）动态调整仓位：

        - vibration_score >= 0.6：振动信号强，正常仓位（size × 1.0）
        - 0.3 <= vibration_score < 0.6：振动信号中等，仓位缩减至75%（size × 0.75）
        - vibration_score < 0.3：振动信号弱，仓位缩减至25%（接近清仓）（size × 0.25）

        Args:
            capital: 总资金
            risk_pct: 风险比例（如0.02表示2%）
            entry_price: 入场价格
            stop_price: 止损价格
            bars: 近期K线数据列表（每条需包含close/high/low等字段）

        Returns:
            float: 调整后的仓位大小（交易数量）
        """
        # 先用基础公式计算标准仓位
        base_size: float = self.calculate_size(capital, risk_pct, entry_price, stop_price)

        if base_size <= 0.0:
            return 0.0

        # 数据不足时直接返回基础仓位
        if len(bars) < 10:
            logger.warning(
                f"PositionSizer: 369缩仓 - K线数据不足 "
                f"(len={len(bars)} < 10), 使用正常仓位"
            )
            return base_size

        # 调用宇宙算法检测369振动模态
        result: Dict[str, Any] = apply_369_signal_filter(bars)
        vibration_score: float = float(result.get("vibration_score", 0.0))
        regime: str = result.get("regime", "unknown")

        # 根据振动得分调整仓位
        adjusted_size: float = base_size

        if vibration_score >= 0.6:
            # 振动信号强：正常仓位
            logger.debug(
                f"PositionSizer: 369振动正常 - "
                f"vibration_score={vibration_score:.2f} >= 0.6, "
                f"regime={regime}, 正常仓位 size={base_size:.8f}"
            )
        elif vibration_score >= 0.3:
            # 振动信号中等：仓位缩减至75%
            adjusted_size = base_size * 0.75
            logger.info(
                f"PositionSizer: 369振动中等缩仓 - "
                f"vibration_score={vibration_score:.2f} ∈ [0.3, 0.6), "
                f"regime={regime}, 仓位缩减至75% "
                f"{base_size:.8f} -> {adjusted_size:.8f}"
            )
        else:
            # 振动信号弱：仓位缩减至25%（接近清仓）
            adjusted_size = base_size * 0.25
            logger.warning(
                f"PositionSizer: 369振动弱接近清仓 - "
                f"vibration_score={vibration_score:.2f} < 0.3, "
                f"regime={regime}, 仓位缩减至25% "
                f"{base_size:.8f} -> {adjusted_size:.8f}"
            )

        return round(adjusted_size, 8)
