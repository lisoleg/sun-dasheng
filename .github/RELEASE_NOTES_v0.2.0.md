# Release Notes — v0.2.0

> 发布日期：2026-06-17  
> 代号：**Phase 2 — Web UI 重设计 + 回测引擎**  
> 完整变更日志：见 [CHANGELOG.md](./CHANGELOG.md)

---

## 🎉 重大更新

### 1. 回测引擎完整实现 🚀

**事件驱动回测核心**（`backend/app/services/backtest/`）：
- 支持鲁兆理论全部 7 个子模块（太极中心律/螺旋律/波浪理论/对偶律/周期律/江恩角度线/BG均线）
- 多策略组合回测 + 信号融合（AND/OR/WEIGHTED 三策略）
- 参数扫描优化（Celery 并行，支持网格搜索）
- 完整绩效指标（16+ 项，numpy 向量化计算）
- 权益曲线 / 回撤曲线 / 交易明细 / 月度收益热力图
- PDF 报告导出（weasyprint + Jinja2 模板 + matplotlib 图表）
- CSV 交易明细导出

**性能**：
- 1825 根 K 线（5 年日线）回测 < 30 秒
- 参数扫描支持并行计算（Celery 任务队列）

### 2. Web UI 重设计 🎨

**专业交易终端风格**（类 TradingView/Bloomberg Terminal）：
- **深色主题系统**（Bloomberg 风，#0d1117 背景）
- **可拖拽面板布局**（react-grid-layout，用户可自定义面板位置和大小）
- **多套布局模板**（默认 / 极简 / 分析师）
- **全局主题切换**（深色/浅色）
- **响应式设计**（1920×1080 为主，向下兼容 1366×768）

**7 个核心页面重设计**：
1. **仪表盘首页**：多市场概览 + 账户总览 + 最近信号 + 实时盈亏
2. **K线图表页**：多时间周期切换 + 叠加技术指标（BG均线/江恩角度线/斐波那契回撤）+ 绘图工具
3. **信号中心**：信号列表（表格+卡片视图）+ 信号详情弹窗（含 TOMAS 置信度/推理过程）+ 筛选/排序
4. **回测页**：策略配置表单 + 回测结果可视化（权益曲线+回撤曲线+交易标注）+ 绩效指标面板
5. **风控监控**：实时风险指标仪表 + 持仓风险矩阵 + 止损止盈状态 + 风险预警
6. **知识图谱页**：鲁兆理论概念关系图 + DNA 节点可视化
7. **设置页**：交易所 API 配置 + 策略参数调优 + 通知设置

### 3. 4 个新鲁兆理论引擎 📐

- **对偶律**（阴阳/涨跌对偶）→ 输出：DUAL_BUY / DUAL_SELL
- **周期律**（周期高低点）→ 输出：CYCLE_TOP / CYCLE_BOTTOM
- **江恩角度线**（1×1, 2×1, 1×2）→ 输出：GANN_SUPPORT / GANN_RESISTANCE
- **BG 均线**（4/8/16/32）→ 输出：BG_GOLDEN_CROSS / BG_DEATH_CROSS

### 4. 信号融合策略扩展 🧠

支持三种融合策略（策略模式）：
- **AND**：所有信号一致才发出（高置信度，低频率）
- **OR**：任一信号发出即发出（低置信度，高频率）
- **WEIGHTED**：加权平均，置信度加权（推荐）

### 5. WebSocket 增强 📡

- 多频道订阅（market / signals / backtest / orders / risk）
- 心跳机制（每 30s 发送 ping）
- 断连重连 + 降级（断连 3 次后自动切为 10s 轮询）
- 回测实时进度推送

### 6. 用户偏好持久化 ⚙️

- 主题模式（dark/light）
- 布局模板（默认/极简/分析师）
- 仪表盘面板配置
- 风控设置
- 通知设置

---

## 📦 安装与升级

### 新安装

