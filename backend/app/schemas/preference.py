"""用户偏好 Pydantic Schema — UserPreferences"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserPreferencesUpdate(BaseModel):
    """用户偏好更新请求"""

    theme_mode: Optional[str] = Field(default=None, description="主题模式: dark/light")
    layout_template: Optional[str] = Field(default=None, description="布局模板")
    dashboard_panels: Optional[Dict[str, Any]] = Field(
        default=None, description="面板布局配置"
    )
    risk_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="风控设置"
    )
    notification_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="通知设置"
    )


class UserPreferencesResponse(BaseModel):
    """用户偏好响应"""

    user_id: str = Field(..., description="用户ID")
    theme_mode: str = Field(default="dark", description="主题模式")
    layout_template: str = Field(default="default", description="布局模板")
    dashboard_panels: Optional[Dict[str, Any]] = Field(
        default=None, description="面板布局配置"
    )
    risk_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="风控设置"
    )
    notification_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="通知设置"
    )
    updated_at: Optional[str] = Field(default=None, description="更新时间 ISO 8601")
