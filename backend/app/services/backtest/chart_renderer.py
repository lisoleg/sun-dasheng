"""图表渲染器 — chart_renderer

使用 matplotlib 绘制权益曲线、回撤曲线、月度收益热力图。
"""

import os
from typing import List, Optional

from loguru import logger

from app.services.backtest.models import BacktestResult


def render_equity_curve(
    equity_curve: List[float],
    output_path: str,
    title: str = "权益曲线",
) -> str:
    """绘制权益曲线，保存为PNG

    Args:
        equity_curve: 权益曲线数据
        output_path: 输出文件路径
        title: 图表标题

    Returns:
        输出文件路径
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve, linewidth=2)
        plt.title(title, fontsize=14)
        plt.xlabel("K线数", fontsize=10)
        plt.ylabel("权益", fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()

        logger.info(f"chart_renderer: saved equity curve to {output_path}")
        return output_path

    except ImportError:
        logger.warning("chart_renderer: matplotlib not installed")
        return ""


def render_drawdown_curve(
    drawdown_curve: List[float],
    output_path: str,
    title: str = "回撤曲线",
) -> str:
    """绘制回撤曲线

    Args:
        drawdown_curve: 回撤曲线数据
        output_path: 输出文件路径
        title: 图表标题

    Returns:
        输出文件路径
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.plot(drawdown_curve, linewidth=2, color="red")
        plt.title(title, fontsize=14)
        plt.xlabel("K线数", fontsize=10)
        plt.ylabel("回撤", fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()

        logger.info(f"chart_renderer: saved drawdown curve to {output_path}")
        return output_path

    except ImportError:
        logger.warning("chart_renderer: matplotlib not installed")
        return ""


def render_monthly_heatmap(
    monthly_returns: dict,
    output_path: str,
    title: str = "月度收益热力图",
) -> str:
    """绘制月度收益热力图

    Args:
        monthly_returns: 月度收益 { "YYYY-MM": return }
        output_path: 输出文件路径
        title: 图表标题

    Returns:
        输出文件路径
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 简化：创建空白图表
        plt.figure(figsize=(12, 6))
        plt.text(
            0.5,
            0.5,
            "月度收益热力图\n(需要seaborn)",
            ha="center",
            va="center",
            fontsize=14,
        )
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()

        logger.info(f"chart_renderer: saved monthly heatmap to {output_path}")
        return output_path

    except ImportError:
        logger.warning("chart_renderer: matplotlib not installed")
        return ""
