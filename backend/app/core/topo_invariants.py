"""
topo_invariants.py — 鲁兆体系拓扑不变量库 (TOMAS v2.0)

基于「复合体理学」文章 TOMAS v2.0 实现：
- 鲁加斯数（Lucas Numbers）
- 八卦常数（Bagua Constants）
- 斐波那契数（Fibonacci Numbers）
- 中国股市拓扑不变量集合
- 相位连续性评分
- 太极中心（相位原点）计算

参考文献：
[1] TOMAS v2.0：基于广义代数理论（GAT）的太乙互搏公理体系与流体智能的统一解释
[2] 鲁兆：波浪理论、费氏数列、八卦历法
"""

from typing import List, Set, Optional, Tuple, Dict
import numpy as np
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# 核心数列生成器
# ─────────────────────────────────────────────

def lucas_numbers(n_terms: int = 20) -> List[float]:
    """
    鲁加斯数（Lucas Numbers）
    
    定义：L(0)=2, L(1)=1, L(n)=L(n-1)+L(n-2)
    序列：2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, ...
    
    鲁兆体系中用于「隔代自相似」验证：
    第 n 浪与第 n-2 浪的时间/幅度比接近鲁加斯数之比。
    
    Args:
        n_terms: 生成项数，默认 20
    
    Returns:
        鲁加斯数列表
    """
    if n_terms <= 0:
        return []
    L = [2.0, 1.0]
    if n_terms <= 2:
        return L[:n_terms]
    for _ in range(n_terms - 2):
        L.append(L[-1] + L[-2])
    return L


def fibonacci_numbers(n_terms: int = 20) -> List[float]:
    """
    斐波那契数（Fibonacci Numbers）
    
    定义：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)
    序列：0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, ...
    
    鲁兆体系中用于「倍数生成」验证：
    第 n 浪的长度 ≈ 第 1 浪长度 × F(n)
    
    Args:
        n_terms: 生成项数，默认 20
    
    Returns:
        斐波那契数列表
    """
    if n_terms <= 0:
        return []
    F = [0.0, 1.0]
    if n_terms <= 2:
        return F[:n_terms]
    for _ in range(n_terms - 2):
        F.append(F[-1] + F[-2])
    return F


def bagua_constants() -> List[int]:
    """
    八卦常数（Bagua Constants）—— 鲁兆体系核心时间窗
    
    来源：易经八卦数 + 鲁兆经验总结
    集合：1, 3, 5, 8, 13, 21, 23, 29, 34, 55, 89, 144
    
    含义：
    - 1/3/5：短周期（日线级别）
    - 8/13/21：中周期（周线级别）
    - 34/55/89：长周期（月线级别）
    - 144：完整市场周期（年线级别）
    
    Returns:
        八卦常数列表（已排序）
    """
    return [1, 3, 5, 8, 13, 21, 23, 29, 34, 55, 89, 144]


def get_chinese_market_invariants(n_terms: int = 15) -> List[int]:
    """
    中国股市拓扑不变量全集
    
    并集运算：Lucas(n) ∪ Bagua ∪ Fibonacci(n)
    去重并排序，作为「相位连续性检测」的候选周期集合。
    
    TOMAS v2.0 推论：
        在相位连续的市场中，价格序列的功率谱密度（PSD）
        在这些不变量对应的频率上出现峰值。
    
    Args:
        n_terms: Lucas 和 Fibonacci 的计算项数
    
    Returns:
        排序后的不变量全集
    """
    lucas = set(int(x) for x in lucas_numbers(n_terms))
    fib = set(int(x) for x in fibonacci_numbers(n_terms))
    bagua = set(bagua_constants())
    return sorted(lucas | fib | bagua)


def golden_ratio_multiples(n: int = 10) -> List[float]:
    """
    黄金比例倍数（φ = 1.618...）
    
    鲁兆「倍数生成」法则的核心比例：
    - φ^1 ≈ 1.618（标准黄金比）
    - φ^2 ≈ 2.618（平方黄金比）
    - 1/φ ≈ 0.618（倒数）
    
    Args:
        n: 生成项数
    
    Returns:
        [1, φ, φ², ..., φⁿ] 列表
    """
    phi = (1 + np.sqrt(5)) / 2
    return [phi ** i for i in range(n)]


# ─────────────────────────────────────────────
# 太极中心（相位原点）计算
# ─────────────────────────────────────────────

