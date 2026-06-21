# 孙大圣量化交易系统 — 部署文档

> 版本：v0.2.0 | 更新：2026-06-17

---

## 目录

1. [环境要求](#环境要求)
2. [快速部署](#快速部署)
3. [生产环境部署](#生产环境部署)
4. [Docker 部署](#docker-部署)
5. [配置说明](#配置说明)
6. [故障排查](#故障排查)

---

## 环境要求

### 后端

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.11 | 推荐使用 pyenv 管理多版本 |
| Redis | ≥ 6.0 | Celery 任务队列 + WebSocket 消息 |
| PostgreSQL | ≥ 14.0 | 主数据库（或 SQLite 开发用） |
| Binance API Key | - | 币安交易 API Key + Secret |
| A 股数据源 | - | 通达信 pytdx 或爬虫接入 |

### 前端

| 依赖 | 版本 |
|------|------|
| Node.js | ≥ 22.0 |
| npm | ≥ 10.0 |

### 可选

| 依赖 | 说明 |
|------|------|
| Celery Worker | 回测引擎异步任务 |
| Celery Beat | 定时任务（信号生成） |
| Nginx | 反向代理（生产环境） |
| WeasyPrint | PDF 报告导出（需要系统依赖） |

---

## 快速部署

### 1. 克隆仓库

```bash
git clone https://github.com/lisoleg/sun-dasheng.git
cd sun-dasheng
```

### 2. 后端部署

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入必要配置（见下方"配置说明"）

# 初始化数据库
alembic upgrade head

# 启动 Redis（本地开发）
redis-server --daemonize yes

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env，设置 VITE_API_BASE_URL=http://localhost:8000

# 启动开发服务器
npm run dev
```

### 4. 访问系统

打开浏览器访问：`http://localhost:5173`

---

## 生产环境部署

### 架构图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  Frontend   │     │   Backend   │
│ (反向代理)   │     │ (静态文件)   │     │ (FastAPI)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                    ┌──────────┼──────────┐
                                    ▼          ▼          ▼
                              ┌─────────┐ ┌─────────┐ ┌─────────┐
                              │  Redis  │ │  PostgreSQL │ │ Celery  │
                              └─────────┘ └────────────┘ └─────────┘
```

### 后端（生产）

```bash
# 使用 gunicorn + uvicorn worker
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 前端（生产）

```bash
cd frontend

# 构建生产版本
npm run build

# 输出在 dist/ 目录，用 Nginx 托管
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 反向代理
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Celery Worker（生产）

```bash
# 启动 Celery Worker（回测引擎）
celery -A app.tasks.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000

# 启动 Celery Beat（定时任务）
celery -A app.tasks.celery_app beat \
  --loglevel=info
```

---

## Docker 部署

### Docker Compose（推荐）

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sun_dasheng
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://postgres:your_password@postgres:5432/sun_dasheng
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "5173:5173"
    command: npm run dev

  celery_worker:
    build: ./backend
    depends_on:
      - redis
      - postgres
    command: celery -A app.tasks.celery_app worker --loglevel=info

volumes:
  postgres_data:
```

启动：

```bash
docker-compose up -d
```

---

## 配置说明

### 后端 `.env`

```bash
# 服务器
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 数据库
DATABASE_URL=postgresql://postgres:password@localhost:5432/sun_dasheng
# 或 SQLite（开发用）
# DATABASE_URL=sqlite+aiosqlite:///./sun_dasheng.db

# Redis
REDIS_URL=redis://localhost:6379/0

# 币安 API
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
BINANCE_TESTNET=true  # 建议先用测试网

# A 股数据源（通达信）
TDX_HOST=120.76.152.17  # 通达信服务器
TDX_PORT=7709

# DeepSeek API（TOMAS 作家引擎）
DEEPSEEK_API_KEY=your_deepseek_api_key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 回测引擎
BACKTEST_MAX_WORKERS=4
BACKTEST_TIMEOUT_SEC=600

# 报告导出
PDF_OUTPUT_DIR=exports/pdf
CSV_OUTPUT_DIR=exports/csv
```

### 前端 `.env`

```bash
# API 地址
VITE_API_BASE_URL=http://localhost:8000

# WebSocket 地址
VITE_WS_URL=ws://localhost:8000/ws

# 是否启用 Mock 数据（开发用）
VITE_ENABLE_MOCK=false
```

---

## 故障排查

### 后端无法启动

**问题**：`ModuleNotFoundError: No module named 'pytdx'`

**解决**：
```bash
pip install pytdx
```

**问题**：`alembic.util.exc.CommandError: Can't locate revision identified by 'xxx'`

**解决**：
```bash
# 删除数据库，重新迁移
dropdb sun_dasheng
createdb sun_dasheng
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 前端无法启动

**问题**：`Error: Cannot find module 'react-grid-layout'`

**解决**：
```bash
cd frontend && npm install
```

**问题**：`Type error: Cannot find module './theme'`

**解决**：检查 `tsconfig.json` 的 `baseUrl` 和 `paths` 配置。

### WebSocket 连接失败

**问题**：前端控制台显示 `WebSocket connection failed`

**解决**：
1. 检查后端是否启动：`curl http://localhost:8000/health`
2. 检查 Redis 是否运行：`redis-cli ping`
3. 检查 Nginx 是否正确代理 `/ws` 路径

### 回测引擎报错

**问题**：`Celery task failed: BacktestEngine not found`

**解决**：
1. 检查 Celery Worker 是否启动：`celery -A app.tasks.celery_app inspect active`
2. 检查 Redis 是否可连接：`redis-cli ping`
3. 查看 Celery Worker 日志

### PDF 报告导出失败

**问题**：`OSError: cannot open resource (字体文件)`

**解决**：
```bash
# Ubuntu/Debian
sudo apt-get install fonts-wqy-microhei

# macOS
brew install --cask font-wqy-microhei

# 或修改 REPORT_FONT_PATH 为系统存在的字体
```

---

## 性能优化

### 后端

- 使用 `asyncio` 异步数据库驱动（asyncpg）
- 启用 Redis 缓存（查询结果缓存）
- 使用连接池（数据库连接池 + Redis 连接池）

### 前端

- 启用代码分割（React.lazy + Suspense）
- 使用虚拟滚动（@mui/x-data-grid）
- 图片懒加载

### 回测引擎

- 使用 NumPy 向量化计算（已内置）
- 并行参数扫描（Celery 任务队列）
- 使用 HDF5 存储历史 K 线数据（避免重复下载）

---

## 安全建议

1. **API Key 管理**：不要提交 `.env` 文件到 Git
2. **CORS 配置**：生产环境设置明确的 `ALLOWED_ORIGINS`
3. **Rate Limiting**：使用 `slowapi` 限制 API 请求频率
4. **HTTPS**：生产环境必须使用 HTTPS（Let's Encrypt 免费证书）
5. **数据库备份**：定期备份 PostgreSQL 数据
6. **日志管理**：使用 Sentry 或 ELK 收集日志

---

## 监控

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# Celery Worker 健康检查
celery -A app.tasks.celery_app inspect ping
```

### 指标监控

- 使用 Prometheus + Grafana 监控：
  - API 请求延迟
  - Celery 任务队列长度
  - Redis 内存使用
  - 数据库连接池

---

## 更新系统

```bash
# 拉取最新代码
git pull origin main

# 后端更新
cd backend
pip install -r requirements.txt
alembic upgrade head

# 前端更新
cd frontend
npm install
npm run build

# 重启服务
sudo systemctl restart sun-dasheng-backend
sudo systemctl restart sun-dasheng-celery
```

---

## 支持

- GitHub Issues：https://github.com/lisoleg/sun-dasheng/issues
- 文档：https://github.com/lisoleg/sun-dasheng/docs/
