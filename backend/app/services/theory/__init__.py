"""鲁兆理论引擎包 - 导出七大理论引擎"""

from app.services.theory.taiji import TaijiEngine
from app.services.theory.spiral import SpiralEngine
from app.services.theory.elliott_wave import ElliottWaveEngine
from app.services.theory.dual_law import DualLawEngine
from app.services.theory.cycle_law import CycleLawEngine
from app.services.theory.gann_angle import GannAngleEngine
from app.services.theory.bg_moving_average import BGMovingAverageEngine

__all__ = [
    "TaijiEngine",
    "SpiralEngine",
    "ElliottWaveEngine",
    "DualLawEngine",
    "CycleLawEngine",
    "GannAngleEngine",
    "BGMovingAverageEngine",
]


def get_all_engines() -> list:
    """获取所有理论引擎实例"""
    return [
        TaijiEngine(),
        SpiralEngine(),
        ElliottWaveEngine(),
        DualLawEngine(),
        CycleLawEngine(),
        GannAngleEngine(),
        BGMovingAverageEngine(),
    ]


def get_engine_by_name(name: str) -> Any:
    """根据名称获取理论引擎实例"""
    name_map = {
        "taiji": TaijiEngine,
        "spiral": SpiralEngine,
        "elliott": ElliottWaveEngine,
        "dual_law": DualLawEngine,
        "cycle_law": CycleLawEngine,
        "gann_angle": GannAngleEngine,
        "bg_ma": BGMovingAverageEngine,
    }
    engine_class = name_map.get(name)
    if engine_class:
        return engine_class()
    return None
