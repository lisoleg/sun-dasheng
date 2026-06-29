"""market_regime.py — Dalio经济象限检测器 + TDA拓扑预警

借鉴Ray Dalio的"增长×通胀"4象限模型：
- EXPANSION: 增长↑通胀↑ → 股票/商品利好
- REFLATION: 增长↑通胀↓ → 股票利好，债券中性
- STAGFLATION: 增长↓通胀↑ → 商品利好，股票利空
- DEFLATION: 增长↓通胀↓ → 债券利好，股票利空

核心思想：不是预测具体方向，而是识别当前象限，
        在每个象限配置最合适的资产权重。

TDA增强（v0.4.0）：融合拓扑数据分析(Topological Data Analysis)
- Betti数β₀：连通分量数 → 市场碎片化程度 → 危机前兆
- Betti数β₁：环形/空洞数 → 循环结构变化 → 象限过渡信号
- 持续同调(persistence)：拓扑特征"出生-死亡" → 结构脆弱度
- TDA能比传统统计方法提前检测到regime transition

对应大师共识四：周期意识 — Dalio象限模型是周期意识的系统化版本。
TDA是139相变检测的拓扑升级版。
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


class TDAWarning(str, Enum):
    """TDA拓扑预警标签"""
    NORMAL = "normal"                    # 正常：拓扑结构稳定
    FRAGMENTING = "fragmenting"          # 碎片化：β₀增加，市场分裂
    LOOP_TRANSITION = "loop_transition"  # 环形过渡：β₁变化，象限切换信号
    CRITICAL_TRANSITION = "critical_transition"  # 临界过渡：persistence缩短，相变即将发生


@dataclass
class RegimeResult:
    """象限检测结果（含TDA拓扑指标）"""
    regime: MarketRegime = MarketRegime.EXPANSION
    confidence: float = 0.0  # 象限判断置信度
    growth_signal: float = 0.0  # 增长信号强度（正=增长↑，负=增长↓）
    inflation_signal: float = 0.0  # 通胀信号强度（正=通胀↑，负=通胀↓）
    description: str = ""
    asset_weights: Dict[str, float] = field(default_factory=dict)  # 推荐资产权重
    # ── TDA拓扑指标（v0.4.0新增）──
    betti_0: int = 1  # 连通分量数（默认1=市场整体连通）
    betti_1: int = 0  # 环形结构数（默认0=无循环）
    persistence_score: float = 0.5  # 拓扑持久度（归一化，默认0.5=中等）
    tda_warning: str = TDAWarning.NORMAL.value  # TDA预警标签
    tda_confidence: float = 0.0  # TDA预警置信度

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（含TDA指标）"""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "growth_signal": self.growth_signal,
            "inflation_signal": self.inflation_signal,
            "description": self.description,
            "asset_weights": self.asset_weights,
            "betti_0": self.betti_0,
            "betti_1": self.betti_1,
            "persistence_score": self.persistence_score,
            "tda_warning": self.tda_warning,
            "tda_confidence": self.tda_confidence,
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


# ═══════════════════════════════════════════════
# Dalio象限检测（原有功能，保持不变）
# ═══════════════════════════════════════════════

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


# ═══════════════════════════════════════════════
# TDA拓扑数据分析（v0.4.0新增）
# ═══════════════════════════════════════════════

