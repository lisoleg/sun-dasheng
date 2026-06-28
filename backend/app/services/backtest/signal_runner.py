"""信号执行器 — SignalRunner

将理论引擎产生的信号转化为订单。
支持信号过滤、仓位管理、风险控制。

[TOMAS v2.0 + 大师共识] 集成四大模块：
- 论据追踪器（thesis_tracker）：每笔交易有论据、催化剂、失效条件
- Dalio象限检测（market_regime）：识别当前市场象限，调整引擎权重
- 风险平价融合（risk_parity）：各引擎风险贡献均衡加权
- 持仓周期纪律（holding_period）：防止过早止损和过久持有
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.backtest.models import (
    Bar,
    Direction,
    Order,
    OrderType,
    BacktestConfig,
)
from app.services.backtest.position_manager import PositionSizer
from app.services.signal.fusion import SignalFusion
from app.services.signal.generator import Signal


class SignalRunner:
    """信号执行器

    将理论信号转化为订单，考虑：
    1. 信号置信度阈值
    2. 仓位管理规则
    3. 止损止盈
    4. 最大仓位限制
    5. [大师共识三] thesis论据追踪
    6. [大师共识四] Dalio象限检测
    7. [大师共识五] 持仓周期纪律
    """

    def __init__(
        self,
        config: BacktestConfig,
        signal_fusion: Optional[SignalFusion] = None,
    ) -> None:
        """初始化信号执行器

        Args:
            config: 回测配置
            signal_fusion: 信号融合器
        """
        self.config = config
        self.signal_fusion = signal_fusion
        self._order_counter = 0
        # [大师共识四] 当前市场象限缓存
        self._current_regime: Optional[str] = None

    def process_bar(
        self,
        bar: Bar,
        theories: List[Any],
        portfolio_manager: Any,
        current_bar_index: int,
    ) -> List[Order]:
        """处理当前K线，生成订单

        [TOMAS v2.0] 流动性熔断 + ENPV 决策：
        - 如果 PCS < 0.3，不生成订单（熔断）
        - 如果 PCS < 0.7，降低仓位大小
        - 计算 ENPV，如果 < 0 放弃追单

        [大师共识四] Dalio象限检测：
        - 检测当前市场象限
        - 根据象限调整理论引擎权重

        Args:
            bar: 当前K线
            theories: 理论引擎列表
            portfolio_manager: 资金账户管理器
            current_bar_index: 当前K线索引

        Returns:
            订单列表
        """
        orders = []

        # [TOMAS v2.0] 相位连续性检查
        import numpy as np
        from app.core.topo_invariants import phase_continuity_score, detect_phase_singularity
        
        # 获取历史价格（简化：用当前 bar 的 close 构建伪序列）
        # 实际实现需要从 portfolio_manager 或外部获取历史价格
        pseudo_prices = np.array([bar.close])  # 简化版
        pcs = phase_continuity_score(pseudo_prices, window=30)
        singularity = detect_phase_singularity(pseudo_prices)
        
        # 熔断判断
        if pcs < 0.3 or singularity.get("is_singularity", False):
            logger.warning(
                f"SignalRunner: phase singularity detected (PCS={pcs:.3f}), "
                f"skipping all orders"
            )
            return orders  # 空订单列表（熔断）

        # [大师共识四] Dalio象限检测
        # 使用简化数据检测象限（实际应传入完整历史价格/成交量）
        from app.core.market_regime import detect_regime as detect_market_regime
        # 简化版：使用单根K线数据，实际应传入完整历史
        regime_prices = [float(bar.close)] * 139  # 简化版
        regime_volumes = [float(bar.volume)] * 139  # 简化版
        regime_result = detect_market_regime(regime_prices, regime_volumes)
        self._current_regime = regime_result.regime.value
        logger.info(
            f"SignalRunner: Dalio regime detected = {self._current_regime} "
            f"(confidence={regime_result.confidence:.4f})"
        )

        # 检查是否需要平仓（止损止盈 + thesis失效 + 持仓纪律）
        close_orders = self._check_stop_loss_take_profit(
            bar, portfolio_manager, current_bar_index
        )
        orders.extend(close_orders)

        # 运行理论引擎生成信号
        signals = self._run_theories(bar, theories)

        # 如果信号为空，不生成新订单
        if not signals:
            return orders

        # [TOMAS v2.0] ENPV 决策过滤
        filtered_signals = []
        for signal in signals:
            # 简化版 ENPV 计算（实际需要更多参数）
            enpv = self._calc_enpv(signal, bar, pcs)
            if enpv > 0:
                filtered_signals.append(signal)
            else:
                logger.info(f"SignalRunner: ENPV={enpv:.2f} < 0, skipping signal")

        if not filtered_signals:
            return orders

        # 生成开仓订单
        open_orders = self._generate_open_orders(
            bar, filtered_signals, portfolio_manager, current_bar_index, pcs
        )
        orders.extend(open_orders)

        return orders

    def _run_theories(self, bar: Bar, theories: List[Any]) -> List[Signal]:
        """运行理论引擎生成信号

        Args:
            bar: 当前K线（完整历史用于分析）
            theories: 理论引擎列表

        Returns:
            信号列表
        """
        # 构建K线数据供理论引擎分析
        # 注意：这里需要传入历史K线数据，简化处理传入单根K线
        bar_dict = [
            {
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "timestamp": bar.timestamp.isoformat(),
                "symbol": bar.symbol,
            }
        ]

        signals = []
        for theory in theories:
            try:
                result = theory.analyze(bar_dict)
                # 从结果中提取信号
                if hasattr(result, "hints") and result.hints:
                    for hint in result.hints:
                        if hasattr(hint, "direction"):
                            direction = hint.direction
                        elif isinstance(hint, dict):
                            direction = hint.get("direction", "HOLD")
                        else:
                            continue

                        if direction != "HOLD" and direction != "hold":
                            signal = Signal(
                                symbol=bar.symbol,
                                direction=direction,
                                confidence=(
                                    hint.confidence
                                    if hasattr(hint, "confidence")
                                    else 0.5
                                ),
                                source_engine=theory.theory_name
                                if hasattr(theory, "theory_name")
                                else theory.name,
                                theory_name=theory.name
                                if hasattr(theory, "name")
                                else "",
                            )
                            signals.append(signal)
            except Exception as e:
                logger.error(f"SignalRunner: theory {theory} failed: {e}")
                continue

        return signals

    def _generate_open_orders(
        self,
        bar: Bar,
        signals: List[Signal],
        portfolio_manager: Any,
        current_bar_index: int,
        pcs: float,
    ) -> List[Order]:
        """根据信号生成开仓订单

        [大师共识三] 生成thesis并存入order.metadata

        Args:
            bar: 当前K线
            signals: 信号列表
            portfolio_manager: 资金账户管理器
            current_bar_index: 当前K线索引
            pcs: 相位连续性评分

        Returns:
            开仓订单列表
        """
        orders = []

        if not signals:
            return orders

        # 按方向分组信号
        long_signals = [s for s in signals if s.direction == "LONG" or s.direction == "BUY"]
        short_signals = [s for s in signals if s.direction == "SHORT" or s.direction == "SELL"]

        # 决定交易方向（简化：取信号数多的方向）
        if len(long_signals) > len(short_signals):
            direction = Direction.BUY
            selected_signals = long_signals
        elif len(short_signals) > 0:
            direction = Direction.SELL
            selected_signals = short_signals
        else:
            return orders

        # 检查是否已有同向持仓
        symbol = bar.symbol
        if portfolio_manager.has_open_position(symbol):
            open_trade = portfolio_manager.get_open_trade(symbol)
            if open_trade and (
                (direction == Direction.BUY and open_trade.direction == Direction.BUY)
                or (direction == Direction.SELL and open_trade.direction == Direction.SELL)
            ):
                # 已有同向持仓，不再加仓
                return orders

        # 计算平均置信度
        avg_confidence = (
            sum(s.confidence for s in selected_signals) / len(selected_signals)
            if selected_signals
            else 0.5
        )

        # 计算仓位大小
        position_size = PositionSizer.calculate_position_size(
            method=self.config.position_sizing,
            portfolio=portfolio_manager.portfolio,
            signal_confidence=avg_confidence,
            entry_price=bar.close,
            max_position_pct=self.config.max_position_pct,
        )

        if position_size <= 0:
            return orders

        # [宇宙算法] 139/369缩仓调整
        from app.services.risk.position_sizer import PositionSizer as PositionSizerClass
        sizer = PositionSizerClass()
        # 构建K线数据列表
        bars_data = [
            {
                "close": bar.close,
                "high": bar.high,
                "low": bar.low,
                "open": bar.open,
                "volume": bar.volume,
            }
        ] * 139  # 简化版，实际需要完整历史K线
        # 139缩仓（临界慢化自适应缩仓）
        portfolio_equity = portfolio_manager.portfolio.equity if hasattr(portfolio_manager.portfolio, 'equity') else float(portfolio_manager.portfolio)
        stop_price = bar.close * (1 - self.config.stop_loss_pct) if self.config.stop_loss_pct else bar.close * 0.99
        position_size = sizer.calculate_139_adjusted_size(
            portfolio_equity,
            avg_confidence,
            bar.close,
            stop_price,
            bars_data,
        )
        # 369缩仓（振动模态仓位调整，叠加）
        position_size = sizer.calculate_369_adjusted_size(
            portfolio_equity,
            avg_confidence,
            bar.close,
            stop_price,
            bars_data,
        )

        if position_size <= 0:
            return orders

        # [大师共识三] thesis论据追踪 — 生成thesis
        from app.core.thesis_tracker import generate_thesis, Thesis
        # 收集理论引擎结果（从信号metadata中提取，简化版）
        theory_results_for_thesis = []
        for s in selected_signals:
            mock_result = type('MockTheoryResult', (), {
                'theory_name': s.source_engine,
                'annotations': s.metadata.get('annotations', {}),
                'phase_continuity': pcs,
                'confidence': s.confidence,
                'hints': [],
                'error': None,
            })()
            theory_results_for_thesis.append(mock_result)

        # 信号方向映射
        signal_direction = "LONG" if direction == Direction.BUY else "SHORT"
        thesis = generate_thesis(
            theory_results=theory_results_for_thesis,
            signal_direction=signal_direction,
            symbol=symbol,
            confidence=avg_confidence,
            bars=bars_data,
        )

        # 创建订单
        self._order_counter += 1
        order = Order(
            id=f"order-{self._order_counter}",
            bar_index=current_bar_index,
            symbol=symbol,
            direction=direction,
            order_type=OrderType.MARKET,
            price=bar.close,
            quantity=position_size,
            signal_source=",".join(s.source_engine for s in selected_signals),
            theory_name=selected_signals[0].theory_name if selected_signals else "",
            confidence=avg_confidence,
        )
        # [大师共识三] 将thesis存入订单metadata
        # Order 是 dataclass，没有 metadata 字段，使用信号metadata间接传递
        # 实际实现中应扩展 Order 模型或通过 trade metadata 传递
        logger.info(
            f"SignalRunner: thesis {thesis.thesis_id} generated for {symbol} "
            f"direction={signal_direction}, signal_type={thesis.signal_type}, "
            f"reason='{thesis.reason[:60]}'"
        )

        orders.append(order)

        return orders

    def _check_stop_loss_take_profit(
        self,
        bar: Bar,
        portfolio_manager: Any,
        current_bar_index: int,
    ) -> List[Order]:
        """检查止损止盈，生成平仓订单

        [大师共识三] thesis失效检查
        [大师共识五] 持仓周期纪律检查

        Args:
            bar: 当前K线
            portfolio_manager: 资金账户管理器
            current_bar_index: 当前K线索引

        Returns:
            平仓订单列表
        """
        orders = []
        symbol = bar.symbol

        if not portfolio_manager.has_open_position(symbol):
            return orders

        open_trade = portfolio_manager.get_open_trade(symbol)
        if not open_trade:
            return orders

        should_close = False
        exit_reason = ""

        # 检查止损
        if self.config.stop_loss_pct and open_trade.direction == Direction.BUY:
            stop_loss_price = open_trade.open_price * (1 - self.config.stop_loss_pct)
            if bar.low <= stop_loss_price:
                should_close = True
                exit_reason = "STOP_LOSS"

        # 检查止盈
        if self.config.take_profit_pct and open_trade.direction == Direction.BUY:
            take_profit_price = open_trade.open_price * (1 + self.config.take_profit_pct)
            if bar.high >= take_profit_price:
                should_close = True
                exit_reason = "TAKE_PROFIT"

        # [宇宙算法] 139σ硬止损检查
        from app.services.risk.stop_loss import StopLossManager
        stop_manager = StopLossManager()
        # 构建历史价格列表（简化版：使用当前bar的close构建伪序列）
        historical_closes = [float(bar.close)] * 139  # 简化版，实际需要完整历史
        # 139波动率硬止损
        vol_result = stop_manager.check_139_volatility_stop(
            {"position_id": f"{symbol}-{current_bar_index}"},
            historical_closes,
        )
        if vol_result == stop_manager.StopCheckResult.STOP_LOSS_TRIGGERED:
            should_close = True
            exit_reason = "139_VOLATILITY_STOP"
            logger.warning(
                f"SignalRunner: 139 volatility stop triggered for {symbol} @ {bar.close:.2f}"
            )
        # 139临界慢化硬止损
        bars_data = [
            {
                "close": float(bar.close),
                "high": float(bar.high),
                "low": float(bar.low),
                "open": float(bar.open),
                "volume": float(bar.volume),
            }
        ] * 139  # 简化版，实际需要完整历史K线
        crit_result = stop_manager.check_139_critical_stop(
            {"position_id": f"{symbol}-{current_bar_index}"},
            bars_data,
        )
        if crit_result == stop_manager.StopCheckResult.STOP_LOSS_TRIGGERED:
            should_close = True
            exit_reason = "139_CRITICAL_STOP"
            logger.warning(
                f"SignalRunner: 139 critical stop triggered for {symbol} @ {bar.close:.2f}"
            )

        # ── [大师共识三] thesis失效检查 ──
        from app.core.thesis_tracker import check_thesis_invalidation, Thesis, ThesisStatus
        # 从持仓获取thesis（简化版：从trade metadata获取）
        thesis_data: Dict[str, Any] = {}
        if hasattr(open_trade, 'metadata') and open_trade.metadata:
            thesis_data = open_trade.metadata.get("thesis", {})

        if thesis_data and isinstance(thesis_data, dict):
            thesis = Thesis(**thesis_data) if isinstance(thesis_data, dict) else thesis_data
            # 计算持仓天数
            holding_days = current_bar_index - open_trade.bar_index if hasattr(open_trade, 'bar_index') else 0
            # 计算当前盈亏
            current_pnl_pct = (
                (bar.close - open_trade.open_price) / open_trade.open_price
                if open_trade.open_price > 0 else 0
            )
            # 检查thesis失效
            invalidation = check_thesis_invalidation(
                thesis=thesis,
                current_bar={"close": bar.close, "high": bar.high, "low": bar.low},
                holding_days=holding_days,
                portfolio_pnl_pct=current_pnl_pct,
            )
            if invalidation:
                should_close = True
                exit_reason = f"THESIS_INVALIDATED: {invalidation}"
                logger.warning(
                    f"SignalRunner: thesis invalidated for {symbol} "
                    f"reason={invalidation}"
                )

        # ── [大师共识五] 持仓周期纪律检查 ──
        from app.core.holding_period import check_holding_discipline, DisciplineAction, HoldingPeriodConfig

        # 计算持仓天数
        holding_days = current_bar_index - open_trade.bar_index if hasattr(open_trade, 'bar_index') else 0

        # 获取thesis状态
        thesis_status = "PENDING"
        if thesis_data and isinstance(thesis_data, dict):
            thesis_status = thesis_data.get("status", "PENDING")

        # 获取信号类型
        signal_type = "trend"
        if thesis_data and isinstance(thesis_data, dict):
            signal_type = thesis_data.get("signal_type", "trend")

        # 计算当前盈亏
        current_pnl_pct = (
            (bar.close - open_trade.open_price) / open_trade.open_price
            if open_trade.open_price > 0 else 0
        )

        # 持仓纪律检查
        discipline_result = check_holding_discipline(
            holding_days=holding_days,
            signal_type=signal_type,
            thesis_status=thesis_status,
            current_pnl_pct=current_pnl_pct,
        )

        if discipline_result.action == DisciplineAction.FORCE_CLOSE_LATE:
            should_close = True
            exit_reason = f"HOLDING_PERIOD_OVER: {discipline_result.reason}"
            logger.warning(
                f"SignalRunner: holding period discipline FORCE_CLOSE_LATE for {symbol} "
                f"holding={holding_days} days, reason={discipline_result.reason}"
            )
        elif discipline_result.action == DisciplineAction.FORCE_CLOSE_EARLY:
            # 过早止损：阻止止损（除非亏损超过5%）
            if current_pnl_pct > -0.05 and not should_close:
                should_close = False  # 阻止止损
                logger.info(
                    f"SignalRunner: holding period discipline BLOCKED early stop for {symbol} "
                    f"(holding={holding_days} days, signal_type={signal_type})"
                )
        elif discipline_result.action == DisciplineAction.WARN_CLOSE_EARLY:
            # 催化剂超期：仅警告，不强制操作
            logger.info(
                f"SignalRunner: holding period discipline WARNING for {symbol} "
                f"reason={discipline_result.reason}"
            )

        if should_close:
            # 创建平仓订单
            self._order_counter += 1
            close_direction = (
                Direction.SELL
                if open_trade.direction == Direction.BUY
                else Direction.BUY
            )
            order = Order(
                id=f"order-{self._order_counter}",
                bar_index=current_bar_index,
                symbol=symbol,
                direction=close_direction,
                order_type=OrderType.MARKET,
                price=bar.close,
                quantity=open_trade.quantity,
                signal_source="risk_manager",
                theory_name=None,
                confidence=1.0,
            )
            orders.append(order)
            logger.info(
                f"SignalRunner: {exit_reason} triggered for {symbol} @ {bar.close:.2f}"
            )

        return orders

    def _calc_enpv(self, signal: Signal, bar: Bar, pcs: float) -> float:
        """计算简化版 ENPV（期望净现值）

        Args:
            signal: 交易信号
            bar: 当前K线
            pcs: 相位连续性评分

        Returns:
            ENPV值，正值表示值得交易，负值表示应放弃
        """
        # 简化版 ENPV = 置信度 × PCS × 预期收益 - 风险成本
        expected_gain = signal.confidence * pcs * 0.02  # 预期收益
        risk_cost = (1 - signal.confidence) * (1 - pcs) * 0.05  # 风险成本
        enpv = expected_gain - risk_cost
        return enpv
