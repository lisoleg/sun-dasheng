"""鲁兆理论引擎抽象基类 - 定义统一分析接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TheoryResult:
    """理论分析结果数据类

    Attributes:
        theory_name: 理论名称
        timestamp: 分析时间戳
        annotations: 标注信息字典，用于图表绘制
        hints: 信号提示列表，每个hint包含类型、方向、置信度等
        confidence: 整体置信度 0.0-1.0
    """

    theory_name: str
    timestamp: str
    annotations: Dict[str, Any] = field(default_factory=dict)
    hints: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0


class TheoryEngine(ABC):
    """鲁兆理论引擎抽象基类

    所有理论引擎（太极中心律、螺旋律、波浪理论）必须实现此接口。
    每个引擎负责：
    1. 对K线数据进行理论分析（analyze）
    2. 生成图表标注信息（get_annotations）
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """理论引擎名称"""
        ...

    @abstractmethod
    def analyze(self, bars: List[Dict]) -> TheoryResult:
        """对K线数据进行理论分析

        Args:
            bars: K线数据列表，每条为包含open/high/low/close/volume/timestamp的字典

        Returns:
            TheoryResult 分析结果
        """
        ...

    @abstractmethod
    def get_annotations(self, bars: List[Dict]) -> List[Dict]:
        """获取图表标注信息

        Args:
            bars: K线数据列表

        Returns:
            标注列表，每个标注包含位置、类型、描述等
        """
        ...
