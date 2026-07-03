"""
Trading Bot Pro - Punto de entrada principal
Sistema de trading automatizado para Binance
"""

import asyncio
import signal
import sys
from loguru import logger

from config.config import Config
from core.exchange_connector import ExchangeConnector
from trading.trader import Trader
from notifications.notification_manager import NotificationManager
from database.db_manager import DatabaseManager
from utils.logger import setup_logger


class TradingBot:
    """Bot de trading principal"""

    def __init__(self):
        self.config = Config()
        self.running = False
        self.exchange = None
        self.trader = None
        self.notifications = None
        self.db = None

    async def initialize(self):
        """Inicializar todos los componentes del bot"""
        logger.info("Inicializando Trading Bot Pro...")

        try:
            # Validar configuracion
            self.config.validate()
            logger.info("Configuracion validada")

            # Configurar logger
            setup_logger(self.config.LOG_LEVEL, str(self.config.LOG_DIR))

            # Inicializar base de datos
            self.db = DatabaseManager(self.config.DB_PATH)
            await self.db.initialize()
            logger.info("Base de datos inicializada")

            # Conectar con exchange
            self.exchange = ExchangeConnector(self.config)
            await self.exchange.connect()
            logger.info("Conectado a Binance")

            # Verificar balance
            balance = await self.exchange.get_balance()
            usdt_balance = balance.get("USDT", 0)
            logger.info(f"Balance: {usdt_balance} USDT")

            # Inicializar notificaciones
            self.notifications = NotificationManager(self.config)
            await self.notifications.initialize()
            logger.info("Notificaciones inicializadas")

            # Enviar mensaje de inicio
            await self.notifications.send_message(
                f"🤖 Bot iniciado\n"
                f"Balance: {usdt_balance} USDT\n"
                f"Modo: {self.config.MODE}\n"
                f"Estrategia: combined\n"
                f"TP: {self.config.TAKE_PROFIT}% | SL: {self.config.STOP_LOSS}%"
            )

            # Inicializar trader
            self.trader = Trader(
                exchange=self.exchange,
                db=self.db,
                telegram=self.notifications,
                config=self.config,
            )
            logger.info("Trading engine inicializado")

            return True

        except Exception as e:
            logger.error(f"Error en inicializacion: {e}")
            return False

    async def run(self):
        """Ejecutar ciclo principal del bot"""
        self.running = True
        logger.info(f"Bot en ejecucion - Modo: {self.config.MODE}")
        logger.info(f"Intervalo de escaneo: {self.config.SCAN_INTERVAL}s")
        logger.info(f"Timeframe: {self.config.TIMEFRAME}")

        try:
            while self.running:
                self.config.reload_dynamic()
                await self.trader.run_cycle()
                await asyncio.sleep(self.config.SCAN_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Interrupcion del usuario...")
            await self.shutdown()
        except Exception as e:
            logger.error(f"Error critico: {e}")
            if self.notifications:
                await self.notifications.notify_alert(
                    f"Error critico en el bot: {e}", level="error"
                )
            await self.shutdown()

    async def shutdown(self):
        """Cerrar el bot de forma limpia"""
        logger.info("Cerrando Trading Bot...")
        self.running = False

        # Cerrar posiciones si es necesario
        if self.trader:
            await self.trader.close_all_positions()

        # Notificar cierre
        if self.notifications:
            await self.notifications.send_message("Bot detenido")
            await self.notifications.stop()

        # Cerrar conexiones
        if self.exchange:
            await self.exchange.close()

        if self.db:
            await self.db.close()

        logger.info("Bot cerrado correctamente")


async def main():
    """Funcion principal"""
    bot = TradingBot()

    # Manejar senales de sistema
    def signal_handler(sig, frame):
        logger.info("Senal de cierre recibida...")
        bot.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Inicializar y ejecutar
    if await bot.initialize():
        await bot.run()
    else:
        logger.error("Fallo la inicializacion del bot")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
