# 孙大圣量化交易系统 — 开发文档

> 版本：v0.2.0 | 更新：2026-06-17

---

## 目录

1. [项目结构](#项目结构)
2. [开发环境搭建](#开发环境搭建)
3. [代码规范](#代码规范)
4. [架构说明](#架构说明)
5. [测试指南](#测试指南)
6. [贡献指南](#贡献指南)
7. [常见问题](#常见问题)

---

## 项目结构

```
sun-dasheng/
├── backend/                 # 后端（FastAPI）
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/       # 业务逻辑
│   │   │   ├── theory/     # 鲁兆理论引擎（7个）
│   │   │   ├── signal/     # 信号生成与融合
│   │   │   ├── backtest/   # 回测引擎
│   │   │   ├── execution/  # 订单执行
│   │   │   └── tomas/      # TOMAS-AGI 集成
│   │   ├── tasks/          # Celery 异步任务
│   │   ├── core/           # 核心配置
│   │   └── main.py         # 入口
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/               # 前端（React + TypeScript）
│   ├── src/
│   │   ├── api/           # API 调用
│   │   ├── components/    # 组件
│   │   │   ├── common/   # 通用组件
│   │   │   ├── layout/   # 布局组件
│   │   │   ├── dashboard/# 仪表盘
│   │   │   ├── chart/    # K 线图表
│   │   │   ├── signals/  # 信号中心
│   │   │   ├── backtest/ # 回测
│   │   │   ├── risk/     # 风控
│   │   │   ├── knowledge/# 知识图谱
│   │   │   └── settings/ # 设置
│   │   ├── hooks/        # 自定义 Hooks
│   │   ├── pages/        # 页面
│   │   ├── store/        # Zustand 状态管理
│   │   ├── theme/        # 主题系统
│   │   └── utils/        # 工具函数
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                   # 文档
│   ├── PRD.md             # 产品需求文档
│   ├── ARCHITECTURE.md    # 系统架构设计
│   ├── API_DOCUMENTATION.md
│   ├── USER_GUIDE.md      # 使用手册
│   ├── DEPLOYMENT.md      # 部署文档
│   └── PAPER.md           # 学术论文
│
├── tests/                  # 集成测试
├── .github/               # GitHub Actions
├── README.md
├── CHANGELOG.md
└── docker-compose.yml
```

---

## 开发环境搭建

### 后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-asyncio httpx black isort mypy

# 配置环境变量
cp .env.example .env
# 编辑 .env（见部署文档）

# 初始化数据库
alembic upgrade head

# 启动开发服务器（自动重载）
uvicorn app.main:app --reload

# 访问 API 文档
# http://localhost:8000/docs
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（热重载）
npm run dev

# 访问前端
# http://localhost:5173
```

### 推荐 IDE 配置

**VS Code**：

安装扩展：
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)

设置（`.vscode/settings.json`）：

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "tailwindCSS.experimental.classRegex": [
    ["tw`([^`]*)", "[\"'`]([^\"'`]*).*?[\"'`]"]
  ]
}
```

---

## 代码规范

### 后端（Python）

**格式化**：
```bash
black backend/
isort backend/
```

**类型检查**：
```bash
mypy backend/
```

**命名规范**：
- 类名：`PascalCase`（`BacktestEngine`）
- 函数/变量：`snake_case`（`calculate_metrics`）
- 常量：`UPPER_SNAKE_CASE`（`MAX_WORKERS`）
- 理论名称：`snake_case`（`taiji`, `spiral`, `elliott`）

**文档字符串**（Google 风格）：
```python
def calculate_sharpe_ratio(returns: np.ndarray) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 日收益率数组
        
    Returns:
        夏普比率（年化）
        
    Raises:
        ValueError: 如果 returns 为空
    """
    ...
```

### 前端（TypeScript）

**格式化**：
```bash
cd frontend
npx prettier --write .
npx eslint . --ext .ts,.tsx
```

**类型检查**：
```bash
cd frontend
npx tsc --noEmit
```

**命名规范**：
- 组件名：`PascalCase`（`BacktestPage.tsx`）
- 函数/变量：`camelCase`（`calculateMetrics`）
- 常量：`UPPER_SNAKE_CASE`（`API_BASE_URL`）
- 文件名：`kebab-case`（`backtest-config-form.tsx`）

**Props 接口**：
```typescript
interface BacktestConfigFormProps {
  onSubmit: (config: BacktestConfig) => void;
  initialConfig?: BacktestConfig;
}
```

**严禁 `any`**：使用 `unknown` + 类型守卫

---

## 架构说明

### 后端分层架构

```
API 层（FastAPI Router）
    ↓
服务层（Services）
    ↓
数据层（Models + Repository）
    ↓
数据库（PostgreSQL / SQLite）
```

**关键设计模式**：
1. **策略模式**：信号融合（`AndFusionStrategy` / `OrFusionStrategy` / `WeightedFusionStrategy`）
2. **事件驱动**：回测引擎（`BacktestEventLoop`）
3. **仓储模式**：数据持久化（`BacktestRepository`）
4. **工作单元**：Celery 异步任务

### 前端状态管理

**Zustand Store 结构**：
```typescript
interface Store {
  // 用户偏好
  themeMode: 'dark' | 'light';
  layoutTemplate: string;
  
  // WebSocket 连接状态
  wsConnected: boolean;
  wsChannels: Record<string, boolean>;
  
  // 回测结果（可选，大型数据用 React Query）
  backtestResult?: BacktestResult;
}
```

**API 调用**：
- 使用 `react-query` 或 `swr` 管理服务器状态
- 使用 `Zustand` 管理 UI 状态（主题/布局/偏好）

### TOMAS-AGI 集成

```
用户请求
    ↓
翻译官（EML 精确检索）→ 高置信度（≥0.7）→ 直接响应
    ↓
作家（LLM 创造性推理）→ 低置信度（<0.7）→ 增强响应
    ↓
置信度路由（≥0.5 → 作家，<0.5 → 降级）
```

---

## 测试指南

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_backtest_engine.py

# 运行特定测试函数
pytest tests/test_backtest_engine.py::test_event_loop

# 覆盖率报告
pytest --cov=app --cov-report=html
```

**测试文件命名**：`test_<模块名>.py`

**测试示例**：
```python
import pytest
from app.services.backtest.engine import BacktestEngine

def test_backtest_engine_basic():
    config = BacktestConfig(
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )
    engine = BacktestEngine(config)
    result = engine.run()
    
    assert result.total_return > -1.0  # 亏损不超过 100%
    assert result.sharpe_ratio != 0
```

### 前端测试

```bash
cd frontend

# 单元测试（Vitest）
npm run test

# 组件测试（React Testing Library）
npm run test:component

# E2E 测试（Playwright，可选）
npm run test:e2e
```

**测试文件命名**：`*.test.tsx` 或 `*.spec.tsx`

### 回测引擎测试

**测试数据**：
- 使用 `tests/fixtures/btc_5y_daily.csv`（真实数据脱敏）
- 或生成模拟数据（`generate_mock_bars()`）

**性能指标**：
- 1825 根 K 线（5 年日线）< 30 秒
- 内存占用 < 500MB

---

## 贡献指南

### 提交 Pull Request

1. **Fork 仓库**（如果不是核心贡献者）
2. **创建分支**：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **编写代码**（遵循代码规范）
4. **添加测试**（新功能必须有测试）
5. **运行测试**：
   ```bash
   # 后端
   cd backend && pytest
   
   # 前端
   cd frontend && npx tsc --noEmit
   ```
6. **提交代码**：
   ```bash
   git commit -m "feat: 添加 XXX 功能"
   ```
7. **推送分支**：
   ```bash
   git push origin feature/your-feature-name
   ```
8. **创建 Pull Request**（GitHub）

### Commit Message 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**：
```
feat(backtest): 添加参数扫描优化功能

- 实现网格搜索
- 支持并行计算（Celery）
- 添加优化目标选择（夏普/最大回撤/胜率）

Closes #123
```

### Code Review 检查清单

- [ ] 代码遵循规范（Black / Prettier）
- [ ] 类型注解完整（Python）或类型检查通过（TypeScript）
- [ ] 有新测试覆盖
- [ ] 测试通过
- [ ] 文档已更新（如需要）
- [ ] 性能影响（如涉及核心循环）
- [ ] 安全风险（如涉及 API Key）

---

## 常见问题

### 如何添加新的鲁兆理论引擎？

1. 在 `backend/app/services/theory/` 下创建新文件（如 `my_theory.py`）
2. 继承 `TheoryEngine` 基类：
   ```python
   from .base import TheoryEngine, TheoryInput, TheoryOutput
   
   class MyTheoryEngine(TheoryEngine):
       theory_name = "my_theory"
       
       def compute(self, input_data: TheoryInput) -> TheoryOutput:
           # 实现理论计算
           ...
   ```
3. 在 `backend/app/services/theory/__init__.py` 中导出
4. 在 `backend/app/services/signal/generator.py` 中注册
5. 添加测试 `tests/test_my_theory.py`

### 如何添加新的 API 端点？

1. 在 `backend/app/api/` 下创建新文件或添加到现有文件
2. 定义 Pydantic schema（`backend/app/schemas/`）
3. 实现业务逻辑（`backend/app/services/`）
4. 在 `backend/app/api/router.py` 中注册路由
5. 更新 `docs/API_DOCUMENTATION.md`

### 如何调试 Celery 任务？

```bash
# 启动 Celery Worker（开发模式）
celery -A app.tasks.celery_app worker \
  --loglevel=debug \
  --pool=solo  # Windows 用 solo，Linux/macOS 用 prefork

# 查看任务队列
celery -A app.tasks.celery_app inspect active

# 查看任务结果
celery -A app.tasks.celery_app result <task-id>
```

### 前端如何连接真实 API（而非 Mock）？

1. 检查 `frontend/src/api/client.ts` 的 `BASE_URL`
2. 设置环境变量 `VITE_API_BASE_URL=http://localhost:8000`
3. 确保后端已启动（`uvicorn app.main:app --reload`）
4. 检查 CORS 配置（`backend/app/main.py` 中的 `ALLOWED_ORIGINS`）

### 如何贡献新的回测指标？

1. 在 `backend/app/services/backtest/metrics.py` 中添加新函数
2. 在 `BacktestMetrics` dataclass 中添加字段
3. 在 `MetricsCalculator.calculate()` 中调用
4. 更新前端 `frontend/src/components/backtest/PerformanceMetrics.tsx`
5. 添加测试

---

## 性能分析

### 后端性能分析

```bash
# 使用 py-spy 分析 CPU 占用
pip install py-spy
py-spy top --pid <backend-pid>

# 使用 memory_profiler 分析内存
pip install memory-profiler
python -m memory_profiler script.py
```

### 前端性能分析

```bash
cd frontend

# 构建分析（包大小）
npm run build -- --analyze

# React DevTools Profiler
# 在浏览器中安装 React DevTools，使用 Profiler 标签
```

---

## 部署到生产环境（开发者视角）

见 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 联系方式

- **项目负责人**：章锋（老铁）
- **GitHub**：https://github.com/lisoleg/sun-dasheng
- **Issues**：https://github.com/lisoleg/sun-dasheng/issues

---

## 许可证

MIT License（或自定义）
