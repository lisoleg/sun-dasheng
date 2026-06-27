# 孙大圣量化交易系统 — API 文档

> 版本：v0.2.1 | 更新：2026-06-23 | 状态：TOMAS v2.0

Base URL：`http://localhost:8000/api/v1`（开发环境）

---

## 目录

1. [通用规范](#1-通用规范)
2. [行情 API](#2-行情-api)
3. [信号 API](#3-信号-api)
4. [订单 API](#4-订单-api)
5. [风控 API](#5-风控-api)
6. [策略 API](#6-策略-api)
7. [回测 API](#7-回测-api)
8. [用户偏好 API](#8-用户偏好-api)
9. [TOMAS v2.0 API](#9-tomas-v20-api) 🆕
10. [WebSocket API](#10-websocket-api)
11. [错误码表](#11-错误码表)

---

## 1. 通用规范

### 请求格式

- 所有请求使用 `JSON` 格式
- `GET` 请求参数通过 Query String 传递
- `POST/PUT` 请求体使用 `application/json`
- 时间字段使用 **ISO 8601 UTC** 格式（如 `2026-06-17T08:30:00Z`）

### 响应格式

```json
{
  "code": 0,
  "data": { ... },
  "message": "ok"
}
```

| code | 含义 |
|------|------|
| 0 | 成功 |
| 404 | 资源不存在 |
| 1001-1999 | 业务错误（策略/理论） |
| 2001-2999 | 行情错误 |
| 3001-3999 | 信号错误 |
| 4001-4999 | 订单错误 |
| 5001-5999 | 风控错误 |
| 6001-6999 | 回测错误 |

### 认证

当前版本 **无需认证**（内网部署）。生产环境建议添加 JWT 或 API Key 认证。

---

## 2. 行情 API

Base Path：`/api/v1/market`

### 2.1 获取 K 线数据

```
GET /api/market/bars
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | ❌ | `BTCUSDT` | 标的代码（如 `BTCUSDT`, `000001.SZ`） |
| timeframe | string | ❌ | `1m` | 时间周期（`1m/5m/15m/1h/4h/1d/1w`） |
| limit | int | ❌ | `100` | 返回条数（1-1000） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "total": 100,
    "items": [
      {
        "id": "bar-000000",
        "symbol": "BTCUSDT",
        "market": "crypto",
        "timeframe": "1d",
        "timestamp": "2026-06-10T00:00:00Z",
        "open": 67500.50,
        "high": 69200.00,
        "low": 66800.00,
        "close": 68800.00,
        "volume": 12345.6789
      }
    ]
  },
  "message": "ok"
}
```

**错误码：**

| code | 说明 |
|------|------|
| 2001 | 行情数据获取失败（数据源连接错误） |

---

### 2.2 获取可用标的列表

```
GET /api/market/symbols
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| market | string | ❌ | `null` | 市场过滤（`crypto` / `a_share`） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "total": 6,
    "items": [
      {"symbol": "BTCUSDT", "market": "crypto", "name": "比特币/USDT", "status": "active"},
      {"symbol": "000001.SZ", "market": "a_share", "name": "平安银行", "status": "active"}
    ]
  },
  "message": "ok"
}
```

---

### 2.3 相位连续性分析（TOMAS v2.0 新增）

```
GET /api/v1/market/phase-analysis
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 否 | `BTCUSDT` | 标的代码 |
| timeframe | string | 否 | `1d` | 时间周期 |
| limit | int | 否 | `100` | K线数量（30-1000） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "1d",
    "pcs": 0.8234,
    "regime": "phase_continuous",
    "action": "normal",
    "taiji_idx": 45,
    "singularity": false,
    "lob_depth": 0.7821
  },
  "message": "ok"
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| pcs | float | 相位连续性评分 [0, 1] |
| regime | string | 市场状态：`phase_continuous` / `transition` / `phase_singularity` |
| action | string | 建议操作：`normal` / `caution` / `circuit_break` |
| taiji_idx | int | 太极中心索引（当前窗口内最具结构意义的K线位置） |
| singularity | bool | 是否处于相位奇点 |
| lob_depth | float | LOB 深度熵（归一化） |

---

### 2.4 DNA 倍发生成验证（TOMAS v2.0 新增）

```
GET /api/v1/market/dna-detection
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 否 | `BTCUSDT` | 标的代码 |
| timeframe | string | 否 | `1d` | 时间周期 |
| limit | int | 否 | `200` | K线数量（50-1000，需足够多为DNA检测） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "1d",
    "dna": {
      "first_wave_duration": 13,
      "first_wave_amplitude": 15.23,
      "direction": "up",
      "start_idx": 10,
      "end_idx": 23
    },
    "wave_count": 7,
    "ksnap_verify": {
      "kappa": 0.72,
      "is_extrapolatable": true,
      "confidence": 0.68,
      "predicted_next_duration": 21,
      "predicted_next_amplitude": 24.6
    }
  },
  "message": "ok"
}
```

**错误码：**

| code | 说明 |
|------|------|
| 2003 | 波浪不足（需要≥3浪） |
| 2004 | DNA基因提取失败 |
| 2005 | DNA检测失败（内部错误） |

### 2.5 宇宙算法三重奏（7-139-369）

```
GET /api/v1/market/cosmic-algorithm
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 否 | `BTCUSDT` | 标的代码 |
| timeframe | string | 否 | `1d` | 时间周期 |
| limit | int | 否 | `200` | K线数量（50-1000） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "1d",
    "trio_score": 0.395,
    "trio_label": "moderate",
    "trading_implication": "部分共振，需谨慎，建议降低仓位或等待确认",
    "risk_control": {
      "should_reduce_position": true,
      "should_hard_stop": false,
      "volatility_warning": false
    },
    "vibration_369": {
      "vibration_score": 0.368,
      "trigger_freq": 0.158,
      "resonance_freq": 0.053,
      "closure_freq": 0.158,
      "mode_label": "moderate"
    },
    "critical_139": {
      "is_critical": true,
      "variance_ratio": 1.05,
      "autocorrelation": 0.779,
      "recovery_rate": 5.528,
      "critical_score": 2.0,
      "regime": "critical_slowing"
    },
    "cycle_7": {
      "has_7_cycle": true,
      "closure_score": 0.482,
      "dominant_period": 7,
      "fft_power_at_7": 0.0062
    }
  },
  "message": "ok"
}
```

**字段含义：**

| 字段 | 说明 |
|------|------|
| trio_score | 三重奏综合评分 [0,1]，≥0.6=强 / 0.3-0.6=中等 / <0.3=弱 |
| vibration_369.vibration_score | 369振动模态分数：触发(3)+共振(6)+归整(9)/总频率 |
| critical_139.is_critical | 是否进入139临界慢化（≥2个征兆） |
| critical_139.regime | 市场状态：stable/transitioning/critical_slowing |
| cycle_7.has_7_cycle | 是否检测到7-day循环群特征（闭合度≥0.3） |

**错误码：**

| code | 说明 |
|------|------|
| 2001 | 数据不足（需要≥50根K线） |
| 2006 | 三重奏分析失败（内部错误） |

---

## 3. 信号 API

Base Path：`/api/v1/signals`

### 3.1 获取信号列表（分页）

```
GET /api/signals
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | ❌ | `null` | 过滤标的代码 |
| direction | string | ❌ | `null` | 过滤方向（`LONG` / `SHORT` / `HOLD`） |
| source_engine | string | ❌ | `null` | 过滤来源引擎（如 `taiji`, `spiral`） |
| min_confidence | float | ❌ | `0.0` | 最小置信度（0.0-1.0） |
| page | int | ❌ | `1` | 页码（≥1） |
| page_size | int | ❌ | `20` | 每页条数（1-100） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "total": 156,
    "items": [
      {
        "signal_id": "sig-20260617-001",
        "symbol": "BTCUSDT",
        "market": "crypto",
        "direction": "LONG",
        "price": 68800.00,
        "confidence": 0.7823,
        "source_engine": "taiji",
        "theory_name": "太极中心律",
        "timestamp": "2026-06-17T08:30:00Z",
        "created_at": "2026-06-17T08:30:05Z",
        "metadata": {"dna_window": 29, "center_price": 67500.00}
      }
    ]
  },
  "message": "ok"
}
```

---

### 3.2 获取最新信号

```
GET /api/signals/latest?limit=10
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | int | ❌ | `10` | 返回条数（1-50） |

---

### 3.3 手动触发信号计算

```
POST /api/signals/generate?symbol=BTCUSDT&timeframe=1d&limit=200
```

**说明：** 调用 `SignalGenerator` 实时计算信号并存入数据库，同时通过 WebSocket 推送。

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | ✅ | 标的代码 |
| timeframe | string | ❌ | 时间周期（默认 `1d`） |
| limit | int | ❌ | K 线条数（默认 `200`，范围 50-1000） |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "generated": 3,
    "signals": [...]
  },
  "message": "成功生成 3 条信号"
}
```

**错误码：**

| code | 说明 |
|------|------|
| 3001 | 信号生成失败（理论引擎错误 / 数据获取错误） |

---

## 4. 订单 API

Base Path：`/api/v1/orders`

### 4.1 创建订单（手动下单）

```
POST /api/orders
```

**请求体：**

```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "type": "MARKET",
  "price": 0.0,
  "quantity": 0.01
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | ✅ | 标的代码 |
| side | string | ✅ | `BUY` 或 `SELL` |
| type | string | ✅ | `MARKET` / `LIMIT` / `STOP` |
| price | float | ❌ | 限价单价格（市价单可不填） |
| quantity | float | ✅ | 数量 |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "order_id": "binance-1234567890",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "price": 68800.00,
    "quantity": 0.01,
    "status": "FILLED",
    "filled_price": 68850.00,
    "filled_quantity": 0.01,
    "commission": 0.52,
    "created_at": "2026-06-17T08:30:00Z",
    "updated_at": "2026-06-17T08:30:01Z",
    "error": null
  },
  "message": "ok"
}
```

> ⚠️ 未配置 `BINANCE_API_KEY` 时返回模拟订单（status: `PENDING`，message 含 `mock` 提示）

---

### 4.2 获取订单列表（分页）

```
GET /api/orders
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | ❌ | `null` | 过滤标的 |
| status | string | ❌ | `null` | 过滤状态（`PENDING` / `FILLED` / `CANCELLED` / `REJECTED`） |
| page | int | ❌ | `1` | 页码 |
| page_size | int | ❌ | `20` | 每页条数 |

---

### 4.3 获取订单详情

```
GET /api/orders/{order_id}
```

---

### 4.4 取消订单

```
DELETE /api/orders/{order_id}
```

**说明：** 仅 `PENDING` 或 `PARTIALLY_FILLED` 状态的订单可取消。

---

## 5. 风控 API

Base Path：`/api/v1/risk`

### 5.1 获取风控配置

```
GET /api/risk/config
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "id": "risk-config-default",
    "name": "default",
    "symbol": "*",
    "market": "*",
    "max_position_pct": 0.1,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10,
    "max_drawdown_pct": 0.20,
    "trailing_stop_enabled": true,
    "trailing_stop_pct": 0.03,
    "is_active": true
  },
  "message": "ok"
}
```

---

### 5.2 更新风控配置

```
PUT /api/risk/config
```

**请求体：**（仅需传要更新的字段）

```json
{
  "stop_loss_pct": 0.03,
  "max_position_pct": 0.15
}
```

---

### 5.3 获取风控告警列表

```
GET /api/risk/alerts
```

**Query 参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| severity | string | ❌ | `null` | 过滤严重级别（`INFO` / `WARNING` / `CRITICAL`） |
| page | int | ❌ | `1` | 页码 |
| page_size | int | ❌ | `20` | 每页条数 |

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "total": 8,
    "items": [
      {
        "id": "alert-000001",
        "alert_type": "STOP_LOSS",
        "symbol": "BTCUSDT",
        "message": "BTCUSDT 止损触发，当前价格已低于止损线",
        "severity": "CRITICAL",
        "timestamp": "2026-06-17T08:30:00Z",
        "details": {"current_price": 65000.00, "threshold": 66000.00}
      }
    ]
  },
  "message": "ok"
}
```

> ⚠️ 当前为 Mock 实现，生产环境需连接真实风控引擎

---

## 6. 策略 API

Base Path：`/api/v1/strategy`

### 6.1 获取理论引擎列表

```
GET /api/strategy/engines
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "total": 4,
    "items": [
      {
        "name": "taiji",
        "display_name": "太极中心律",
        "description": "基于鲁兆太极中心律理论，通过DNA29/DNA13时间窗口计算太极中心点",
        "enabled": true,
        "theory_name": "太极中心律",
        "params": {"dna29_window": 29, "dna13_window": 13, "min_confidence": 0.5}
      }
    ]
  },
  "message": "ok"
}
```

---

### 6.2 启用/禁用理论引擎

```
PUT /api/strategy/engines/{name}/toggle
```

**路径参数：**

| 参数 | 类型 | 说明 |
|--------|------|------|
| name | string | 引擎名称（`taiji` / `spiral` / `elliott` / `tomas` / `dual` / `cycle` / `gann` / `bg_ma`） |

---

### 6.3 触发 EML 知识蒸馏

```
POST /api/strategy/eml/distill
```

**请求体：**

```json
{
  "theory_texts": [
    "太极中心律的核心在于...",
    "螺旋律使用斐波那契数列..."
  ],
  "overwrite": false
}
```

> ⚠️ 当前为 Mock 实现

---

## 7. 回测 API 🆕（Phase 2 新增）

Base Path：`/api/v1/backtest`

### 7.1 启动回测

```
POST /api/backtest/run
```

**请求体：**

```json
{
  "config": {
    "symbol": "BTCUSDT",
    "market_type": "crypto",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "timeframe": "1d",
    "initial_cash": 100000.0,
    "commission_rate": 0.001,
    "slippage_bps": 5.0,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10,
    "max_position_pct": 0.10,
    "theory_weights": {
      "taiji": 0.25,
      "spiral": 0.20,
      "elliott": 0.20,
      "tomas": 0.35
    },
    "fusion_strategy": "weighted",
    "position_sizing": "fixed_pct"
  }
}
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "backtest_id": "a1b2c3d4-5e6f-7890-abcd-ef1234567890",
    "status": "pending"
  },
  "message": "回测任务已创建"
}
```

> 📌 回测为**异步执行**，需通过 `/progress` 接口或 WebSocket 查询进度

---

### 7.2 获取回测结果

```
GET /api/backtest/{backtest_id}
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "backtest_id": "a1b2c3d4-...",
    "status": "completed",
    "progress": 100.0,
    "current_stage": "finished",
    "started_at": "2026-06-17T08:00:00Z",
    "finished_at": "2026-06-17T08:00:25Z",
    "duration_seconds": 25.3,
    "error_message": null,
    "result_summary": {
      "total_return": 0.25,
      "annualized_return": 0.12,
      "sharpe_ratio": 1.5,
      "max_drawdown": -0.08,
      "win_rate": 0.58,
      "total_trades": 42
    },
    "report_path": "/static/reports/backtest_a1b2c3d4.pdf",
    "csv_path": "/static/csv/backtest_a1b2c3d4_trades.csv"
  },
  "message": "ok"
}
```

**status 枚举：**

| 值 | 说明 |
|-----|------|
| `pending` | 等待中 |
| `running` | 运行中 |
| `completed` | 已完成 |
| `failed` | 失败 |

---

### 7.3 获取回测进度

```
GET /api/backtest/{backtest_id}/progress
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "backtest_id": "a1b2c3d4-...",
    "status": "running",
    "progress": 45.0,
    "current_stage": "computing_signals"
  },
  "message": "ok"
}
```

**current_stage 枚举：**

| 值 | 说明 |
|-----|------|
| `initializing` | 初始化 |
| `loading_bars` | 加载历史数据 |
| `computing_signals` | 计算信号 |
| `executing_orders` | 执行订单 |
| `calculating_metrics` | 计算绩效指标 |
| `saving_results` | 保存结果 |
| `finished` | 完成 |

---

### 7.4 获取回测历史列表

```
GET /api/backtest/history?page=1&page_size=20
```

---

### 7.5 删除回测任务

```
DELETE /api/backtest/{backtest_id}
```

---

### 7.6 启动参数扫描 🆕

```
POST /api/backtest/scan
```

**请求体：**

```json
{
  "base_config": {
    "symbol": "BTCUSDT",
    "market_type": "crypto",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    ...
  },
  "grid": {
    "stop_loss_pct": [0.03, 0.05, 0.08],
    "take_profit_pct": [0.05, 0.10, 0.15],
    "theory_weights.taiji": [0.20, 0.25, 0.30]
  },
  "optimization_target": "sharpe_ratio"
}
```

---

### 7.7 获取参数扫描结果

```
GET /api/backtest/scan/{scan_id}
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "scan_id": "scan-001",
    "status": "completed",
    "total_jobs": 27,
    "completed_jobs": 27,
    "progress": 100.0,
    "best_params": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10},
    "best_metrics": {"sharpe_ratio": 1.85, "total_return": 0.32},
    "results": {"items": [...]}
  },
  "message": "ok"
}
```

---

## 8. 用户偏好 API 🆕（Phase 2 新增）

Base Path：`/api/v1/preferences`

### 8.1 获取用户偏好

```
GET /api/preferences/{user_id}
```

**说明：** 用户不存在时返回默认偏好（不报错）

---

### 8.2 更新用户偏好

```
PUT /api/preferences/{user_id}
```

**请求体：**

```json
{
  "theme_mode": "dark",
  "layout_template": "default",
  "dashboard_panels": [
    {"i": "market-overview", "x": 0, "y": 0, "w": 6, "h": 4}
  ],
  "notification_settings": {
    "browser_enabled": true,
    "sound_enabled": false,
    "alert_level": "warning"
  }
}
```

---

### 8.3 删除用户偏好（恢复默认）

```
DELETE /api/preferences/{user_id}
```

---

### 8.4 导出偏好设置

```
GET /api/preferences/{user_id}/export
```

**说明：** 用于跨设备同步，返回完整偏好 JSON

---

### 8.5 导入偏好设置

```
POST /api/preferences/{user_id}/import
```

**请求体：** 完整的偏好 JSON（同导出格式）

---

## 9. WebSocket API

Base URL：`ws://localhost:8000/ws`

