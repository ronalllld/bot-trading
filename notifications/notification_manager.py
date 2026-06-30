"""
Gestor centralizado de notificaciones
Coordina envio por Telegram y Email
"""

from loguru import logger
from notifications.telegram_bot import TelegramBot
from notifications.email_sender import EmailSender


class NotificationManager:
    """Gestionar todas las notificaciones del sistema"""

    def __init__(self, config):
        self.config = config
        self.telegram = TelegramBot(config)
        self.email = EmailSender(config)

    async def initialize(self):
        """Inicializar todos los canales de notificacion"""
        await self.telegram.start()
        await self.email.initialize()
        logger.info("Sistema de notificaciones inicializado")

    async def notify_trade(self, trade_data: dict):
        """Notificar trade ejecutado por todos los canales"""
        await self.telegram.send_trade_notification(trade_data)

    async def notify_alert(self, message: str, level: str = "warning"):
        """Enviar alerta por todos los canales"""
        await self.telegram.send_alert(message, level)
        if level == "error":
            await self.email.send_error_alert(message)

    async def notify_daily_summary(self, data: dict):
        """Enviar resumen diario"""
        await self.telegram.send_daily_summary(data)
        from utils.formatters import Formatters
        report = Formatters.format_daily_summary(data)
        await self.email.send_daily_report(report)

    async def send_message(self, message: str):
        """Enviar mensaje simple por Telegram"""
        await self.telegram.send_message(message)

    async def stop(self):
        """Detener notificaciones"""
        await self.telegram.stop()
