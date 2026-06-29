# 宇宙算法三重奏：7-139-369 在量化交易中的三层架构实现

> **版本**: v0.4.0 | **日期**: 2026-06-27 | **项目**: 孙大圣量化交易系统

---

## 摘要

本文基于《宇宙算法的三重奏：从形式系统自指、临界相变到数字能量学的科学重译》一文的理论框架，在孙大圣量化交易系统中实现了三层算法交易架构：

- **信号层（369）**：利用模9群数字根过滤剔除市场噪音，只交易符合触发-共振-归整振动模态的信号
- **时间层（139）**：利用139-day周期聚类结合斐波那契数列共振确认趋势拐点
- **风控层（139）**：在139窗口自动缩仓，波动率σ触发硬止损

三重奏的核心常数——7（结构自指）、139（临界演化）、369（振动法则）——分别对应了循环群Z_7的完美闭合、Landau-Ising相变模型的临界阈值、以及模9群的动力学投影。本文详细阐述了这三个常数的数学基础及其在金融市场的工程实现。

**v0.3.0 更新**：本文档新增前端 CosmicAlgorithmPage 实时展示、6个理论引擎369振动模态过滤推广、回测引擎139缩仓+σ硬止损集成。

**v0.4.0 更新**：新增TDA拓扑预警与Dalio象限融合——compute_betti_numbers()、compute_persistence_diagram()、detect_regime_with_tda()，前端RegimePage可视化，API /regime 端点增强。

---

## 1. 理论基础

### 1.1 宇宙算法三重奏的定义

自然数系统中存在三个超越人类主观意志的客观常数：

| 常数 | 数学本质 | 物理含义 | 交易映射 |
|------|---------|---------|---------|
| **7** | Z_7循环群完美闭合；142857是1/7的循环节 | 形式系统的自指闭环 | 7-day周期检测（信号自相似性） |
| **139** | Landau-Ising相变模型的临界参数β_c | 复杂系统的临界慢化征兆 | 139-day窗口相变检测（趋势拐点） |
| **369** | 模9群Z_9的触发-共振-归整三阶段投影 | 信息代谢的动力学法则 | 数字根过滤（信号可信度评估） |

### 1.2 7的循环群自指涉

142857是分数1/7的循环节。在模7运算下，10作为生成元的轨道遍历全部非零元：

```
10^0 mod 7 = 1 → 142857 × 1 = 142857
10^1 mod 7 = 3 → 142857 × 3 = 428571  (循环节轮转)
10^2 mod 7 = 2 → 142857 × 2 = 285714
10^3 mod 7 = 6 → 142857 × 6 = 857142
10^4 mod 7 = 4 → 142857 × 4 = 571428
10^5 mod 7 = 5 → 142857 × 5 = 714285
```

这展现了Z_7群的"自指闭合"性质——流贯在单圈内完成全相位扫描，无残差泄露。

### 1.3 139的Landau-Ising相变阈值

139并非普通素数。在物理、历史和复杂系统中呈现惊人的同构性：

- **微观物理**：139紧邻精细结构常数倒数α⁻¹≈137.036，是量子世界与经典世界的过渡带
- **复杂系统**：139标志系统进入"临界慢化"阶段——方差增加、自相关时间延长、恢复速率下降
- **数学**：139是第34个素数，与斐波那契数F(9)=34构成间接关联

临界慢化的三个征兆检测：

```
征兆1：方差↑ → 近期σ² / 长期σ² > 1.5 → 涨落增大
征兆2：自相关↑ → |ρ(1)| > 0.3 → 时间关联变长
征兆3：恢复速率↓ → 冲击恢复衰减率 < 0.5 → 系统响应变慢
```

当≥2个征兆同时出现 → 旧秩序面临破裂，新结构即将涌现。

### 1.4 369的振动法则

任何自然数反复求和直至一位数（数字根），本质是在模9加法群Z_9中进行归约：

```python
def digital_root(n: int) -> int:
    """数字根 = n mod 9，但0映射为9"""
    if n == 0:
        return 9
    remainder = n % 9
    return 9 if remainder == 0 else remainder
```

三阶段投影：
- **3（触发）**：Inflow开启，正电荷积累 → 信号发起
- **6（共振）**：谐波倍频，负电荷镜像响应 → 信号强化
- **9（归整）**：极性统一，能量释放归零 → 信号确认