def find_taiji_center(
    prices: np.ndarray,
    window: int = 60,
    method: str = "extremum"
) -> Optional[int]:
    """
    寻找「太极中心」—— 相位原点 T₀
    
    太极中心是鲁兆体系中的「重要历史顶/底」，
    所有波浪的时间/幅度均相对于此点计算相位。
    
    TOMAS v2.0 GAT 形式化：
        T₀ = argmin_{t} MDL(Price[t:], DNA)
        即：使得后续序列的 MDL 最小的极值点
    
    Args:
        prices: 价格序列 (N,)
        window: 搜索窗口（向后看多少根K线）
        method: 寻找方法
            - "extremum": 找窗口内最高/最低点
            - "cluster": 找拐点聚类中心
    
    Returns:
        太极中心在 prices 中的索引，未找到返回 None
    """
    if len(prices) < window:
        window = len(prices)
    
    if method == "extremum":
        # 找窗口内的全局极值
        recent = prices[-window:]
        max_idx = np.argmax(recent)
        min_idx = np.argmin(recent)
        
        # 选择离当前更「重要」的极值（幅度更大的）
        max_val = recent[max_idx]
        min_val = recent[min_idx]
        mid = np.mean(recent)
        
        if abs(max_val - mid) > abs(min_val - mid):
            return len(prices) - window + max_idx
        else:
            return len(prices) - window + min_idx
    
    elif method == "cluster":
        # 拐点聚类（简化版）
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(prices, distance=5)
        troughs, _ = find_peaks(-prices, distance=5)
        all_turning = np.sort(np.concatenate([peaks, troughs]))
        
        if len(all_turning) == 0:
            return None
        
        # 返回最重要（最极端）的拐点
        extreme_idx = all_turning[np.argmax(np.abs(
            prices[all_turning] - np.mean(prices)
        ))]
        return int(extreme_idx)
    
    return None


def compute_phase_origin(
    taiji_idx: int,
    prices: np.ndarray,
    time_index: Optional[np.ndarray] = None
) -> Dict:
    """
    计算相位原点 T₀ 的完整信息
    
    Returns:
        包含 T₀ 索引、价格、时间、相对相位的字典
    """
    taiji_price = prices[taiji_idx]
    
    result = {
        "index": taiji_idx,
        "price": float(taiji_price),
        "relative_phase": 0.0,  # T₀ 自身相位为 0
    }
    
    if time_index is not None and taiji_idx < len(time_index):
        result["time"] = str(time_index[taiji_idx])
    
    # 计算后续所有点的相对相位（简化：用价格偏离度表示）
    if taiji_idx < len(prices):
        subsequent = prices[taiji_idx:]
        result["phase_evolution"] = ((subsequent - taiji_price) / taiji_price).tolist()
    
    return result


# ─────────────────────────────────────────────
# 相位连续性评分
# ─────────────────────────────────────────────

def phase_continuity_score(
    prices: np.ndarray,
    window: int = 30,
    taiji_idx: Optional[int] = None
) -> float:
    """
    相位连续性评分（Phase Continuity Score, PCS）
    
    TOMAS v2.0 定义：
        PCS = 1 - (Δϕ_actual - Δϕ_expected)² / σ²_ϕ
    
    其中：
    - Δϕ_actual：实际价格变化的相位角
    - Δϕ_expected：基于拓扑不变量的期望相位变化
    - σ²_ϕ：相位方差
    
    鲁兆体系生效边界：PCS > 0.7（相位连续区）
    鲁兆体系失效边界：PCS < 0.3（相变奇点区）
    
    Args:
        prices: 价格序列
        window: 计算窗口
        taiji_idx: 太极中心索引（可选）
    
    Returns:
        PCS 分数 [0, 1]，越高表示相位越连续
    """
    if len(prices) < window:
        window = len(prices)
    
    if len(prices) < 10:
        return 0.5  # 数据不足，返回中性值
    
    # 计算对数收益率（相位变化的代理变量）
    log_returns = np.diff(np.log(prices[-window:]))
    
    if len(log_returns) < 5:
        return 0.5
    
    # 计算「期望相位变化」—— 基于拓扑不变量
    invariants = get_chinese_market_invariants(10)
    expected_phases = []
    for inv in invariants:
        if inv <= len(log_returns):
            # 用不变量周期的样本方差作为「期望相位」
            expected_phases.append(np.var(log_returns[-inv:]))
    
    if not expected_phases:
        expected_phase_var = np.var(log_returns)
    else:
        expected_phase_var = np.mean(expected_phases)
    
    # 实际相位方差
    actual_phase_var = np.var(log_returns)
    
    # PCS 计算
    if expected_phase_var < 1e-10:
        return 1.0
    
    pcs = 1.0 - min(1.0, abs(actual_phase_var - expected_phase_var) / expected_phase_var)
    return max(0.0, min(1.0, pcs))


