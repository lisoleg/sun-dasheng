"""
phase_analyzer.py — 相位连续性分析器 (TOMAS v2.0)

实现：
- LOB 深度熵计算（限价簿深度模拟）
- 相位连续性评分（PCS）
- 流动性熔断判据（LOB 深度奇点检测）
- ENPV（期望净正收益）决策计算

参考文献：
[1] TOMAS v2.0：基于广义代数理论（GAT）的太乙互搏公理体系
[2] 鲁兆：波浪理论中的相位连续性假设
"""

from typing import Dict, Optional, Tuple, List
import numpy as np
from datetime import datetime

from app.core.topo_invariants import (
    phase_continuity_score,
    detect_phase_singularity,
    find_taiji_center,
)


# ────────────────────────────────────────────
# LOB 深度模拟（无真实 LOB 数据时的替代方案）
# ────────────────────────────────────────────

def compute_lob_depth_entropy(
    prices: np.ndarray,
    volumes: np.ndarray,
    window: int = 20,
    num_levels: int = 10
) -> Dict:
    """
    计算限价簿（LOB）深度熵
    
    当无真实 LOB 数据时，用成交量分布模拟 LOB 深度：
    - 买盘深度 ∝ 下跌时的成交量
    - 卖盘深度 ∝ 上涨时的成交量
    
    熵定义：H = -Σ p_i log(p_i)
    其中 p_i 为第 i 个价位的深度占比。
    
    熔断判据：
        H < H_threshold → 流动性枯竭（奇点）
        经验阈值：H < 0.5（归一化后）
    
    Args:
        prices: 价格序列
        volumes: 成交量序列
        window: 计算窗口
        num_levels: 模拟价位层数
    
    Returns:
        包含 entropy, bid_depth, ask_depth, is_singularity 的字典
    """
    if len(prices) < window or len(volumes) < window:
        return {"entropy": 0.5, "is_singularity": False, "reason": "数据不足"}
    
    recent_prices = prices[-window:]
    recent_volumes = volumes[-window:]
    
    # 计算收益率，判断买卖方向
    returns = np.diff(recent_prices) / recent_prices[:-1]
    
    # 模拟买盘深度（价格下跌时的成交量 = 被动买盘）
    buy_volume = recent_volumes[1:][returns < 0]
    # 模拟卖盘深度（价格上涨时的成交量 = 被动卖盘）
    sell_volume = recent_volumes[1:][returns > 0]
    
    # 构建模拟价位（简化：用分位数划分 num_levels 层）
    if len(buy_volume) > 0:
        bid_levels = np.percentile(
            recent_prices[1:][returns < 0] if len(recent_prices[1:][returns < 0]) > 0 
            else recent_prices, 
            np.linspace(10, 90, num_levels)
        )
        bid_depths = np.ones(num_levels) * (np.sum(buy_volume) / num_levels)
    else:
        bid_depths = np.ones(num_levels) * 0.01
    
    if len(sell_volume) > 0:
        ask_levels = np.percentile(
            recent_prices[1:][returns > 0] if len(recent_prices[1:][returns > 0]) > 0
            else recent_prices,
            np.linspace(10, 90, num_levels)
        )
        ask_depths = np.ones(num_levels) * (np.sum(sell_volume) / num_levels)
    else:
        ask_depths = np.ones(num_levels) * 0.01
    
    # 归一化深度
    total_bid = np.sum(bid_depths)
    total_ask = np.sum(ask_depths)
    total = total_bid + total_ask + 1e-10
    
    bid_probs = bid_depths / total
    ask_probs = ask_depths / total
    all_probs = np.concatenate([bid_probs, ask_probs])
    
    # 计算熵（去除零概率）
    non_zero = all_probs[all_probs > 0]
    entropy = -np.sum(non_zero * np.log(non_zero))
    
    # 归一化熵（最大熵 = log(2 * num_levels)）
    max_entropy = np.log(2 * num_levels)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5
    
    # 熔断判据
    is_singularity = normalized_entropy < 0.4
    
    return {
        "entropy": float(normalized_entropy),
        "raw_entropy": float(entropy),
        "bid_depth": float(total_bid),
        "ask_depth": float(total_ask),
        "bid_ask_ratio": float(total_bid / (total_ask + 1e-10)),
        "is_singularity": is_singularity,
        "singularity_type": "lob_depth_collapse" if is_singularity else None,
    }