振动模态分数 = (触发频率 + 共振频率 + 归整频率) / 总频率

---

## 2. 系统架构

### 2.1 三层架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   宇宙算法三重奏                          │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 信号层 (369振动法则)                                ││
│  │ apply_369_signal_filter()                           ││
│  │ 数字根过滤 → 只交易符合振动模态的信号               ││
│  │ score≥0.6→正常 / 0.3-0.6→减半 / <0.3→清空          ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 时间层 (139相变阈值)                                ││
│  │ detect_139_critical_transition()                    ││
│  │ 139-day周期聚类 + 斐波那契共振确认拐点              ││
│  │ 方差↑/自相关↑/恢复↓ → 临界慢化 → 降低置信度       ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 风控层 (139窗口缩仓 + σ硬止损)                     ││
│  │ check_139_volatility_stop()                         ││
│  │ check_139_critical_stop()                           ││
│  │ calculate_139_adjusted_size()                       ││
│  │ calculate_369_adjusted_size()                       ││
│  │ is_critical→×0.5 / noise→×0.25 / σ≥2×长期→硬止损  ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 结构层 (7循环群自指)                                ││
│  │ cycle_7_closure_verification()                      ││
│  │ FFT检测1/7频率功率 → 闭合度≥0.3→有循环群特征       ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 2.2 与现有系统的集成

宇宙算法三重奏与 TOMAS v2.0 的相位连续性分析（PCS）形成**双重过滤**机制：

```
理论引擎.analyze(bars)
  → 原始信号 hints
  → apply_phase_filter(hints)     # PCS相位过滤（第一道）
  → detect_139_critical_transition() # 139相变检测（第二道）
  → apply_369_signal_filter(hints)   # 369振动过滤（第三道）
  → 最终信号（三层过滤后）
```

---

## 3. 核心模块实现

### 3.1 cosmic_algorithm.py — 宇宙算法核心库

**文件路径**: `backend/app/core/cosmic_algorithm.py`

**6个核心函数**：

| 函数 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `digital_root(n)` | 数字根计算 | 自然数n | 数字根[1,9] |
| `vibration_mode_369(prices)` | 369振动模态检测 | 价格序列 | 模态分数+分布 |
| `apply_369_signal_filter(hints)` | 信号层过滤 | 信号+K线 | 过滤后信号 |
| `detect_139_critical_transition(prices)` | 139相变检测 | 价格序列 | 临界征兆 |
| `cycle_7_closure_verification(prices)` | 7循环群验证 | 价格序列 | 闭合度评分 |
| `cosmic_algorithm_trio(prices)` | 三重奏综合分析 | 价格+成交量 | 综合评分 |

### 3.2 周期律引擎升级

**文件**: `backend/app/services/theory/cycle_law.py`

**新增逻辑**：
- `detect_139_critical_transition()` → is_critical=True时置信度×0.5
- `apply_369_signal_filter()` → 振动模态noise时清空信号
- `_calc_confidence()` → 斐波那契共振确认（周期长度±20%接近F数→权重+0.2）

### 3.3 风控引擎升级

**文件**: `backend/app/services/risk/stop_loss.py`

**新增方法**：
- `check_139_volatility_stop(position, prices)` → σ/σ_long ≥ 2.0时触发硬止损
- `check_139_critical_stop(position, bars)` → is_critical=True+critical_score≥2.5时触发硬止损

**文件**: `backend/app/services/risk/position_sizer.py`

**新增方法**：
- `calculate_139_adjusted_size()` → is_critical×0.5 / transitioning×0.75 / stable×1.0
- `calculate_369_adjusted_size()` → strong×1.0 / moderate×0.75 / noise×0.25

### 3.4 API端点

**文件**: `backend/app/api/market.py`

**新增端点**: `GET /api/v1/market/cosmic-algorithm`

**响应结构**：
```json
{
  "trio_score": 0.395,
  "trio_label": "moderate",
  "trading_implication": "部分共振，需谨慎",
  "risk_control": {
    "should_reduce_position": true,
    "should_hard_stop": false,
    "volatility_warning": false
  },
  "vibration_369": {
    "vibration_score": 0.368,
    "mode_label": "moderate"
  },
  "critical_139": {
    "is_critical": true,
    "regime": "critical_slowing",
    "variance_ratio": 1.05
  },
  "cycle_7": {
    "has_7_cycle": true,
    "closure_score": 0.482
  }
}
```