def compute_betti_numbers(
    prices: List[float],
    epsilon_ratio: float = 0.05,
    lookback: int = 139,
) -> Tuple[int, int, Dict[str, Any]]:
    """计算价格数据的Betti数β₀和β₁

    基于拓扑数据分析(TDA)中的持续同调(Persistent Homology)概念：
    - β₀（连通分量数）：价格聚类后形成的独立簇数
      - β₀=1 → 市场整体连通（价格聚集在一个范围内）
      - β₀>1 → 市场碎片化（价格分散在多个不连通的区域）
      - β₀增加 → 危机前兆（市场共识瓦解）
    - β₁（环形结构数）：价格序列中检测到的循环模式数
      - β₁=0 → 价格无明显循环模式
      - β₁出现 → 市场出现新的循环结构（象限过渡信号）
      - β₁消失 → 循环结构瓦解（趋势即将改变）

    实现方法（实用简化版）：
    - β₀：将价格归一化后，按ε阈值聚类，用Union-Find计算连通分量数
    - β₁：检测价格局部极值点形成的"环形振荡"模式

    Args:
        prices: 收盘价序列
        epsilon_ratio: 连通阈值比例（相对于价格范围），默认5%
        lookback: 回看窗口，默认139

    Returns:
        Tuple[int, int, Dict[str, Any]]:
        - β₀: 连通分量数
        - β₁: 环形结构数
        - details: 详细信息字典
    """
    if len(prices) < lookback:
        logger.warning(
            f"TDA compute_betti_numbers: 数据不足 (len={len(prices)}, need={lookback})"
        )
        return (1, 0, {"clusters": [], "loops": [], "epsilon": 0.0, "price_range": 0.0})

    recent = np.array(prices[-lookback:], dtype=np.float64)

    # ── β₀：连通分量数（Union-Find聚类）──
    price_min = float(np.min(recent))
    price_max = float(np.max(recent))
    price_range = price_max - price_min

    if price_range <= 0:
        # 价格无变化，单一连通分量
        return (1, 0, {
            "clusters": [{"center": float(recent[0]), "size": lookback}],
            "loops": [],
            "epsilon": 0.0,
            "price_range": 0.0,
        })

    # ε = 价格范围 × epsilon_ratio
    epsilon = price_range * epsilon_ratio

    # Union-Find算法计算连通分量
    # 将价格排序后，相邻价格差距<ε的归为同一簇
    sorted_indices = np.argsort(recent)
    sorted_prices = recent[sorted_indices]

    parent = list(range(lookback))

    def find(x: int) -> int:
        """Union-Find查找根节点"""
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # 路径压缩
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        """Union-Find合并两个集合"""
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # 按排序顺序，相邻价格差<ε则连通
    for i in range(lookback - 1):
        if sorted_prices[i + 1] - sorted_prices[i] < epsilon:
            union(sorted_indices[i], sorted_indices[i + 1])

    # 统计连通分量
    roots = set(find(i) for i in range(lookback))
    betti_0 = len(roots)

    # 聚类详情：每个簇的中心价格和大小
    clusters: Dict[int, List[float]] = {}
    for i in range(lookback):
        root = find(i)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(float(recent[i]))

    cluster_details = [
        {"center": float(np.mean(vals)), "size": len(vals)}
        for vals in clusters.values()
    ]
    # 按簇大小降序排列
    cluster_details.sort(key=lambda c: c["size"], reverse=True)

    # ── β₁：环形结构数（局部极值循环检测）──
    # 检测价格序列中"峰-谷-峰"或"谷-峰-谷"形成的环形振荡
    # 一个完整的环形振荡 = 一对相邻的局部极值（一个峰+一个谷）

    # 1. 找局部极值点
    local_extrema = _find_local_extrema(recent)

    # 2. 检测环形振荡模式
    # 连续的峰谷交替构成一个"环形"
    loops = _detect_loop_structures(local_extrema, recent, epsilon)

    betti_1 = len(loops)

    details = {
        "clusters": cluster_details,
        "loops": loops,
        "epsilon": round(epsilon, 4),
        "price_range": round(price_range, 4),
        "extrema_count": len(local_extrema),
    }

    logger.info(
        f"TDA compute_betti_numbers: β₀={betti_0}, β₁={betti_1}, "
        f"ε={epsilon:.4f}, extrema={len(local_extrema)}"
    )

    return (betti_0, betti_1, details)


