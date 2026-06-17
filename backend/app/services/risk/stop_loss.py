"""止损止盈管理器

核心功能：
- set_stop_loss: 设置止损止盈
- check_stop_loss: 检查是否触发止损/止盈
- calculate_trailing_stop: 计算追踪止损价（基于ATR的2倍距离）

支持固定止损和追踪止损两种模式。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from loguru import logger

from app.config import settings


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
        self, position: Dict[str, Any], current_price: float
    ) -> StopCheckResult:
        """检查是否触发止损/止盈

        对于多头持仓：
        - 止损：current_price <= stop_loss_price
        - 止盈：current_price >= take_profit_price

        对于空头持仓：
        - 止损：current_price >= stop_loss_price
        - 止盈：current_price <= take_profit_price

        Args:
            position: 持仓信息（需包含position_id, entry_price, quantity）
            current_price: 当前市场价格

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
