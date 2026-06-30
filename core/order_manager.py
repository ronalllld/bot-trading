"""
Gestion y ejecucion de ordenes de trading
Capa intermedia entre estrategias y el exchange
"""

from typing import Optional
from datetime import datetime, timezone
from loguru import logger

from core.exchange_connector import ExchangeConnector
from config.config import Config
from config.exchange_config import ExchangeConfig
from database.db_manager import DatabaseManager
from database.models import Trade
from utils.helpers import Helpers
from utils.validators import Validators


class OrderManager:
    """Gestionar la ejecucion de ordenes"""

    def __init__(self, exchange: ExchangeConnector, db: DatabaseManager, config: Config):
        self.exchange = exchange
        self.db = db
        self.config = config

    async def execute_buy(self, symbol: str, amount_usdt: float,
                          strategy: str = "combined") -> Optional[Trade]:
        """Ejecutar orden de compra"""
        try:
            # Validaciones previas
            if not self._validate_buy(symbol, amount_usdt):
                return None

            # Obtener precio actual
            ticker = await self.exchange.fetch_ticker(symbol)
            price = ticker.get("last", 0)
            if price <= 0:
                logger.error(f"Precio invalido para {symbol}: {price}")
                return None

            # Calcular cantidad de crypto a comprar
            quantity = amount_usdt / price

            # Verificar minimos del exchange
            market_info = await self.exchange.get_market_info(symbol)
            min_amount = market_info.get("min_amount", 0)
            if min_amount and quantity < min_amount:
                logger.warning(f"Cantidad {quantity} menor al minimo {min_amount} para {symbol}")
                return None

            # Ejecutar orden
            order = await self.exchange.create_market_order(symbol, "buy", quantity)
            if not order:
                logger.error(f"Fallo al ejecutar orden de compra para {symbol}")
                return None

            # Precio real de ejecucion
            fill_price = order.get("price", price)
            fill_amount = order.get("filled", quantity)

            # Calcular niveles de TP/SL
            take_profit_price = fill_price * (1 + self.config.TAKE_PROFIT / 100)
            stop_loss_price = fill_price * (1 - self.config.STOP_LOSS / 100)

            # Crear registro en BD
            trade = Trade(
                trade_id=Helpers.generate_trade_id(symbol, "buy", datetime.now(timezone.utc)),
                symbol=symbol,
                side="buy",
                entry_price=fill_price,
                quantity=fill_amount,
                investment=amount_usdt,
                strategy=strategy,
                status="open",
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                exchange_order_id=order.get("id", ""),
            )

            saved_trade = self.db.save_trade(trade)
            logger.info(
                f"TRADE COMPRA: {symbol} @ ${fill_price:.4f} | "
                f"Qty: {fill_amount:.8f} | Inv: ${amount_usdt:.2f} | "
                f"TP: ${take_profit_price:.4f} | SL: ${stop_loss_price:.4f}"
            )
            return saved_trade

        except Exception as e:
            logger.error(f"Error ejecutando compra de {symbol}: {e}")
            return None

    async def execute_sell(self, trade: Trade, exit_reason: str = "manual") -> Optional[Trade]:
        """Ejecutar orden de venta para cerrar una posicion"""
        try:
            symbol = trade.symbol
            quantity = trade.quantity

            # Ejecutar orden de venta
            order = await self.exchange.create_market_order(symbol, "sell", quantity)
            if not order:
                logger.error(f"Fallo al ejecutar venta de {symbol}")
                return None

            exit_price = order.get("price", 0)
            if exit_price <= 0:
                ticker = await self.exchange.fetch_ticker(symbol)
                exit_price = ticker.get("last", 0)

            # Cerrar trade en BD
            closed_trade = self.db.close_trade(trade.trade_id, exit_price, exit_reason)
            if closed_trade:
                logger.info(
                    f"TRADE VENTA ({exit_reason}): {symbol} @ ${exit_price:.4f} | "
                    f"PnL: ${closed_trade.pnl:.4f} ({closed_trade.pnl_percentage:.2f}%)"
                )
            return closed_trade

        except Exception as e:
            logger.error(f"Error ejecutando venta de {trade.symbol}: {e}")
            return None

    def _validate_buy(self, symbol: str, amount_usdt: float) -> bool:
        """Validar todas las condiciones antes de comprar"""
        if not Validators.validate_symbol(symbol, ExchangeConfig.ALLOWED_PAIRS):
            return False

        if not Validators.validate_order_size(amount_usdt, ExchangeConfig.MIN_ORDER_USDT):
            return False

        open_trades = self.db.get_open_trades()
        if not Validators.validate_positions_limit(len(open_trades), self.config.MAX_POSITIONS):
            return False

        existing = self.db.get_trade_by_symbol(symbol)
        if existing:
            logger.warning(f"Ya existe posicion abierta en {symbol}")
            return False

        daily_count = self.db.count_daily_trades()
        if not Validators.validate_daily_trades(daily_count, self.config.MAX_DAILY_TRADES):
            return False

        daily_pnl_pct = self.db.get_daily_pnl_percentage(self.config.INITIAL_CAPITAL)
        if not Validators.validate_daily_loss(daily_pnl_pct, self.config.MAX_DAILY_LOSS):
            return False

        return True

    async def close_all_positions(self) -> list:
        """Cerrar todas las posiciones abiertas"""
        open_trades = self.db.get_open_trades()
        closed = []

        for trade in open_trades:
            result = await self.execute_sell(trade, exit_reason="manual")
            if result:
                closed.append(result)

        logger.info(f"Cerradas {len(closed)}/{len(open_trades)} posiciones")
        return closed