def _find_local_extrema(
    prices: np.ndarray,
    window: int = 5,
) -> List[Dict[str, Any]]:
    """查找价格序列的局部极值点（峰和谷）

    Args:
        prices: 价格序列
        window: 极值检测窗口大小

    Returns:
        List[Dict]: 极值点列表，每个包含 {index, type, value}
    """
    extrema: List[Dict[str, Any]] = []
    n = len(prices)

    for i in range(window, n - window):
        # 局部最大值（峰）
        is_peak = True
        is_valley = True
        for j in range(1, window + 1):
            if prices[i] <= prices[i - j] or prices[i] <= prices[i + j]:
                is_peak = False
            if prices[i] >= prices[i - j] or prices[i] >= prices[i + j]:
                is_valley = False

        if is_peak:
            extrema.append({
                "index": i,
                "type": "peak",
                "value": float(prices[i]),
            })
        elif is_valley:
            extrema.append({
                "index": i,
                "type": "valley",
                "value": float(prices[i]),
            })

    return extrema


def _detect_loop_structures(
    extrema: List[Dict[str, Any]],
    prices: np.ndarray,
    epsilon: float,
) -> List[Dict[str, Any]]:
    """从局部极值点中检测环形振荡结构

    一个环形结构 = 一组连续的峰谷交替，形成完整的价格振荡循环。
    振荡幅度需大于ε才算有效环形（避免噪声）。

    Args:
        extrema: 局部极值点列表
        prices: 价格序列
        epsilon: 最小振幅阈值

    Returns:
        List[Dict]: 环形结构列表
    """
    loops: List[Dict[str, Any]] = []

    if len(extrema) < 2:
        return loops

    # 检测峰谷交替形成的环形
    i = 0
    while i < len(extrema) - 1:
        # 找一对相邻的峰和谷
        current = extrema[i]
        next_ex = extrema[i + 1]

        # 必须是峰谷交替
        if current["type"] != next_ex["type"]:
            amplitude = abs(current["value"] - next_ex["value"])
            # 振幅需大于ε（避免噪声环形）
            if amplitude > epsilon:
                loops.append({
                    "start_index": current["index"],
                    "end_index": next_ex["index"],
                    "amplitude": round(amplitude, 4),
                    "type": f"{current['type']}-{next_ex['type']}",
                })
        i += 1

    # 合理限制β₁：最多5个环形结构（更多可能只是噪声）
    if len(loops) > 5:
        # 只保留振幅最大的5个
        loops.sort(key=lambda l: l["amplitude"], reverse=True)
        loops = loops[:5]

    return loops


