"""止损止盈管理器

核心功能：
- set_stop_loss: 设置止损止盈
- check_stop_loss: 检查是否触发止损/止盈
- calculate_trailing_stop: 计算追踪止损价（基于ATR的2倍距离）

支持固定止损和追踪止损两种模式。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from app.config import settings
from app.core.cosmic_algorithm import detect_139_critical_transition


class StopLossType(str, Enum):
    """止损类型"""

    FIXED = "fixed"  # 固定止损
    TRAILING = "trailing"  # 追踪止损


class StopCheckResult(str, Enum):
    """止损检查结果"""

    POSITION_SAFE = "POSITION_SAFE"
    STOP_LOSS_TRIGGERED = "STOP_LOSS_TRIGGERED"
    TAKE_PROFIT_TRIGGERED = "TAKE_PROFIT_TRIGGERED"


@dataclass
class StopLossConfig:
    """止损止盈配置"""

    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    stop_loss_type: StopLossType = StopLossType.FIXED
    trailing_stop_pct: float = 0.0  # 追踪止损百分比
    trailing_stop_price: float = 0.0  # 当前追踪止损价格
    atr_value: float = 0.0  # ATR值（用于计算追踪止损）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "stop_loss_price": self.stop_loss_price,
            "take_profit_price": self.take_profit_price,
            "stop_loss_type": self.stop_loss_type.value,
            "trailing_stop_pct": self.trailing_stop_pct,
            "trailing_stop_price": self.trailing_stop_price,
            "atr_value": self.atr_value,
        }


class StopLossManager:
    """止损止盈管理器

    管理持仓的止损止盈参数，支持固定止损和追踪止损两种模式。

    固定止损：
    - 止损价格固定不变
    - 当前价格触及止损价时触发

    追踪止损：
    - 止损价格随价格有利方向移动
    - 基于ATR的2倍距离计算
    - 价格回撤超过追踪距离时触发

    风控保守处理：异常时保持现有止损，不放松止损线。
    """

    # 追踪止损ATR倍数
    TRAILING_STOP_ATR_MULTIPLIER: float = 2.0

    # 默认止损比例
    DEFAULT_STOP_LOSS_PCT: float = settings.RISK_STOP_LOSS_PCT

    # 默认止盈比例
    DEFAULT_TAKE_PROFIT_PCT: float = settings.RISK_TAKE_PROFIT_PCT

    def __init__(self) -> None:
        """初始化止损止盈管理器"""
        self._stop_configs: Dict[str, StopLossConfig] = {}

    def set_stop_loss(
        self,
        position: Dict[str, Any],
        stop_price: float,
        take_profit_price: float,
        stop_loss_type: StopLossType = StopLossType.FIXED,
        trailing_stop_pct: float = 0.0,
    ) -> StopLossConfig:
        """设置止损止盈

        Args:
            position: 持仓信息字典
            stop_price: 止损价格
            take_profit_price: 止盈价格
            stop_loss_type: 止损类型（固定/追踪）
            trailing_stop_pct: 追踪止损百分比（追踪模式时使用）

        Returns:
            StopLossConfig: 止损止盈配置
        """
        position_id = position.get("position_id", "")

        config = StopLossConfig(
            stop_loss_price=stop_price,
            take_profit_price=take_profit_price,
            stop_loss_type=stop_loss_type,
            trailing_stop_pct=trailing_stop_pct or settings.RISK_TAKE_PROFIT_PCT,
            trailing_stop_price=stop_price,
        )

        self._stop_configs[position_id] = config

        logger.info(
            f"StopLossManager: set stop loss for position {position_id} - "
            f"stop={stop_price:.2f}, take_profit={take_profit_price:.2f}, "
            f"type={stop_loss_type.value}"
        )

        return config

    def check_stop_loss(
        self,
        position: Dict[str, Any],
        current_price: float,
        closes_139: Optional[List[float]] = None,
        bars_139: Optional[List[Dict[str, Any]]] = None,
    ) -> StopCheckResult:
        """检查是否触发止损/止盈

        对于多头持仓：
        - 止损：current_price <= stop_loss_price
        - 止盈：current_price >= take_profit_price

        对于空头持仓：
        - 止损：current_price >= stop_loss_price
        - 止盈：current_price <= take_profit_price

        新增139宇宙算法硬止损检查：
        - 139波动率σ硬止损：短期σ超过长期σ的2倍时触发
        - 139临界慢化止损：critical_score >= 2.5 且 is_critical时触发

        Args:
            position: 持仓信息（需包含position_id, entry_price, quantity）
            current_price: 当前市场价格
            closes_139: 近期收盘价序列（用于139波动率硬止损检查）
            bars_139: 近期K线数据（用于139临界慢化止损检查）

        Returns:
            StopCheckResult: 检查结果
        """
        position_id = position.get("position_id", "")
        entry_price = position.get("entry_price", 0.0)
        quantity = position.get("quantity", 0.0)

        if quantity <= 0:
            return StopCheckResult.POSITION_SAFE

        config = self._stop_configs.get(position_id)

        if config is None:
            # 无配置时使用默认比例
            stop_loss_price = entry_price * (1 - self.DEFAULT_STOP_LOSS_PCT)
            take_profit_price = entry_price * (1 + self.DEFAULT_TAKE_PROFIT_PCT)
        else:
            # 追踪止损：更新追踪止损价格
            if config.stop_loss_type == StopLossType.TRAILING:
                self._update_trailing_stop(config, current_price, entry_price)
                stop_loss_price = config.trailing_stop_price
            else:
                stop_loss_price = config.stop_loss_price
            take_profit_price = config.take_profit_price

        # 判断是否为多头（quantity > 0 视为多头）
        is_long = quantity > 0

        if is_long:
            # 多头止损检查
            if stop_loss_price > 0 and current_price <= stop_loss_price:
                logger.warning(
                    f"StopLossManager: STOP LOSS TRIGGERED for {position_id} - "
                    f"current={current_price:.2f} <= stop={stop_loss_price:.2f}"
                )
                return StopCheckResult.STOP_LOSS_TRIGGERED

            # 多头止盈检查
            if take_profit_price > 0 and current_price >= take_profit_price:
                logger.info(
                    f"StopLossManager: TAKE PROFIT TRIGGERED for {position_id} - "
                    f"current={current_price:.2f} >= take_profit={take_profit_price:.2f}"
                )
                return StopCheckResult.TAKE_PROFIT_TRIGGERED
        else:
            # 空头止损检查
            if stop_loss_price > 0 and current_price >= stop_loss_price:
                logger.warning(
                    f"StopLossManager: STOP LOSS TRIGGERED (SHORT) for {position_id} - "
                    f"current={current_price:.2f} >= stop={stop_loss_price:.2f}"
                )
                return StopCheckResult.STOP_LOSS_TRIGGERED

            # 空头止盈检查
            if take_profit_price > 0 and current_price <= take_profit_price:
                logger.info(
                    f"StopLossManager: TAKE PROFIT TRIGGERED (SHORT) for {position_id} - "
                    f"current={current_price:.2f} <= take_profit={take_profit_price:.2f}"
                )
                return StopCheckResult.TAKE_PROFIT_TRIGGERED

        # 139波动率σ硬止损
        if closes_139 is not None:
            vol_result = self.check_139_volatility_stop(position, closes_139)
            if vol_result == StopCheckResult.STOP_LOSS_TRIGGERED:
                return StopCheckResult.STOP_LOSS_TRIGGERED

        # 139临界慢化止损
        if bars_139 is not None:
            crit_result = self.check_139_critical_stop(position, bars_139)
            if crit_result == StopCheckResult.STOP_LOSS_TRIGGERED:
                return StopCheckResult.STOP_LOSS_TRIGGERED

        return StopCheckResult.POSITION_SAFE

    def check_139_volatility_stop(
        self,
        position: Dict[str, Any],
        prices: List[float],
        window: int = 139,
    ) -> StopCheckResult:
        """139窗口波动率σ硬止损检查

        计算近139根K线的波动率σ（标准差），当σ超过长期均值σ的2倍时，
        强制触发硬止损——市场波动异常剧烈，必须立即退出。

        Args:
            position: 持仓信息（需包含position_id）
            prices: 近期收盘价序列（长度需 >= window）
            window: 波动率计算窗口，默认139

        Returns:
            StopCheckResult: 波动率触发硬止损时返回 STOP_LOSS_TRIGGERED，
                             否则返回 POSITION_SAFE
        """
        position_id = position.get("position_id", "")

        if len(prices) < window:
            logger.warning(
                f"StopLossManager: 139波动率硬止损 - 价格序列不足 "
                f"(len={len(prices)} < window={window}), 跳过检查"
            )
            return StopCheckResult.POSITION_SAFE

        # 取近window根K线的收盘价
        recent_prices = np.array(prices[-window:], dtype=np.float64)

        # 计算短期波动率σ（近window根K线的标准差）
        short_sigma: float = float(np.std(recent_prices, ddof=1))

        # 计算长期均值σ（全部价格的标准差）
        all_prices = np.array(prices, dtype=np.float64)
        long_sigma: float = float(np.std(all_prices, ddof=1))

        # 防止长期σ为零（极端情况：价格完全不变）
        if long_sigma <= 0.0:
            logger.warning(
                f"StopLossManager: 139波动率硬止损 - 长期σ为零，无法比较，跳过检查"
            )
            return StopCheckResult.POSITION_SAFE

        # σ硬止损阈值：短期σ超过长期σ的2倍
        sigma_ratio: float = short_sigma / long_sigma
        threshold: float = 2.0

        if sigma_ratio >= threshold:
            logger.warning(
                f"StopLossManager: 139波动率σ硬止损触发 for {position_id} - "
                f"短期σ={short_sigma:.6f}, 长期σ={long_sigma:.6f}, "
                f"σ比值={sigma_ratio:.2f} >= 阈值={threshold:.2f}"
            )
            return StopCheckResult.STOP_LOSS_TRIGGERED

        logger.debug(
            f"StopLossManager: 139波动率σ硬止损安全 for {position_id} - "
            f"短期σ={short_sigma:.6f}, 长期σ={long_sigma:.6f}, "
            f"σ比值={sigma_ratio:.2f} < 阈值={threshold:.2f}"
        )
        return StopCheckResult.POSITION_SAFE

    def check_139_critical_stop(
        self,
        position: Dict[str, Any],
        bars: List[Dict[str, Any]],
    ) -> StopCheckResult:
        """139窗口临界慢化硬止损检查

        调用宇宙算法的 detect_139_critical_transition() 检测临界慢化征兆。
        当 is_critical=True 且 critical_score >= 2.5 时，强制触发硬止损——
        不用等到价格触线，直接止损退出。

        Args:
            position: 持仓信息（需包含position_id）
            bars: 近期K线数据列表（每条需包含close/high/low等字段）

        Returns:
            StopCheckResult: 临界慢化触发硬止损时返回 STOP_LOSS_TRIGGERED，
                             否则返回 POSITION_SAFE
        """
        position_id = position.get("position_id", "")

        if len(bars) < 139:
            logger.warning(
                f"StopLossManager: 139临界止损 - K线数据不足 "
                f"(len={len(bars)} < 139), 跳过检查"
            )
            return StopCheckResult.POSITION_SAFE

        # 调用宇宙算法检测139窗口临界慢化
        result: Dict[str, Any] = detect_139_critical_transition(bars)
        is_critical: bool = result.get("is_critical", False)
        critical_score: float = float(result.get("critical_score", 0.0))

        if is_critical and critical_score >= 2.5:
            logger.warning(
                f"StopLossManager: 139临界慢化硬止损触发 for {position_id} - "
                f"is_critical={is_critical}, critical_score={critical_score:.2f} >= 2.5"
            )
            return StopCheckResult.STOP_LOSS_TRIGGERED

        logger.debug(
            f"StopLossManager: 139临界止损安全 for {position_id} - "
            f"is_critical={is_critical}, critical_score={critical_score:.2f}"
        )
        return StopCheckResult.POSITION_SAFE

    def calculate_trailing_stop(self, entry_price: float, atr: float) -> float:
        """计算追踪止损价（基于ATR的2倍距离）

        公式：追踪止损价 = 入场价 - ATR × 2（多头）
              追踪止损价 = 入场价 + ATR × 2（空头）

        Args:
            entry_price: 入场价格
            atr: ATR（平均真实波幅）值

        Returns:
            float: 追踪止损价格
        """
        if atr <= 0:
            logger.warning("StopLossManager: invalid ATR value, using default stop loss pct")
            return entry_price * (1 - self.DEFAULT_STOP_LOSS_PCT)

        trailing_distance = atr * self.TRAILING_STOP_ATR_MULTIPLIER
        trailing_stop_price = entry_price - trailing_distance

        # 确保止损价不为负
        trailing_stop_price = max(trailing_stop_price, 0.0)

        logger.debug(
            f"StopLossManager: trailing stop calculated - "
            f"entry={entry_price:.2f}, atr={atr:.2f}, "
            f"distance={trailing_distance:.2f}, "
            f"stop={trailing_stop_price:.2f}"
        )

        return round(trailing_stop_price, 8)

    def remove_stop_config(self, position_id: str) -> None:
        """移除止损止盈配置（平仓后调用）

        Args:
            position_id: 持仓ID
        """
        if position_id in self._stop_configs:
            del self._stop_configs[position_id]
            logger.info(f"StopLossManager: removed stop config for position {position_id}")

    def get_stop_config(self, position_id: str) -> Optional[StopLossConfig]:
        """获取止损止盈配置

        Args:
            position_id: 持仓ID

        Returns:
            Optional[StopLossConfig]: 配置，不存在返回None
        """
        return self._stop_configs.get(position_id)

    def _update_trailing_stop(
        self,
        config: StopLossConfig,
        current_price: float,
        entry_price: float,
    ) -> None:
        """更新追踪止损价格

        追踪止损只向有利方向移动：
        - 多头：止损价只能上移，不能下移
        - 空头：止损价只能下移，不能上移

        Args:
            config: 止损配置
            current_price: 当前价格
            entry_price: 入场价格
        """
        if config.trailing_stop_pct > 0:
            # 基于百分比的追踪止损
            new_stop = current_price * (1 - config.trailing_stop_pct)
        elif config.atr_value > 0:
            # 基于ATR的追踪止损
            new_stop = self.calculate_trailing_stop(entry_price, config.atr_value)
        else:
            # 使用默认比例
            new_stop = current_price * (1 - self.DEFAULT_STOP_LOSS_PCT)

        # 追踪止损只能向有利方向移动（上移）
        if new_stop > config.trailing_stop_price:
            config.trailing_stop_price = round(new_stop, 8)
            logger.debug(
                f"StopLossManager: trailing stop updated to {new_stop:.2f} "
                f"for current_price={current_price:.2f}"
            )
