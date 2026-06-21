"""用户偏好 API 路由 — 获取/更新/删除用户偏好设置"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user_preference import UserPreferences as UserPreferencesModel
from app.schemas.preference import (
    UserPreferencesUpdate,
    UserPreferencesResponse,
)

router = APIRouter()


@router.get("/{user_id}", response_model=Dict[str, Any], tags=["用户偏好"])
async def get_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取用户偏好设置"""
    result = await db.get(UserPreferencesModel, user_id)
    if not result:
        # 返回默认偏好
        return {
            "code": 0,
            "data": {
                "user_id": user_id,
                "theme_mode": "dark",
                "layout_template": "default",
                "dashboard_panels": None,
                "risk_settings": None,
                "notification_settings": None,
                "updated_at": None,
            },
            "message": "使用默认偏好",
        }

    return {
        "code": 0,
        "data": {
            "user_id": user_id,
            "theme_mode": result.theme_mode,
            "layout_template": result.layout_template,
            "dashboard_panels": result.custom_layout,
            "risk_settings": None,  # 扩展字段，暂时返回 None
            "notification_settings": result.notifications,
            "updated_at": result.updated_at.isoformat() if hasattr(result, "updated_at") else None,
        },
        "message": "ok",
    }


@router.put("/{user_id}", response_model=Dict[str, Any], tags=["用户偏好"])
async def update_preferences(
    user_id: str,
    update: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新用户偏好设置"""
    result = await db.get(UserPreferencesModel, user_id)

    if not result:
        # 创建新偏好记录
        result = UserPreferencesModel(
            preference_id=user_id,
            theme_mode=update.theme_mode or "dark",
            layout_template=update.layout_template or "default",
            custom_layout=update.dashboard_panels,
            notifications=update.notification_settings or {
                "browser_enabled": True,
                "sound_enabled": False,
                "alert_level": "warning",
            },
        )
        db.add(result)
    else:
        # 更新已有记录
        if update.theme_mode is not None:
            result.theme_mode = update.theme_mode
        if update.layout_template is not None:
            result.layout_template = update.layout_template
        if update.dashboard_panels is not None:
            result.custom_layout = update.dashboard_panels
        if update.notification_settings is not None:
            result.notifications = update.notification_settings

    await db.commit()
    await db.refresh(result)

    return {
        "code": 0,
        "data": {
            "user_id": user_id,
            "theme_mode": result.theme_mode,
            "layout_template": result.layout_template,
            "dashboard_panels": result.custom_layout,
            "risk_settings": None,
            "notification_settings": result.notifications,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "message": "偏好设置已更新",
    }


@router.delete("/{user_id}", response_model=Dict[str, Any], tags=["用户偏好"])
async def delete_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """删除用户偏好设置（恢复默认）"""
    result = await db.get(UserPreferencesModel, user_id)
    if result:
        await db.delete(result)
        await db.commit()

    return {
        "code": 0,
        "data": {"user_id": user_id},
        "message": "偏好设置已删除，将恢复默认",
    }


@router.get("/{user_id}/export", response_model=Dict[str, Any], tags=["用户偏好"])
async def export_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """导出用户偏好设置（用于跨设备同步）"""
    result = await db.get(UserPreferencesModel, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="用户偏好不存在")

    return {
        "code": 0,
        "data": {
            "user_id": user_id,
            "theme_mode": result.theme_mode,
            "layout_template": result.layout_template,
            "custom_layout": result.custom_layout,
            "chart_indicators": result.chart_indicators,
            "notifications": result.notifications,
            "refresh_mode": result.refresh_mode,
            "shortcuts_enabled": result.shortcuts_enabled,
        },
        "message": "ok",
    }


@router.post("/{user_id}/import", response_model=Dict[str, Any], tags=["用户偏好"])
async def import_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """导入用户偏好设置（用于跨设备同步）"""
    result = await db.get(UserPreferencesModel, user_id)

    if not result:
        result = UserPreferencesModel(preference_id=user_id)
        db.add(result)

    # 更新字段
    for key, value in preferences.items():
        if hasattr(result, key) and key != "preference_id":
            setattr(result, key, value)

    await db.commit()

    return {
        "code": 0,
        "data": {"user_id": user_id},
        "message": "偏好设置已导入",
    }
