"""全局配置管理 - Pydantic Settings"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，支持从.env文件和环境变量加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 应用基础配置
    APP_NAME: str = "孙大圣量化交易系统"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./sundasheng.db"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 币安API配置
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET: bool = True

    # TOMAS-AGI配置
    TOMAS_TRANSLATOR_URL: str = "http://localhost:8001/api/translator"
    TOMAS_WRITER_URL: str = "http://localhost:8002/api/writer"

    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # 风控配置
    RISK_MAX_POSITION_PCT: float = 0.1  # 单笔最大仓位比例 10%
    RISK_STOP_LOSS_PCT: float = 0.05  # 默认止损比例 5%
    RISK_TAKE_PROFIT_PCT: float = 0.10  # 默认止盈比例 10%
    RISK_MAX_DRAWDOWN_PCT: float = 0.20  # 最大回撤比例 20%

    # 行情采集配置
    MARKET_FETCH_INTERVAL: int = 60  # 行情采集间隔(秒)
    MARKET_SYMBOLS: str = "BTCUSDT,ETHUSDT"  # 默认监控标的(逗号分隔)

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # 回测引擎配置
    BACKTEST_MAX_WORKERS: int = 4
    BACKTEST_TIMEOUT_SEC: int = 600
    BACKTEST_MAX_PARAMS_PER_SCAN: int = 1000

    # PDF报告配置
    PDF_OUTPUT_DIR: str = "./reports/pdf"
    CSV_OUTPUT_DIR: str = "./reports/csv"
    REPORT_TEMPLATE_PATH: str = "./app/templates/backtest_report.html.j2"
    REPORT_FONT_PATH: str = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/sundasheng.log"


# 全局配置单例
settings = Settings()