def detect_phase_singularity(
    prices: np.ndarray,
    volume: Optional[np.ndarray] = None,
    window: int = 20,
    threshold: float = 0.3
) -> Dict:
    """
    检测相变奇点（Phase Singularity）
    
    TOMAS v2.0 定义：
        当 PCS < threshold 时，市场处于「相变区」，
        旧有的拓扑不变量失效，需重新进行 κ-Snap 溯因。
    
    实务判据（鲁兆体系）：
        - 相位连续性评分骤降
        - 成交量异常放大（闪崩/暴涨）
        - 波动率突破鲁加斯数对应的阈值
    
    Args:
        prices: 价格序列
        volume: 成交量序列（可选）
        window: 检测窗口
        threshold: 奇点阈值（PCS < threshold 视为奇点）
    
    Returns:
        检测结果字典
    """
    pcs = phase_continuity_score(prices, window)
    
    result = {
        "pcs": pcs,
        "is_singularity": pcs < threshold,
        "severity": "high" if pcs < 0.2 else ("medium" if pcs < 0.3 else "low"),
    }
    
    # 波动率突破检测
    if len(prices) >= window:
        recent = prices[-window:]
        volatility = np.std(np.diff(np.log(recent)))
        lucas = lucas_numbers(10)
        # 用鲁加斯数第5项作为波动率阈值（经验值）
        vol_threshold = float(lucas[5]) * 0.01
        result["volatility"] = volatility
        result["volatility_breach"] = volatility > vol_threshold
    
    # 成交量异常检测
    if volume is not None and len(volume) >= window:
        recent_vol = volume[-window:]
        avg_vol = np.mean(recent_vol)
        std_vol = np.std(recent_vol)
        latest_vol = recent_vol[-1]
        result["volume_z_score"] = (latest_vol - avg_vol) / std_vol if std_vol > 0 else 0
        result["volume_anomaly"] = abs(result["volume_z_score"]) > 2.0
    
    return result


# ─────────────────────────────────────────────
# 波浪 DNA 倍发生成验证
# ─────────────────────────────────────────────

def verify_fibonacci_multiples(
    wave_lengths: List[float],
    tolerance: float = 0.15
) -> Dict:
    """
    验证波浪长度是否满足斐波那契倍数关系
    
    鲁兆规则：
        第 n 浪的长度 ≈ 第 1 浪长度 × F(n)
        常见比例：1, 1.618, 2.0, 2.618, 3.0
    
    Args:
        wave_lengths: 各浪长度列表 [浪1, 浪2, ...]
        tolerance: 容许误差（相对误差 < tolerance 视为匹配）
    
    Returns:
        验证结果字典
    """
    if len(wave_lengths) < 2:
        return {"valid": False, "reason": "至少需要2浪"}
    
    first_wave = wave_lengths[0]
    fib = fibonacci_numbers(len(wave_lengths) + 5)
    
    results = []
    for i, length in enumerate(wave_lengths):
        expected = first_wave * fib[i + 1]  # F(1)=1, F(2)=1, ...
        if expected > 0:
            error = abs(length - expected) / expected
            results.append({
                "wave": i + 1,
                "actual": length,
                "expected": expected,
                "error": error,
                "matches": error < tolerance
            })
    
    matches = [r for r in results if r["matches"]]
    return {
        "valid": len(matches) >= len(results) * 0.6,  # 60% 以上匹配
        "match_rate": len(matches) / len(results) if results else 0,
        "details": results,
        "fibonacci_used": fib[:len(wave_lengths) + 1].tolist(),
    }


def verify_lucas_self_similarity(
    wave_times: List[float],
    tolerance: float = 0.20
) -> Dict:
    """
    验证「隔代自相似」（鲁加斯数约束）
    
    鲁兆规则：
        第 n 浪与第 n-2 浪的时间比 ≈ L(n) / L(n-2)
    
    Args:
        wave_times: 各浪时间长度列表
        tolerance: 容许误差
    
    Returns:
        验证结果字典
    """
    if len(wave_times) < 3:
        return {"valid": False, "reason": "至少需要3浪"}
    
    lucas = lucas_numbers(len(wave_times) + 5)
    results = []
    
    for i in range(2, len(wave_times)):
        actual_ratio = wave_times[i] / wave_times[i - 2] if wave_times[i - 2] > 0 else 0
        expected_ratio = lucas[i] / lucas[i - 2] if lucas[i - 2] != 0 else 0
        
        if expected_ratio > 0:
            error = abs(actual_ratio - expected_ratio) / expected_ratio
            results.append({
                "wave": i + 1,
                "compare_with": i - 1,
                "actual_ratio": actual_ratio,
                "expected_ratio": expected_ratio,
                "error": error,
                "matches": error < tolerance
            })
    
    matches = [r for r in results if r["matches"]]
    return {
        "valid": len(matches) >= len(results) * 0.5 if results else False,
        "match_rate": len(matches) / len(results) if results else 0,
        "details": results,
    }


# ─────────────────────────────────────────────
# 拓朴不变量在价格序列中的检测
# ─────────────────────────────────────────────

