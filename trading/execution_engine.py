"""
Motor de ejecucion de ordenes
Coordina la ejecucion de compras y ventas con validaciones
"""

from typing import Optional
from loguru import logger

from core.exchange_connector import ExchangeConnector
from core.order_manager import OrderManager
from database.db_manager import DatabaseManager
from database.models import Trade
from risk_management.position_sizer import PositionSizer
from config.config import Config


class ExecutionEngine:
    """Motor de ejecucion de ordenes con validaciones completas"""

    def __init__(self, exchange: ExchangeConnector, db: DatabaseManager, config: Config):
        self.exchange = exchange
        self.db = db
        self.config = config
        self.order_manager = OrderManager(exchange, db, config)
        self.position_sizer = PositionSizer(config)

    async def execute_buy_signal(self, symbol: str, signal: dict,
                                  available_balance: float,
                                  strategy: str = "combined") -> Optional[Trade]:
        """Ejecutar senal de compra con todas las validaciones"""
        try:
            # Verificar que el bot puede operar
            score = signal.get("score", 0)
            action = signal.get("action", "hold")

            if action != "buy":
                return None

            logger.info(
                f"Procesando senal BUY para {symbol} - Score: {score:.2f} - "
                f"Razon: {signal.get('reason', 'N/A')}"
            )

            # Obtener precio actual
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker.get("last", 0)
            if current_price <= 0:
                logger.error(f"No se pudo obtener precio de {symbol}")
                return None

            # Calcular tamano de posicion
            position = self.position_sizer.calculate_position_size(
                available_balance, current_price
            )

            if not position["valid"]:
                logger.warning(f"Posicion no valida: {position.get('reason')}")
                return None

            # Ejecutar compra
            trade = await self.order_manager.execute_buy(
                symbol=symbol,
                amount_usdt=position["amount_usdt"],
                strategy=strategy,
            )

            return trade

        except Exception as e:
            logger.error(f"Error en execute_buy_signal para {symbol}: {e}")
            return None

    async def execute_sell_signal(self, trade: Trade,
                                   reason: str = "signal") -> Optional[Trade]:
        """Ejecutar senal de venta"""
        try:
            logger.info(f"Ejecutando venta de {trade.symbol} - Razon: {reason}")
            return await self.order_manager.execute_sell(trade, exit_reason=reason)
        except Exception as e:
            logger.error(f"Error en execute_sell_signal para {trade.symbol}: {e}")
            return None

    async def close_all(self) -> list:
        """Cerrar todas las posiciones abiertas"""
        return await self.order_manager.close_all_positions()
