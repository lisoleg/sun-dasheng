# 变更日志 (Changelog)

本文档记录孙大圣量化交易系统的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased] — 待发布

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

### 修改
- 前端整体 UI 从 MVP 升级为专业交易终端风格
- WebSocket Hub 新增异常处理和断连清理
- 市场数据 / 信号 / 订单 / 风控 API 端点连接真实服务（移除 Mock）
- 回测页面从占位升级为完整功能页面
- 知识图谱组件增强（D3.js 力导向图 + DNA 日历 + 搜索高亮）

### 修复
- 修复 WebSocket Hub `broadcast()` 异常导致的断连问题
- 修复后端 API 端点（market.py / signal.py / order.py / risk.py）返回 Mock 数据的问题
- 修复前端路由配置不完整的问题

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
