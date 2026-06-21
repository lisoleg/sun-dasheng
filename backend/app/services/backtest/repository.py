"""回测结果持久化 — BacktestRepository

将回测结果保存到数据库。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from loguru import logger

from app.models.backtest import BacktestRun, BacktestScan
from app.models.backtest_trade import BacktestTrade


class BacktestRepository:
    """回测结果持久化

    负责将回测结果保存到数据库。
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        """初始化回测仓库

        Args:
            db: 数据库会话
        """
        self.db = db

    async def save_run(
        self,
        backtest_id: str,
        config: Dict[str, Any],
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """保存回测任务

        Args:
            backtest_id: 回测ID
            config: 回测配置
            status: 状态
            result: 回测结果

        Returns:
            回测ID
        """
        if not self.db:
            logger.warning("BacktestRepository: no database session")
            return backtest_id

        run = BacktestRun(
            backtest_id=backtest_id,
            config=config,
            status=status,
        )

        if result:
            run.result_summary = result
            run.finished_at = datetime.now()

        self.db.add(run)
        await self.db.commit()

        logger.info(f"BacktestRepository: saved run {backtest_id}")
        return backtest_id

    async def get_run(self, backtest_id: str) -> Optional[BacktestRun]:
        """获取回测任务

        Args:
            backtest_id: 回测ID

        Returns:
            回测任务记录
        """
        if not self.db:
            return None

        result = await self.db.get(BacktestRun, backtest_id)
        return result

    async def update_run_status(
        self,
        backtest_id: str,
        status: str,
        progress: float = 0.0,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """更新回测任务状态

        Args:
            backtest_id: 回测ID
            status: 新状态
            progress: 进度
            result: 回测结果
        """
        if not self.db:
            return

        run = await self.db.get(BacktestRun, backtest_id)
        if run:
            run.status = status
            run.progress = progress
            if result:
                run.result_summary = result
                run.finished_at = datetime.now()
            await self.db.commit()

    async def save_trades(
        self,
        backtest_id: str,
        trades: List[Dict[str, Any]],
    ) -> None:
        """保存交易明细

        Args:
            backtest_id: 回测ID
            trades: 交易明细列表
        """
        if not self.db:
            return

        for trade_data in trades:
            trade = BacktestTrade(
                backtest_id=backtest_id,
                symbol=trade_data.get("symbol", ""),
                side=trade_data.get("direction", "BUY"),
                open_time=trade_data.get("open_time"),
                open_price=trade_data.get("open_price", 0),
                close_time=trade_data.get("close_time"),
                close_price=trade_data.get("close_price"),
                quantity=trade_data.get("quantity", 0),
                pnl=trade_data.get("pnl"),
                pnl_pct=trade_data.get("pnl_pct"),
            )
            self.db.add(trade)

        await self.db.commit()
        logger.info(f"BacktestRepository: saved {len(trades)} trades for {backtest_id}")

    async def list_runs(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> List[BacktestRun]:
        """获取回测任务列表

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            回测任务列表
        """
        if not self.db:
            return []

        from sqlalchemy import select

        offset = (page - 1) * page_size
        stmt = (
            select(BacktestRun)
            .order_by(BacktestRun.started_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_run(self, backtest_id: str) -> bool:
        """删除回测任务

        Args:
            backtest_id: 回测ID

        Returns:
            是否成功删除
        """
        if not self.db:
            return False

        run = await self.db.get(BacktestRun, backtest_id)
        if run:
            await self.db.delete(run)
            await self.db.commit()
            logger.info(f"BacktestRepository: deleted run {backtest_id}")
            return True

        return False
