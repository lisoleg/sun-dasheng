# 孙大圣 Phase 3 规划文档

**版本**: v0.3.0-draft
**日期**: 2026-06-23
**状态**: 规划中 · 待评审

---

## 1. 背景与目标

### 1.1 当前状态（Phase 1 + 2）

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 (v0.1.0) | 3个理论引擎 + TOMAS-AGI双引擎 + 前端MVP | ✅ 已完成 |
| Phase 2 (v0.2.0) | 4个新理论引擎 + 完整回测引擎 + Bloomberg风格Web UI + 信号融合 | ✅ 已完成 |
| TOMAS v2.0 升级 | 拓扑不变量 + 相位连续性过滤 + DNA倍发生成验证 | ✅ 已完成 |

### 1.2 Phase 3 核心目标

基于**复合体理学文章3《代币化AGI经济架构》**的理论框架，在孙大圣系统中引入**多Agent协作交易机制**：

1. **多Agent并行推理** — 7个理论引擎作为独立Agent并行运行
2. **代币激励经济** — 基于信号准确率的代币奖励/惩罚机制
3. **协同决策** — 多Agent投票 + 协调者Agent最终决策
4. **持续学习** — Agent根据历史表现动态调整权重

---

## 2. 多Agent系统架构

### 2.1 系统拓扑

```
┌─────────────────────────────────────────────────────────┐
│                   协调者Agent                          │
│  (CoordinatorAgent)                                 │
│  - 收集各Agent信号                                     │
│  - 代币权重投票                                        │
│  - 输出最终交易决策                                     │
│  - 风险熔断 override                                   │
└──────────┬──────────────────────────┬──────────────────┘
             │                          │
    ┌────────▼────────┐    ┌───────▼────────┐
    │  理论Agent池      │    │  功能Agent池       │
    ├──────────────────┤    ├──────────────────┤
    │ · 太极Agent      │    │ · 相位分析Agent   │
    │ · 螺旋律Agent    │    │ · DNA检测Agent    │
    │ · 波浪理论Agent   │    │ · 风控Agent       │
    │ · 对偶律Agent    │    │ · 执行Agent       │
    │ · 周期律Agent    │    └──────────────────┘
    │ · 江恩角度线Agent │
    │ · BG均线Agent     │
    └──────────────────┘
```

### 2.2 Agent 定义

#### 2.2.1 理论Agent（7个）

每个理论Agent封装一个理论引擎，独立运行，输出结构化信号。

```python
@dataclass
class AgentSignal:
    agent_name: str           # "TaijiAgent"
    direction: str            # "BUY" | "SELL" | "HOLD"
    confidence: float         # 0.0 ~ 1.0
    target_price: float | None
    stop_loss: float | None
    take_profit: float | None
    reasoning: str            # 可追溯的推理链
    phase_valid: bool        # 相位连续性是否通过
    tokens_earned: float = 0.0  # 历史累计代币（只读）
```

#### 2.2.2 协调者Agent（1个）

核心决策组件，实现**代币权重投票**：

```python
class CoordinatorAgent:
    """
    协调者Agent — 多Agent决策融合
    
    决策规则（代币化AGI经济架构）：
    1. 每个Agent的投票权重 = 历史准确率 × 当前代币余额
    2. 相位连续性过滤：PCS < 0.3 时所有Agent信号熔断
    3. 仲裁机制：若 top-2 Agent方向冲突且置信度差 < 0.15，
       触发kappa-Snap溯因验证，由协调者做出仲裁决策
    4. 风险override：风控Agent有最高优先级（强平/止损）
    """
    
    def decide(self, agent_signals: list[AgentSignal],
               market_state: MarketState) -> FinalDecision:
        # 1. 相位连续性过滤
        if market_state.pcs < 0.3:
            return FinalDecision(action="HALT", reason="相变奇点熔断")
        
        # 2. 代币权重投票
        weighted_votes = self._token_weighted_vote(agent_signals)
        
        # 3. 冲突仲裁
        if self._has_conflict(weighted_votes):
            arbitrated = self._kappa_snap_arbitrate(
                agent_signals, market_state
            )
            return arbitrated
        
        # 4. 输出最终决策
        return self._aggregate(weighted_votes)
```

#### 2.2.3 功能Agent（3个）

| Agent | 职责 | 输入 | 输出 |
|--------|------|------|------|
| 相位分析Agent | 实时计算PCS + LOB熵 + ENPV | 最近120根K线 | PhaseState |
| DNA检测Agent | 波浪检测 + κ-Snap验证 | 最近200根K线 | DNAVerification |
| 风控Agent | 实时VaR/CVaR计算 + 强平线监控 | 当前持仓 + 市场数据 | RiskAlert |

