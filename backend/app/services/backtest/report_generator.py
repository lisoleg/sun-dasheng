"""报告生成器 — report_generator

生成PDF和CSV报告。
"""

import csv
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Template
from loguru import logger

from app.services.backtest.models import BacktestResult
from app.services.backtest.chart_renderer import (
    render_equity_curve,
    render_drawdown_curve,
)


class ReportGenerator:
    """报告生成器

    支持：
    1. 生成PDF报告（HTML -> PDF）
    2. 生成CSV交易明细
    """

    def __init__(
        self,
        template_path: str = "./app/templates/backtest_report.html.j2",
        output_dir: str = "./reports",
    ) -> None:
        """初始化报告生成器

        Args:
            template_path: Jinja2模板路径
            output_dir: 输出目录
        """
        self.template_path = template_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pdf(
        self,
        result: BacktestResult,
        output_path: Optional[str] = None,
    ) -> str:
        """生成PDF报告

        Args:
            result: 回测结果
            output_path: 输出路径（可选）

        Returns:
            输出文件路径
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.output_dir, f"backtest_report_{timestamp}.pdf"
            )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 渲染图表
        chart_dir = os.path.join(self.output_dir, "charts")
        chart_paths = {}
        if result.equity_curve:
            equity_path = os.path.join(chart_dir, "equity_curve.png")
            chart_paths["equity"] = render_equity_curve(result.equity_curve, equity_path)

        if result.drawdown_curve:
            dd_path = os.path.join(chart_dir, "drawdown_curve.png")
            chart_paths["drawdown"] = render_drawdown_curve(
                result.drawdown_curve, dd_path
            )

        # 渲染HTML
        html_content = self._render_html(result, chart_paths)

        # HTML -> PDF
        try:
            import weasyprint

            weasyprint.HTML(string=html_content).write_pdf(output_path)
            logger.info(f"report_generator: generated PDF report {output_path}")
        except ImportError:
            # weasyprint未安装，保存HTML
            html_path = output_path.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.warning(
                f"report_generator: weasyprint not installed, saved HTML to {html_path}"
            )
            output_path = html_path

        return output_path

    def generate_csv(
        self,
        trades: List[Any],
        output_path: Optional[str] = None,
    ) -> str:
        """生成CSV交易明细

        Args:
            trades: 交易列表
            output_path: 输出路径（可选）

        Returns:
            输出文件路径
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.output_dir, f"trades_{timestamp}.csv"
            )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "trade_id",
                "symbol",
                "direction",
                "open_time",
                "open_price",
                "close_time",
                "close_price",
                "quantity",
                "pnl",
                "pnl_pct",
                "holding_hours",
                "signal_source",
                "exit_reason",
            ])

            for trade in trades:
                writer.writerow([
                    trade.trade_id,
                    trade.symbol,
                    trade.direction.value if hasattr(trade.direction, "value") else str(trade.direction),
                    trade.open_time.isoformat() if trade.open_time else "",
                    trade.open_price,
                    trade.close_time.isoformat() if trade.close_time else "",
                    trade.close_price,
                    trade.quantity,
                    trade.pnl,
                    trade.pnl_pct,
                    trade.holding_hours,
                    trade.signal_source,
                    trade.exit_reason,
                ])

        logger.info(f"report_generator: generated CSV {output_path}")
        return output_path

    def _render_html(
        self,
        result: BacktestResult,
        chart_paths: Dict[str, str],
    ) -> str:
        """渲染HTML报告

        Args:
            result: 回测结果
            chart_paths: 图表路径

        Returns:
            HTML内容
        """
        # 简化HTML模板（实际应使用Jinja2模板）
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>回测报告</title>
    <style>
        body {{ font-family: SimHei, Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>回测报告</h1>
    <p>标的: {result.config.symbol} | 周期: {result.config.timeframe}</p>
    <p>时间: {result.config.start_date} ~ {result.config.end_date}</p>

    <h2>绩效指标</h2>
    <div class="metric">
        <strong>总收益率</strong><br>
        {result.total_return:.2%}
    </div>
    <div class="metric">
        <strong>年化收益率</strong><br>
        {result.annual_return:.2%}
    </div>
    <div class="metric">
        <strong>夏普比率</strong><br>
        {result.sharpe_ratio:.2f}
    </div>
    <div class="metric">
        <strong>最大回撤</strong><br>
        {result.max_drawdown:.2%}
    </div>
    <div class="metric">
        <strong>胜率</strong><br>
        {result.win_rate:.2%}
    </div>
    <div class="metric">
        <strong>总交易次数</strong><br>
        {result.total_trades}
    </div>

    <h2>权益曲线</h2>
    <p>图表路径: {chart_paths.get("equity", "未生成")}</p>

    <h2>交易明细</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>标的</th>
            <th>方向</th>
            <th>开仓时间</th>
            <th>开仓价</th>
            <th>平仓时间</th>
            <th>平仓价</th>
            <th>盈亏</th>
        </tr>
        {self._render_trade_rows(result.trades)}
    </table>
</body>
</html>
        """
        return html

    def _render_trade_rows(self, trades: List[Any]) -> str:
        """渲染交易明细节"""
        rows = []
        for trade in trades[:50]:  # 限制显示50条
            rows.append(
                f"<tr>"
                f"<td>{trade.trade_id}</td>"
                f"<td>{trade.symbol}</td>"
                f"<td>{trade.direction.value if hasattr(trade.direction, 'value') else str(trade.direction)}</td>"
                f"<td>{trade.open_time.isoformat() if trade.open_time else ''}</td>"
                f"<td>{trade.open_price:.2f}</td>"
                f"<td>{trade.close_time.isoformat() if trade.close_time else ''}</td>"
                f"<td>{trade.close_price:.2f if trade.close_price else ''}</td>"
                f"<td>{trade.pnl:.2f if trade.pnl else ''}</td>"
                f"</tr>"
            )
        return "\n".join(rows)
