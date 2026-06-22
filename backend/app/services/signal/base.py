"""信号模块基础类型定义"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class SignalHint:
    """理论引擎的信号提示"""

    direction: str = "HOLD"  # LONG / SHORT / HOLD
    confidence: float = 0.0
    reason: str = ""
    price_target: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "direction": self.direction,
            "confidence": self.confidence,
            "reason": self.reason,
            "price_target": self.price_target,
        }


@dataclass
class TheoryResult:
    """理论引擎分析结果"""

    theory_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    annotations: Dict[str, Any] = field(default_factory=dict)
    hints: List[SignalHint] = field(default_factory=list)
    confidence: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "theory_name": self.theory_name,
            "timestamp": self.timestamp,
            "annotations": self.annotations,
            "hints": [h.to_dict() for h in self.hints],
            "confidence": self.confidence,
            "error": self.error,
        }


@dataclass
class Signal:
    """交易信号（服务层，非 ORM 模型）"""

    signal_id: str = field(default_factory=lambda: f"sig-{uuid.uuid4().hex[:8]}")
    symbol: str = ""
    market: str = "crypto"
    direction: str = "HOLD"  # LONG / SHORT / HOLD
    price: float = 0.0
    confidence: float = 0.0
    source_engine: str = ""  # taiji/spiral/elliott/tomas
    theory_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "market": self.market,
            "direction": self.direction,
            "price": self.price,
            "confidence": self.confidence,
            "source_engine": self.source_engine,
            "theory_name": self.theory_name,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class TheoryEngine(Protocol):
    """理论引擎协议（Protocol-based 接口）

    所有理论引擎需实现此协议，提供 analyze 方法。
    """

    name: str

    async def analyze(self, bars: List[Dict[str, Any]]) -> TheoryResult:
        """分析 K 线数据，返回理论结果

        Args:
            bars: K 线数据列表

        Returns:
            TheoryResult: 理论分析结果
        ...
        """
        ...