# ────────────────────────────────────────────
# 相位连续性分析
# ────────────────────────────────────────────

def analyze_phase_continuity(
    prices: np.ndarray,
    volumes: Optional[np.ndarray] = None,
    window: int = 30,
    taiji_idx: Optional[int] = None,
) -> Dict:
    """
    完整的相位连续性分析
    
    TOMAS v2.0 定义：
        相位连续区（PCS > 0.7）→ 鲁兆体系有效
        过渡区（0.3 < PCS < 0.7）→ 谨慎使用鲁兆
        相变奇点区（PCS < 0.3）→ 鲁兆体系失效，触发熔断
    
    Args:
        prices: 价格序列
        volumes: 成交量序列（可选，用于 LOB 熵计算）
        window: 分析窗口
        taiji_idx: 太极中心索引（可选）
    
    Returns:
        完整分析结果字典
    """
    # 1. 相位连续性评分（来自 topo_invariants）
    pcs = phase_continuity_score(prices, window, taiji_idx)
    
    # 2. 奇点检测
    singularity = detect_phase_singularity(prices, volumes, window)
    
    # 3. LOB 深度熵（如果有成交量数据）
    lob_result = None
    if volumes is not None and len(volumes) == len(prices):
        lob_result = compute_lob_depth_entropy(prices, volumes, window)
        # LOB 奇点覆盖相位奇点判断
        if lob_result and lob_result.get("is_singularity"):
            singularity["is_singularity"] = True
            singularity["severity"] = "high"
            singularity["lob_contribution"] = True
    
    # 4. 太极中心（如果未提供）
    if taiji_idx is None and len(prices) >= 60:
        taiji_idx = find_taiji_center(prices, min(60, len(prices)))
    
    # 5. 综合判断
    if pcs >= 0.7:
        regime = "phase_continuous"
        lu_zhao_valid = True
        action = "normal"
    elif pcs >= 0.3:
        regime = "transition"
        lu_zhao_valid = False
        action = "caution"
    else:
        regime = "phase_singularity"
        lu_zhao_valid = False
        action = "circuit_break"
    
    return {
        "pcs": float(pcs),
        "regime": regime,
        "lu_zhao_valid": lu_zhao_valid,
        "action": action,
        "singularity": singularity,
        "lob_depth": lob_result,
        "taiji_idx": taiji_idx,
        "window_used": window,
    }


# ────────────────────────────────────────────
# ENPV（期望净正收益）决策计算
# ────────────────────────────────────────────

