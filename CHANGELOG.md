# 变更日志 (Changelog)

本文档记录孙大圣量化交易系统的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.2.1] — 2026-06-23

### 新增
- 拓扑不变量库（`topo_invariants.py`）：鲁加斯数列、八卦常数、`apply_phase_filter()` 通用相位过滤函数
- 相位连续性分析器（`phase_analyzer.py`）：LOB 深度熵计算、PCS 评分、三档熔断机制、ENPV 决策
- DNA 倍发生成验证（`dna_replication.py`）：波浪检测、DNA 基因提取、斐波那契/鲁加斯自相似验证、κ-Snap 外推推理
- 信号基类模块（`signal/base.py`）：提取 SignalHint/TheoryResult/Signal/TheoryEngine 解决循环导入
- 2 个 TOMAS v2.0 API 端点：`/market/phase-analysis` 和 `/market/dna-detection`
- PhaseAnalysisPage 前端图表增强：PCS 历史走势线图 + PCS/价格双 Y 轴叠加图
- DNADetectionPage 前端图表增强：波浪结构可视化（面积图 + 菱形标记 + 虚线边界）
- Phase 3 规划文档（`docs/PHASE3_PLANNING.md`）：多 Agent 协作交易机制
- TOMAS v2.0 技术论文（`docs/PAPER-tomas-v2.md`）

### 修改
- 全部 7 个理论引擎 `analyze()` 方法末尾统一接入 `apply_phase_filter()` 相位连续性过滤
- 信号融合 WEIGHTED 策略增加全局相位连续性门控
- 回测滑点模型升级：滑点 = 相位失配成本（TOMAS v2.0 核心概念）
- 回测信号执行器增加流动性熔断 + ENPV 决策逻辑
- TheoryResult 数据结构新增 `phase_continuity` 和 `is_phase_valid` 字段
- `generator.py` 重构：移除内联类定义，从 `base.py` 导入
- `fusion.py` 和 `fusion_strategies.py` 导入路径从 `generator` 改为 `base`
- `signal.py` 和 `order.py`：`async_session` → `async_session_factory`，`metadata` → `meta_data`
- Signal 模型：`metadata` 字段重命名为 `meta_data`（保留 DB 列名 `metadata`）
- `main.py` 路由前缀从 `/api` 改为 `/api/v1`
- `requirements.txt`：注释掉 TA-Lib（无 C 编译器），清理重复依赖
- 前端 `postcss.config.js` 重命名为 `postcss.config.cjs`（ES module 兼容）

### 修复
- 信号模块循环导入：`generator.py` ↔ `fusion.py` ↔ `fusion_strategies.py` 三角依赖
- SQLAlchemy 保留属性名冲突：`metadata` 是 SQLAlchemy 保留字，改为 `meta_data`
- `async_session` 导入错误：`app.database` 导出的是 `async_session_factory`
- numpy 1.26 无 Python 3.13 预编译 wheel：降级至 Python 3.10
- 前端 Vite 启动失败：`postcss.config.js` 与 `"type": "module"` 冲突

### 已知问题
- 币安测试网连接超时（网络环境问题，非代码Bug）
- TA-Lib 未安装（需 C 编译器，当前未在代码中使用）
- Redis 未运行时 Celery 任务不可用

---

## [0.2.0] — 2026-06-21

### 新增
- 回测引擎完整实现（事件驱动 + numpy 向量化绩效计算）
- 4 个新鲁兆理论引擎（对偶律 / 周期律 / 江恩角度线 / BG 均线）
- 信号融合策略模式（AND / OR / WEIGHTED）
- 参数扫描优化器（Celery 并行，支持网格搜索）
- PDF 报告导出（weasyprint + Jinja2 模板 + matplotlib 图表）
- CSV 交易明细导出
- 专业深色主题系统（Bloomberg 风格）
- 可拖拽面板布局（react-grid-layout）
- 多套布局模板（默认 / 极简 / 分析师）
- 7 个核心页面重设计（仪表盘 / K线 / 信号 / 回测 / 风控 / 知识图谱 / 设置）
- WebSocket 频道扩展（backtest / orders / risk）
- 用户偏好持久化（主题 / 布局 / 风控设置）
- 月度收益热力图（recharts）
- 理论贡献度饼图
- Phase 2 技术论文（docs/PAPER-phase2.md）
- 系统实现白皮书（docs/IMPLEMENTATION_WHITEPAPER.md）
- MIT 许可证（LICENSE）
- 贡献指南（CONTRIBUTING.md）

### 修改
- 前端整体 UI 从 MVP 升级为专业交易终端风格
- WebSocket Hub 新增异常处理和断连清理
- 市场数据 / 信号 / 订单 / 风控 API 端点连接真实服务（移除 Mock）
- 回测页面从占位升级为完整功能页面
- 知识图谱组件增强（D3.js 力导向图 + DNA 日历 + 搜索高亮）
- README 更新至 v0.2.0，新增回测引擎和信号融合章节

### 修复
- 修复 WebSocket Hub `broadcast()` 异常导致的断连问题
- 修复后端 API 端点（market.py / signal.py / order.py / risk.py）返回 Mock 数据的问题
- 修复前端路由配置不完整的问题
- 修复前端类型错误（DashboardPage 导入 + Panel lucide-react 导入 + useLayoutTemplate 导入）

### 已知问题
- K线图 lightweight-charts 集成需进一步完善
- 信号详情对话框（SignalDetailDialog）未实现
- 回测交易明细表格未实现
- 参数扫描 UI 未实现
- 回测引擎 `_run_backtest_task` 为 Mock，需连接真实历史数据
- A股自动下单功能为 Mock，需合规路径

---

## [0.1.0] — 2026-06-17

### 新增
- 初始版本发布
- 核心后端框架（FastAPI + Celery + SQLAlchemy）
- 前端框架（Vite + React 18 + TypeScript + MUI v5 + Tailwind CSS）
- 3 个鲁兆理论引擎（太极中心律 / 螺旋律 / 波浪理论）
- TOMAS-AGI 引擎骨架（翻译官 + 作家 + Token Bridge）
- 信号融合引擎（多源加权）
- 风控引擎基础（止损 / 止盈 / 仓位管理）
- 币安交易执行器（支持 Testnet）
- 前端 5 个核心页面（仪表盘 / K线 / 信号 / 回测占位 / 风控 / 知识图谱）
- WebSocket 实时推送（market / signals 频道）
- EML 知识蒸馏框架
- 用户使用文档（中文 USER_GUIDE.md）
- 学术论文（PAPER.md，~12,000 字）
- GitHub 仓库初始化（lisoleg/sun-dasheng）

### 已知问题
- 回测引擎仅为前端占位，未实现后端逻辑
- 4 个鲁兆理论引擎（对偶律 / 周期律 / 江恩 / BG 均线）未实现
- 前端 UI 为快速 MVP 版本，非专业交易终端风格
- A 股自动下单功能为 Mock，需合规路径
- 回测仅支持日线，不支持分钟线

---

## [0.0.1] — 2026-06-10 (原型)

### 新增
- 项目立项
- 技术栈调研与选型
- 鲁兆理论数学形式化初步研究
- TOMAS-AGI 双推理架构设计

---

**图例：**
- 🆕 新增功能
- ♻️ 修改
- 🐛 修复 Bug
- 🗑️ 删除
- 🔒 安全修复
