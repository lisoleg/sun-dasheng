"""策略配置API端点骨架"""

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# 内存中的模拟引擎配置
_mock_engines: List[Dict[str, Any]] = [
    {
        "name": "taiji",
        "display_name": "太极中心律",
        "description": "基于鲁兆太极中心律理论，通过DNA29/DNA13时间窗口计算太极中心点",
        "enabled": True,
        "theory_name": "太极中心律",
        "params": {
            "dna29_window": 29,
            "dna13_window": 13,
            "min_confidence": 0.5,
        },
    },
    {
        "name": "spiral",
        "display_name": "螺旋律",
        "description": "基于斐波那契数列的螺旋律理论，计算回撤与扩展位",
        "enabled": True,
        "theory_name": "螺旋律",
        "params": {
            "fibonacci_levels": [0.236, 0.382, 0.5, 0.618, 0.786],
            "extension_levels": [1.272, 1.618, 2.618],
        },
    },
    {
        "name": "elliott",
        "display_name": "波浪理论",
        "description": "基于艾略特波浪理论，检测推动浪与调整浪",
        "enabled": True,
        "theory_name": "波浪理论",
        "params": {
            "min_wave_length": 5,
            "max_retracement": 0.618,
        },
    },
    {
        "name": "tomas",
        "display_name": "TOMAS-AGI",
        "description": "TOMAS-AGI推理引擎，翻译官(EML检索)+作家(LLM推理)双路由",
        "enabled": True,
        "theory_name": "TOMAS-AGI",
        "params": {
            "confidence_threshold": 0.5,
            "translator_timeout": 2.0,
            "writer_timeout": 10.0,
        },
    },
]


class EmlDistillRequest(BaseModel):
    """EML知识蒸馏请求"""

    theory_texts: List[str] = Field(..., description="理论文本列表")
    overwrite: bool = Field(False, description="是否覆盖已有知识")


@router.get("/engines")
async def get_engines() -> Dict[str, Any]:
    """获取理论引擎列表"""
    return {
        "code": 0,
        "data": {
            "total": len(_mock_engines),
            "items": _mock_engines,
        },
        "message": "ok",
    }


@router.put("/engines/{name}/toggle")
async def toggle_engine(name: str) -> Dict[str, Any]:
    """启用/禁用理论引擎"""
    for engine in _mock_engines:
        if engine["name"] == name:
            engine["enabled"] = not engine["enabled"]
            return {
                "code": 0,
                "data": engine,
                "message": "ok",
            }

    return {
        "code": 1001,
        "data": None,
        "message": f"引擎 {name} 不存在",
    }


@router.post("/eml/distill")
async def distill_eml(request: EmlDistillRequest) -> Dict[str, Any]:
    """触发EML知识蒸馏"""
    return {
        "code": 0,
        "data": {
            "distilled": True,
            "nodes_count": len(request.theory_texts) * 3,
            "edges_count": len(request.theory_texts) * 2,
            "conflicts_resolved": 0,
            "message": f"已处理 {len(request.theory_texts)} 条理论文本",
        },
        "message": "ok",
    }