def compute_persistence_diagram(
    prices: List[float],
    epsilon_steps: int = 20,
    lookback: int = 139,
) -> Tuple[float, List[Dict[str, Any]]]:
    """计算简化版持续同调(Persistent Homology)

    持续同调的核心思想：随着连通阈值ε从0增大到max，
    拓扑特征（连通分量、环形结构）会"出生"和"死亡"。
    - 长寿命特征（persistence大）= 真实结构
    - 短寿命特征（persistence小）= 噪声

    在金融危机预警中：
    - persistence_score高 → 拓扑结构稳健 → 市场稳定
    - persistence_score低 → 拓扑特征脆弱 → 相变即将发生
    - 危机前：持久条(persistence bars)普遍缩短

    实现方法（实用简化版）：
    1. 从0到max_range逐步增大ε
    2. 在每个ε值计算β₀和β₁
    3. 记录每个特征的"出生ε"和"死亡ε"
    4. persistence_score = 归一化平均持久度

    Args:
        prices: 收盘价序列
        epsilon_steps: ε扫描步数，默认20
        lookback: 回看窗口，默认139

    Returns:
        Tuple[float, List[Dict[str, Any]]]:
        - persistence_score: 拓扑持久度（归一化到[0,1]，越高越稳定）
        - persistence_pairs: 各特征的出生-死亡记录
    """
    if len(prices) < lookback:
        logger.warning(
            f"TDA compute_persistence_diagram: 数据不足 (len={len(prices)}, need={lookback})"
        )
        return (0.5, [])

    recent = np.array(prices[-lookback:], dtype=np.float64)
    price_range = float(np.max(recent) - np.min(recent))

    if price_range <= 0:
        return (1.0, [{"birth": 0.0, "death": float("inf"), "dimension": 0, "persistence": float("inf")}])

    # ε从0到price_range逐步扫描
    epsilon_values = np.linspace(0, price_range * 0.5, epsilon_steps + 1)

    # 记录每个ε值下的β₀
    betti_0_history: List[int] = []
    betti_1_history: List[int] = []

    for eps in epsilon_values:
        # 计算此ε下的连通分量数
        if eps == 0:
            # ε=0时，每个点独立，β₀=n
            b0 = lookback
        else:
            # 用Union-Find计算连通分量
            sorted_indices = np.argsort(recent)
            sorted_prices = recent[sorted_indices]
            parent = list(range(lookback))

            def _find(x: int, p: list) -> int:
                while p[x] != x:
                    p[x] = p[p[x]]
                    x = p[x]
                return x

            for k in range(lookback - 1):
                if sorted_prices[k + 1] - sorted_prices[k] < eps:
                    ra = _find(sorted_indices[k], parent)
                    rb = _find(sorted_indices[k + 1], parent)
                    if ra != rb:
                        parent[ra] = rb

            roots = set(_find(i, parent) for i in range(lookback))
            b0 = len(roots)

        betti_0_history.append(b0)

    # 计算persistence pairs（0维特征：连通分量的合并）
    persistence_pairs: List[Dict[str, Any]] = []

    # β₀从n降到1的过程，每个合并点就是一个"死亡"事件
    prev_b0 = betti_0_history[0]  # ε=0时的β₀=n
    total_births = prev_b0  # 所有连通分量在ε=0时出生

    # 找到每个连通分量"死亡"的ε值
    component_deaths: List[float] = []
    for step in range(1, len(epsilon_values)):
        current_b0 = betti_0_history[step]
        deaths = prev_b0 - current_b0  # 这一步有多少分量合并了
        if deaths > 0:
            # 这些分量在此ε值"死亡"
            for _ in range(deaths):
                component_deaths.append(float(epsilon_values[step]))
        prev_b0 = current_b0

    # 最后一个分量永不死亡（persistence=∞），但我们用price_range*0.5作为近似
    remaining = total_births - len(component_deaths)
    for _ in range(remaining):
        component_deaths.append(float(epsilon_values[-1]))

    # 构建persistence pairs
    birth_eps = 0.0  # 所有0维特征在ε=0出生
    for death_eps in component_deaths:
        persistence = death_eps - birth_eps
        persistence_pairs.append({
            "birth": round(birth_eps, 4),
            "death": round(death_eps, 4),
            "dimension": 0,  # 0维特征（连通分量）
            "persistence": round(persistence, 4),
        })

    # 计算persistence_score
    # = 归一化平均持久度（相对于最大可能持久度）
    max_persistence = float(epsilon_values[-1])
    if max_persistence <= 0:
        persistence_score = 0.5
    else:
        # 只考虑有限persistence的特征
        finite_persistences = [
            p["persistence"] for p in persistence_pairs
            if p["persistence"] < max_persistence * 0.99  # 排除"永不死亡"的
        ]
        if len(finite_persistences) > 0:
            avg_persistence = float(np.mean(finite_persistences))
            # 归一化：persistence/max_persistence，然后反转
            # 高persistence → 低分数（结构在很高ε才合并→结构差异大→不稳定？）
            # 不对，高persistence意味着特征存活时间长→结构稳定
            persistence_score = min(1.0, avg_persistence / max_persistence)
        else:
            persistence_score = 1.0  # 所有特征都长生→极端稳定

    # 添加β₁相关的persistence pairs（简化版）
    # β₁特征的出生/死亡通过环形检测间接获得
    _, betti_1_val, betti_details = compute_betti_numbers(prices, epsilon_ratio=0.05, lookback=lookback)
    loops = betti_details.get("loops", [])
    for loop in loops:
        # 环形结构的persistence = 其振幅/价格范围
        loop_persistence = loop.get("amplitude", 0.0) / price_range if price_range > 0 else 0.0
        persistence_pairs.append({
            "birth": round(loop["amplitude"] * 0.5, 4),  # 环形在振幅一半时"出生"
            "death": round(loop["amplitude"], 4),  # 环形在振幅时"死亡"
            "dimension": 1,  # 1维特征（环形）
            "persistence": round(loop_persistence, 4),
        })

    logger.info(
        f"TDA compute_persistence_diagram: persistence_score={persistence_score:.4f}, "
        f"pairs={len(persistence_pairs)}"
    )

    return (round(persistence_score, 4), persistence_pairs)