### 9.1 连接鉴权

当前版本 **无需鉴权**。连接后需先发送订阅消息。

---

### 9.2 频道列表

| 频道路径 | 说明 |
|-----------|------|
| `/ws/market` | 行情实时推送 |
| `/ws/signals` | 信号实时推送 |
| `/ws/backtest` | 回测进度推送 |
| `/ws/orders` | 订单状态推送 |
| `/ws/risk` | 风控告警推送 |

---

### 9.3 消息格式

**客户端 → 服务端：**

```json
{
  "action": "subscribe",
  "channel": "signals",
  "task_id": "bt-xxx"   // backtest 频道需指定任务 ID
}
```

**服务端 → 客户端：**

```json
{
  "type": "signals_generated",
  "channel": "signals",
  "payload": {
    "symbol": "BTCUSDT",
    "count": 3,
    "signals": [...]
  },
  "timestamp": "2026-06-17T08:30:00Z"
}
```

---

### 9.4 心跳机制

客户端每 **30 秒**发送：

```json
{"type": "ping"}
```

服务端响应：

```json
{"type": "pong"}
```

---

### 9.5 回测进度推送格式（示例）

```json
{
  "type": "backtest_progress",
  "channel": "backtest",
  "payload": {
    "backtest_id": "a1b2c3d4-...",
    "status": "running",
    "progress": 45.0,
    "stage": "computing_signals",
    "current_bar": 820,
    "total_bars": 1825
  },
  "timestamp": "2026-06-17T08:05:00Z"
}
```

