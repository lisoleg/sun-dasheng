"""用户偏好数据库模型 — UserPreferences"""

import uuid
from typing import Optional

from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class UserPreferences(Base, BaseMixin):
    """用户偏好设置表

    Attributes:
        preference_id: 偏好唯一标识
        theme_mode: 主题模式(dark/light)
        layout_template: 布局模板(default/minimal/analyst/custom)
        custom_layout: 自定义布局配置(react-grid-layout格式)
        chart_indicators: K线图表指标配置
        notifications: 通知设置
        refresh_mode: 数据刷新模式(auto/manual)
        shortcuts_enabled: 是否启用快捷键
    """
    __tablename__ = "user_preferences"

    preference_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4())
    )
    theme_mode: Mapped[str] = mapped_column(String(10), default="dark", nullable=False)
    layout_template: Mapped[str] = mapped_column(String(20), default="default", nullable=False)
    custom_layout: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    chart_indicators: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: {
            "bg_ma": True,
            "gann": False,
            "fibonacci": False,
            "macd": True,
            "kdj": False,
            "rsi": True,
        }
    )
    notifications: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: {
            "browser_enabled": True,
            "sound_enabled": False,
            "alert_level": "warning",
        }
    )
    refresh_mode: Mapped[str] = mapped_column(String(10), default="auto", nullable=False)
    shortcuts_enabled: Mapped[bool] = mapped_column(default=True)