def compute_enpv(
    entry_price: float,
    target_price: float,
    stop_loss: float,
    fill_probability: float,
    slippage_cost: float,
    opportunity_cost: float,
    position_size: float,
    win_probability: Optional[float] = None,
) -> Dict:
    """
    计算 ENPV（期望净正收益）
    
    TOMAS v2.0 判据 1：
        ENPV = P_fill × [P_win × (T - S) + P_lose × (SL - S)] - C_opp
    
    其中：
    - P_fill：成交概率（LOB 深度决定）
    - P_win：盈利概率（信号置信度）
    - T：目标价位
    - SL：止损价
    - S：入场价（含滑点）
    - C_opp：机会成本（错过行情）
    
    决策规则：
        ENPV > 0 → 追单
        ENPV < 0 → 放弃
        ENPV > 0 但 LOB 奇点 → 极小仓 IOC
    
    Args:
        entry_price: 入场价（理论）
        target_price: 目标止盈价
        stop_loss: 止损价
        fill_probability: 成交概率 [0, 1]
        slippage_cost: 滑点成本（金额）
        opportunity_cost: 机会成本（错过行情的损失）
        position_size: 仓位大小（股数/合约数）
        win_probability: 盈利概率（可选，默认用风险报酬比估算）
    
    Returns:
        ENPV 计算结果及决策建议
    """
    # 计算入场实际成本（含滑点）
    actual_entry = entry_price + slippage_cost
    
    # 估算盈利概率（如果未提供）
    if win_probability is None:
        risk = abs(actual_entry - stop_loss)
        reward = abs(target_price - actual_entry)
        if risk > 0:
            win_probability = reward / (reward + risk)  # 简化：用风险报酬比
        else:
            win_probability = 0.5
    
    lose_probability = 1.0 - win_probability
    
    # 盈亏金额
    win_amount = (target_price - actual_entry) * position_size
    lose_amount = (stop_loss - actual_entry) * position_size
    
    # ENPV 计算
    expected_gross = (
        fill_probability * 
        (win_probability * win_amount + lose_probability * lose_amount)
    )
    enpv = expected_gross - opportunity_cost
    
    # 决策
    if enpv > 0:
        decision = "chase"
        reason = f"ENPV = {enpv:.2f} > 0，期望收益为正"
    elif enpv == 0:
        decision = "neutral"
        reason = "ENPV = 0，盈亏平衡"
    else:
        decision = "abandon"
        reason = f"ENPV = {enpv:.2f} < 0，期望收益为负"
    
    return {
        "enpv": float(enpv),
        "decision": decision,
        "reason": reason,
        "details": {
            "fill_probability": fill_probability,
            "win_probability": win_probability,
            "lose_probability": lose_probability,
            "expected_win": float(win_amount),
            "expected_lose": float(lose_amount),
            "expected_gross": float(expected_gross),
            "opportunity_cost": float(opportunity_cost),
            "slippage_cost": float(slippage_cost),
        }
    }


def enpv_with_lob_adjustment(
    entry_price: float,
    target_price: float,
    stop_loss: float,
    bid_depth: float,
    ask_depth: float,
    spread: float,
    slippage_model: str = "linear",
    position_size: float = 1.0,
    volatility: float = 0.02,
) -> Dict:
    """
    带 LOB 调整的 ENPV 计算
    
    考虑 LOB 深度对成交概率和滑点的动态影响：
    - 深度充足 → fill_probability 高，滑点小
    - 深度不足 → fill_probability 低，滑点大，触发熔断
    
    TOMAS v2.0 滑点模型：
        slippage = spread/2 + α × (order_size / avg_depth)
        α 为调整系数（市场冲击）
    
    Args:
        entry_price: 入场价
        target_price: 目标止盈价
        stop_loss: 止损价
        bid_depth: 买盘深度
        ask_depth: 卖盘深度
        spread: 买卖价差
        slippage_model: 滑点模型（"linear" | "percentage" | "none"）
        position_size: 仓位大小
        volatility: 波动率（用于 percentage 模型）
    
    Returns:
        调整后的 ENPV 结果
    """
    # 1. 计算成交概率（基于 LOB 深度）
    avg_depth = (bid_depth + ask_depth) / 2.0
    if avg_depth > 0:
        # 深度越深，成交概率越高（简化模型）
        fill_probability = min(0.95, avg_depth / (avg_depth + position_size))
    else:
        fill_probability = 0.05  # 深度为 0，几乎无法成交
    
    # 2. 计算滑点成本
    if slippage_model == "linear":
        slippage = spread / 2.0 + 0.1 * (position_size / (avg_depth + 1e-10))
    elif slippage_model == "percentage":
        slippage = entry_price * volatility * (position_size / (avg_depth + 1e-10))
    else:  # "none"
        slippage = spread / 2.0
    
    # 3. 机会成本（简化：用 ATR 估算）
    opportunity_cost = volatility * entry_price * 0.5
    
    # 4. 调用基础 ENPV 计算
    result = compute_enpv(
        entry_price=entry_price,
        target_price=target_price,
        stop_loss=stop_loss,
        fill_probability=fill_probability,
        slippage_cost=slippage,
        opportunity_cost=opportunity_cost,
        position_size=position_size,
    )
    
    # 5. 附加 LOB 信息
    result["lob_adjustment"] = {
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "spread": spread,
        "avg_depth": avg_depth,
        "fill_probability": fill_probability,
        "slippage": slippage,
        "slippage_model": slippage_model,
    }
    
    # 6. 熔断覆盖
    if avg_depth < 0.01 * entry_price:  # 深度严重不足
        result["decision"] = "circuit_break"
        result["reason"] = "LOB 深度奇点，触发流动性熔断"
        result["enpv"] = float(-opportunity_cost)  # 强制为负
    
    return result


