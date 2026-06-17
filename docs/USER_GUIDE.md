# 孙大圣量化交易系统 - 用户指南

> 版本：v1.0 | 日期：2026-06-17 | 适用对象：量化交易员、开发者

---

## 目录

- [孙大圣量化交易系统 - 用户指南](#孙大圣量化交易系统---用户指南)
  - [目录](#目录)
  - [1. 系统概述](#1-系统概述)
  - [2. 环境要求](#2-环境要求)
  - [3. 安装部署](#3-安装部署)
    - [3.1 Windows](#31-windows)
    - [3.2 macOS](#32-macos)
    - [3.3 Linux (Ubuntu/Debian)](#33-linux-ubuntudebian)
  - [4. 配置说明](#4-配置说明)
  - [5. 启动系统](#5-启动系统)
    - [5.1 后端启动](#51-后端启动)
    - [5.2 前端启动](#52-前端启动)
    - [5.3 验证启动状态](#53-验证启动状态)
  - [6. 各页面使用指南](#6-各页面使用指南)
    - [6.1 K线图表页](#61-k线图表页)
    - [6.2 信号面板](#62-信号面板)
    - [6.3 回测中心](#63-回测中心)
    - [6.4 风控监控](#64-风控监控)
    - [6.5 知识图谱](#65-知识图谱)
  - [7. 策略配置](#7-策略配置)
  - [8. 币安API配置](#8-币安api配置)
  - [9. 通达信配置](#9-通达信配置)
  - [10. 常见问题（FAQ）](#10-常见问题faq)
  - [11. 故障排除](#11-故障排除)
  - [12. 最佳实践](#12-最佳实践)

---

## 1. 系统概述

孙大圣（Sun Dasheng）量化交易系统是一款**融合中国传统易学量化理论（鲁兆理论）与现代AGI推理框架（TOMAS-AGI）**的双市场量化交易平台。

**核心能力**：
- **双理论引擎**：鲁兆理论引擎（太极中心律/螺旋律/波浪理论/对偶律/周期律/江恩角度线/BG均线系统/万物皆为数/DNA核数繁衍）+ TOMAS-AGI推理引擎（翻译官EML检索 + 作家LLM推理）
- **双市场支持**：A股（通达信）+ 币安（Binance）自动交易
- **实时风控**：止损止盈、仓位管理、最大回撤控制、异常监控
- **可视化仪表盘**：K线图表+理论标注、实时信号流、回测中心、风控监控、知识图谱

**系统架构**：
```
数据接入层（通达信/币安） → 理论引擎层（鲁兆引擎+TOMAS-AGI） → 信号融合层 → 交易执行层（币安+风控） → 可视化仪表盘
```

---

## 2. 环境要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.11 | 3.11+ | 后端运行环境 |
| Node.js | 18 | 20 LTS | 前端运行环境 |
| Redis | 5.0 | 7.0+ | Celery任务队列 |
| SQLite | 3.35+ | 最新 | 开发数据库（零配置） |
| PostgreSQL | 14 | 15+ | 生产数据库（可选） |

**硬件建议**：
- 开发环境：4核CPU / 8GB内存 / 50GB磁盘
- 生产环境：8核CPU / 16GB内存 / 100GB SSD / 低延迟网络（币安交易）

---

## 3. 安装部署

### 3.1 Windows

1. **安装依赖软件**
   - 安装 [Python 3.11](https://www.python.org/downloads/)
   - 安装 [Node.js 20 LTS](https://nodejs.org/)
   - 安装 [Redis for Windows](https://github.com/microsoftarchive/redis/releases) 或使用 WSL2 安装 Redis

2. **克隆项目**
   ```powershell
   git clone https://github.com/your-org/sundasheng-quant.git
   cd sundasheng-quant
   ```

3. **安装后端依赖**
   ```powershell
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **安装前端依赖**
   ```powershell
   cd ..\frontend
   npm install
   ```

5. **启动 Redis**
   ```powershell
   # 如果已安装 Redis for Windows
   redis-server
   # 或使用 WSL2
   wsl -d Ubuntu -e redis-server
   ```

### 3.2 macOS

1. **安装依赖**
   ```bash
   # 使用 Homebrew 安装
   brew install python@3.11 node redis
   brew services start redis
   ```

2. **克隆项目**
   ```bash
   git clone https://github.com/your-org/sundasheng-quant.git
   cd sundasheng-quant
   ```

3. **安装后端**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **安装前端**
   ```bash
   cd ../frontend
   npm install
   ```

### 3.3 Linux (Ubuntu/Debian)

1. **安装系统依赖**
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm redis-server
   sudo systemctl enable redis-server
   sudo systemctl start redis-server
   ```

2. **克隆项目**
   ```bash
   git clone https://github.com/your-org/sundasheng-quant.git
   cd sundasheng-quant
   ```

3. **安装后端**
   ```bash
   cd backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **安装前端**
   ```bash
   cd ../frontend
   npm install
   ```

---

## 4. 配置说明

所有配置通过 `backend/.env` 文件管理。复制模板并编辑：

```bash
cd backend
cp .env.example .env
```

### 配置项详解

| 配置项 | 默认值 | 说明 | 推荐值 |
|--------|--------|------|--------|
| **DATABASE_URL** | `sqlite+aiosqlite:///./sundasheng.db` | 数据库连接串 | 开发保持默认；生产改为PostgreSQL |
| **REDIS_URL** | `redis://localhost:6379/0` | Redis连接 | 保持默认 |
| **BINANCE_API_KEY** | *(空)* | 币安API Key | 填入你的币安API Key |
| **BINANCE_API_SECRET** | *(空)* | 币安API Secret | 填入你的币安API Secret |
| **BINANCE_TESTNET** | `true` | 是否使用测试网 | **新手必设true**，熟练后设false |
| **TOMAS_TRANSLATOR_URL** | `http://localhost:8001/api/translator` | 翻译官服务地址 | 如部署TOMAS-AGI则修改 |
| **TOMAS_WRITER_URL** | `http://localhost:8002/api/writer` | 作家服务地址 | 如部署TOMAS-AGI则修改 |
| **OPENAI_API_KEY** | *(空)* | OpenAI API Key | 用于作家LLM推理，必填 |
| **OPENAI_MODEL** | `gpt-4` | LLM模型 | `gpt-4` 或 `gpt-4-turbo` |
| **RISK_MAX_POSITION_PCT** | `0.1` | 单笔最大仓位比例 | 新手建议 `0.05` (5%) |
| **RISK_STOP_LOSS_PCT** | `0.05` | 默认止损比例 | 保守 `0.03` (3%)，激进 `0.08` (8%) |
| **RISK_TAKE_PROFIT_PCT** | `0.10` | 默认止盈比例 | 建议 `0.15` (15%) 或更高 |
| **RISK_MAX_DRAWDOWN_PCT** | `0.20` | 最大回撤比例 | 建议 `0.15` (15%) |
| **MARKET_FETCH_INTERVAL** | `60` | 行情采集间隔(秒) | 日内交易可改为 `30` |
| **MARKET_SYMBOLS** | `BTCUSDT,ETHUSDT` | 默认监控标的 | 按需修改，逗号分隔 |
| **CELERY_BROKER_URL** | `redis://localhost:6379/1` | Celery消息队列 | 保持默认 |
| **CELERY_RESULT_BACKEND** | `redis://localhost:6379/2` | Celery结果存储 | 保持默认 |
| **CORS_ORIGINS** | `["http://localhost:5173"]` | 前端跨域允许 | 如前端改端口则同步修改 |
| **LOG_LEVEL** | `INFO` | 日志级别 | 开发用 `DEBUG`，生产用 `INFO` |
| **LOG_FILE** | `logs/sundasheng.log` | 日志文件路径 | 保持默认 |

### 风控配置建议

| 用户类型 | 单笔仓位 | 止损 | 止盈 | 最大回撤 |
|----------|---------|------|------|----------|
| 保守型 | 3% | 3% | 8% | 10% |
| 稳健型 | 5% | 5% | 10% | 15% |
| 激进型 | 10% | 8% | 15% | 20% |

---

## 5. 启动系统

### 5.1 后端启动

需要同时启动三个服务：FastAPI主服务、Celery Worker、Celery Beat调度器。

**方式一：多个终端窗口**

```bash
# 终端1：FastAPI 主服务
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# 终端2：Celery Worker
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# 终端3：Celery Beat（定时任务调度）
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

**方式二：使用进程管理器（生产推荐）**

```bash
# 安装 pm2 或 supervisor
# 使用 pm2 示例
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name sds-api
pm2 start "celery -A app.tasks.celery_app worker" --name sds-worker
pm2 start "celery -A app.tasks.celery_app beat" --name sds-beat
```

### 5.2 前端启动

```bash
cd frontend
npm run dev
```

前端默认运行在 `http://localhost:5173`，支持热模块替换（HMR）。

### 5.3 验证启动状态

1. **浏览器访问前端**：`http://localhost:5173`
2. **检查后端健康**：`http://localhost:8000/health`
   - 应返回：`{"code":0,"data":{"status":"healthy","version":"0.1.0"},"message":"ok"}`
3. **查看API文档**：`http://localhost:8000/docs`（Swagger UI）
4. **检查Redis连接**：后端日志中应显示 `Redis: redis://localhost:6379/0`

---

## 6. 各页面使用指南

### 6.1 K线图表页

**路径**：`/`（默认首页）

**功能**：
- **K线图主体**：基于 lightweight-charts 的高性能K线图，支持 1m/5m/15m/1h/4h/1d/1w 周期切换
- **理论标注层**：
  - 太极中心律：DNA29/DNA13 时间窗口用竖线标注，太极中心点用 "▲太极底" / "▼太极顶" 标记
  - 螺旋律：斐波那契回撤/扩展水平线自动绘制
  - 波浪理论：1-5浪+ABC调整浪自动标记
- **信号叠加**：买入/卖出信号以箭头标注，颜色编码置信度：
  - 绿色（>=0.8）：高置信度
  - 黄色（0.5-0.8）：中等置信度
  - 红色（<0.5）：低置信度
- **底部信号列表**：最近10条信号的简要信息
- **标的搜索**：输入标的代码（如 BTCUSDT、000001.SZ）搜索并切换

**操作**：
1. 在顶部工具栏切换时间周期
2. 在搜索框输入标的代码按回车切换
3. 观察K线图上的理论标注和信号箭头
4. 查看底部最近信号列表

### 6.2 信号面板

**路径**：`/signals`

**功能**：
- **顶部统计卡片**：今日信号总数、多头信号数、空头信号数、平均置信度
- **筛选区**：
  - 市场筛选：全部 / A股 / 币安
  - 方向筛选：全部 / 多头(LONG) / 空头(SHORT) / 持有(HOLD)
  - 置信度范围：0-1 滑块筛选
  - 标的搜索：按代码模糊搜索
- **信号表格**：
  - 列：时间、标的、方向、价格、置信度、来源理论、引擎
  - 方向用颜色区分：红色=LONG，绿色=SHORT
  - 置信度用进度条可视化

**操作**：
1. 使用筛选器缩小关注的信号范围
2. 点击表头可按列排序
3. 分页浏览历史信号

### 6.3 回测中心

**路径**：`/backtest`

**功能**：
- **策略配置**：
  - 勾选启用的理论引擎（太极中心律/螺旋律/波浪理论/TOMAS终裁）
  - 设置回测时间范围、初始资金
- **运行回测**：点击"运行"按钮，显示进度条
- **收益曲线**：策略收益 vs 基准收益对比图
- **统计指标**：
  - 总收益率、最大回撤、夏普比率
  - 胜率、盈亏比、交易次数
- **交易明细**：每笔交易的入场价、出场价、盈亏

**操作**：
1. 勾选要测试的策略引擎
2. 设置时间范围和初始资金
3. 点击"运行"等待回测完成
4. 查看收益曲线和统计指标
5. 分析交易明细，找出盈亏原因

### 6.4 风控监控

**路径**：`/risk`

**功能**：
- **风控配置**：
  - 最大仓位比例：1%-30% 滑块调节
  - 止损比例：1%-20% 滑块调节
  - 止盈比例：1%-50% 滑块调节
  - 最大回撤比例：5%-30% 滑块调节
  - 点击"保存"生效
- **持仓监控**：
  - 当前所有持仓的标的、方向、数量、入场价、当前价
  - 浮盈亏、止损价、止盈价、止损距离%
  - 止损距离<2%时标红警示
- **风控告警**：
  - 实时告警列表（CRITICAL/WARNING/INFO）
  - 显示告警时间、标的、消息内容

**操作**：
1. 调整风控参数滑块，点击"保存"
2. 实时监控持仓的止损距离
3. 关注未处理的风控告警

### 6.5 知识图谱

**路径**：`/knowledge`

**功能**：
- **EML蒸馏**：点击"EML蒸馏"按钮，系统将鲁兆理论文本蒸馏为知识图谱
- **搜索节点**：输入关键词（如"太极"、"螺旋"、"波浪"）搜索知识节点
- **D3力导向图**：可视化展示知识节点和关系边
- **节点详情面板**：
  - 点击节点显示：类型、名称、描述
  - 关联关系列表
  - 关联节点快速跳转

**操作**：
1. 点击"EML蒸馏"生成最新知识图谱
2. 在搜索框输入关键词过滤节点
3. 点击图谱中的节点查看详情
4. 点击关联节点跳转到相关概念

---

## 7. 策略配置

### 启用/禁用理论引擎

通过 API 或前端（未来版本）控制：

```bash
# 查看当前引擎状态
curl http://localhost:8000/api/strategy/engines

# 禁用某个引擎（如波浪理论）
curl -X PUT http://localhost:8000/api/strategy/engines/elliott/toggle

# 启用某个引擎
curl -X PUT http://localhost:8000/api/strategy/engines/elliott/toggle
```

**当前可用引擎**：
| 引擎名称 | 标识 | 默认状态 |
|----------|------|---------|
| 太极中心律 | `taiji` | 启用 |
| 螺旋律 | `spiral` | 启用 |
| 波浪理论 | `elliott` | 启用 |
| TOMAS-AGI | `tomas` | 启用 |

### 调整权重

目前系统采用**等权融合**策略。权重调整功能将在 v0.3.0 中通过配置文件支持：

```python
# backend/app/services/signal/fusion.py 中修改
ENGINE_WEIGHTS = {
    "taiji": 0.30,    # 太极中心律权重
    "spiral": 0.25,   # 螺旋律权重
    "elliott": 0.25,  # 波浪理论权重
    "tomas": 0.20,    # TOMAS-AGI权重
}
```

---

## 8. 币安API配置

### 申请API Key

1. 登录 [币安官网](https://www.binance.com/) 或 [币安测试网](https://testnet.binance.vision/)
2. 进入"API管理"页面
3. 创建新的API Key，启用以下权限：
   - **读取**（查询账户、订单）
   - **现货交易**（下单、撤单）
   - **合约交易**（如需要合约交易）
4. 配置IP白名单（推荐绑定服务器IP）
5. 保存 **API Key** 和 **Secret Key**

### 配置测试网（强烈推荐新手）

测试网使用虚拟资金，可安全测试交易功能：

1. 访问 [币安测试网](https://testnet.binance.vision/)
2. 使用GitHub账号登录，自动生成测试API Key
3. 在 `.env` 中设置：
   ```env
   BINANCE_API_KEY=your_testnet_api_key
   BINANCE_API_SECRET=your_testnet_secret
   BINANCE_TESTNET=true
   ```

### 配置生产环境

```env
BINANCE_API_KEY=your_production_api_key
BINANCE_API_SECRET=your_production_secret
BINANCE_TESTNET=false
```

> **警告**：生产环境将使用真实资金交易。请确保：
> 1. 已完成充分回测
> 2. 风控参数设置合理
> 3. 初始仓位比例较低（建议3%-5%）
> 4. 已启用止损

---

## 9. 通达信配置

### 连接方式

系统使用 **pytdx** 库连接通达信服务器，无需安装通达信客户端。

**默认配置**：
- pytdx 自动连接通达信免费行情服务器
- 支持实时行情、历史K线、分时数据
- 无需账号密码（使用公共行情接口）

### A股标的格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 深交所 | `000001.SZ` | 平安银行 |
| 上交所 | `600519.SH` | 贵州茅台 |
| 简写 | `sz000001` | pytdx 内部格式 |

### 使用限制

- 免费接口频率限制：建议每分钟不超过200次请求
- 系统默认采集间隔为60秒，符合限制要求
- 如需更高频率，建议购买通达信Level2或券商专业接口

### 备选方案

如需更稳定的A股数据，可考虑：
- **AKShare**（免费Python财经数据接口库）
- **Tushare**（需注册获取Token）
- **QMT/Ptrade**（券商量化交易终端，需合规评估）

---

## 10. 常见问题（FAQ）

**Q1：系统是否支持A股自动下单？**
> 当前版本（v0.1.0）仅支持币安自动下单。A股自动下单涉及券商合规接口（如QMT/Ptrade），计划在 v1.0.0 中评估接入。

**Q2：为什么信号是Mock数据？**
> 当前版本为MVP，部分核心模块（TOMAS-AGI、交易执行器）使用Mock实现。根据TEST_REPORT，P0问题正在修复中，预计v0.2.0将全部接入真实数据。

**Q3：如何切换A股和币安市场？**
> 在顶部导航栏的"市场切换"下拉框中选择"A股"或"币安"。切换后，K线图、信号面板、持仓面板的数据源将自动切换。

**Q4：TOMAS-AGI是什么？需要额外安装吗？**
> TOMAS-AGI是系统的AGI推理引擎，包含"翻译官"（EML知识检索）和"作家"（LLM推理）。当前版本使用Mock实现，后续需要部署Translator和Writer服务，或配置OpenAI API Key使用云端LLM。

**Q5：如何调整回测的时间范围？**
> 在"回测中心"页面，修改"开始日期"和"结束日期"输入框，然后点击"运行"。注意当前回测使用的是Mock数据，真实回测需接入历史数据库。

**Q6：WebSocket断开连接怎么办？**
> 前端已实现自动重连机制（指数退避）。如果长时间断开，请检查：
> 1. 后端服务是否正常运行
> 2. 网络连接是否稳定
> 3. 防火墙是否阻止了WebSocket端口

**Q7：如何查看系统日志？**
> 后端日志默认输出到 `backend/logs/sundasheng.log`，同时输出到控制台。可在 `.env` 中调整 `LOG_LEVEL` 控制日志详细程度。

**Q8：Celery Worker 没有执行任务？**
> 请检查：
> 1. Redis是否正常运行：`redis-cli ping` 应返回 `PONG`
> 2. Celery Worker是否正确启动：查看worker日志是否有任务接收
> 3. 检查 `.env` 中的 `CELERY_BROKER_URL` 和 `CELERY_RESULT_BACKEND` 是否正确

**Q9：前端编译失败/类型错误？**
> 请确保：
> 1. Node.js 版本 >= 18
> 2. 已运行 `npm install` 安装所有依赖
> 3. 检查 `frontend/tsconfig.json` 和 `vite.config.ts` 配置是否正确

**Q10：如何备份数据库？**
> **SQLite**：直接复制 `backend/sundasheng.db` 文件。
> **PostgreSQL**：使用 `pg_dump` 命令：
> ```bash
> pg_dump -h localhost -U postgres sundasheng > backup.sql
> ```

**Q11：系统支持多币种/多A股同时监控吗？**
> 支持。在 `.env` 中设置 `MARKET_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,000001.SZ,600519.SH`，系统将通过Celery定时任务轮询所有标的数据。

**Q12：如何设置模拟盘模式（只发信号不下单）？**
> 当前版本可通过不配置 `BINANCE_API_KEY` 实现模拟模式（系统会生成Mock订单）。v0.5.0 将正式支持"纸上交易"模式。

---

## 11. 故障排除

### 后端启动失败

| 症状 | 可能原因 | 解决方案 |
|------|---------|----------|
| `ModuleNotFoundError` | 依赖未安装 | 运行 `pip install -r requirements.txt` |
| `Connection refused` (Redis) | Redis未启动 | 启动Redis：`redis-server` |
| `Address already in use` | 端口8000被占用 | 更换端口：`uvicorn app.main:app --port 8001` |
| `Alembic error` | 数据库迁移问题 | 删除 `sundasheng.db` 重新启动，或运行 `alembic upgrade head` |
| `Permission denied` | 日志目录无权限 | 创建 `backend/logs` 目录并赋予写入权限 |

### 前端启动失败

| 症状 | 可能原因 | 解决方案 |
|------|---------|----------|
| `npm install` 失败 | Node版本过低 | 升级Node.js到18+ |
| `vite` 命令不存在 | 依赖未安装 | 运行 `npm install` |
| 页面空白 | 后端未启动或CORS配置错误 | 检查后端状态和 `.env` 中的 `CORS_ORIGINS` |
| 图表不显示 | lightweight-charts未加载 | 检查 `npm install` 是否完整，无网络代理问题 |

### 数据异常

| 症状 | 可能原因 | 解决方案 |
|------|---------|----------|
| K线图无数据 | 数据提供者未连接 | 检查网络，查看后端日志中的provider连接状态 |
| 信号长时间不更新 | Celery Beat未启动 | 启动Beat：`celery -A app.tasks.celery_app beat` |
| 币安数据延迟 | 网络延迟或API限流 | 检查网络，增加 `MARKET_FETCH_INTERVAL` |
| 通达信连接失败 | pytdx服务器繁忙 | 稍后重试，或更换备用服务器 |

### 交易异常

| 症状 | 可能原因 | 解决方案 |
|------|---------|----------|
| 下单失败 | API Key无效 | 检查 `.env` 中的Key是否正确，是否在测试网/生产网匹配 |
| 订单状态一直是PENDING | 网络问题或价格未触及 | 检查网络，查看币安订单状态 |
| 风控拒绝所有订单 | 风控参数过于严格 | 调整 `RISK_MAX_POSITION_PCT` 和 `RISK_STOP_LOSS_PCT` |
| 止损未触发 | 风控任务未运行 | 检查Celery Worker是否正常 |

---

## 12. 最佳实践

### 开发与测试

1. **始终使用测试网**：在熟悉系统前，将 `BINANCE_TESTNET=true` 保持启用
2. **先回测再实盘**：任何策略调整先在"回测中心"验证，观察至少3个月的历史数据
3. **逐步增加仓位**：从3%单笔仓位开始，验证系统稳定性后再逐步提高
4. **监控日志**：定期查看 `logs/sundasheng.log`，关注WARNING和ERROR级别日志
5. **保持备份**：定期备份 `.env` 文件和数据库文件

### 生产部署

1. **使用PostgreSQL**：生产环境将 `DATABASE_URL` 改为PostgreSQL连接串
2. **启用Alembic迁移**：使用 `alembic revision --autogenerate` 管理数据库版本
3. **配置反向代理**：使用Nginx作为反向代理，启用HTTPS
4. **限制API访问**：配置防火墙，仅允许前端服务器IP访问后端API
5. **监控Redis**：使用Redis监控工具，确保内存和连接数正常
6. **使用Docker**：生产环境建议使用Docker Compose部署所有服务

### 策略优化

1. **多引擎验证**：不要仅依赖单一理论引擎，信号融合后的结果更可靠
2. **关注置信度**：高置信度（>=0.8）信号优先执行，低置信度信号可仅观察
3. **动态调整权重**：根据市场环境调整各引擎权重（震荡市重视太极/螺旋，趋势市重视波浪/均线）
4. **定期蒸馏EML**：当鲁兆理论有新资料时，通过 `POST /api/strategy/eml/distill` 更新知识图谱
5. **记录交易日志**：手动记录每笔交易的心理状态和决策依据，用于后期复盘

### 安全建议

1. **保护API Key**：`.env` 文件不要提交到Git仓库，使用 `.gitignore` 排除
2. **限制IP白名单**：币安API Key配置IP白名单，防止Key泄露后被滥用
3. **定期更换Key**：建议每3个月更换一次币安API Key
4. **最小权限原则**：币安API仅开启需要的权限（读取+现货交易），不要开启提现权限
5. **敏感信息脱敏**：日志中API Key已脱敏显示（前4位+****），但仍需保护日志文件访问权限

---

> **免责声明**：本系统提供的交易信号仅供参考，不构成投资建议。金融市场存在风险，使用本系统进行交易可能产生亏损。请根据自身风险承受能力谨慎决策。开发者不对因使用本系统产生的任何损失承担责任。

---

*本文档由孙大圣技术文档团队维护，如有问题请联系技术支持。*
