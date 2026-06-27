"""
cosmic_algorithm.py — 宇宙算法三重奏 (7-139-369) 核心库

基于《宇宙算法的三重奏》文章实现：
- 7（结构自指）：循环群 Z_7 完美闭合，142857 是 1/7 的循环节
- 139（临界演化）：Landau-Ising 相变阈值，复杂系统临界慢化征兆检测
- 369（振动法则）：模9群的触发-共振-归整三阶段投影

算法交易三层架构：
- 信号层：369数字根过滤剔除市场噪音
- 时间层：139-day周期聚类结合斐波那契共振确认趋势拐点
- 风控层：139窗口自动缩仓，波动率σ触发硬止损

参考文献：
[1] 宇宙算法的三重奏：7-139-369
[2] Landau-Ising 相变理论
[3] κ-Snap 动态演化框架
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from loguru import logger


# ─────────────────────────────────────────────
# 常量定义
# ─────────────────────────────────────────────

# 369振动法则模态阈值
VIBRATION_STRONG_THRESHOLD: float = 0.6  # 振动模态分数 ≥ 此值 → 信号可信
VIBRATION_NOISE_THRESHOLD: float = 0.3   # 振动模态分数 < 此值 → 噪音主导

# 139相变阈值判定
CRITICAL_VARIANCE_RATIO: float = 1.5     # 方差比值阈值（近期/长期）
CRITICAL_AUTOCORR: float = 0.3           # 自相关系数阈值
CRITICAL_RECOVERY_SLOW: float = 0.5      # 恢复速率慢化阈值
CRITICAL_SCORE_THRESHOLD: float = 2.0    # ≥2个征兆 → 进入临界慢化

# 7循环群闭合阈值
CYCLE_7_CLOSURE_THRESHOLD: float = 0.3   # 闭合度评分 ≥ 此值 → 有循环群特征

# 142857循环节（1/7的循环节）
CIRCULATING_UNIT_7: str = "142857"


# ─────────────────────────────────────────────
# 函数1: digital_root
# ─────────────────────────────────────────────

def digital_root(n: int) -> int:
    """
    数字根计算

    对自然数反复求和直至一位数，本质是 mod 9 运算。
    规则：n % 9，但 0 的数字根是 9（而非 0）。
    这是模9群 Z_9 的基础运算，支撑 369 振动法则的投影逻辑。

    数学性质：
        digital_root(a + b) = digital_root(digital_root(a) + digital_root(b))
        digital_root(a × b) = digital_root(digital_root(a) × digital_root(b))
        数字根 = 3 → 触发模态（Inflow开启）
        数字根 = 6 → 共振模态（谐波倍频）
        数字根 = 9 → 归整模态（极性统一）

    Args:
        n: 自然数

    Returns:
        数字根 [1, 9]

    Examples:
        >>> digital_root(369)
        9
        >>> digital_root(142857)
        9
        >>> digital_root(139)
        4
        >>> digital_root(0)
        9
    """
    if n == 0:
        return 9
    remainder = n % 9
    return 9 if remainder == 0 else remainder


# ─────────────────────────────────────────────
# 函数2: vibration_mode_369
# ─────────────────────────────────────────────

def vibration_mode_369(prices: np.ndarray, window: int = 20) -> Dict:
    """
    369振动模态检测

    对近 window 根K线的收益率序列计算数字根序列，
    统计数字根分布，计算"振动模态分数"。

    三阶段投影逻辑（κ-Snap动态演化）：
        - 触发模态(数字根=3): 代表 Inflow 开启，正电荷积累
        - 共振模态(数字根=6): 代表谐波倍频，负电荷镜像响应
        - 归整模态(数字根=9): 代表极性统一，能量释放归零

    振动模态分数 = (触发频率 + 共振频率 + 归整频率) / 总频率

    判定规则：
        - 分数 ≥ 0.6 → 振动模态强，信号可信
        - 分数 < 0.3 → 噪音主导，信号应过滤

    Args:
        prices: 价格序列 (N,)
        window: 近多少根K线参与计算，默认 20

    Returns:
        检测结果字典，包含：
        - vibration_score: 振动模态分数
        - trigger_freq: 触发模态(3)频率
        - resonance_freq: 共振模态(6)频率
        - closure_freq: 归整模态(9)频率
        - root_distribution: 数字根完整分布 {1-9: count}
        - is_strong: 模态分数 ≥ 0.6
        - is_noise: 模态分数 < 0.3
        - mode_label: 模态标签 ("strong"/"moderate"/"noise")
    """
    # 数据长度校验
    if len(prices) < window:
        window = len(prices)

    if len(prices) < 3:
        logger.warning("vibration_mode_369: 价格序列过短 (<3)，返回中性结果")
        return {
            "vibration_score": 0.5,
            "trigger_freq": 0.0,
            "resonance_freq": 0.0,
            "closure_freq": 0.0,
            "root_distribution": {i: 0 for i in range(1, 10)},
            "is_strong": False,
            "is_noise": False,
            "mode_label": "moderate",
        }

    # 计算近 window 根K线的收益率序列
    recent_prices = prices[-window:]
    returns = np.diff(recent_prices) / recent_prices[:-1]

    # 避免除零和无效收益率
    returns = returns[np.isfinite(returns)]

    if len(returns) == 0:
        logger.warning("vibration_mode_369: 无有效收益率，返回中性结果")
        return {
            "vibration_score": 0.5,
            "trigger_freq": 0.0,
            "resonance_freq": 0.0,
            "closure_freq": 0.0,
            "root_distribution": {i: 0 for i in range(1, 10)},
            "is_strong": False,
            "is_noise": False,
            "mode_label": "moderate",
        }

    # 将收益率转换为整数用于数字根计算
    # 方法：取收益率的绝对值，乘以放大因子后取整
    # 放大因子 = 10000，将 0.01% 的变化映射为整数 1
    SCALE_FACTOR: int = 10000
    scaled_returns = np.abs(returns * SCALE_FACTOR).astype(int)

    # 计算数字根序列
    root_sequence = np.array([digital_root(int(r)) for r in scaled_returns])
    total_count = len(root_sequence)

    # 统计数字根分布
    root_distribution: Dict[int, int] = {i: 0 for i in range(1, 10)}
    for root in root_sequence:
        root_distribution[root] = root_distribution.get(root, 0) + 1

    # 计算369三阶段频率
    trigger_count = root_distribution.get(3, 0)    # 触发模态
    resonance_count = root_distribution.get(6, 0)   # 共振模态
    closure_count = root_distribution.get(9, 0)     # 归整模态

    trigger_freq = trigger_count / total_count
    resonance_freq = resonance_count / total_count
    closure_freq = closure_count / total_count

    # 振动模态分数
    vibration_score = (trigger_count + resonance_count + closure_count) / total_count

    # 模态判定
    is_strong = vibration_score >= VIBRATION_STRONG_THRESHOLD
    is_noise = vibration_score < VIBRATION_NOISE_THRESHOLD

    if is_strong:
        mode_label = "strong"
    elif is_noise:
        mode_label = "noise"
    else:
        mode_label = "moderate"

    logger.debug(
        f"vibration_mode_369: score={vibration_score:.3f}, "
        f"trigger={trigger_freq:.3f}, resonance={resonance_freq:.3f}, "
        f"closure={closure_freq:.3f}, label={mode_label}"
    )

    return {
        "vibration_score": vibration_score,
        "trigger_freq": trigger_freq,
        "resonance_freq": resonance_freq,
        "closure_freq": closure_freq,
        "root_distribution": root_distribution,
        "is_strong": is_strong,
        "is_noise": is_noise,
        "mode_label": mode_label,
    }


# ─────────────────────────────────────────────
# 函数3: apply_369_signal_filter
# ─────────────────────────────────────────────

def apply_369_signal_filter(
    hints: list,
    confidence: float,
    bars: list,
    log_prefix: str = ""
) -> Tuple[list, float, float, Dict]:
    """
    信号层过滤函数（369振动法则），供所有理论引擎调用

    计算振动模态分数，根据模态强度调整信号输出：
    - 模态分数 ≥ 0.6: 信号正常输出
    - 0.3 ≤ 模态分数 < 0.6: 信号置信度减半
    - 模态分数 < 0.3: 清空信号，只保留 10% 置信度

    此函数与 topo_invariants.apply_phase_filter 互补：
    - apply_phase_filter 基于 PCS（相位连续性）过滤
    - apply_369_signal_filter 基于 369振动模态过滤
    两者可叠加使用，双重过滤机制。

    Args:
        hints: 原始信号列表（每个信号为 dict）
        confidence: 原始置信度 [0, 1]
        bars: K线数据列表（每个 bar 为 dict，需含 "close" 字段）
        log_prefix: 日志前缀（引擎名称）

    Returns:
        (filtered_hints, adjusted_confidence, vibration_score, mode_details)
        - filtered_hints: 过滤后的信号列表
        - adjusted_confidence: 调整后的置信度
        - vibration_score: 振动模态分数
        - mode_details: vibration_mode_369 的完整返回结果
    """
    # 提取收盘价序列
    closes = np.array([float(bar.get("close", 0)) for bar in bars])

    # 计算振动模态
    mode_details = vibration_mode_369(closes)
    vibration_score = mode_details["vibration_score"]

    filtered_hints = list(hints)
    adjusted_confidence = confidence

    if vibration_score >= VIBRATION_STRONG_THRESHOLD:
        # 模态分数 ≥ 0.6: 信号正常输出，不做调整
        logger.info(
            f"[{log_prefix}] 369 vibration STRONG: score={vibration_score:.3f}, "
            f"信号正常输出"
        )
    elif vibration_score >= VIBRATION_NOISE_THRESHOLD:
        # 0.3 ≤ 模态分数 < 0.6: 信号置信度减半
        adjusted_confidence = confidence * 0.5
        for hint in filtered_hints:
            if isinstance(hint, dict):
                hint["confidence"] = hint.get("confidence", 0) * 0.5
        logger.info(
            f"[{log_prefix}] 369 vibration MODERATE: score={vibration_score:.3f}, "
            f"置信度减半"
        )
    else:
        # 模态分数 < 0.3: 清空信号，只保留 10% 置信度
        filtered_hints = []
        adjusted_confidence = confidence * 0.1
        logger.warning(
            f"[{log_prefix}] 369 vibration NOISE: score={vibration_score:.3f}, "
            f"清空所有信号，置信度降至10%"
        )

    return filtered_hints, adjusted_confidence, vibration_score, mode_details


# ─────────────────────────────────────────────
# 函数4: detect_139_critical_transition
# ─────────────────────────────────────────────

def detect_139_critical_transition(
    prices: np.ndarray,
    window: int = 139
) -> Dict:
    """
    139相变阈值检测（Landau-Ising临界慢化征兆）

    在139窗口内检测三个临界慢化征兆：
    1. 方差↑: 近期方差 vs 长期方差比值 > 1.5 → 方差上升
    2. 自相关时间↑: 收益率自相关系数 > 0.3 → 自相关增强
    3. 恢复速率↓: 价格冲击后的恢复速度变慢 → 临界慢化

    综合评分：2个以上征兆出现 → 进入临界慢化
    → 旧秩序面临破裂，新结构即将涌现

    物理类比（Landau-Ising相变）：
        当系统接近临界点时，序参量的涨落增大（方差↑），
        系统对外扰动的响应变慢（恢复速率↓），
        时间关联变长（自相关↑）。
        这三个征兆同时出现，意味着市场正处于"相变窗口"。

    Args:
        prices: 价格序列 (N,)
        window: 139-day检测窗口，默认 139

    Returns:
        检测结果字典，包含：
        - is_critical: 是否进入临界慢化
        - variance_ratio: 方差比值（近期/长期）
        - autocorrelation: 自相关系数
        - recovery_rate: 恢复速率
        - critical_score: 征兆计数 (0-3)
        - regime: 市场状态标签
    """
    # 数据长度校验
    effective_window = min(window, len(prices))

    if len(prices) < 20:
        logger.warning(
            "detect_139_critical_transition: 价格序列过短 (<20)，返回非临界结果"
        )
        return {
            "is_critical": False,
            "variance_ratio": 1.0,
            "autocorrelation": 0.0,
            "recovery_rate": 1.0,
            "critical_score": 0.0,
            "regime": "insufficient_data",
        }

    # 计算收益率序列
    returns = np.diff(np.log(prices[-effective_window:]))
    returns = returns[np.isfinite(returns)]

    if len(returns) < 10:
        return {
            "is_critical": False,
            "variance_ratio": 1.0,
            "autocorrelation": 0.0,
            "recovery_rate": 1.0,
            "critical_score": 0.0,
            "regime": "insufficient_data",
        }

    # ── 征兆1: 方差↑ ──
    # 近期方差（最近1/3窗口）vs 长期方差（整个窗口）
    recent_len = max(len(returns) // 3, 5)
    long_len = len(returns)

    recent_var = np.var(returns[-recent_len:])
    long_var = np.var(returns)

    variance_ratio = recent_var / long_var if long_var > 1e-12 else 1.0
    variance_rising = variance_ratio > CRITICAL_VARIANCE_RATIO

    # ── 征兆2: 自相关时间↑ ──
    # 计算滞后1的自相关系数
    if len(returns) > 2:
        autocorrelation = np.corrcoef(returns[:-1], returns[1:])[0, 1]
    else:
        autocorrelation = 0.0

    # 处理 NaN（序列标准差为0时）
    if not np.isfinite(autocorrelation):
        autocorrelation = 0.0

    autocorr_enhanced = abs(autocorrelation) > CRITICAL_AUTOCORR

    # ── 征兆3: 恢复速率↓ ──
    # 计算最近5根K线的均值回复速度
    # 方法：价格偏离均值的衰减速率
    # recovery_rate = |Δ(price - mean)| / |price - mean|_initial
    # 小值 → 恢复慢 → 临界慢化
    recent_prices_slice = prices[-effective_window:]
    n_recent = min(5, len(recent_prices_slice))

    if n_recent >= 3:
        recent_slice = recent_prices_slice[-n_recent:]
        local_mean = np.mean(recent_slice)
        deviations = recent_slice - local_mean

        # 均值回复速度 = 后续偏离度 / 初始偏离度 的衰减率
        initial_dev = abs(deviations[0]) if abs(deviations[0]) > 1e-12 else 1e-12
        final_dev = abs(deviations[-1])

        recovery_rate = final_dev / initial_dev
    else:
        recovery_rate = 1.0

    # 恢复慢 → recovery_rate 大（偏离未衰减）
    recovery_slow = recovery_rate > CRITICAL_RECOVERY_SLOW

    # ── 综合评分 ──
    critical_score = float(sum([
        variance_rising,
        autocorr_enhanced,
        recovery_slow,
    ]))

    is_critical = critical_score >= CRITICAL_SCORE_THRESHOLD

    # 市场状态标签
    if is_critical:
        regime = "critical_slowing"  # 临界慢化
    elif critical_score >= 1.0:
        regime = "transitioning"     # 过渡区
    else:
        regime = "stable"            # 稳态区

    logger.debug(
        f"detect_139_critical_transition: "
        f"var_ratio={variance_ratio:.2f}, autocorr={autocorrelation:.3f}, "
        f"recovery={recovery_rate:.3f}, score={critical_score:.1f}, "
        f"critical={is_critical}, regime={regime}"
    )

    return {
        "is_critical": is_critical,
        "variance_ratio": float(variance_ratio),
        "autocorrelation": float(autocorrelation),
        "recovery_rate": float(recovery_rate),
        "critical_score": float(critical_score),
        "regime": regime,
    }


# ─────────────────────────────────────────────
# 函数5: cycle_7_closure_verification
# ─────────────────────────────────────────────

def cycle_7_closure_verification(
    prices: np.ndarray,
    window: int = 60
) -> Dict:
    """
    7循环群自指验证（142857完美闭合）

    在价格序列中检测是否有"自相似周期结构"：
    - 计算 Z_7 循环群特征：价格序列是否有 7-day 完美循环模式
    - 检测方法：计算价格的 7-day 周期性（用 FFT 在 1/7 频率处的功率）
    - 闭合度评分：功率峰值强度 / 总功率，≥ 0.3 → 有循环群特征

    数学背景：
        Z_7 是7阶循环群，142857 是 1/7 的循环节：
        1/7 = 0.142857142857...
        142857 × 1 = 142857 → 数字根 = 1+4+2+8+5+7 = 27 → 9
        142857 × 2 = 285714 → 同一循环节的轮转
        142857 × 3 = 428571 → ...
        这展现了 Z_7 群的"自指闭合"性质。

    Args:
        prices: 价格序列 (N,)
        window: 检测窗口长度，默认 60

    Returns:
        检测结果字典，包含：
        - has_7_cycle: 是否检测到7循环群特征
        - closure_score: 闭合度评分 [0, 1]
        - dominant_period: 主周期长度
        - fft_power_at_7: 在1/7频率处的功率值
    """
    effective_window = min(window, len(prices))

    if len(prices) < 14:  # 至少需要 2×7 个数据点
        logger.warning(
            "cycle_7_closure_verification: 价格序列过短 (<14)，返回无循环结果"
        )
        return {
            "has_7_cycle": False,
            "closure_score": 0.0,
            "dominant_period": 0,
            "fft_power_at_7": 0.0,
        }

    # 计算对数收益率（去除趋势）
    recent_prices = prices[-effective_window:]
    log_returns = np.diff(np.log(recent_prices))
    log_returns = log_returns[np.isfinite(log_returns)]

    if len(log_returns) < 10:
        return {
            "has_7_cycle": False,
            "closure_score": 0.0,
            "dominant_period": 0,
            "fft_power_at_7": 0.0,
        }

    # 去均值后计算 FFT
    centered = log_returns - np.mean(log_returns)
    n = len(centered)

    fft_result = np.fft.rfft(centered)
    power_spectrum = np.abs(fft_result) ** 2 / n
    total_power = np.sum(power_spectrum)

    # 频率轴
    frequencies = np.fft.rfftfreq(n)

    # 在 1/7 频率处检测功率
    target_freq = 1.0 / 7.0

    if len(frequencies) > 1 and total_power > 1e-12:
        # 找最接近 1/7 频率的点
        freq_idx = np.argmin(np.abs(frequencies - target_freq))
        fft_power_at_7 = float(power_spectrum[freq_idx])

        # 闭合度评分 = 目标频率功率 / 总功率
        closure_score = fft_power_at_7 / total_power
    else:
        fft_power_at_7 = 0.0
        closure_score = 0.0

    # 主周期检测（功率最大的频率对应的周期）
    if len(power_spectrum) > 1 and total_power > 1e-12:
        peak_idx = np.argmax(power_spectrum[1:]) + 1  # 跳过直流分量(idx=0)
        peak_freq = frequencies[peak_idx]
        dominant_period = int(round(1.0 / peak_freq)) if peak_freq > 1e-12 else 0
    else:
        dominant_period = 0

    # 闭合度评分钳位到 [0, 1]
    closure_score = max(0.0, min(1.0, closure_score))

    has_7_cycle = closure_score >= CYCLE_7_CLOSURE_THRESHOLD

    logger.debug(
        f"cycle_7_closure_verification: "
        f"closure_score={closure_score:.3f}, "
        f"dominant_period={dominant_period}, "
        f"power_at_7={fft_power_at_7:.4f}, "
        f"has_7_cycle={has_7_cycle}"
    )

    return {
        "has_7_cycle": has_7_cycle,
        "closure_score": float(closure_score),
        "dominant_period": dominant_period,
        "fft_power_at_7": fft_power_at_7,
    }


# ─────────────────────────────────────────────
# 函数6: cosmic_algorithm_trio
# ─────────────────────────────────────────────

def cosmic_algorithm_trio(
    prices: np.ndarray,
    volumes: Optional[np.ndarray] = None
) -> Dict:
    """
    三重奏综合分析

    同时调用 vibration_mode_369、detect_139_critical_transition、
    cycle_7_closure_verification，计算综合评分。

    综合评分 = (369模态分数 + 139相变评分 + 7闭合评分) / 3

    各层贡献：
    - 369模态分数 [0, 1]: 信号层的振动可信度
    - 139相变评分 [0, 1]: critical_score/3（3个征兆满分为1）
    - 7闭合评分 [0, 1]: 循环群闭合度

    综合评分含义：
    - ≥ 0.6: 三重奏共振强，市场结构清晰，信号高度可信
    - 0.3-0.6: 部分共振，需谨慎
    - < 0.3: 三重奏失效，市场处于混沌态

    Args:
        prices: 价格序列 (N,)
        volumes: 成交量序列 (N,)（可选，供139层扩展使用）

    Returns:
        综合分析结果字典，包含：
        - trio_score: 综合评分 [0, 1]
        - vibration_369: vibration_mode_369 的完整返回
        - critical_139: detect_139_critical_transition 的完整返回
        - cycle_7: cycle_7_closure_verification 的完整返回
        - trio_label: 综合标签 ("strong"/"moderate"/"weak")
        - trading_implication: 交易含义建议
    """
    # ── 369振动法则 ──
    vibration_369 = vibration_mode_369(prices)
    vibration_score = vibration_369["vibration_score"]

    # ── 139临界演化 ──
    critical_139 = detect_139_critical_transition(prices)
    # 将 critical_score (0-3) 归一化到 [0, 1]
    critical_score_normalized = critical_139["critical_score"] / 3.0

    # ── 7结构自指 ──
    cycle_7 = cycle_7_closure_verification(prices)
    closure_score = cycle_7["closure_score"]

    # ── 综合评分 ──
    trio_score = (vibration_score + critical_score_normalized + closure_score) / 3.0
    trio_score = max(0.0, min(1.0, trio_score))

    # 综合标签
    if trio_score >= VIBRATION_STRONG_THRESHOLD:
        trio_label = "strong"
    elif trio_score < VIBRATION_NOISE_THRESHOLD:
        trio_label = "weak"
    else:
        trio_label = "moderate"

    # 交易含义建议
    trading_implications = {
        "strong": "三重奏共振强，市场结构清晰，信号高度可信，可正常交易",
        "moderate": "部分共振，需谨慎，建议降低仓位或等待确认",
        "weak": "三重奏失效，市场混沌态，建议暂停交易或仅做防御性操作",
    }
    trading_implication = trading_implications.get(trio_label, "数据不足，无法判断")

    # 风控建议（基于139层）
    risk_control = {
        "should_reduce_position": critical_139["is_critical"],
        "should_hard_stop": critical_139["critical_score"] >= 3.0,
        "volatility_warning": critical_139["variance_ratio"] > 2.0,
    }

    logger.info(
        f"cosmic_algorithm_trio: "
        f"trio_score={trio_score:.3f}, "
        f"vibration={vibration_score:.3f}, "
        f"critical={critical_score_normalized:.3f}, "
        f"closure={closure_score:.3f}, "
        f"label={trio_label}"
    )

    return {
        "trio_score": trio_score,
        "vibration_369": vibration_369,
        "critical_139": critical_139,
        "cycle_7": cycle_7,
        "trio_label": trio_label,
        "trading_implication": trading_implication,
        "risk_control": risk_control,
        # 各层原始分数
        "vibration_score": vibration_score,
        "critical_score_normalized": critical_score_normalized,
        "closure_score": closure_score,
    }


# ─────────────────────────────────────────────
# 模块自检
# ─────────────────────────────────────────────

def _self_test() -> None:
    """模块自检：测试所有核心函数"""
    print("=" * 60)
    print("宇宙算法三重奏 (7-139-369) 核心库 — 模块自检")
    print("=" * 60)

    # ── 1. digital_root 测试 ──
    print("\n[1] digital_root 数字根测试")
    test_cases = [
        (369, 9),
        (142857, 9),  # 1+4+2+8+5+7=27, 2+7=9; 142857%9=0 → 映射为9
        (139, 4),
        (0, 9),
        (7, 7),
        (9, 9),
        (18, 9),
        (27, 9),
        (10, 1),
        (12345, 6),
    ]
    all_pass = True
    for n, expected in test_cases:
        result = digital_root(n)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_pass = False
        print(f"  digital_root({n}) = {result} (期望 {expected}) [{status}]")
    print(f"  数字根测试: {'全部通过' if all_pass else '有失败'}")

    # ── 2. vibration_mode_369 测试 ──
    print("\n[2] vibration_mode_369 振动模态测试")
    # 构造一个包含较多3、6、9数字根的序列
    # 使用特定价格序列使收益率映射到369模态
    np.random.seed(42)
    test_prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 100))
    mode_result = vibration_mode_369(test_prices, window=20)
    print(f"  振动模态分数: {mode_result['vibration_score']:.3f}")
    print(f"  触发频率(3): {mode_result['trigger_freq']:.3f}")
    print(f"  共振频率(6): {mode_result['resonance_freq']:.3f}")
    print(f"  归整频率(9): {mode_result['closure_freq']:.3f}")
    print(f"  模态标签: {mode_result['mode_label']}")
    print(f"  数字根分布: {mode_result['root_distribution']}")

    # ── 3. apply_369_signal_filter 测试 ──
    print("\n[3] apply_369_signal_filter 信号过滤测试")
    test_hints = [
        {"direction": "bullish", "confidence": 0.8, "reason": "趋势向上"},
        {"direction": "bearish", "confidence": 0.6, "reason": "阻力位"},
    ]
    test_bars = [{"close": float(p)} for p in test_prices[-20:]]
    filtered, adj_conf, vib_score, mode_det = apply_369_signal_filter(
        test_hints, 0.7, test_bars, log_prefix="SELF_TEST"
    )
    print(f"  原始信号数: {len(test_hints)}, 置信度: 0.7")
    print(f"  过滤后信号数: {len(filtered)}, 调整置信度: {adj_conf:.3f}")
    print(f"  振动模态分数: {vib_score:.3f}")

    # ── 4. detect_139_critical_transition 测试 ──
    print("\n[4] detect_139_critical_transition 相变检测测试")
    # 正常市场序列
    stable_prices = np.cumprod(1 + np.random.normal(0.0005, 0.01, 200))
    stable_result = detect_139_critical_transition(stable_prices)
    print(f"  稳态序列: is_critical={stable_result['is_critical']}, "
          f"regime={stable_result['regime']}, "
          f"score={stable_result['critical_score']:.1f}")

    # 构造临界序列（方差增大 + 自相关增强）
    np.random.seed(99)
    n_critical = 200
    # 前半段正常波动，后半段波动增大且自相关增强
    base_returns = np.zeros(n_critical)
    base_returns[:n_critical // 2] = np.random.normal(0, 0.01, n_critical // 2)
    # 后半段：增大方差 + 添加自相关
    for i in range(n_critical // 2, n_critical):
        base_returns[i] = 0.7 * base_returns[i - 1] + np.random.normal(0, 0.03)
    critical_prices = np.cumprod(1 + base_returns)
    critical_result = detect_139_critical_transition(critical_prices)
    print(f"  临界序列: is_critical={critical_result['is_critical']}, "
          f"regime={critical_result['regime']}, "
          f"var_ratio={critical_result['variance_ratio']:.2f}, "
          f"autocorr={critical_result['autocorrelation']:.3f}, "
          f"recovery={critical_result['recovery_rate']:.3f}, "
          f"score={critical_result['critical_score']:.1f}")

    # ── 5. cycle_7_closure_verification 测试 ──
    print("\n[5] cycle_7_closure_verification 7循环群验证测试")
    # 构造含7-day周期的序列
    t = np.arange(200)
    cyclic_prices = 100 + 5 * np.sin(2 * np.pi * t / 7) + np.random.normal(0, 0.5, 200)
    cyclic_prices = np.abs(cyclic_prices) + 50  # 确保价格>0
    cycle_result = cycle_7_closure_verification(cyclic_prices)
    print(f"  含7周期序列: has_7_cycle={cycle_result['has_7_cycle']}, "
          f"closure_score={cycle_result['closure_score']:.3f}, "
          f"dominant_period={cycle_result['dominant_period']}, "
          f"fft_power={cycle_result['fft_power_at_7']:.4f}")

    # 无周期随机序列
    random_prices = np.cumprod(1 + np.random.normal(0, 0.02, 200))
    random_cycle_result = cycle_7_closure_verification(random_prices)
    print(f"  随机序列: has_7_cycle={random_cycle_result['has_7_cycle']}, "
          f"closure_score={random_cycle_result['closure_score']:.3f}")

    # ── 6. cosmic_algorithm_trio 综合测试 ──
    print("\n[6] cosmic_algorithm_trio 三重奏综合测试")
    trio_result = cosmic_algorithm_trio(cyclic_prices)
    print(f"  综合评分: {trio_result['trio_score']:.3f}")
    print(f"  标签: {trio_result['trio_label']}")
    print(f"  交易含义: {trio_result['trading_implication']}")
    print(f"  风控建议: {trio_result['risk_control']}")
    print(f"  各层分数:")
    print(f"    369振动: {trio_result['vibration_score']:.3f}")
    print(f"    139相变: {trio_result['critical_score_normalized']:.3f}")
    print(f"    7闭合: {trio_result['closure_score']:.3f}")

    print("\n" + "=" * 60)
    print("模块自检完成")
    print("=" * 60)


if __name__ == "__main__":
    _self_test()