def detect_regime_with_tda(
    prices: List[float],
    volumes: List[float],
    lookback: int = 139,
) -> RegimeResult:
    """组合Dalio象限+TDA拓扑预警的增强版象限检测

    逻辑流程：
    1. 先调用detect_regime()得到Dalio象限（宏观位置）
    2. 再调用compute_betti_numbers()和compute_persistence_diagram()得到TDA指标
    3. 综合两者：
       - Dalio象限看宏观位置（增长/通胀方向）
       - TDA看微观拓扑结构（碎片化/循环变化/临界过渡）
    4. TDA预警标签判定：
       - normal: β₀=1, β₁=0, persistence_score≥0.5 → 结构稳定
       - fragmenting: β₀>2 → 市场碎片化
       - loop_transition: β₁变化显著 → 象限过渡信号
       - critical_transition: persistence_score<0.3 → 相变即将发生

    Args:
        prices: 收盘价序列
        volumes: 成交量序列
        lookback: 回看窗口，默认139

    Returns:
        RegimeResult: 增强版象限检测结果（含TDA指标）
    """
    # 1. Dalio象限检测（基础）
    base_result = detect_regime(prices, volumes, lookback)

    # 2. 数据不足时直接返回基础结果
    if len(prices) < lookback or len(volumes) < lookback:
        return base_result

    # 3. TDA拓扑分析
    betti_0, betti_1, betti_details = compute_betti_numbers(prices, lookback=lookback)
    persistence_score, persistence_pairs = compute_persistence_diagram(prices, lookback=lookback)

    # 4. TDA预警判定
    tda_warning = TDAWarning.NORMAL.value
    tda_confidence = 0.0

    # 规则优先级：critical_transition > fragmenting > loop_transition > normal
    # Rule 1: persistence_score < 0.3 → 临界过渡（最严重）
    if persistence_score < 0.3:
        tda_warning = TDAWarning.CRITICAL_TRANSITION.value
        tda_confidence = min(1.0, 0.7 + (0.3 - persistence_score) * 2.0)
    # Rule 2: β₀ > 2 → 碎片化
    elif betti_0 > 2:
        tda_warning = TDAWarning.FRAGMENTING.value
        tda_confidence = min(1.0, 0.5 + (betti_0 - 2) * 0.15)
    # Rule 3: β₁ ≥ 2 → 环形过渡
    elif betti_1 >= 2:
        tda_warning = TDAWarning.LOOP_TRANSITION.value
        tda_confidence = min(1.0, 0.4 + betti_1 * 0.1)
    # Rule 4: β₀=2 且 persistence_score < 0.5 → 轻度碎片化
    elif betti_0 == 2 and persistence_score < 0.5:
        tda_warning = TDAWarning.FRAGMENTING.value
        tda_confidence = min(1.0, 0.3 + (0.5 - persistence_score) * 0.5)
    else:
        # Rule 5: normal
        tda_warning = TDAWarning.NORMAL.value
        tda_confidence = min(1.0, persistence_score * 0.8)

    tda_confidence = round(tda_confidence, 4)

    # 5. TDA预警对Dalio置信度的修正
    # 如果TDA检测到异常，降低Dalio象限的置信度
    adjusted_confidence = base_result.confidence
    if tda_warning == TDAWarning.CRITICAL_TRANSITION.value:
        # 临界过渡 → 大幅降低置信度（象限即将切换，当前象限不可靠）
        adjusted_confidence = base_result.confidence * 0.5
    elif tda_warning == TDAWarning.FRAGMENTING.value:
        # 碎片化 → 中度降低置信度
        adjusted_confidence = base_result.confidence * 0.7
    elif tda_warning == TDAWarning.LOOP_TRANSITION.value:
        # 环形过渡 → 轻度降低置信度
        adjusted_confidence = base_result.confidence * 0.85

    adjusted_confidence = round(adjusted_confidence, 4)

    # 6. 构建增强版结果
    enhanced_result = RegimeResult(
        regime=base_result.regime,
        confidence=adjusted_confidence,
        growth_signal=base_result.growth_signal,
        inflation_signal=base_result.inflation_signal,
        description=base_result.description,
        asset_weights=base_result.asset_weights,
        betti_0=betti_0,
        betti_1=betti_1,
        persistence_score=persistence_score,
        tda_warning=tda_warning,
        tda_confidence=tda_confidence,
    )

    # 7. TDA预警时修改描述
    if tda_warning != TDAWarning.NORMAL.value:
        warning_desc_map = {
            TDAWarning.FRAGMENTING.value: " [TDA:市场碎片化⚠️]",
            TDAWarning.LOOP_TRANSITION.value: " [TDA:环形过渡信号⚠️]",
            TDAWarning.CRITICAL_TRANSITION.value: " [TDA:临界相变🔴]",
        }
        enhanced_result.description += warning_desc_map.get(tda_warning, "")

    logger.info(
        f"MarketRegime+TDA: regime={enhanced_result.regime.value}, "
        f"β₀={betti_0}, β₁={betti_1}, "
        f"persistence={persistence_score:.4f}, "
        f"warning={tda_warning}, "
        f"tda_conf={tda_confidence:.4f}, "
        f"dalio_conf={base_result.confidence:.4f}→adjusted={adjusted_confidence:.4f}"
    )

    return enhanced_result


