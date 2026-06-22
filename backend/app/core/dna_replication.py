"""
dna_replication.py — 鲁兆 DNA 倍发生成验证器 (TOMAS v2.0)

实现 TOMAS v2.0 定义的「DNA 基因」检测与验证：
- 第一浪幅度/时间作为 DNA 基因
- 倍数生成验证（第 n 浪长度 ≈ 第 1 浪 × F(n)）
- 隔代自相似验证（鲁加斯数约束）
- κ-Snap 溯因验证（MDL 搜索）
- 太极中心（相位原点）检测

参考文献：
[1] TOMAS v2.0：面向流体智能与金融市场的太乙互搏公理体系
[2] 鲁兆：波浪理论、费氏数列、八卦历法
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class WaveDNA:
    """波浪 DNA 基因"""
    first_wave_duration: int    # 第一浪时间长度（K线数）
    first_wave_amplitude: float # 第一浪幅度（价格差）
    taiji_idx: int              # 太极中心索引
    taiji_price: float          # 太极中心价格
    wave_counts: List[int]      # 各浪的 K 线数
    wave_amplitudes: List[float] # 各浪的幅度
    fibonacci_match: bool       # 是否满足斐波那契倍数
    lucas_match: bool          # 是否满足鲁加斯自相似
    mdl_score: float           # MDL 压缩得分
    confidence: float           # 置信度 [0, 1]
    
    def to_dict(self) -> Dict:
        return {
            "first_wave_duration": self.first_wave_duration,
            "first_wave_amplitude": self.first_wave_amplitude,
            "taiji_idx": self.taiji_idx,
            "taiji_price": self.taiji_price,
            "wave_counts": self.wave_counts,
            "wave_amplitudes": self.wave_amplitudes,
            "fibonacci_match": self.fibonacci_match,
            "lucas_match": self.lucas_match,
            "mdl_score": self.mdl_score,
            "confidence": self.confidence,
        }


# ─────────────────────────────────────────────
# DNA 基因检测
# ─────────────────────────────────────────────

def detect_waves(
    prices: np.ndarray,
    method: str = "zigzag",
    min_segment: int = 5,
    volatility_window: int = 20,
) -> List[Tuple[int, int, str]]:
    """
    检测价格序列中的波浪分段
    
    Args:
        prices: 价格序列 (N,)
        method: 检测方法
            - "zigzag": 使用 scipy.signal 的 find_peaks（Z字形拐点）
            - "volatility_break": 波动率突破法
        min_segment: 最小浪长度（K线数）
        volatility_window: 波动率计算窗口
    
    Returns:
        waves: [(start_idx, end_idx, type), ...]
        type: "impulse"（驱动浪）或 "corrective"（调整浪）
    """
    if len(prices) < min_segment * 3:
        return []
    
    if method == "zigzag":
        return _detect_waves_zigzag(prices, min_segment)
    elif method == "volatility_break":
        return _detect_waves_volatility(prices, min_segment, volatility_window)
    else:
        raise ValueError(f"Unknown method: {method}")


def _detect_waves_zigzag(
    prices: np.ndarray,
    min_segment: int,
) -> List[Tuple[int, int, str]]:
    """Z 字形拐点检测法"""
    try:
        from scipy.signal import find_peaks
    except ImportError:
        # fallback：简化版峰值检测
        return _detect_waves_simple(prices, min_segment)
    
    # 找峰值和谷值
    peaks, _ = find_peaks(prices, distance=min_segment)
    troughs, _ = find_peaks(-prices, distance=min_segment)
    
    # 合并并排序所有拐点
    turning_points = []
    for p in peaks:
        turning_points.append((p, "peak"))
    for t in troughs:
        turning_points.append((t, "trough"))
    turning_points.sort(key=lambda x: x[0])
    
    if len(turning_points) < 3:
        return []
    
    # 构建波浪分段
    waves = []
    for i in range(len(turning_points) - 1):
        start_idx = turning_points[i][0]
        end_idx = turning_points[i + 1][0]
        wave_type = "impulse" if i % 2 == 0 else "corrective"
        waves.append((start_idx, end_idx, wave_type))
    
    return waves


def _detect_waves_simple(
    prices: np.ndarray,
    min_segment: int,
) -> List[Tuple[int, int, str]]:
    """简化版拐点检测（无需 scipy）"""
    waves = []
    i = 0
    last_type = None
    
    while i < len(prices) - min_segment:
        # 找局部极值
        window = prices[i:i + min_segment * 2]
        local_max = np.argmax(window) + i
        local_min = np.argmin(window) + i
        
        if abs(prices[local_max] - prices[i]) > abs(prices[local_min] - prices[i]):
            end_idx = local_max
            wave_type = "impulse"
        else:
            end_idx = local_min
            wave_type = "corrective"
        
        if last_type != wave_type or len(waves) == 0:
            waves.append((i, end_idx, wave_type))
            last_type = wave_type
            i = end_idx
        else:
            i += 1
    
    return waves


def _detect_waves_volatility(
    prices: np.ndarray,
    min_segment: int,
    window: int,
) -> List[Tuple[int, int, str]]:
    """波动率突破检测法"""
    returns = np.diff(np.log(prices))
    volatility = np.array([
        np.std(returns[max(0, i - window):i + 1])
        for i in range(len(returns))
    ])
    
    # 找波动率拐点（简化）
    vol_threshold = np.percentile(volatility, 70)
    waves = []
    i = 0
    
    while i < len(volatility) - min_segment:
        if volatility[i] > vol_threshold:
            # 高波动区 = 驱动浪
            end_idx = min(i + min_segment * 2, len(prices) - 1)
            waves.append((i, end_idx, "impulse"))
            i = end_idx
        else:
            end_idx = min(i + min_segment, len(prices) - 1)
            waves.append((i, end_idx, "corrective"))
            i = end_idx
    
    return waves


# ─────────────────────────────────────────────
# DNA 基因提取
# ─────────────────────────────────────────────

def extract_dna(
    prices: np.ndarray,
    waves: List[Tuple[int, int, str]],
    taiji_idx: Optional[int] = None,
) -> Optional[WaveDNA]:
    """
    从波浪分段中提取 DNA 基因
    
    TOMAS v2.0 定义：
        DNA 基因 = （第一浪时间长度，第一浪幅度）
        太极中心 = 最重要的历史顶/底
    
    Args:
        prices: 价格序列
        waves: 波浪分段列表
        taiji_idx: 太极中心索引（可选，未提供则自动检测）
    
    Returns:
        WaveDNA 对象，未检测到返回 None
    """
    if len(waves) < 2:
        return None
    
    # 自动检测太极中心
    if taiji_idx is None:
        taiji_idx = _find_taiji_center(prices)
    
    taiji_price = prices[taiji_idx] if taiji_idx < len(prices) else prices[0]
    
    # 提取第一浪（通常是前两个分段之一）
    first_wave = waves[0]
    first_duration = first_wave[1] - first_wave[0]
    first_amplitude = abs(prices[first_wave[1]] - prices[first_wave[0]])
    
    # 提取所有浪的长度和幅度
    wave_counts = []
    wave_amplitudes = []
    for start, end, _ in waves:
        wave_counts.append(end - start)
        wave_amplitudes.append(abs(prices[end] - prices[start]))
    
    # 验证斐波那契倍数
    from app.core.topo_invariants import (
        verify_fibonacci_multiples,
        verify_lucas_self_similarity,
    )
    
    fib_result = verify_fibonacci_multiples(wave_amplitudes)
    lucas_result = verify_lucas_self_similarity(
        [c for _, _, _ in waves]  # 用时间长度
    )
    
    # 计算 MDL 得分（简化：用压缩比）
    mdl_score = _compute_mdl_score(prices, waves)
    
    # 计算置信度
    confidence = _compute_confidence(
        fib_result["match_rate"],
        lucas_result["match_rate"],
        mdl_score,
    )
    
    return WaveDNA(
        first_wave_duration=first_duration,
        first_wave_amplitude=first_amplitude,
        taiji_idx=taiji_idx,
        taiji_price=taiji_price,
        wave_counts=wave_counts,
        wave_amplitudes=wave_amplitudes,
        fibonacci_match=fib_result["valid"],
        lucas_match=lucas_result["valid"],
        mdl_score=mdl_score,
        confidence=confidence,
    )


def _find_taiji_center(prices: np.ndarray) -> int:
    """自动检测太极中心（最重要的历史顶/底）"""
    if len(prices) < 60:
        return 0
    
    window = min(60, len(prices) // 2)
    recent = prices[-window:]
    
    # 找窗口内的最高点和最低点
    max_idx = np.argmax(recent)
    min_idx = np.argmin(recent)
    
    # 选择更极端的那个
    mid = np.mean(recent)
    if abs(recent[max_idx] - mid) > abs(recent[min_idx] - mid):
        return len(prices) - window + max_idx
    else:
        return len(prices) - window + min_idx


def _compute_mdl_score(
    prices: np.ndarray,
    waves: List[Tuple[int, int, str]],
) -> float:
    """
    计算 MDL（最小描述长度）得分
    
    TOMAS v2.0 定义：
        MDL = L(Program) + L(Data|Program)
        得分越高表示压缩越好（DNA 基因越有效）
    
    简化实现：
        用波浪分段的规则性作为 Program 长度，
        用残差作为 Data|Program 长度。
    """
    if len(waves) < 2:
        return 0.0
    
    # 计算波浪长度的规律性（用变异系数）
    wave_lengths = np.array([end - start for start, end, _ in waves])
    if len(wave_lengths) < 2:
        return 0.0
    
    cv = np.std(wave_lengths) / (np.mean(wave_lengths) + 1e-10)
    
    # 计算残差（实际价格 vs 波浪模型预测）
    residuals = []
    for start, end, wave_type in waves:
        segment = prices[start:end]
        if len(segment) > 1:
            # 简化：用线性趋势的残差
            x = np.arange(len(segment))
            coeffs = np.polyfit(x, segment, 1)
            predicted = np.polyval(coeffs, x)
            residuals.extend(segment - predicted)
    
    residual_entropy = np.var(residuals) if residuals else 1.0
    
    # MDL 得分（简化：正则化负对数似然）
    mdl_score = 1.0 / (1.0 + cv + residual_entropy)
    return float(mdl_score)


def _compute_confidence(
    fib_match_rate: float,
    lucas_match_rate: float,
    mdl_score: float,
) -> float:
    """计算 DNA 置信度"""
    # 加权平均
    confidence = (
        0.4 * fib_match_rate +
        0.3 * lucas_match_rate +
        0.3 * mdl_score
    )
    return float(np.clip(confidence, 0.0, 1.0))


# ─────────────────────────────────────────────
# κ-Snap 溯因验证
# ─────────────────────────────────────────────

def ksnap_verify(
    prices: np.ndarray,
    dna: WaveDNA,
    tolerance: float = 0.15,
) -> Dict:
    """
    κ-Snap 溯因验证
    
    TOMAS v2.0 定义：
        κ-Snap 是一种溯因推理算法，
        通过搜索最小描述长度（MDL）的程序来解释观测数据。
        
        验证步骤：
        1. 用 DNA 基因生成预测（倍数生成）
        2. 比较预测与实际
        3. 计算 MDL 得分
        4. 若得分 > κ（阈值），则接受 DNA
    
    Args:
        prices: 价格序列
        dna: WaveDNA 对象
        tolerance: 容许误差
    
    Returns:
        验证结果字典
    """
    if dna is None:
        return {"valid": False, "reason": "No DNA provided"}
    
    # 1. 用 DNA 基因生成预测
    from app.core.topo_invariants import fibonacci_numbers
    
    predicted_amplitudes = []
    fib = fibonacci_numbers(len(dna.wave_amplitudes) + 2)
    
    for i in range(len(dna.wave_amplitudes)):
        predicted = dna.first_wave_amplitude * fib[i + 1]  # F(1)=1, F(2)=1, ...
        predicted_amplitudes.append(predicted)
    
    # 2. 比较预测与实际
    errors = []
    for actual, predicted in zip(dna.wave_amplitudes, predicted_amplitudes):
        if predicted > 0:
            error = abs(actual - predicted) / predicted
            errors.append(error)
    
    if not errors:
        return {"valid": False, "reason": "No valid predictions"}
    
    avg_error = np.mean(errors)
    max_error = np.max(errors)
    
    # 3. 计算 MDL 得分
    mdl_score = dna.mdl_score
    
    # 4. 决策（κ = tolerance）
    kappa = tolerance
    valid = (avg_error < kappa) and (mdl_score > 0.3)
    
    return {
        "valid": valid,
        "avg_error": float(avg_error),
        "max_error": float(max_error),
        "mdl_score": mdl_score,
        "kappa": kappa,
        "predicted_amplitudes": predicted_amplitudes,
        "actual_amplitudes": dna.wave_amplitudes,
        "details": [
            {
                "wave": i + 1,
                "predicted": predicted_amplitudes[i],
                "actual": dna.wave_amplitudes[i],
                "error": errors[i],
            }
            for i in range(len(errors))
        ],
    }


# ─────────────────────────────────────────────
# 相位连续性验证（接入 topo_invariants）
# ─────────────────────────────────────────────

def verify_phase_continuity(
    prices: np.ndarray,
    dna: Optional[WaveDNA] = None,
    window: int = 30,
) -> Dict:
    """
    验证相位连续性
    
    TOMAS v2.0 定义：
        相位连续区（PCS > 0.7）→ DNA 有效
        过渡区（0.3 < PCS < 0.7）→ DNA 谨慎使用
        相变奇点区（PCS < 0.3）→ DNA 失效
    
    Args:
        prices: 价格序列
        dna: WaveDNA 对象（可选）
        window: 分析窗口
    
    Returns:
        相位连续性验证结果
    """
    from app.core.topo_invariants import phase_continuity_score
    
    pcs = phase_continuity_score(prices, window)
    
    if dna is not None:
        # 如果提供了 DNA，验证其是否在相位连续区内
        dna_valid_in_phase = (pcs >= 0.7) and dna.confidence >= 0.6
    else:
        dna_valid_in_phase = None
    
    if pcs >= 0.7:
        regime = "phase_continuous"
        action = "normal"
    elif pcs >= 0.3:
        regime = "transition"
        action = "caution"
    else:
        regime = "phase_singularity"
        action = "circuit_break"
    
    return {
        "pcs": float(pcs),
        "regime": regime,
        "action": action,
        "dna_valid_in_phase": dna_valid_in_phase,
        "threshold": {
            "phase_continuous": 0.7,
            "transition": 0.3,
        },
    }


# ─────────────────────────────────────────────
# 模块自检
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # 测试波浪检测
    print("=== 波浪检测 ===")
    test_prices = np.array([
        100, 105, 110, 108, 112, 115, 113, 110, 108, 105,
        103, 106, 110, 115, 120, 118, 115, 112, 110, 108,
    ])
    waves = detect_waves(test_prices, method="simple")
    print(f"Detected {len(waves)} waves: {waves}")
    
    # 测试 DNA 提取
    print("\n=== DNA 提取 ===")
    dna = extract_dna(test_prices, waves)
    if dna:
        print(f"DNA: duration={dna.first_wave_duration}, amplitude={dna.first_wave_amplitude:.2f}")
        print(f"Confidence: {dna.confidence:.2f}")
    
    # 测试 κ-Snap 验证
    print("\n=== κ-Snap 验证 ===")
    if dna:
        result = ksnap_verify(test_prices, dna)
        print(f"Valid: {result['valid']}")
        print(f"Avg Error: {result['avg_error']:.3f}")
    
    # 测试相位连续性
    print("\n=== 相位连续性 ===")
    phase_result = verify_phase_continuity(test_prices)
    print(f"PCS: {phase_result['pcs']:.3f}")
    print(f"Regime: {phase_result['regime']}")
