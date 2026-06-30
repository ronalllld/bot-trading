"""
Envio de notificaciones por email
Soporte para Gmail y otros servidores SMTP
"""

import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

try:
    import aiosmtplib
    HAS_SMTP = True
except ImportError:
    HAS_SMTP = False


class EmailSender:
    """Enviar notificaciones por email"""

    def __init__(self, config):
        self.config = config
        self.enabled = False
        self.server = config.SMTP_SERVER
        self.port = config.SMTP_PORT
        self.user = config.SMTP_USER
        self.password = config.SMTP_PASSWORD

    async def initialize(self):
        """Verificar configuracion de email"""
        if not HAS_SMTP:
            logger.warning("aiosmtplib no instalado, email deshabilitado")
            return

        if self.user and self.password:
            self.enabled = True
            logger.info(f"Email configurado: {self.user}")
        else:
            logger.warning("Email no configurado (falta usuario o password)")

    async def send_email(self, subject: str, body: str, to_email: str = None):
        """Enviar email"""
        if not self.enabled:
            return

        if to_email is None:
            to_email = self.user

        try:
            message = MIMEMultipart()
            message["From"] = self.user
            message["To"] = to_email
            message["Subject"] = f"[Trading Bot] {subject}"
            message.attach(MIMEText(body, "plain"))

            await aiosmtplib.send(
                message,
                hostname=self.server,
                port=self.port,
                start_tls=True,
                username=self.user,
                password=self.password,
            )
            logger.debug(f"Email enviado: {subject}")
        except Exception as e:
            logger.error(f"Error enviando email: {e}")

    async def send_daily_report(self, report: str):
        """Enviar reporte diario por email"""
        await self.send_email("Resumen Diario de Trading", report)

    async def send_error_alert(self, error_msg: str):
        """Enviar alerta de error por email"""
        await self.send_email("ALERTA - Error en Trading Bot", error_msg)