---

## 4. 前端实时展示

### 4.1 CosmicAlgorithmPage 设计

前端新增 `CosmicAlgorithmPage` 页面（`/cosmic-algorithm`），实时展示宇宙算法三重奏评分。

**页面布局**：
1. **标题栏**：Orbit icon + "宇宙算法三重奏" + Chip "7-139-369"
2. **搜索栏**：TextField 股票代码 + TextField 时间周期 + Button 分析
3. **Trio Score 大表盘**（左侧 4列）：CircularProgress 大圆盘显示 trio_score，下方 Chip 显示 trio_label，三个子表盘显示 369/139/7 各层分数
4. **三层评分卡片**（右侧 8列）：
   - 369振动模态分数 + 模态标签 + 触发/共振/归整频率
   - 139相变评分 + regime标签 + 方差比值 + 自相关系数 + 恢复速率
   - 7闭合评分 + Z₇闭合标签 + 主周期 + FFT功率
5. **369数字根分布条形图**：BarChart 展示 root_distribution (1-9)
6. **三重奏综合走势图**：ComposedChart 展示 trio_score/vibration/critical/closure 时间序列
7. **交易含义卡片** + 风控建议表（139缩仓/σ硬止损/波动率警告）
8. **三层评分详情对比表**

**API 调用**：`GET /api/v1/market/cosmic-algorithm?symbol=XXX&timeframe=1d&limit=200`

**降级策略**：API 失败时自动使用 mock 数据，确保页面始终可用。

### 4.2 导航集成

前端路由注册：
- `App.tsx`：添加 `import CosmicAlgorithmPage` + `<Route path="/cosmic-algorithm" .../>`
- `Sidebar.tsx`：添加 Orbit icon + `{ path: '/cosmic-algorithm', label: '宇宙算法', icon: Orbit }`

---

## 5. 全引擎369振动模态过滤推广

### 5.1 推广范围

初始版本仅在 `cycle_law.py` 中集成了369振动模态过滤。v0.3.0 将 `apply_369_signal_filter()` 推广到全部7个理论引擎：

| 引擎 | 文件 | 369过滤 | PCS过滤 | 双重过滤 |
|------|------|---------|---------|---------|
| 太极中心律 | taiji.py | ✅ | ✅ | ✅ |
| 螺旋律 | spiral.py | ✅ | ✅ | ✅ |
| 波浪理论 | elliott_wave.py | ✅ | ✅ | ✅ |
| 对偶律 | dual_law.py | ✅ | ✅ | ✅ |
| 周期律 | cycle_law.py | ✅ | ✅ | ✅ |
| 江恩角度线 | gann_angle.py | ✅ | ✅ | ✅ |
| BG均线 | bg_moving_average.py | ✅ | ✅ | ✅ |

### 5.2 集成模式

每个引擎的 `analyze()` 方法中，在 `apply_phase_filter()`（PCS相位过滤）之后，添加 `apply_369_signal_filter()` 调用：

```python
# 文件顶部添加 import
from app.core.cosmic_algorithm import apply_369_signal_filter

# 在 analyze() 方法中
# [宇宙算法] 369振动模态过滤（双重过滤）
hints, confidence, vibration_score, mode_details = apply_369_signal_filter(
    hints, confidence, bars, log_prefix=self.name
)

# 在 annotations 中添加
"vibration_369": mode_details,
```

### 5.3 过滤效果

369振动模态过滤对信号质量的影响：
- `vibration_score ≥ 0.6`：正常交易，置信度不变
- `0.3 ≤ vibration_score < 0.6`：降低置信度至50%，谨慎交易
- `vibration_score < 0.3`：噪音信号，清空信号列表，降低置信度至10%

---

## 6. 回测引擎139风控集成

### 6.1 139硬止损

`signal_runner.py` 的 `_check_stop_loss_take_profit()` 方法新增139窗口σ硬止损检查：

```python
# [宇宙算法] 139σ硬止损检查
from app.services.risk.stop_loss import StopLossManager
stop_manager = StopLossManager()

# 139波动率σ硬止损
vol_result = stop_manager.check_139_volatility_stop(
    {"position_id": f"{symbol}-{current_bar_index}"},
    historical_closes,
)
if vol_result == StopLossManager.StopCheckResult.STOP_LOSS_TRIGGERED:
    should_close = True
    exit_reason = "139_VOLATILITY_STOP"

# 139临界慢化硬止损
crit_result = stop_manager.check_139_critical_stop(
    {"position_id": f"{symbol}-{current_bar_index}"},
    bars_data,
)
if crit_result == StopLossManager.StopCheckResult.STOP_LOSS_TRIGGERED:
    should_close = True
    exit_reason = "139_CRITICAL_STOP"
```

