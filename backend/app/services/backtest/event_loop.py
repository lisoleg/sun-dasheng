"""回测主事件循环 — BacktestEventLoop

核心回测循环：
1. 遍历每根K线
2. 标记持仓市值
3. 运行理论引擎
4. 信号融合
5. 生成订单
6. 撮合成交
7. 更新持仓
8. 记录权益
9. 广播进度
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import (
    Bar,
    BacktestConfig,
    BacktestResult,
    Portfolio,
    Trade,
)
from app.services.backtest.portfolio import PortfolioManager
from app.services.backtest.order_book import OrderBook
from app.services.backtest.slippage_model import SlippageModel
from app.services.backtest.signal_runner import SignalRunner


class BacktestEventLoop:
    """回测主事件循环

    按时间顺序遍历K线，模拟交易过程。
    """

    def __init__(
        self,
        config: BacktestConfig,
    ) -> None:
        """初始化回测事件循环

        Args:
            config: 回测配置
        """
        self.config = config
        self.portfolio_manager: Optional[PortfolioManager] = None
        self.order_book: Optional[OrderBook] = None
        self.slippage_model: Optional[SlippageModel] = None
        self.signal_runner: Optional[SignalRunner] = None

    def run(
        self,
        config: BacktestConfig,
        bars: List[Bar],
        theories: List[Any],
    ) -> BacktestResult:
        """运行回测主循环

        Args:
            config: 回测配置
            bars: K线数据列表
            theories: 理论引擎列表

        Returns:
            回测结果
        """
        logger.info(f"BacktestEventLoop: starting backtest with {len(bars)} bars")

        # 初始化
        self.portfolio_manager = PortfolioManager(config.initial_cash)
        self.order_book = OrderBook()
        self.slippage_model = SlippageModel(config.slippage_bps)
        self.signal_runner = SignalRunner(config)

        # 主循环
        for i, bar in enumerate(bars):
            # 1. 标记持仓市值
            self.portfolio_manager.mark_to_market({bar.symbol: bar})

            # 2. 运行理论引擎 & 3. 信号融合 & 4. 生成订单
            orders = self.signal_runner.process_bar(
                bar, theories, self.portfolio_manager, i
            )

            # 5. 撮合
            fills = self.order_book.match_orders(bar, config.commission_rate)

            # 6. 更新持仓
            for fill in fills:
                self._apply_fill(fill, bar, orders)

            # 7. 记录权益（已在 mark_to_market 中完成）

            # 8. 进度广播（简化：每100根K线记录一次）
            if i % 100 == 0:
                progress = (i / len(bars)) * 100
                logger.info(
                    f"BacktestEventLoop: progress {progress:.1f}% ({i}/{len(bars)})"
                )

        # 平仓所有未平仓交易
        self._close_all_positions(bars[-1] if bars else None)

        # 编译结果
        result = self._compile_results(config, bars)

        logger.info(
            f"BacktestEventLoop: backtest completed, "
            f"total return: {result.total_return:.2%}, "
            f"sharpe: {result.sharpe_ratio:.2f}"
        )

        return result

    def _apply_fill(
        self,
        fill: Any,
        bar: Bar,
        orders: List[Any],
    ) -> None:
        """应用成交记录更新持仓

        Args:
            fill: 成交记录
            bar: 当前K线
            orders: 订单列表（用于查找对应的订单）
        """
        if not self.portfolio_manager:
            return

        # 找到对应的订单
        order = None
        for o in orders:
            if hasattr(o, "id") and o.id == fill.order_id:
                order = o
                break

        if not order:
            return

        # 判断是开仓还是平仓
        symbol = order.symbol
        direction = order.direction

        if not self.portfolio_manager.has_open_position(symbol):
            # 开仓
            self.portfolio_manager.open_position(
                symbol=symbol,
                direction=direction,
                price=fill.fill_price,
                quantity=fill.fill_quantity,
                commission=fill.commission,
                timestamp=fill.timestamp,
                signal_source=order.signal_source,
                theory_name=order.theory_name,
                confidence=order.confidence,
            )
        else:
            # 平仓
            self.portfolio_manager.close_position(
                symbol=symbol,
                price=fill.fill_price,
                commission=fill.commission,
                timestamp=fill.timestamp,
                exit_reason="SIGNAL",
            )

    def _close_all_positions(self, last_bar: Optional[Bar]) -> None:
        """平仓所有未平仓持仓

        Args:
            last_bar: 最后一根K线（用于确定平仓价格）
        """
        if not self.portfolio_manager or not last_bar:
            return

        open_trades = [
            t for t in self.portfolio_manager._open_trades.values()
        ]

        for trade in open_trades:
            if self.portfolio_manager:
                self.portfolio_manager.close_position(
                    symbol=trade.symbol,
                    price=last_bar.close,
                    commission=last_bar.close
                    * trade.quantity
                    * self.config.commission_rate,
                    timestamp=last_bar.timestamp,
                    exit_reason="END_OF_DATA",
                )

    def _compile_results(
        self,
        config: BacktestConfig,
        bars: List[Bar],
    ) -> BacktestResult:
        """编译回测结果

        Args:
            config: 回测配置
            bars: K线数据列表

        Returns:
            回测结果
        """
        if not self.portfolio_manager:
            return BacktestResult(config=config)

        portfolio = self.portfolio_manager.portfolio
        trades = self.portfolio_manager.get_trades()
        equity_curve = self.portfolio_manager.get_equity_curve()
        drawdown_curve = self.portfolio_manager.get_drawdown_curve()

        # 计算基础指标
        total_return = (
            (portfolio.equity - portfolio.initial_cash) / portfolio.initial_cash
            if portfolio.initial_cash > 0
            else 0
        )

        # 简化计算其他指标（完整计算在 metrics.py）
        win_trades = [t for t in trades if t.pnl and t.pnl > 0]
        win_rate = len(win_trades) / len(trades) if trades else 0

        result = BacktestResult(
            config=config,
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            trades=trades,
            max_drawdown=portfolio.max_drawdown_pct,
        )

        return result
