"""
Motor principal de trading
Ciclo principal que escanea mercado, analiza y ejecuta operaciones
"""

import asyncio
from datetime import datetime, timezone
from loguru import logger

from core.exchange_connector import ExchangeConnector
from core.market_data import MarketData
from analysis.technical_indicators import TechnicalIndicators
from analysis.market_scanner import MarketScanner
from strategies.strategy_manager import StrategyManager
from trading.position_tracker import PositionTracker
from trading.execution_engine import ExecutionEngine
from risk_management.portfolio_manager import PortfolioManager
from database.db_manager import DatabaseManager
from config.config import Config


class Trader:
    """Motor principal de trading - Coordina todo el sistema"""

    def __init__(self, exchange: ExchangeConnector, db: DatabaseManager,
                 telegram=None, config: Config = None):
        self.config = config or Config()
        self.exchange = exchange
        self.db = db
        self.telegram = telegram

        # Componentes
        self.market_data = MarketData(exchange)
        self.scanner = MarketScanner(self.market_data)
        self.strategy_manager = StrategyManager()
        self.position_tracker = PositionTracker(exchange, db, self.config)
        self.execution_engine = ExecutionEngine(exchange, db, self.config)
        self.portfolio_manager = PortfolioManager(self.config, db)

        # Estado
        self.cycle_count = 0
        self.paper_balance = self.config.INITIAL_CAPITAL

    async def run_cycle(self):
        """Ejecutar un ciclo completo de trading"""
        self.cycle_count += 1
        logger.debug(f"--- Ciclo #{self.cycle_count} ---")

        try:
            # 1. Verificar si el bot puede operar
            if not self.portfolio_manager.can_trade():
                logger.debug("Bot pausado, saltando ciclo")
                return

            # 2. Obtener balance disponible
            available_balance = await self._get_available_balance()

            # 3. Monitorear posiciones abiertas (TP/SL)
            await self._monitor_positions()

            # 4. Buscar nuevas oportunidades
            await self._scan_and_trade(available_balance)

            # 5. Actualizar metricas periodicamente
            if self.cycle_count % 12 == 0:  # Cada ~60 segundos
                await self._update_metrics()

        except Exception as e:
            logger.error(f"Error en ciclo de trading #{self.cycle_count}: {e}")
            self.db.save_log("error", f"Error en ciclo: {e}", "trader")

    async def _get_available_balance(self) -> float:
        """Obtener balance disponible para trading"""
        if self.config.is_paper_mode():
            # En paper mode, calcular balance simulado
            open_trades = self.db.get_open_trades()
            invested = sum(t.investment for t in open_trades)
            closed_pnl = sum(t.pnl for t in self.db.get_closed_trades(1000))
            self.paper_balance = self.config.INITIAL_CAPITAL + closed_pnl - invested
            return max(self.paper_balance, 0)
        else:
            balance = await self.exchange.get_balance()
            return balance.get("USDT", 0)

    async def _monitor_positions(self):
        """Monitorear posiciones abiertas y ejecutar TP/SL"""
        exits = await self.position_tracker.check_exits()

        for exit_info in exits:
            trade = exit_info["trade"]
            reason = exit_info["reason"]

            closed = await self.execution_engine.execute_sell_signal(trade, reason)
            if closed and self.telegram:
                try:
                    from utils.formatters import Formatters
                    msg = Formatters.format_sell_message({
                        "symbol": closed.symbol,
                        "entry_price": closed.entry_price,
                        "exit_price": closed.exit_price,
                        "pnl": closed.pnl,
                        "pnl_percentage": closed.pnl_percentage,
                        "exit_reason": reason,
                    })
                    await self.telegram.send_message(msg)
                except Exception as e:
                    logger.error(f"Error enviando notificacion de venta: {e}")

    async def _scan_and_trade(self, available_balance: float):
        """Escanear mercado y ejecutar trades si hay oportunidades"""
        # Verificar si podemos abrir mas posiciones
        open_trades = self.db.get_open_trades()
        if len(open_trades) >= self.config.MAX_POSITIONS:
            logger.debug("Limite de posiciones alcanzado, no se buscan nuevas oportunidades")
            return

        # Escanear mercado
        opportunities = await self.scanner.scan_market(self.config.TIMEFRAME)

        for opp in opportunities:
            # Verificar de nuevo los limites (pudimos haber abierto una posicion)
            open_trades = self.db.get_open_trades()
            if len(open_trades) >= self.config.MAX_POSITIONS:
                break

            # Verificar que no tenemos posicion en este par
            existing = self.db.get_trade_by_symbol(opp["symbol"])
            if existing:
                continue

            # Ejecutar compra
            signal = {"action": "buy", "score": opp["score"], "reason": "Scanner"}
            trade = await self.execution_engine.execute_buy_signal(
                symbol=opp["symbol"],
                signal=signal,
                available_balance=available_balance,
                strategy=self.strategy_manager.active_strategy,
            )

            if trade and self.telegram:
                try:
                    from utils.formatters import Formatters
                    msg = Formatters.format_trade_message({
                        "symbol": trade.symbol,
                        "side": "buy",
                        "price": trade.entry_price,
                        "quantity": trade.quantity,
                        "investment": trade.investment,
                        "stop_loss": trade.stop_loss,
                        "take_profit": trade.take_profit,
                    })
                    await self.telegram.send_message(msg)
                except Exception as e:
                    logger.error(f"Error enviando notificacion de compra: {e}")

                # Actualizar balance disponible
                available_balance -= trade.investment

    async def _update_metrics(self):
        """Actualizar metricas y guardar snapshot de balance"""
        try:
            balance = await self._get_available_balance()
            open_trades = self.db.get_open_trades()

            # Agregar valor de posiciones abiertas
            total_value = balance
            for trade in open_trades:
                ticker = await self.exchange.fetch_ticker(trade.symbol)
                current_price = ticker.get("last", 0)
                if current_price > 0:
                    total_value += trade.quantity * current_price

            daily_pnl = self.db.get_daily_pnl()
            daily_pnl_pct = self.db.get_daily_pnl_percentage(self.config.INITIAL_CAPITAL)
            total_pnl = total_value - self.config.INITIAL_CAPITAL

            self.db.save_balance_snapshot(
                balance=total_value,
                positions_count=len(open_trades),
                daily_pnl=daily_pnl,
                daily_pnl_pct=daily_pnl_pct,
                total_pnl=total_pnl,
            )

        except Exception as e:
            logger.error(f"Error actualizando metricas: {e}")

    async def close_all_positions(self):
        """Cerrar todas las posiciones abiertas"""
        logger.info("Cerrando todas las posiciones...")
        closed = await self.execution_engine.close_all()

        if self.telegram and closed:
            total_pnl = sum(t.pnl for t in closed)
            msg = f"Cerradas {len(closed)} posiciones. PnL total: ${total_pnl:.4f}"
            try:
                await self.telegram.send_message(msg)
            except Exception:
                pass

        return closed

    def get_status(self) -> dict:
        """Obtener estado actual del trader"""
        return {
            "running": True,
            "cycle_count": self.cycle_count,
            "strategy": self.strategy_manager.active_strategy,
            "paused": self.portfolio_manager.paused,
            "mode": self.config.MODE,
        }