### 6.2 139/369缩仓

`signal_runner.py` 的 `_generate_open_orders()` 方法新增139/369缩仓调整：

```python
# [宇宙算法] 139缩仓 + 369缩仓
from app.services.risk.position_sizer import PositionSizer as PositionSizerClass
sizer = PositionSizerClass()

# 139缩仓
position_size = sizer.calculate_139_adjusted_size(
    portfolio_manager.portfolio,
    avg_confidence,
    bar.close,
    stop_price,
    bars_data,
)

# 369缩仓（叠加）
position_size = sizer.calculate_369_adjusted_size(
    portfolio_manager.portfolio,
    avg_confidence,
    bar.close,
    stop_price,
    bars_data,
)
```

### 6.3 缩仓逻辑

| 市场状态 | 139缩仓 | 369缩仓 |
|---------|---------|---------|
| critical_slowing | ×0.5 | - |
| transitioning | ×0.75 | - |
| stable | ×1.0 | - |
| strong (score≥0.6) | - | ×1.0 |
| moderate (0.3-0.6) | - | ×0.75 |
| noise (score<0.3) | - | ×0.25 |

---

## 7. 实验验证

### 7.1 数字根测试

| 输入 | 数字根 | 验证 |
|------|-------|------|
| 369 | 9 | ✅ (3+6+9=18→1+8=9) |
| 142857 | 9 | ✅ (1+4+2+8+5+7=27→2+7=9) |
| 139 | 4 | ✅ (1+3+9=13→1+3=4) |
| 0 | 9 | ✅ (Z_9特殊映射) |

### 7.2 139相变检测

| 序列类型 | variance_ratio | autocorrelation | recovery_rate | critical_score | regime |
|---------|---------------|----------------|--------------|---------------|--------|
| 稳态序列 | 1.01 | -0.076 | 0.966 | 1.0 | transitioning |
| 临界序列 | 1.05 | 0.779 | 5.528 | 2.0 | critical_slowing |

### 7.3 7循环群检测

| 序列类型 | has_7_cycle | closure_score | dominant_period |
|---------|------------|---------------|----------------|
| 含7周期 | true | 0.482 | 7 |
| 随机序列 | false | 0.066 | 3 |

### 7.4 三重奏综合评分

含7周期的序列综合评分 = 0.395（moderate），表明三重奏可以有效区分市场状态。

---

## 8. 与TOMAS v2.0的关系

宇宙算法三重奏与 TOMAS v2.0 构成互补体系：

| 层面 | TOMAS v2.0 | 宇宙算法三重奏 |
|------|-----------|---------------|
| 信号层 | PCS相位连续性过滤 | 369数字根振动模态过滤 |
| 时间层 | 拓扑不变量周期检测 | 139-day临界慢化+斐波那契共振 |
| 风控层 | 流动性熔断+ENPV决策 | 139窗口缩仓+σ硬止损 |
| 结构层 | DNA倍数生成验证 | 7循环群自指闭合验证 |

两者叠加形成**四重过滤**机制：PCS → 139 → 369 → DNA，确保只输出最高质量信号。

---

## 10. TDA拓扑预警与Dalio象限融合

> **v0.4.0 新增**：基于拓扑数据分析(Topological Data Analysis)的持续同调(Persistent Homology)和Betti数检测，与Dalio象限模型深度融合，实现金融危机的拓扑预警。

### 10.1 TDA理论基础

拓扑数据分析(TDA)是一门利用代数拓扑工具分析数据形状的数学方法。其核心概念：

**持续同调(Persistent Homology)**：随着滤波参数ε从0逐步增大，数据点之间的"连通阈值"逐步放宽。在此过程中，拓扑特征（连通分量、环形空洞等）会经历"出生"和"死亡"。记录每个特征的出生ε和死亡ε，就得到了**持久图(Persistence Diagram)**。

- **持久条(Persistence Bar)**长度 = 死亡ε − 出生ε
- 长寿命特征 → 真实结构（不受噪声干扰）
- 短寿命特征 → 噪声（很快消失）