见 [部署文档](./docs/DEPLOYMENT.md)

### 从 v0.1.0 升级

```bash
# 拉取最新代码
git pull origin main

# 后端更新
cd backend
pip install -r requirements.txt
alembic upgrade head  # 新增 backtest_runs / backtest_trades / user_preferences 表

# 前端更新
cd frontend
npm install

# 重启服务
# (见部署文档)
```

**⚠️ 注意事项**：
1. 新增依赖：`weasyprint`, `jinja2`, `matplotlib`, `scipy`（后端）；`react-grid-layout`, `recharts`, `zustand`, `lucide-react`（前端）
2. 新增环境变量（见 `.env.example`）：
   - `BACKTEST_MAX_WORKERS`
   - `PDF_OUTPUT_DIR`
   - `REPORT_TEMPLATE_PATH`
3. 需要运行数据库迁移：`alembic upgrade head`

---

## 🐛 修复问题

- 修复 WebSocket Hub `broadcast()` 异常导致的断连问题
- 修复后端 API 端点（market.py / signal.py / order.py / risk.py）返回 Mock 数据的问题
- 修复前端路由配置不完整的问题
- 修复信号融合引擎未连接真实服务的问题

---

## 📚 文档更新

- ✅ README.md (v0.2.0，16 章节)
- ✅ CHANGELOG.md
- ✅ docs/PRD-phase2.md（许清楚，755 行）
- ✅ docs/ARCHITECTURE-phase2.md（高见远，2154 行）
- ✅ docs/USER_GUIDE-phase2.md（中文，16 章节）
- ✅ docs/API_DOCUMENTATION.md（27 个 REST 端点 + 5 个 WS 频道）
- ✅ docs/DEPLOYMENT.md（部署文档）
- ✅ docs/DEVELOPMENT.md（开发文档）

---

## 🔮 已知问题（Phase 2.1 计划）

1. **回测引擎 `_run_backtest_task` 为 Mock 实现**（需要连接真实历史 K 线数据）
2. **风控 API 为 Mock 实现**（需要连接真实持仓数据）
3. **K 线图表 `lightweight-charts` 集成未完成**（当前为骨架版本）
4. **A 股自动下单功能为 Mock**（需要合规路径）
5. **回测仅支持日线**，不支持分钟线（Phase 2.1 计划）
6. **参数扫描并行优化未完全测试**（大规模参数组合可能超时）

---

## 👥 贡献者

- **章锋（老铁）** — 项目发起人与需求方
- **许清楚（PM）** — 产品需求文档（PRD）
- **高见远（Arch）** — 系统架构设计
- **寇豆码（Eng）** — 代码实现
- **严过关（QA）** — 测试验证

---

## 📊 统计数据

| 指标 | v0.1.0 | v0.2.0 | 增长 |
|------|--------|--------|------|
| 文件数 | 98 | 196 | +100% |
| 代码行数 | 15,893 | 31,500+ | +98% |
| 后端文件 | 52 | 95 | +83% |
| 前端文件 | 46 | 101 | +120% |
| 文档文件 | 5 | 13 | +160% |
| API 端点 | 14 | 41 | +193% |
| 理论引擎 | 3 | 7 | +133% |

---

## 🔗 链接

- **GitHub 仓库**：https://github.com/lisoleg/sun-dasheng
- **Issue Tracker**：https://github.com/lisoleg/sun-dasheng/issues
- **学术论文**：https://github.com/lisoleg/sun-dasheng/blob/main/docs/PAPER.md
- **在线演示**：（待部署）

---

## ❤️ 致谢

感谢鲁兆先生的《鲁兆股市预测与实战操作系统》提供的理论基础。

感谢开源社区提供的优秀工具：FastAPI, React, MUI, lightweight-charts, D3.js, Celery, Redis, PostgreSQL.

---

**完整 commit 历史**：https://github.com/lisoleg/sun-dasheng/commits/main
