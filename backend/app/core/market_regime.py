"""market_regime.py — Dalio经济象限检测器

借鉴Ray Dalio的"增长×通胀"4象限模型：
- EXPANSION: 增长↑通胀↑ → 股票/商品利好
- REFLATION: 增长↑通胀↓ → 股票利好，债券中性
- STAGFLATION: 增长↓通胀↑ → 商品利好，股票利空
- DEFLATION: 增长↓通胀↓ → 债券利好，股票利空

核心思想：不是预测具体方向，而是识别当前象限，
        在每个象限配置最合适的资产权重。

对应大师共识四：周期意识 — Dalio象限模型是周期意识的系统化版本。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from loguru import logger


class MarketRegime(str, Enum):
    """市场象限（Dalio 4象限模型）"""
    EXPANSION = "expansion"      # 增长↑通胀↑
    REFLATION = "reflation"       # 增长↑通胀↓
    STAGFLATION = "stagflation"   # 增长↓通胀↑
    DEFLATION = "deflation"       # 增长↓通胀↓


@dataclass
class RegimeResult:
    """象限检测结果"""
    regime: MarketRegime = MarketRegime.EXPANSION
    confidence: float = 0.0  # 象限判断置信度
    growth_signal: float = 0.0  # 增长信号强度（正=增长↑，负=增长↓）
    inflation_signal: float = 0.0  # 通胀信号强度（正=通胀↑，负=通胀↓）
    description: str = ""
    asset_weights: Dict[str, float] = field(default_factory=dict)  # 推荐资产权重

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "growth_signal": self.growth_signal,
            "inflation_signal": self.inflation_signal,
            "description": self.description,
            "asset_weights": self.asset_weights,
        }


# 每个象限的推荐资产权重（Dalio全天候模型的简化版）
REGIME_ASSET_WEIGHTS: Dict[MarketRegime, Dict[str, float]] = {
    MarketRegime.EXPANSION: {
        "equity": 0.40,   # 股票：增长期利好
        "commodity": 0.25, # 商品：通胀期利好
        "bond": 0.15,     # 债券：通胀期利空
        "gold": 0.10,     # 黄金：通胀对冲
        "cash": 0.10,     # 现金：缓冲
    },
    MarketRegime.REFLATION: {
        "equity": 0.50,   # 股票：增长期+低通胀=最强利好
        "commodity": 0.10, # 商品：低通胀利空
        "bond": 0.25,     # 债券：低通胀利好
        "gold": 0.05,     # 黄金：低通胀利空
        "cash": 0.10,     # 现金：缓冲
    },
    MarketRegime.STAGFLATION: {
        "equity": 0.10,   # 股票：滞胀期利空
        "commodity": 0.40, # 商品：通胀期利好
        "bond": 0.10,     # 债券：通胀期利空
        "gold": 0.30,     # 黄金：滞胀期最强利好
        "cash": 0.10,     # 现金：缓冲
    },
    MarketRegime.DEFLATION: {
        "equity": 0.15,   # 股票：通缩期利空
        "commodity": 0.05, # 商品：通缩期利空
        "bond": 0.50,     # 债券：通缩期最强利好
        "gold": 0.10,     # 黄金：通缩期中性
        "cash": 0.20,     # 现金：通缩期利好
    },
}


def detect_regime(
    prices: List[float],
    volumes: List[float],
    lookback: int = 139,
) -> RegimeResult:
    """检测当前市场象限

    从价格和成交量数据推断增长/通胀信号：
    - 增长信号：价格上涨趋势 + 成交量放大 → 增长↑
    - 通胀信号：价格波动率增大 + 价格持续走高 → 通胀↑

    Args:
        prices: 收盘价序列
        volumes: 成交量序列
        lookback: 回看窗口，默认139

    Returns:
        RegimeResult: 象限检测结果
    """
    if len(prices) < lookback or len(volumes) < lookback:
        logger.warning(
            f"MarketRegime: 数据不足 (prices={len(prices)}, volumes={len(volumes)}, "
            f"need={lookback}), 使用默认象限EXPANSION"
        )
        return RegimeResult(
            regime=MarketRegime.EXPANSION,
            confidence=0.0,
            description="数据不足，使用默认象限",
            asset_weights=REGIME_ASSET_WEIGHTS[MarketRegime.EXPANSION],
        )

    recent_prices = np.array(prices[-lookback:], dtype=np.float64)
    recent_volumes = np.array(volumes[-lookback:], dtype=np.float64)

    # ── 增长信号 ──
    # 方法1：价格趋势方向（线性回归斜率）
    x = np.arange(lookback, dtype=np.float64)
    slope, _ = np.polyfit(x, recent_prices, 1)
    # 标准化斜率（相对于均价的百分比变化率）
    mean_price = float(np.mean(recent_prices))
    growth_trend = slope / mean_price if mean_price > 0 else 0.0

    # 方法2：成交量趋势（放量=增长信号）
    vol_slope, _ = np.polyfit(x, recent_volumes, 1)
    mean_vol = float(np.mean(recent_volumes))
    volume_trend = vol_slope / mean_vol if mean_vol > 0 else 0.0

    # 综合增长信号
    growth_signal = growth_trend * 100 + volume_trend * 50  # 加权

    # ── 通胀信号 ──
    # 方法1：波动率变化（近期σ / 长期σ）
    short_window = min(30, lookback)
    short_sigma = float(np.std(recent_prices[-short_window:], ddof=1))
    long_sigma = float(np.std(recent_prices, ddof=1))
    sigma_ratio = short_sigma / long_sigma if long_sigma > 0 else 1.0

    # 方法2：价格加速度（二阶导数）
    returns = np.diff(recent_prices) / recent_prices[:-1]
    returns = returns[np.isfinite(returns)]
    if len(returns) > 10:
        # 近期回报率 vs 远期回报率
        recent_returns = returns[-short_window:]
        older_returns = returns[:-short_window]
        recent_mean_ret = float(np.mean(recent_returns))
        older_mean_ret = float(np.mean(older_returns)) if len(older_returns) > 0 else 0.0
        inflation_signal = (recent_mean_ret - older_mean_ret) * 100 + (sigma_ratio - 1.0) * 50
    else:
        inflation_signal = (sigma_ratio - 1.0) * 50

    # ── 象限判定 ──
    growth_up = growth_signal > 0
    inflation_up = inflation_signal > 0

    if growth_up and inflation_up:
        regime = MarketRegime.EXPANSION
        description = "增长↑通胀↑ — 扩张期，股票和商品利好"
    elif growth_up and not inflation_up:
        regime = MarketRegime.REFLATION
        description = "增长↑通胀↓ — 再膨胀期，股票最强利好"
    elif not growth_up and inflation_up:
        regime = MarketRegime.STAGFLATION
        description = "增长↓通胀↑ — 滞胀期，黄金和商品利好"
    else:
        regime = MarketRegime.DEFLATION
        description = "增长↓通胀↓ — 通缩期，债券最强利好"

    # 置信度：信号绝对值的平均值
    confidence = min(1.0, (abs(growth_signal) + abs(inflation_signal)) / 20.0)

    result = RegimeResult(
        regime=regime,
        confidence=round(confidence, 4),
        growth_signal=round(growth_signal, 4),
        inflation_signal=round(inflation_signal, 4),
        description=description,
        asset_weights=REGIME_ASSET_WEIGHTS[regime],
    )

    logger.info(
        f"MarketRegime: detected {regime.value} "
        f"(growth={growth_signal:.4f}, inflation={inflation_signal:.4f}, "
        f"confidence={confidence:.4f})"
    )

    return result


def get_regime_theory_weights(regime: MarketRegime) -> Dict[str, float]:
    """根据象限调整理论引擎权重

    不同象限下，不同理论引擎的表现不同：
    - EXPANSION：趋势引擎(taiji/spiral/elliott)权重↑
    - REFLATION：趋势引擎权重↑↑
    - STAGFLATION：周期引擎(cycle_law)权重↑，Gann角度↑
    - DEFLATION：均值回归(bg_moving_average)权重↑

    Args:
        regime: 当前市场象限

    Returns:
        Dict[str, float]: 各引擎的权重调整系数
    """
    default_keys = [
        "taiji", "spiral", "elliott_wave", "cycle_law",
        "dual_law", "gann_angle", "bg_moving_average",
    ]
    weight_adjustments: Dict[MarketRegime, Dict[str, float]] = {
        MarketRegime.EXPANSION: {
            "taiji": 1.2, "spiral": 1.2, "elliott_wave": 1.1,
            "cycle_law": 1.0, "dual_law": 1.0,
            "gann_angle": 0.9, "bg_moving_average": 0.8,
        },
        MarketRegime.REFLATION: {
            "taiji": 1.3, "spiral": 1.3, "elliott_wave": 1.2,
            "cycle_law": 0.9, "dual_law": 1.0,
            "gann_angle": 0.8, "bg_moving_average": 0.7,
        },
        MarketRegime.STAGFLATION: {
            "taiji": 0.7, "spiral": 0.8, "elliott_wave": 0.7,
            "cycle_law": 1.3, "dual_law": 1.2,
            "gann_angle": 1.3, "bg_moving_average": 1.0,
        },
        MarketRegime.DEFLATION: {
            "taiji": 0.6, "spiral": 0.7, "elliott_wave": 0.6,
            "cycle_law": 1.0, "dual_law": 1.1,
            "gann_angle": 0.9, "bg_moving_average": 1.4,
        },
    }

    return weight_adjustments.get(regime, {k: 1.0 for k in default_keys})


def _self_test() -> None:
    """自测函数"""
    import random

    # 测试EXPANSION象限
    prices = [100 + i * 0.5 + random.gauss(0, 1) for i in range(200)]
    volumes = [1000 + i * 10 + random.gauss(0, 50) for i in range(200)]
    result = detect_regime(prices, volumes)
    print(f"EXPANSION test: regime={result.regime.value}, confidence={result.confidence}")
    assert result.regime in [MarketRegime.EXPANSION, MarketRegime.REFLATION]

    # 测试STAGFLATION象限
    prices2 = [100 - i * 0.3 + random.gauss(0, 2) for i in range(200)]
    volumes2 = [1000 - i * 5 + random.gauss(0, 30) for i in range(200)]
    result2 = detect_regime(prices2, volumes2)
    print(f"STAGFLATION test: regime={result2.regime.value}, confidence={result2.confidence}")

    # 测试权重调整
    weights = get_regime_theory_weights(MarketRegime.EXPANSION)
    print(f"EXPANSION theory weights: {weights}")

    print("✅ MarketRegime _self_test passed!")


if __name__ == "__main__":
    _self_test()
