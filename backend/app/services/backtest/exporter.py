"""导出入口 — exporter

统一调用 report_generator 生成报告。
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import BacktestResult
from app.services.backtest.report_generator import ReportGenerator


class BacktestExporter:
    """回测报告导出器

    统一入口，支持导出：
    1. PDF报告
    2. CSV交易明细
    3. HTML报告（PDF不可用时的备选）
    """

    def __init__(
        self,
        output_dir: str = "./reports",
        template_path: Optional[str] = None,
    ) -> None:
        """初始化导出器

        Args:
            output_dir: 输出目录
            template_path: 模板路径
        """
        self.generator = ReportGenerator(
            template_path=template_path or "./app/templates/backtest_report.html.j2",
            output_dir=output_dir,
        )

    def export(
        self,
        result: BacktestResult,
        formats: List[str] = ("pdf", "csv"),
    ) -> Dict[str, str]:
        """导出报告

        Args:
            result: 回测结果
            formats: 导出格式列表 (pdf/csv/html)

        Returns:
            导出文件路径字典 {format: path}
        """
        paths: Dict[str, str] = {}

        for fmt in formats:
            if fmt == "pdf":
                paths["pdf"] = self.generator.generate_pdf(result)
            elif fmt == "csv":
                paths["csv"] = self.generator.generate_csv(result.trades)
            elif fmt == "html":
                # 生成HTML报告
                html_path = self.generator.generate_pdf(
                    result, output_path=result.config.symbol + ".html"
                )
                paths["html"] = html_path

        logger.info(f"BacktestExporter: exported {list(paths.keys())}")
        return paths
