"""Celery配置与初始化"""

from celery import Celery

from app.config import settings

# 创建Celery应用实例
celery_app = Celery(
    "sundasheng",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery配置
celery_app.conf.update(
    # 序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果
    result_expires=3600,  # 结果保留1小时
    task_track_started=True,

    # 并发
    worker_concurrency=4,
    worker_prefetch_multiplier=1,

    # 任务超时
    task_soft_time_limit=300,  # 5分钟软超时
    task_time_limit=600,  # 10分钟硬超时

    # Beat定时任务
    beat_schedule={
        "fetch-market-data": {
            "task": "app.tasks.market_tasks.fetch_market_data",
            "schedule": settings.MARKET_FETCH_INTERVAL,
        },
        "check-risk-positions": {
            "task": "app.tasks.risk_tasks.check_risk_positions",
            "schedule": 1.0,  # 每秒检查
        },
    },

    # 自动发现任务模块
    autodiscover_tasks=["app.tasks"],
)

if __name__ == "__main__":
    celery_app.start()
