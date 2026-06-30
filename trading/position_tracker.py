"""
Seguimiento de posiciones abiertas
Monitorea precios actuales y calcula P&L en tiempo real
"""

from typing import List, Optional
from loguru import logger

from core.exchange_connector import ExchangeConnector
from database.db_manager import DatabaseManager
from database.models import Trade
from risk_management.stop_loss_manager import StopLossManager
from risk_management.take_profit_manager import TakeProfitManager
from config.config import Config


class PositionTracker:
    """Rastrear y monitorear posiciones abiertas"""

    def __init__(self, exchange: ExchangeConnector, db: DatabaseManager, config: Config):
        self.exchange = exchange
        self.db = db
        self.config = config
        self.sl_manager = StopLossManager(config)
        self.tp_manager = TakeProfitManager(config)

    async def get_positions_with_pnl(self) -> List[dict]:
        """Obtener posiciones abiertas con P&L actual"""
        open_trades = self.db.get_open_trades()
        positions = []

        for trade in open_trades:
            try:
                ticker = await self.exchange.fetch_ticker(trade.symbol)
                current_price = ticker.get("last", 0)

                if current_price > 0:
                    pnl = (current_price - trade.entry_price) * trade.quantity
                    pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                    current_value = trade.quantity * current_price
                else:
                    pnl = 0
                    pnl_pct = 0
                    current_value = trade.investment

                positions.append({
                    "trade": trade,
                    "current_price": current_price,
                    "pnl": pnl,
                    "pnl_percentage": pnl_pct,
                    "current_value": current_value,
                    "distance_to_tp": ((trade.take_profit - current_price) / current_price * 100) if trade.take_profit else 0,
                    "distance_to_sl": ((current_price - trade.stop_loss) / current_price * 100) if trade.stop_loss else 0,
                })

            except Exception as e:
                logger.error(f"Error rastreando {trade.symbol}: {e}")

        return positions

    async def check_exits(self) -> List[dict]:
        """Verificar si alguna posicion debe cerrarse por TP/SL"""
        exits = []
        open_trades = self.db.get_open_trades()

        for trade in open_trades:
            try:
                ticker = await self.exchange.fetch_ticker(trade.symbol)
                current_price = ticker.get("last", 0)
                if current_price <= 0:
                    continue

                # Verificar Take Profit
                if self.tp_manager.should_trigger_take_profit(trade, current_price):
                    exits.append({
                        "trade": trade,
                        "reason": "tp",
                        "current_price": current_price,
                    })
                    continue

                # Verificar Stop Loss
                if self.sl_manager.should_trigger_stop_loss(trade, current_price):
                    exits.append({
                        "trade": trade,
                        "reason": "sl",
                        "current_price": current_price,
                    })
                    continue

                # Actualizar trailing stop si esta configurado
                new_sl = self.sl_manager.update_trailing_stop(trade, current_price)
                if new_sl != trade.stop_loss:
                    self.db.update_trade(trade.trade_id, stop_loss=new_sl)

            except Exception as e:
                logger.error(f"Error verificando exits para {trade.symbol}: {e}")

        return exits

    def get_total_exposure(self) -> float:
        """Calcular exposicion total en USDT"""
        open_trades = self.db.get_open_trades()
        return sum(t.investment for t in open_trades)
