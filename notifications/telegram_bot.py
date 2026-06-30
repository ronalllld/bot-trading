"""
Bot de notificaciones Telegram
Envia alertas de trades, resumen diario y alertas del sistema
"""

import asyncio
from loguru import logger

try:
    from telegram import Bot
    from telegram.error import TelegramError
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False


class TelegramBot:
    """Bot de Telegram para notificaciones de trading"""

    def __init__(self, config):
        self.config = config
        self.bot = None
        self.enabled = False
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.token = config.TELEGRAM_BOT_TOKEN

    async def start(self):
        """Inicializar bot de Telegram"""
        if not HAS_TELEGRAM:
            logger.warning("python-telegram-bot no instalado, notificaciones deshabilitadas")
            return

        if not self.token or not self.chat_id:
            logger.warning("Telegram no configurado (falta token o chat_id)")
            return

        try:
            self.bot = Bot(token=self.token)
            # Verificar conexion
            me = await self.bot.get_me()
            self.enabled = True
            logger.info(f"Telegram bot conectado: @{me.username}")
        except Exception as e:
            logger.error(f"Error conectando Telegram bot: {e}")
            self.enabled = False

    async def send_message(self, message: str):
        """Enviar mensaje al chat configurado"""
        if not self.enabled or not self.bot:
            logger.debug(f"Telegram deshabilitado, mensaje no enviado: {message[:50]}...")
            return

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML",
            )
            logger.debug(f"Mensaje Telegram enviado: {message[:50]}...")
        except TelegramError as e:
            logger.error(f"Error enviando mensaje Telegram: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en Telegram: {e}")

    async def send_trade_notification(self, trade_data: dict):
        """Enviar notificacion de trade ejecutado"""
        from utils.formatters import Formatters

        if trade_data.get("side") == "buy":
            msg = Formatters.format_trade_message(trade_data)
        else:
            msg = Formatters.format_sell_message(trade_data)

        await self.send_message(msg)

    async def send_daily_summary(self, data: dict):
        """Enviar resumen diario"""
        from utils.formatters import Formatters
        msg = Formatters.format_daily_summary(data)
        await self.send_message(msg)

    async def send_alert(self, message: str, level: str = "warning"):
        """Enviar alerta del sistema"""
        emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}.get(level, "⚠️")
        await self.send_message(f"{emoji} {message}")

    async def stop(self):
        """Detener bot de Telegram"""
        self.enabled = False
        self.bot = None
        logger.info("Telegram bot detenido")