---

## 3. 代币经济机制

### 3.1 设计原则（来自文章3）

文章3提出：**AGI经济系统的核心问题是Arrow不可能定理**——
> 不存在一种投票机制能同时满足：公平性、帕累托最优、独立性、非独裁性。

**孙大圣的解决方案**：用**代币激励**替代纯投票：
- 准确信号 → 赚代币 → 未来投票权重上升
- 错误信号 → 扣代币 → 未来投票权重下降
- 代币耗尽 → Agent被暂时禁用（市场经济惩罚）

### 3.2 代币流通设计

```
                    ┌─────────────┐
        准确信号奖励 │  代币池        │ 错误信号惩罚
        (+Token)   │  (TokenPool)  │ (-Token)
                    └──────┬────────┘
                           │
              ┌────────────▼────────────┐
              │  协调者Agent分配         │
              │  - 按信号质量分配奖励    │
              │  - 按错误程度分配惩罚    │
              │  - 通胀控制（每月销毁2%）│
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  理论Agent代币余额        │
              │  - 决定未来投票权重      │
              │  - 余额>0才可参与投票   │
              │  - 余额<0 → 冻结10个周期│
              └─────────────────────────┘
```

### 3.3 代币计算规则

```python
def calculate_token_reward(
    agent: TheoryAgent,
    signal: AgentSignal,
    actual_outcome: Literal["profit", "loss", "neutral"],
    pcs_at_signal: float,
) -> float:
    """
    代币奖励计算（TOMAS v3.0核心机制）
    
    奖励 = 基础奖励 × 置信度 × 相位连续性系数 × 稀有度乘数
    """
    BASE_REWARD = 10.0
    RARE_MULTIPLIER = 1.5  # 当其他Agent都错、仅此Agent对时
    
    # 置信度加权
    conf_weight = signal.confidence
    
    # 相位连续性系数（PCS越高，奖励越有效）
    phase_coeff = pcs_at_signal  # 0.0 ~ 1.0
    
    # 稀有度乘数
    rare_mult = RARE_MULTIPLIER if _is_rare_correct(agent, signal) else 1.0
    
    if actual_outcome == "profit":
        return BASE_REWARD * conf_weight * phase_coeff * rare_mult
    elif actual_outcome == "loss":
        # 惩罚 = 奖励的1.2倍（鼓励保守）
        return -BASE_REWARD * conf_weight * 1.2
    else:
        return 0.0
```

---

## 4. 协同决策协议

### 4.1 消息传递架构

使用**事件总线（Event Bus）** 实现Agent间通信（基于现有WebSocket基础设施扩展）：

```python
# Agent间消息格式
class AgentMessage:
    sender: str               # "TaijiAgent"
    receiver: str | "broadcast"  # "CoordinatorAgent" | "broadcast"
    msg_type: str             # "SIGNAL" | "VOTE" | "ARBITRATION" | "RISK_ALERT"
    payload: dict
    timestamp: datetime
    correlation_id: str       # 追踪一次决策的全链路
```

### 4.2 决策流水线

```
MarketData → [理论Agent池并行] → AgentSignal[]
                                 │
                                 ▼
                          [相位分析Agent] → PhaseState
                                 │
                                 ▼
                        AgentSignal[] + PhaseState
                                 │
                                 ▼
                      [协调者Agent] → FinalDecision
                                 │
                                 ▼
                            [风控Agent] → RiskAdjustedDecision
                                 │
                                 ▼
                           [执行Agent] → Order
```

### 4.3 并行加速策略

```python
# 使用 asyncio 并行运行所有理论Agent
async def run_all_agents(bar: Bar) -> list[AgentSignal]:
    tasks = [
        taiji_agent.analyze(bar),
        spiral_agent.analyze(bar),
        elliott_agent.analyze(bar),
        dual_law_agent.analyze(bar),
        cycle_law_agent.analyze(bar),
        gann_angle_agent.analyze(bar),
        bg_ma_agent.analyze(bar),
    ]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
```

---

## 5. 实现路线图

### 5.1 里程碑划分

| 里程碑 | 内容 | 预估工作量 |
|--------|------|------------|
| **M1: Agent框架** | 定义Agent基类 + AgentMessage协议 + 事件总线 | 3天 |
| **M2: 理论Agent封装** | 7个理论引擎封装为独立Agent | 2天 |
| **M3: 协调者Agent** | 代币权重投票 + 冲突仲裁 + 决策输出 | 4天 |
| **M4: 代币经济** | TokenPool + 奖励/惩罚计算 + 余额持久化 | 3天 |
| **M5: 功能Agent** | 相位分析/DNA检测/风控Agent | 3天 |
| **M6: 执行集成** | 与现有回测引擎 + 实盘执行集成 | 3天 |
| **M7: 前端可视化** | Agent投票可视化 + 代币排行榜 + 决策溯源 | 4天 |
| **M8: 测试网验证** | 历史数据回测 + Agent准确率排名 | 2天 |