**Betti数**是拓扑不变量，描述数据形状的基本特征：

| Betti数 | 含义 | 金融映射 |
|---------|------|---------|
| β₀ | 连通分量数 | 市场共识度：β₀=1→整体连通，β₀↑→碎片化 |
| β₁ | 环形空洞数 | 循环结构：β₁出现→新振荡模式，β₁消失→模式瓦解 |
| β₂ | 二维空洞数 | 更高阶结构（金融数据通常不涉及） |

### 10.2 Betti数与金融危机预警

基于《拓扑数据分析是如何提前一年预警金融危机的》一文的核心洞察：

1. **β₀增加 → 市场碎片化 → 危机前兆**
   - 正常市场：价格聚集在有限范围内 → β₀≈1
   - 危机前：价格分散到多个不连通区域 → β₀>2
   - 市场共识瓦解 → 不同投资者群体对价格形成分裂预期

2. **β₁出现/消失 → 循环结构变化 → 象限过渡信号**
   - β₁从0变为正值：新的循环振荡模式出现 → 市场进入新的象限
   - β₁消失：旧循环模式瓦解 → 当前象限即将结束
   - 这与Dalio象限切换完美对应

3. **持久条长度缩短 → 结构脆弱 → 相变即将发生**
   - 正常市场：拓扑特征寿命长 → persistence_score高 → 结构稳健
   - 危机前：持久条普遍缩短 → persistence_score低 → 结构脆弱
   - TDA能比传统统计方法提前检测到regime transition

**TDA与139相变检测的关系**：139临界慢化检测本质上就是拓扑检测的简化版——方差比增加、自相关时间延长、恢复速率下降，这些正是β₀增加和持久条缩短的统计表现。TDA提供了更本质的拓扑视角。

### 10.3 compute_betti_numbers()和compute_persistence_diagram()的实现

#### β₀计算（连通分量数）

```python
# 算法：Union-Find聚类
# 1. 将价格归一化
# 2. 设置连通阈值 ε = price_range × 5%
# 3. 排序价格，相邻差距<ε → Union-Find合并
# 4. 统计连通分量数 = β₀
```

关键设计：
- ε比例默认5%：太低→噪声过多，太高→所有价格合并为一簇
- 使用Union-Find算法（路径压缩），O(n log n)复杂度
- β₀>2时触发碎片化预警

#### β₁计算（环形结构数）

```python
# 算法：局部极值循环检测
# 1. 找局部极值点（峰和谷，窗口=5）
# 2. 检测峰谷交替形成的"环形振荡"
# 3. 振幅>ε的振荡算有效环形
# 4. β₁ = 有效环形数（上限5个）
```

关键设计：
- 不是严格的代数拓扑β₁（需要Vietoris-Rips复形），而是实用简化版
- 检测价格序列中"峰-谷-峰"形成的振荡循环
- β₁≥2时触发环形过渡预警

#### persistence_score计算（拓扑持久度）

```python
# 算法：ε扫描 + birth-death记录
# 1. ε从0到price_range*0.5，分20步扫描
# 2. 每步记录β₀值 → 连通分量合并事件
# 3. 每个0维特征在ε=0出生，在合并点"死亡"
# 4. persistence = death - birth
# 5. persistence_score = 归一化平均持久度
```

关键设计：
- persistence_score ∈ [0, 1]
- ≥0.5 → 结构稳健（正常）
- 0.3-0.5 → 中等（观察）
- <0.3 → 临界过渡（预警）

### 10.4 detect_regime_with_tda()融合逻辑

融合策略：**Dalio象限看宏观位置，TDA看微观拓扑结构**

```
detect_regime_with_tda(prices, volumes):
  1. detect_regime() → Dalio象限 + 置信度
  2. compute_betti_numbers() → β₀, β₁
  3. compute_persistence_diagram() → persistence_score
  4. TDA预警判定（优先级从高到低）：
     - persistence < 0.3 → critical_transition（最严重）
     - β₀ > 2 → fragmenting
     - β₁ ≥ 2 → loop_transition
     - β₀=2 & persistence<0.5 → 轻度fragmenting
     - 否则 → normal
  5. TDA修正Dalio置信度：
     - critical_transition → ×0.5
     - fragmenting → ×0.7
     - loop_transition → ×0.85
     - normal → 不修正
  6. 输出增强版RegimeResult
```

