# 贡献指南 (Contributing Guide)

感谢你对孙大圣量化交易系统的关注！本文档指导你如何参与项目开发。

---

## 行为准则

- 尊重所有参与者，保持专业和友善
- 关注技术讨论，避免人身攻击
- 欢迎不同背景和经验的贡献者

---

## 开发环境准备

### 前置条件

| 依赖 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.11+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| Git | 2.30+ | 版本控制 |
| Redis | 6.0+ | Celery 消息队列 |
| PostgreSQL | 13+ | 生产数据库（开发可用 SQLite） |

### 本地启动

```bash
# 1. 克隆仓库
git clone https://github.com/lisoleg/sun-dasheng.git
cd sun-dasheng

# 2. 后端设置
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 配置环境变量
alembic upgrade head  # 数据库迁移
uvicorn app.main:app --reload --port 8000

# 3. 前端设置
cd ../frontend
npm install
npm run dev  # 启动开发服务器 (http://localhost:5173)
```

详细配置请参考 [部署文档](docs/DEPLOYMENT.md) 和 [开发文档](docs/DEVELOPMENT.md)。

---

## 代码规范

### Python 后端

- **风格**：遵循 [PEP 8](https://peps.python.org/pep-0008/)，使用 `ruff` 检查
- **类型标注**：所有函数必须添加类型标注（`-> ReturnType`）
- **文档字符串**：公共函数/类必须添加 docstring（Google 风格）
- **命名**：模块 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE`
- **异步**：API 端点使用 `async def`，I/O 密集操作使用 `await`

```python
# 正确示例
async def get_signals(
    symbol: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> list[SignalResponse]:
    """获取指定股票的信号列表。

    Args:
        symbol: 股票代码，如 "000001"
        limit: 返回数量上限
        db: 数据库会话

    Returns:
        信号响应列表
    """
    ...
```

### TypeScript 前端

- **风格**：遵循 [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- **Lint**：ESLint + Prettier
- **组件**：函数式组件 + Hooks，不使用 Class 组件
- **命名**：组件 `PascalCase`，函数/变量 `camelCase`，常量 `UPPER_SNAKE`
- **类型**：严格模式 `strict: true`，禁止 `any`

```typescript
// 正确示例
interface SignalCardProps {
  signal: Signal;
  onSelect?: (id: string) => void;
}

export function SignalCard({ signal, onSelect }: SignalCardProps): JSX.Element {
  const handleClick = useCallback(() => {
    onSelect?.(signal.id);
  }, [signal.id, onSelect]);

  return <Card onClick={handleClick}>...</Card>;
}
```

### Git 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（非新功能、非修复） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖变更 |

**示例**：
```
feat(backtest): 新增参数扫描优化器，支持网格搜索

- 实现 GridSearchOptimizer 类
- 集成 Celery 并行任务调度
- 支持多参数组合批量回测

Closes #42
```

---

## 开发工作流

### 1. 创建分支

```bash
git checkout -b feat/your-feature-name
```

分支命名规范：
- `feat/` — 新功能
- `fix/` — Bug 修复
- `docs/` — 文档
- `refactor/` — 重构

### 2. 开发与测试

```bash
# 后端测试
cd backend
pytest tests/ -v --cov=app

# 前端类型检查
cd frontend
npx tsc --noEmit

# 前端构建
npm run build
```

### 3. 提交 Pull Request

- PR 标题遵循 Conventional Commits 格式
- PR 描述包含：变更内容、测试方式、关联 Issue
- 确保所有 CI 检查通过
- 至少需要 1 个 Reviewer 批准

---

## 项目结构

```
sun-dasheng/
├── backend/              # Python 后端 (FastAPI)
│   ├── app/
│   │   ├── api/          # REST API 端点
│   │   ├── models/       # SQLAlchemy 数据模型
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── services/     # 业务逻辑层
│   │   │   ├── backtest/    # 回测引擎
│   │   │   ├── theory/      # 鲁兆理论引擎
│   │   │   ├── signal/      # 信号融合
│   │   │   ├── risk/        # 风控引擎
│   │   │   ├── execution/   # 交易执行
│   │   │   └── market_data/ # 行情数据
│   │   ├── config.py    # 配置管理
│   │   └── main.py      # 应用入口
│   ├── alembic/         # 数据库迁移
│   └── requirements.txt
├── frontend/            # TypeScript 前端 (Vite + React)
│   ├── src/
│   │   ├── api/         # API 客户端
│   │   ├── components/  # UI 组件
│   │   ├── pages/       # 页面
│   │   ├── hooks/       # 自定义 Hooks
│   │   ├── store/       # Zustand 状态管理
│   │   ├── theme/       # 主题系统
│   │   └── layouts/     # 布局模板
│   └── package.json
├── docs/                # 项目文档
├── docker-compose.yml   # 容器编排
└── README.md
```

---

## 新增理论引擎

如果要添加新的鲁兆理论引擎，请遵循以下步骤：

1. 在 `backend/app/services/theory/` 下创建新模块
2. 实现 `TheoryEngine` 基类接口：
   ```python
   class TheoryEngine(ABC):
       @abstractmethod
       async def analyze(self, bars: list[Bar]) -> TheoryResult:
           ...
   ```
3. 在 `backend/app/services/theory/__init__.py` 中注册
4. 在 `backend/app/services/signal/fusion.py` 中添加到融合引擎列表
5. 编写单元测试
6. 更新文档

---

## 报告 Bug

通过 [GitHub Issues](https://github.com/lisoleg/sun-dasheng/issues) 报告 Bug，请包含：

- 问题描述和期望行为
- 重现步骤
- 环境信息（OS、Python/Node 版本、浏览器）
- 错误日志/截图

---

## 许可证

本项目使用 [MIT License](LICENSE)。提交的代码将自动适用此许可证。

---

## 联系方式

- **GitHub Issues**: [lisoleg/sun-dasheng/issues](https://github.com/lisoleg/sun-dasheng/issues)
- **作者**: 章锋 (Zhang Feng)

---

感谢你的贡献！
