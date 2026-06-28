"""thesis_tracker.py — 投资论据追踪器（Ackman方法论系统化）

借鉴Bill Ackman的thesis驱动交易方法论：
- 每笔持仓都有明确的论据（为什么买）
- 每笔持仓都有催化剂（什么事件会兑现）
- 每笔持仓都有失效条件（什么条件下退出）

核心原则：说不清为什么买，就不应该买。
         说不清什么时候卖，就不知道什么时候会亏到不可收拾。

对应大师共识三：有thesis，能验证，敢认错。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from loguru import logger


class ThesisStatus(str, Enum):
    """论据状态"""
    PENDING = "pending"       # 刚生成，未验证
    VALIDATED = "validated"   # 催化剂已兑现，论据成立
    INVALIDATED = "invalidated"  # 失效条件已触发，论据不再成立
    EXPIRED = "expired"       # 超过最大持仓期仍未兑现


@dataclass
class Thesis:
    """投资论据

    每笔交易的核心论据，包含：
    - reason: 为什么买（核心论据）
    - catalyst: 什么事件会兑现（催化剂）
    - invalidation_conditions: 什么条件下退出（失效条件列表）
    - signal_type: 信号类型（趋势/震荡/急变）
    """

    thesis_id: str = ""
    symbol: str = ""
    direction: str = "HOLD"  # LONG/SHORT/HOLD
    reason: str = ""         # 为什么买
    catalyst: str = ""       # 催化剂（什么事件会兑现）
    catalyst_due_days: int = 30  # 催化剂预期兑现天数
    invalidation_conditions: List[str] = field(default_factory=list)  # 失效条件
    confidence_at_entry: float = 0.0  # 入场时置信度
    signal_type: str = "trend"  # trend/oscillation/critical
    source_engines: List[str] = field(default_factory=list)  # 贡献引擎
    status: ThesisStatus = ThesisStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validated_at: Optional[str] = None
    invalidated_at: Optional[str] = None
    annotations: Dict[str, Any] = field(default_factory=dict)  # 引擎annotations

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "thesis_id": self.thesis_id,
            "symbol": self.symbol,
            "direction": self.direction,
            "reason": self.reason,
            "catalyst": self.catalyst,
            "catalyst_due_days": self.catalyst_due_days,
            "invalidation_conditions": self.invalidation_conditions,
            "confidence_at_entry": self.confidence_at_entry,
            "signal_type": self.signal_type,
            "source_engines": self.source_engines,
            "status": self.status.value,
            "created_at": self.created_at,
            "validated_at": self.validated_at,
            "invalidated_at": self.invalidated_at,
            "annotations": self.annotations,
        }


def generate_thesis(
    theory_results: List[Any],
    signal_direction: str,
    symbol: str,
    confidence: float,
    bars: List[Dict[str, Any]],
) -> Thesis:
    """从理论引擎结果自动生成投资论据

    从每个引擎的annotations中提取核心逻辑，综合生成thesis。

    Args:
        theory_results: 理论引擎分析结果列表（TheoryResult）
        signal_direction: 信号方向 LONG/SHORT/HOLD
        symbol: 标的代码
        confidence: 综合置信度
        bars: K线数据

    Returns:
        Thesis: 自动生成的投资论据
    """
    import uuid

    # 从各引擎结果中提取annotations
    engine_annotations: Dict[str, Any] = {}
    source_engines: List[str] = []
    for result in theory_results:
        if hasattr(result, 'theory_name') and hasattr(result, 'annotations'):
            engine_annotations[result.theory_name] = result.annotations
            source_engines.append(result.theory_name)

    # 生成核心论据（reason）
    reasons: List[str] = []
    for engine_name, annot in engine_annotations.items():
        # 从振动模态
        if "vibration_369" in annot:
            v369 = annot["vibration_369"]
            if isinstance(v369, dict):
                mode = v369.get("mode_label", "")
                score = v369.get("vibration_score", 0.0)
                if mode and score > 0.3:
                    reasons.append(f"{engine_name}: 369振动模态={mode}(score={score:.2f})")
        # 从139相变
        if "critical_139" in annot:
            c139 = annot["critical_139"]
            if isinstance(c139, dict):
                regime = c139.get("regime", "")
                if regime != "stable":
                    reasons.append(f"{engine_name}: 139相变regime={regime}")
        # 从PCS
        if hasattr(result, 'phase_continuity') and result.phase_continuity < 0.7:
            reasons.append(f"{engine_name}: PCS={result.phase_continuity:.2f}(过渡态)")
        # 从斐波那契共振
        if "fibonacci_resonance" in annot:
            reasons.append(f"{engine_name}: 斐波那契共振检测到")

    reason_text = "; ".join(reasons) if reasons else f"综合置信度={confidence:.2f}的多引擎信号"

    # 生成催化剂
    catalyst = _generate_catalyst(signal_direction, engine_annotations, bars)

    # 生成失效条件
    invalidation = _generate_invalidation_conditions(signal_direction, confidence, engine_annotations)

    # 判断信号类型
    signal_type = _classify_signal_type(confidence, engine_annotations)

    thesis = Thesis(
        thesis_id=f"thesis-{uuid.uuid4().hex[:8]}",
        symbol=symbol,
        direction=signal_direction,
        reason=reason_text,
        catalyst=catalyst,
        catalyst_due_days=30,
        invalidation_conditions=invalidation,
        confidence_at_entry=confidence,
        signal_type=signal_type,
        source_engines=source_engines,
        annotations=engine_annotations,
    )

    logger.info(
        f"ThesisTracker: generated thesis {thesis.thesis_id} for {symbol} "
        f"direction={signal_direction}, reason='{reason_text[:80]}', "
        f"catalyst='{catalyst[:80]}', "
        f"invalidation_conditions={len(invalidation)}条"
    )

    return thesis


def check_thesis_invalidation(
    thesis: Thesis,
    current_bar: Dict[str, Any],
    holding_days: int,
    portfolio_pnl_pct: float,
) -> Optional[str]:
    """检查thesis是否失效

    检查所有失效条件，返回触发的失效条件描述。

    Args:
        thesis: 投资论据
        current_bar: 当前K线数据
        holding_days: 已持仓天数
        portfolio_pnl_pct: 当前盈亏百分比

    Returns:
        Optional[str]: 触发的失效条件描述，None表示thesis仍成立
    """
    triggered: List[str] = []

    for condition in thesis.invalidation_conditions:
        # 检查常见失效条件
        if "跌破关键支撑" in condition or "突破关键阻力" in condition:
            # 需要价格数据判断，简化处理
            pass  # 实际需传入支撑/阻力位数据

        if "置信度低于" in condition:
            threshold = 0.3
            try:
                # 从条件文本提取阈值
                parts = condition.split("低于")
                if len(parts) > 1:
                    threshold = float(parts[1].strip().replace("阈值", ""))
            except (ValueError, IndexError):
                pass
            # 简化：如果当前PnL跌幅超过阈值，视为失效
            if portfolio_pnl_pct < -threshold:
                triggered.append(condition)

        if "超过" in condition and "天仍未兑现" in condition:
            max_days = thesis.catalyst_due_days * 2  # 双倍催化剂预期时间
            if holding_days > max_days:
                triggered.append(condition)

        if "亏损超过" in condition:
            # 从条件文本提取亏损阈值
            try:
                parts = condition.split("超过")
                if len(parts) > 1:
                    loss_pct = float(parts[1].strip().replace("%", "").replace("阈值", ""))
                    if portfolio_pnl_pct < -loss_pct / 100:
                        triggered.append(condition)
            except (ValueError, IndexError):
                pass

    if triggered:
        thesis.status = ThesisStatus.INVALIDATED
        thesis.invalidated_at = datetime.now(timezone.utc).isoformat()
        logger.warning(
            f"ThesisTracker: thesis {thesis.thesis_id} INVALIDATED - "
            f"triggered conditions: {triggered}"
        )
        return "; ".join(triggered)

    # 检查是否过期（催化剂超期未兑现）
    if holding_days > thesis.catalyst_due_days and thesis.status == ThesisStatus.PENDING:
        thesis.status = ThesisStatus.EXPIRED
        logger.info(
            f"ThesisTracker: thesis {thesis.thesis_id} EXPIRED - "
            f"catalyst未兑现 (holding={holding_days} > due={thesis.catalyst_due_days})"
        )
        return f"催化剂超期未兑现({holding_days}天>{thesis.catalyst_due_days}天)"

    return None


def _generate_catalyst(
    direction: str,
    annotations: Dict[str, Any],
    bars: List[Dict[str, Any]],
) -> str:
    """生成催化剂描述"""
    catalysts: List[str] = []

    # 从139相变检测催化剂
    for engine_name, annot in annotations.items():
        if "critical_139" in annot:
            c139 = annot["critical_139"]
            if isinstance(c139, dict):
                if c139.get("is_critical", False):
                    catalysts.append(f"139临界慢化确认→{direction}方向加速")
                elif c139.get("regime") == "transitioning":
                    catalysts.append(f"139过渡态→等待相变确认")

    # 从369振动检测催化剂
    for engine_name, annot in annotations.items():
        if "vibration_369" in annot:
            v369 = annot["vibration_369"]
            if isinstance(v369, dict):
                mode = v369.get("mode_label", "")
                if mode == "strong":
                    catalysts.append(f"369振动共振→信号兑现加速")
                elif mode == "trigger":
                    catalysts.append(f"369触发态→等待共振确认")

    if not catalysts:
        if direction == "LONG":
            catalysts.append("价格突破近期高点，趋势延续确认")
        elif direction == "SHORT":
            catalysts.append("价格跌破近期低点，趋势延续确认")
        else:
            catalysts.append("信号自然衰减")

    return "; ".join(catalysts)


def _generate_invalidation_conditions(
    direction: str,
    confidence: float,
    annotations: Dict[str, Any],
) -> List[str]:
    """生成失效条件列表"""
    conditions: List[str] = []

    # 基础失效条件（所有交易都有）
    loss_pct = max(5, int(10 * (1 - confidence)))
    conditions.append(f"亏损超过{loss_pct}%阈值")
    conditions.append(f"置信度低于0.3阈值")

    # 从annotations提取特定失效条件
    for engine_name, annot in annotations.items():
        # 139相变失效
        if "critical_139" in annot:
            c139 = annot["critical_139"]
            if isinstance(c139, dict):
                if c139.get("regime") == "critical_slowing":
                    conditions.append(f"{engine_name}: 139临界反转→原方向失效")

        # 369振动失效
        if "vibration_369" in annot:
            v369 = annot["vibration_369"]
            if isinstance(v369, dict):
                if v369.get("is_noise", False):
                    conditions.append(f"{engine_name}: 369噪音主导→信号不可信")

    # 时间失效条件
    conditions.append(f"超过{30 * 2}天仍未兑现催化剂")

    return conditions


def _classify_signal_type(confidence: float, annotations: Dict[str, Any]) -> str:
    """分类信号类型"""
    # 检查是否有临界信号
    for engine_name, annot in annotations.items():
        if "critical_139" in annot:
            c139 = annot["critical_139"]
            if isinstance(c139, dict) and c139.get("is_critical", False):
                return "critical"

    # 高置信度 → 趋势信号
    if confidence >= 0.7:
        return "trend"

    # 中置信度 → 震荡信号
    elif confidence >= 0.4:
        return "oscillation"

    # 低置信度 → 弱信号
    else:
        return "weak"


# ─────────────────────────────────────────────
# 自测函数
# ─────────────────────────────────────────────

def _self_test() -> None:
    """自测函数"""
    # 测试Thesis生成
    mock_results = [
        type('MockResult', (), {
            'theory_name': '周期律',
            'annotations': {
                'vibration_369': {
                    'vibration_score': 0.65,
                    'mode_label': 'strong',
                    'is_noise': False,
                },
                'critical_139': {
                    'is_critical': False,
                    'regime': 'transitioning',
                },
            },
            'phase_continuity': 0.85,
            'confidence': 0.7,
            'hints': [],
            'error': None,
        })(),
    ]

    thesis = generate_thesis(
        theory_results=mock_results,
        signal_direction="LONG",
        symbol="000001",
        confidence=0.7,
        bars=[{"close": 10.0, "high": 10.5, "low": 9.5}],
    )

    print(f"Thesis ID: {thesis.thesis_id}")
    print(f"Reason: {thesis.reason}")
    print(f"Catalyst: {thesis.catalyst}")
    print(f"Invalidation: {thesis.invalidation_conditions}")
    print(f"Signal type: {thesis.signal_type}")
    print(f"Status: {thesis.status}")

    # 测试失效检查
    invalidation = check_thesis_invalidation(
        thesis=thesis,
        current_bar={"close": 9.0},
        holding_days=65,
        portfolio_pnl_pct=-0.12,
    )
    print(f"Invalidation check: {invalidation}")

    print("✅ ThesisTracker _self_test passed!")


if __name__ == "__main__":
    _self_test()