def detect_invariant_cycles(
    prices: np.ndarray,
    min_period: int = 5,
    max_period: int = 120
) -> List[Dict]:
    """
    在价格序列中检测拓扑不变量对应的周期
    
    方法：计算收益率序列的功率谱密度（PSD），
    在拓扑不变量对应的频率处检测峰值。
    
    TOMAS v2.0 推论：
        相位连续的市场中，PSD 在 1/T（T ∈ 不变量集合）
        对应的频率处出现显著峰值。
    
    Args:
        prices: 价格序列
        min_period: 最小周期
        max_period: 最大周期
    
    Returns:
        检测到的周期列表，按强度排序
    """
    if len(prices) < max_period:
        max_period = len(prices) // 2
    
    # 计算对数收益率
    returns = np.diff(np.log(prices))
    
    # 计算功率谱密度（简化：用自相关）
    from numpy.fft import rfft, irfft
    n = len(returns)
    fft = rfft(returns - np.mean(returns))
    psd = np.abs(fft) ** 2 / n
    
    frequencies = np.fft.rfftfreq(n)
    periods = 1.0 / frequencies[1:] if len(frequencies) > 1 else np.array([])
    
    # 检测拓扑不变量对应的周期
    invariants = get_chinese_market_invariants(20)
    detections = []
    
    for inv in invariants:
        if inv < min_period or inv > max_period:
            continue
        
        # 找最接近的频率
        if len(periods) > 0:
            idx = np.argmin(np.abs(periods - inv))
            if abs(periods[idx] - inv) < inv * 0.1:  # 10% 容差
                detections.append({
                    "invariant": inv,
                    "detected_period": float(periods[idx]),
                    "power": float(psd[idx + 1]),  # +1 因为 periods 从 idx=1 开始
                    "match": True,
                })
    
    # 按功率排序
    detections.sort(key=lambda x: x["power"], reverse=True)
    return detections


# ─────────────────────────────────────────────
# 通用相位过滤工具（供所有理论引擎调用）
# ─────────────────────────────────────────────

def apply_phase_filter(
    hints: list,
    confidence: float,
    bars: list,
    window: int = 30,
    log_prefix: str = ""
) -> tuple:
    """
    通用相位连续性过滤函数（TOMAS v2.0）
    
    供所有理论引擎在 analyze() 返回前调用，统一应用相位过滤逻辑：
    
    - PCS < 0.3（相变奇点区）：清空所有信号，置信度降至 10%
    - 0.3 <= PCS < 0.7（过渡区）：信号置信度减半，整体置信度减半
    - PCS >= 0.7（相位连续区）：信号正常输出
    
    Args:
        hints: 原始信号列表
        confidence: 原始置信度
        bars: K线数据列表
        window: PCS计算窗口
        log_prefix: 日志前缀（引擎名称）
    
    Returns:
        (filtered_hints, adjusted_confidence, pcs, is_singularity)
    """
    import numpy as np
    from loguru import logger
    
    closes = np.array([float(bar.get("close", 0)) for bar in bars])
    pcs = phase_continuity_score(closes, window=window)
    singularity = detect_phase_singularity(closes, threshold=0.3)
    is_sing = singularity.get("is_singularity", False)
    
    filtered_hints = list(hints)
    adjusted_confidence = confidence
    
    if is_sing:
        # 相变奇点区：清空信号，强制熔断
        filtered_hints = []
        adjusted_confidence = confidence * 0.1
        logger.warning(f"[{log_prefix}] Phase singularity: PCS={pcs:.3f}, clearing all hints")
    elif pcs < 0.7:
        # 过渡区：降低置信度
        adjusted_confidence = confidence * 0.5
        for hint in filtered_hints:
            hint["confidence"] = hint.get("confidence", 0) * 0.5
        logger.info(f"[{log_prefix}] Phase transition zone: PCS={pcs:.3f}, reducing confidence")
    
    return filtered_hints, adjusted_confidence, pcs, is_sing


# ─────────────────────────────────────────────
# 模块自检
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # 单元测试
    print("=== 鲁加斯数 ===")
    print(lucas_numbers(12))
    
    print("\n=== 八卦常数 ===")
    print(bagua_constants())
    
    print("\n=== 中国股市拓扑不变量 ===")
    print(get_chinese_market_invariants(12))
    
    print("\n=== 相位连续性评分 ===")
    test_prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 100))
    print(f"PCS = {phase_continuity_score(test_prices, 30):.3f}")
    
    print("\n=== 奇点检测 ===")
    result = detect_phase_singularity(test_prices)
    print(f"PCS = {result['pcs']:.3f}, 奇点 = {result['is_singularity']}")
    
    print("\n=== 斐波那契倍数验证 ===")
    waves = [100, 61.8, 161.8, 100, 261.8]  # 理想斐波那契比例
    print(verify_fibonacci_multiples(waves))
