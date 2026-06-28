"""holding_period.py — 持仓周期纪律机制

借鉴大师共识五：长期 > 短期
以及Howard Marks的钟摆理论：市场在过度乐观和过度悲观之间摆动，
很少停在"合理"的中间位置。

持仓纪律机制确保：
1. 不因短期波动而过早止损（说长期却天天看盘的问题）
2. 不因犹豫而过久持有（亏损不止损的问题）
3. 不同信号类型有不同的最小/最大持仓期

核心原则：选择一个时间框架并坚持——
         不要既想做长期又天天看盘。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from loguru import logger


class DisciplineAction(str, Enum):
    """纪律检查动作"""
    HOLD = "hold"              # 正常持有
    FORCE_CLOSE_EARLY = "force_close_early"   # 过早止损→阻止
    FORCE_CLOSE_LATE = "force_close_late"     # 过久持有→强制退出
    WARN_CLOSE_EARLY = "warn_close_early"     # 接近最小持仓期→警告


@dataclass
class HoldingPeriodConfig:
    """持仓周期配置

    不同信号类型有不同的最小/最大持仓期：
    - trend: 趋势信号，需要较长持仓期验证
    - oscillation: 震荡信号，持仓期适中
    - critical: 急变信号（139临界等），持仓期短但也要有底线
    - weak: 弱信号，最小持仓期短，最大持仓期也短
    """
    signal_type: str = "trend"
    min_holding_days: int = 5    # 最小持仓天数（防止过早止损）
    max_holding_days: int = 60   # 最大持仓天数（防止过久持有）
    catalyst_due_days: int = 30  # 催化剂预期兑现天数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal_type": self.signal_type,
            "min_holding_days": self.min_holding_days,
            "max_holding_days": self.max_holding_days,
            "catalyst_due_days": self.catalyst_due_days,
        }


# 默认持仓周期配置（不同信号类型）
DEFAULT_HOLDING_PERIODS: Dict[str, HoldingPeriodConfig] = {
    "trend": HoldingPeriodConfig(
        signal_type="trend",
        min_holding_days=5,
        max_holding_days=60,
        catalyst_due_days=30,
    ),
    "oscillation": HoldingPeriodConfig(
        signal_type="oscillation",
        min_holding_days=3,
        max_holding_days=30,
        catalyst_due_days=15,
    ),
    "critical": HoldingPeriodConfig(
        signal_type="critical",
        min_holding_days=1,
        max_holding_days=15,
        catalyst_due_days=7,
    ),
    "weak": HoldingPeriodConfig(
        signal_type="weak",
        min_holding_days=1,
        max_holding_days=10,
        catalyst_due_days=5,
    ),
}


@dataclass
class DisciplineCheckResult:
    """纪律检查结果"""
    action: DisciplineAction = DisciplineAction.HOLD
    reason: str = ""
    holding_days: int = 0
    config: Optional[HoldingPeriodConfig] = None
    thesis_status: str = ""  # PENDING/VALIDATED/INVALIDATED/EXPIRED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action": self.action.value,
            "reason": self.reason,
            "holding_days": self.holding_days,
            "config": self.config.to_dict() if self.config else None,
            "thesis_status": self.thesis_status,
        }


def check_holding_discipline(
    holding_days: int,
    signal_type: str = "trend",
    thesis_status: str = "PENDING",
    current_pnl_pct: float = 0.0,
    custom_config: Optional[HoldingPeriodConfig] = None,
) -> DisciplineCheckResult:
    """检查持仓纪律

    三条规则：
    1. 最小持仓期规则：持仓天数 < min_holding_days 时，
       如果不是thesis失效，阻止止损（防止"说长期却天天看盘"）
    2. 最大持仓期规则：持仓天数 > max_holding_days 时，
       强制退出（防止过久持有亏损不止损）
    3. 催化剂超期规则：持仓天数 > catalyst_due_days 且 thesis仍PENDING时，
       警告并降低持仓

    特例：thesis已失效(INVALIDATED)时，无视最小持仓期，立即退出

    Args:
        holding_days: 已持仓天数
        signal_type: 信号类型 (trend/oscillation/critical/weak)
        thesis_status: thesis状态 (PENDING/VALIDATED/INVALIDATED/EXPIRED)
        current_pnl_pct: 当前盈亏百分比
        custom_config: 自定义持仓周期配置

    Returns:
        DisciplineCheckResult: 纪律检查结果
    """
    config = custom_config or DEFAULT_HOLDING_PERIODS.get(
        signal_type, DEFAULT_HOLDING_PERIODS["trend"]
    )

    # thesis失效时，无视最小持仓期
    if thesis_status == "INVALIDATED":
        logger.warning(
            f"HoldingPeriod: thesis INVALIDATED, bypassing min holding period "
            f"(holding={holding_days}, min={config.min_holding_days})"
        )
        return DisciplineCheckResult(
            action=DisciplineAction.HOLD,  # 交给thesis失效逻辑处理
            reason="thesis已失效，由thesis失效逻辑处理退出",
            holding_days=holding_days,
            config=config,
            thesis_status=thesis_status,
        )

    # 规则1：最小持仓期检查
    if holding_days < config.min_holding_days:
        # thesis未失效 + 未到最小持仓期 → 阻止止损
        if current_pnl_pct > -0.05:  # 亏损不超过5%，阻止止损
            logger.warning(
                f"HoldingPeriod: 过早止损阻止 - "
                f"holding={holding_days} < min={config.min_holding_days}, "
                f"pnl={current_pnl_pct:.2%}, thesis={thesis_status}"
            )
            return DisciplineCheckResult(
                action=DisciplineAction.FORCE_CLOSE_EARLY,
                reason=f"未到最小持仓期({holding_days}天<{config.min_holding_days}天)，"
                       f"除非thesis失效否则不应止损",
                holding_days=holding_days,
                config=config,
                thesis_status=thesis_status,
            )
        else:
            # 亏损超过5%时，即使未到最小持仓期也允许止损
            logger.info(
                f"HoldingPeriod: 亏损超5%({current_pnl_pct:.2%})，"
                f"允许突破最小持仓期止损"
            )

    # 规则2：最大持仓期检查
    if holding_days > config.max_holding_days:
        logger.warning(
            f"HoldingPeriod: 过久持有强制退出 - "
            f"holding={holding_days} > max={config.max_holding_days}, "
            f"pnl={current_pnl_pct:.2%}"
        )
        return DisciplineCheckResult(
            action=DisciplineAction.FORCE_CLOSE_LATE,
            reason=f"超过最大持仓期({holding_days}天>{config.max_holding_days}天)，"
                   f"强制退出防止过久持有",
            holding_days=holding_days,
            config=config,
            thesis_status=thesis_status,
        )

    # 规则3：催化剂超期警告
    if holding_days > config.catalyst_due_days and thesis_status == "PENDING":
        logger.info(
            f"HoldingPeriod: 催化剂超期警告 - "
            f"holding={holding_days} > catalyst_due={config.catalyst_due_days}, "
            f"thesis仍PENDING"
        )
        return DisciplineCheckResult(
            action=DisciplineAction.WARN_CLOSE_EARLY,
            reason=f"催化剂超期未兑现({holding_days}天>{config.catalyst_due_days}天)，"
                   f"thesis仍PENDING，考虑缩减持仓",
            holding_days=holding_days,
            config=config,
            thesis_status=thesis_status,
        )

    # 正常持有
    return DisciplineCheckResult(
        action=DisciplineAction.HOLD,
        reason="正常持有，未违反持仓纪律",
        holding_days=holding_days,
        config=config,
        thesis_status=thesis_status,
    )


def _self_test() -> None:
    """自测函数"""
    # 测试正常持有
    result = check_holding_discipline(holding_days=10, signal_type="trend", thesis_status="PENDING")
    print(f"Normal hold: action={result.action.value}, reason={result.reason}")
    assert result.action == DisciplineAction.HOLD

    # 测试过早止损阻止
    result2 = check_holding_discipline(
        holding_days=2, signal_type="trend", thesis_status="PENDING", current_pnl_pct=-0.02
    )
    print(f"Early stop: action={result2.action.value}")
    assert result2.action == DisciplineAction.FORCE_CLOSE_EARLY

    # 测试过久持有强制退出
    result3 = check_holding_discipline(holding_days=70, signal_type="trend", thesis_status="PENDING")
    print(f"Late exit: action={result3.action.value}")
    assert result3.action == DisciplineAction.FORCE_CLOSE_LATE

    # 测试催化剂超期警告
    result4 = check_holding_discipline(holding_days=35, signal_type="trend", thesis_status="PENDING")
    print(f"Catalyst overdue: action={result4.action.value}")
    assert result4.action == DisciplineAction.WARN_CLOSE_EARLY

    # 测试thesis失效绕过最小持仓期
    result5 = check_holding_discipline(holding_days=1, signal_type="trend", thesis_status="INVALIDATED")
    print(f"Thesis invalidated: action={result5.action.value}")

    print("✅ HoldingPeriod _self_test passed!")


if __name__ == "__main__":
    _self_test()