# ────────────────────────────────────────────
# 流动性熔断执行器
# ────────────────────────────────────────────

def execute_circuit_breaker(
    phase_result: Dict,
    enpv_result: Dict,
    action_mode: str = "strict",
) -> Dict:
    """
    执行流动性熔断决策
    
    TOMAS v2.0 熔断规则：
        if LOB_depth_singularity:
            → 无论 ENPV 如何，不追单，只 IOC（极小仓）
        if phase_singularity AND enpv < 0:
            → 强制平仓/放弃所有追单
        if phase_continuous AND enpv > 0:
            → 正常执行
    
    Args:
        phase_result: analyze_phase_continuity 的输出
        enpv_result: compute_enpv 或 enpv_with_lob_adjustment 的输出
        action_mode: 执行模式
            - "strict"：严格熔断（奇点区全部停止）
            - "lenient"：宽松模式（仅覆盖 ENPV > 0 的追单决策）
    
    Returns:
        最终执行决策字典
    """
    is_singularity = phase_result.get("singularity", {}).get("is_singularity", False)
    pcs = phase_result.get("pcs", 0.5)
    enpv = enpv_result.get("enpv", 0)
    original_decision = enpv_result.get("decision", "abandon")
    
    # 严格模式
    if action_mode == "strict":
        if is_singularity or pcs < 0.3:
            final_decision = "circuit_break"
            reason = f"严格熔断：奇点检测={is_singularity}, PCS={pcs:.2f}"
            risk_action = "close_all"
        elif pcs < 0.7:
            final_decision = "caution"
            reason = f"过渡区：PCS={pcs:.2f}，降低仓位至 30%"
            risk_action = "reduce_position"
        else:
            final_decision = original_decision
            reason = f"相位连续区：PCS={pcs:.2f}，正常执行"
            risk_action = "normal"
    
    # 宽松模式
    else:  # "lenient"
        if is_singularity and original_decision == "chase":
            final_decision = "ioc_small"
            reason = f"宽松熔断：奇点区禁止追单，改为 IOC 极小仓"
            risk_action = "ioc_only"
        elif pcs < 0.3 and enpv > 0:
            final_decision = "abandon"
            reason = f"相变区 ENPV 不可信，放弃追单"
            risk_action = "no_new_position"
        else:
            final_decision = original_decision
            reason = "未触发熔断条件"
            risk_action = "normal"
    
    return {
        "final_decision": final_decision,
        "reason": reason,
        "risk_action": risk_action,
        "original_enpv_decision": original_decision,
        "pcs": pcs,
        "is_singularity": is_singularity,
        "action_mode": action_mode,
        "timestamp": datetime.now().isoformat(),
    }


# ────────────────────────────────────────────
# 模块自检
# ────────────────────────────────────────────

if __name__ == "__main__":
    # 测试相位分析
    print("=== 相位连续性分析 ===")
    test_prices = np.cumprod(1 + np.random.normal(0.001, 0.015, 100))
    test_volumes = np.random.uniform(1000, 5000, 100)
    
    result = analyze_phase_continuity(test_prices, test_volumes, window=30)
    print(f"PCS = {result['pcs']:.3f}")
    print(f"Regime = {result['regime']}")
    print(f"Action = {result['action']}")
    
    # 测试 ENPV
    print("\n=== ENPV 计算 ===")
    enpv_result = compute_enpv(
        entry_price=100.0,
        target_price=110.0,
        stop_loss=95.0,
        fill_probability=0.8,
        slippage_cost=0.1,
        opportunity_cost=1.0,
        position_size=100,
    )
    print(f"ENPV = {enpv_result['enpv']:.2f}")
    print(f"Decision = {enpv_result['decision']}")
    
    # 测试熔断
    print("\n=== 熔断执行 ===")
    circuit_result = execute_circuit_breaker(result, enpv_result, "strict")
    print(f"Final Decision = {circuit_result['final_decision']}")
    print(f"Reason = {circuit_result['reason']}")