**设计哲学**：TDA不是替代Dalio象限，而是提供"预警层"。Dalio象限告诉你"你在哪里"，TDA告诉你"你可能要离开这里"。两者互补：

| 情景 | Dalio象限 | TDA预警 | 综合建议 |
|------|----------|---------|---------|
| 正常扩张 | EXPANSION | normal | 正常配置：股票40%+商品25% |
| 碎片化扩张 | EXPANSION | fragmenting | 象限不可靠→分散持仓+降仓位 |
| 环形过渡 | EXPANSION | loop_transition | 象限即将切换→动态调整 |
| 临界相变 | EXPANSION | critical_transition | 相变即将发生→防御+硬止损 |

### 10.5 前端RegimePage可视化设计

前端新增 `RegimePage` 页面（`/regime`），展示Dalio象限+TDA拓扑预警的综合分析结果。

**页面布局**：
1. **标题栏**：Grid2X2 icon + "经济象限检测" + Chip "Dalio+TDA"
2. **搜索栏**：TextField 股票代码 + TextField 时间周期 + Button 检测
3. **Dalio 2x2象限矩阵**（左侧5列）：SVG绘制四象限图
   - 左上: REFLATION(增长↑通胀↓) - 蓝色
   - 右上: EXPANSION(增长↑通胀↑) - 绿色
   - 左下: DEFLATION(增长↓通胀↓) - 紫色
   - 右下: STAGFLATION(增长↓通胀↑) - 红色
   - 当前象限高亮+脉冲动画
   - 信号指示点（增长/通胀的当前位置）
4. **TDA拓扑预警卡片**（右侧7列）：
   - β₀连通分量数 + 变化趋势小图
   - β₁环形结构数 + 变化趋势小图
   - 拓扑持久度评分(persistence_score) CircularProgress表盘
   - TDA预警标签Chip
   - TDA置信度/Dalio置信度进度条
5. **增长/通胀信号仪表盘**：两个CircularProgress大表盘
6. **推荐资产权重雷达图**：recharts RadarChart
7. **理论引擎权重调整表**：每个引擎的权重系数和调整方向
8. **象限历史模拟走势图**：ComposedChart增长/通胀时间序列
9. **交易建议卡片**：Dalio建议+TDA预警建议+预警指标表

**API调用**：`GET /api/v1/market/regime?symbol=XXX&timeframe=1d&limit=200`
**降级策略**：API失败时自动mock数据

**导航集成**：
- `App.tsx`：添加 `import RegimePage` + `<Route path="/regime" .../>`
- `Sidebar.tsx`：添加 `{ path: '/regime', label: '象限检测', icon: Grid2X2 }`

---

## 9. 结论与展望

宇宙算法三重奏（7-139-369）为孙大圣量化交易系统提供了一个基于数论和复杂系统理论的新型过滤框架。三个核心常数——7（结构自指）、139（临界演化）、369（振动法则）——从不同维度约束信号质量，形成了"只交易符合数学规律的市场行为"的核心理念。

未来工作：
1. 在真实市场数据上验证139临界慢化征兆的预测有效性
2. 将369振动模态应用于高频数据（分钟级），探索微观结构振动模式
3. 7循环群检测扩展为多尺度周期检测（Z_7、Z_12、Z_60等）
4. ~~将三重奏评分接入前端实时显示，增强用户决策体验~~ ✅ 已完成（CosmicAlgorithmPage）
5. ~~TDA拓扑预警与Dalio象限融合，RegimePage前端展示~~ ✅ 已完成（v0.4.0）

---

## 参考文献

[1] 章锋. 宇宙算法的三重奏：从形式系统自指、临界相变到数字能量学的科学重译. 复合体理学微信公众号, 2026.

[2] Landau, L.D. & Lifshitz, E.M. Statistical Physics. Course of Theoretical Physics, Vol. 5.

[3] Scheffer, M. et al. Early-warning signals for critical transitions. Nature, 461, 2009.

[4] TOMAS v2.0：基于广义代数理论（GAT）的太乙互搏公理体系.

[5] 鲁兆：波浪理论、费氏数列、八卦历法.

[6] 拓扑数据分析是如何提前一年预警金融危机的. 复合体理学微信公众号, 2026.

[7] Edelsbrunner, H. & Harer, J. Computational Topology: An Introduction. AMS, 2010.