**总计**: ~24工作日（约5周）

### 5.2 技术栈补充

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| 事件总线 | `asyncio.Queue` + Redis Pub/Sub（可选） | 轻量，与现有async架构兼容 |
| Agent状态持久化 | SQLite（本地）+ PostgreSQL（生产） | Agent代币余额需持久化 |
| 决策溯源 | Mermaid时序图生成（服务端） | 每次决策生成可追溯的推理链图表 |
| 前端Agent可视化 | D3.js关系图 | 展示Agent投票网络 |

---

## 6. 与现有系统的集成

### 6.1 复用现有模块

```
现有模块                    Phase 3 升级
─────────────────────────────────────────────
backend/app/services/theory/*  →  封装为 TheoryAgent 子类
backend/app/services/signal/*   →  升级为 CoordinatorAgent
backend/app/services/backtest/* →  加入多Agent并行回测模式
backend/app/api/ws.py          →  新增 agent_vote 频道
frontend/src/pages/SignalsPage  →  新增 Agent投票可视化面板
```

### 6.2 数据库变更

```sql
-- 新增 Agent 状态表
CREATE TABLE agent_states (
    agent_name    TEXT PRIMARY KEY,
    token_balance FLOAT NOT NULL DEFAULT 100.0,
    total_earned  FLOAT NOT NULL DEFAULT 0.0,
    total_penalty FLOAT NOT NULL DEFAULT 0.0,
    accuracy_30d  FLOAT NOT NULL DEFAULT 0.5,  -- 近30日准确率
    is_active     BOOLEAN DEFAULT TRUE,
    last_signal_at TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 新增 决策记录表（溯源用）
CREATE TABLE agent_decisions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    correlation_id TEXT NOT NULL,
    symbol         TEXT NOT NULL,
    final_action   TEXT NOT NULL,  -- BUY/SELL/HOLD/HALT
    agent_votes    JSON NOT NULL,  -- 各Agent投票详情
    coordinator_reasoning TEXT,
    actual_outcome TEXT,         -- profit/loss/neutral（后续回填）
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. 风险与挑战

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Agent并行性能瓶颈 | 120根K线 × 7Agent 可能超时 | 使用`asyncio.gather` + 设置单Agent超时（500ms） |
| 代币经济博弈攻击 | Agent可能"串通"（如果实现不当） | 每个Agent独立运行，无法访问其他Agent状态 |
| 协调者成为单点故障 | 协调者Agent崩溃 → 无法决策 | 协调者无状态设计，可从AgentSignal重新计算 |

### 7.2 理论风险

- **Arrow不可能定理**仍可能在极端市场条件下显现（所有Agent同时看错）
  - 缓解：引入**人类专家override**（可选功能， Phase 3 后期）
- **过度拟合代币机制**：Agent可能"讨好"近期市场，忽略长期规律
  - 缓解：代币奖励加入**衰减因子**（旧表现权重下降）

---

## 8. 下一步行动

### 8.1 立即启动（如批准）

1. **创建 `agent` 目录** — `backend/app/agents/`
2. **定义Agent基类** — `base_agent.py`
3. **实现事件总线** — `message_bus.py`
4. **封装第一个理论Agent** — `taiji_agent.py`（验证框架可行性）
5. **单元测试** — 验证Agent并行运行 + 消息传递

### 8.2 决策点（需老铁确认）

- [ ] **代币初始分配**：每个Agent初始100代币？还是根据Phase 1/2历史准确率分配？
- [ ] **协调者决策频率**：每根K线决策一次？还是仅在PCS变化 > 0.1时重新决策？
- [ ] **实盘交易优先级**：Phase 3 完成后是否立即接入实盘（币安）？还是继续纸面交易？
- [ ] **前端技术栈**：Agent投票可视化用D3.js还是直接用recharts？

---

## 附录A：参考理论

1. **复合体理学文章3**（2026-06-22）— 代币化AGI经济架构
2. **Arrow, K. J.** (1950) — *A Difficulty in the Concept of Social Welfare*
3. **Tokenomics设计模式** — 参考1inch、Curve投票托管制
4. **多Agent强化学习（MARL）** — 参考《Multi-Agent Reinforcement Learning: A Selective Overview》

---

*本文档由 WorkBuddy (齐活林) 根据复合体理学文章3生成，2026-06-23*