---

## 10. 错误码表

| code | 模块 | 说明 |
|------|------|------|
| 0 | 通用 | 成功 |
| 404 | 通用 | 资源不存在 |
| 1001 | 策略 | 引擎不存在 |
| 2001 | 行情 | 行情数据获取失败 |
| 3001 | 信号 | 信号查询/生成失败 |
| 4001 | 订单 | 下单失败 |
| 4004 | 订单 | 订单不存在 |
| 5001 | 风控 | 风控检查失败 |
| 6001 | 回测 | 回测任务不存在 |
| 6002 | 回测 | 回测任务创建失败 |
| 6003 | 回测 | 回测引擎执行失败 |

---

## 附录 A：完整端点清单

| # | 方法 | 路径 | 功能 | Phase |
|----|------|------|------|-------|
| 1 | GET | `/api/market/bars` | 获取 K 线 | 1 |
| 2 | GET | `/api/market/symbols` | 获取标的信息 | 1 |
| 3 | GET | `/api/signals` | 信号列表 | 1 |
| 4 | GET | `/api/signals/latest` | 最新信号 | 1 |
| 5 | POST | `/api/signals/generate` | 生成信号 | 1 |
| 6 | POST | `/api/orders` | 创建订单 | 1 |
| 7 | GET | `/api/orders` | 订单列表 | 1 |
| 8 | GET | `/api/orders/{id}` | 订单详情 | 1 |
| 9 | DELETE | `/api/orders/{id}` | 取消订单 | 1 |
| 10 | GET | `/api/risk/config` | 风控配置 | 1 |
| 11 | PUT | `/api/risk/config` | 更新风控配置 | 1 |
| 12 | GET | `/api/risk/alerts` | 风控告警 | 1 |
| 13 | GET | `/api/strategy/engines` | 引擎列表 | 1 |
| 14 | PUT | `/api/strategy/engines/{name}/toggle` | 切换引擎 | 1 |
| 15 | POST | `/api/strategy/eml/distill` | EML 蒸馏 | 1 |
| 16 | POST | `/api/backtest/run` | 启动回测 | **2** |
| 17 | GET | `/api/backtest/{id}` | 回测结果 | **2** |
| 18 | GET | `/api/backtest/{id}/progress` | 回测进度 | **2** |
| 19 | GET | `/api/backtest/history` | 回测历史 | **2** |
| 20 | DELETE | `/api/backtest/{id}` | 删除回测 | **2** |
| 21 | POST | `/api/backtest/scan` | 参数扫描 | **2** |
| 22 | GET | `/api/backtest/scan/{id}` | 扫描结果 | **2** |
| 23 | GET | `/api/preferences/{id}` | 获取偏好 | **2** |
| 24 | PUT | `/api/preferences/{id}` | 更新偏好 | **2** |
| 25 | DELETE | `/api/preferences/{id}` | 删除偏好 | **2** |
| 26 | GET | `/api/preferences/{id}/export` | 导出偏好 | **2** |
| 27 | POST | `/api/preferences/{id}/import` | 导入偏好 | **2** |

### WebSocket 端点

| # | 路径 | 功能 | Phase |
|----|------|------|-------|
| W1 | `/ws/market` | 行情推送 | 1 |
| W2 | `/ws/signals` | 信号推送 | 1 |
| W3 | `/ws/backtest` | 回测进度推送 | **2** |
| W4 | `/ws/orders` | 订单推送 | 1 |
| W5 | `/ws/risk` | 风控推送 | 1 |

---

*文档生成时间：2026-06-17 | 联系人：章锋（lisoleg@gmail.com）*