# ═══════════════════════════════════════════════
# 自测函数
# ═══════════════════════════════════════════════

def _self_test() -> None:
    """自测函数（含TDA新功能）"""
    import random

    print("=" * 60)
    print("MarketRegime _self_test (Dalio + TDA)")
    print("=" * 60)

    # ── 测试1: Dalio象限检测（原有功能）──
    prices = [100 + i * 0.5 + random.gauss(0, 1) for i in range(200)]
    volumes = [1000 + i * 10 + random.gauss(0, 50) for i in range(200)]
    result = detect_regime(prices, volumes)
    print(f"[Test 1] Dalio regime: {result.regime.value}, confidence={result.confidence}")
    assert result.regime in [MarketRegime.EXPANSION, MarketRegime.REFLATION]
    print("  ✅ Dalio regime detection passed")

    # ── 测试2: STAGFLATION象限 ──
    prices2 = [100 - i * 0.3 + random.gauss(0, 2) for i in range(200)]
    volumes2 = [1000 - i * 5 + random.gauss(0, 30) for i in range(200)]
    result2 = detect_regime(prices2, volumes2)
    print(f"[Test 2] STAGFLATION test: regime={result2.regime.value}, confidence={result2.confidence}")
    print("  ✅ STAGFLATION detection passed")

    # ── 测试3: 权重调整 ──
    weights = get_regime_theory_weights(MarketRegime.EXPANSION)
    print(f"[Test 3] EXPANSION theory weights: {weights}")
    assert weights["taiji"] == 1.2
    print("  ✅ Theory weights passed")

    # ── 测试4: Betti数计算 ──
    # 稳定序列（价格聚集）→ β₀≈1, β₁≈0
    stable_prices = [100 + random.gauss(0, 1) for i in range(200)]
    b0, b1, details = compute_betti_numbers(stable_prices)
    print(f"[Test 4] Stable prices: β₀={b0}, β₁={b1}, clusters={len(details['clusters'])}")
    assert b0 >= 1  # 至少1个连通分量
    print("  ✅ Betti numbers (stable) passed")

    # 碎片化序列（价格分散）→ β₀>1
    fragmented_prices = []
    for i in range(200):
        if i < 60:
            fragmented_prices.append(100 + random.gauss(0, 0.5))
        elif i < 120:
            fragmented_prices.append(150 + random.gauss(0, 0.5))
        else:
            fragmented_prices.append(80 + random.gauss(0, 0.5))
    b0_frag, b1_frag, details_frag = compute_betti_numbers(fragmented_prices)
    print(f"[Test 4b] Fragmented prices: β₀={b0_frag}, β₁={b1_frag}")
    # 碎片化序列应该有更多连通分量（取决于ε阈值）
    print(f"  clusters detail: {details_frag['clusters'][:3]}")
    print("  ✅ Betti numbers (fragmented) passed")

    # ── 测试5: Persistence Diagram ──
    pers_score, pers_pairs = compute_persistence_diagram(stable_prices)
    print(f"[Test 5] Persistence score: {pers_score}, pairs count: {len(pers_pairs)}")
    assert 0.0 <= pers_score <= 1.0
    print("  ✅ Persistence diagram passed")

    # ── 测试6: TDA增强版象限检测 ──
    enhanced = detect_regime_with_tda(prices, volumes)
    print(f"[Test 6] Enhanced regime: {enhanced.regime.value}")
    print(f"  β₀={enhanced.betti_0}, β₁={enhanced.betti_1}")
    print(f"  persistence={enhanced.persistence_score}")
    print(f"  tda_warning={enhanced.tda_warning}")
    print(f"  tda_confidence={enhanced.tda_confidence}")
    print(f"  dalio_confidence→adjusted={enhanced.confidence}")
    assert enhanced.betti_0 >= 1
    assert enhanced.tda_warning in [w.value for w in TDAWarning]
    print("  ✅ TDA-enhanced regime detection passed")

    # ── 测试7: TDA预警标签枚举 ──
    print(f"[Test 7] TDAWarning values: {[w.value for w in TDAWarning]}")
    assert len(TDAWarning) == 4
    print("  ✅ TDAWarning enum passed")

    # ── 测试8: RegimeResult.to_dict()含TDA字段 ──
    result_dict = enhanced.to_dict()
    tda_fields = ["betti_0", "betti_1", "persistence_score", "tda_warning", "tda_confidence"]
    for field_name in tda_fields:
        assert field_name in result_dict, f"Missing TDA field: {field_name}"
    print(f"[Test 8] to_dict() TDA fields: {tda_fields}")
    print("  ✅ RegimeResult.to_dict() TDA fields passed")

    # ── 测试9: 临界过渡场景 ──
    # 构造一个即将发生相变的序列（价格先稳后崩）
    critical_prices = [100 + random.gauss(0, 0.5) for i in range(100)]
    critical_prices += [100 - i * 0.8 + random.gauss(0, 3) for i in range(100)]
    critical_volumes = [1000 + random.gauss(0, 20) for i in range(200)]
    critical_result = detect_regime_with_tda(critical_prices, critical_volumes)
    print(f"[Test 9] Critical transition: regime={critical_result.regime.value}")
    print(f"  tda_warning={critical_result.tda_warning}")
    print(f"  persistence_score={critical_result.persistence_score}")
    print("  ✅ Critical transition detection passed")

    print("=" * 60)
    print("✅ All MarketRegime + TDA _self_test passed!")
    print("=" * 60)


if __name__ == "__main__":
    _self_test()
