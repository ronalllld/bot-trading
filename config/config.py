"""
Configuracion general del sistema de trading
Carga variables de entorno y proporciona valores por defecto
"""

import os
from dotenv import load_dotenv
from pathlib import Path


class Config:
    """Clase principal de configuracion del bot"""

    def __init__(self, env_path: str = None):
        """Cargar configuracion desde archivo .env"""
        if env_path:
            load_dotenv(env_path)
        else:
            # Buscar .env en la raiz del proyecto
            root = Path(__file__).parent.parent
            load_dotenv(root / ".env")

        # --- KuCoin API ---
        self.KUCOIN_API_KEY = os.getenv("KUCOIN_API_KEY", "")
        self.KUCOIN_API_SECRET = os.getenv("KUCOIN_API_SECRET", "")
        self.KUCOIN_API_PASSPHRASE = os.getenv("KUCOIN_API_PASSPHRASE", "")

        # --- Telegram ---
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

        # --- Email ---
        self.SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER = os.getenv("SMTP_USER", "")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

        # --- Trading ---
        self.INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "10.0"))
        self.RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "2.0"))
        self.MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "2"))
        self.POSITION_SIZE_PERCENTAGE = float(os.getenv("POSITION_SIZE_PERCENTAGE", "50.0"))
        self.TAKE_PROFIT = float(os.getenv("TAKE_PROFIT", "3.0"))
        self.STOP_LOSS = float(os.getenv("STOP_LOSS", "1.5"))
        self.MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "5.0"))
        self.MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "20"))

        # --- Sistema ---
        self.MODE = os.getenv("MODE", "paper")  # paper / real
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.TIMEFRAME = os.getenv("TIMEFRAME", "5m")
        self.SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "5"))

        # --- Rutas ---
        self.BASE_DIR = Path(__file__).parent.parent
        self.LOG_DIR = self.BASE_DIR / "logs"
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DB_PATH = self.DATA_DIR / "trading_bot.db"

        # Crear directorios si no existen
        self.LOG_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)

    def validate(self) -> bool:
        """Validar que la configuracion esencial este presente"""
        errors = []

        if self.MODE == "real":
            if not self.KUCOIN_API_KEY:
                errors.append("KUCOIN_API_KEY es requerida en modo real")
            if not self.KUCOIN_API_SECRET:
                errors.append("KUCOIN_API_SECRET es requerida en modo real")
            if not self.KUCOIN_API_PASSPHRASE:
                errors.append("KUCOIN_API_PASSPHRASE es requerida en modo real")

        if self.INITIAL_CAPITAL <= 0:
            errors.append("INITIAL_CAPITAL debe ser mayor a 0")

        if self.POSITION_SIZE_PERCENTAGE <= 0 or self.POSITION_SIZE_PERCENTAGE > 100:
            errors.append("POSITION_SIZE_PERCENTAGE debe estar entre 0 y 100")

        if self.TAKE_PROFIT <= 0:
            errors.append("TAKE_PROFIT debe ser mayor a 0")

        if self.STOP_LOSS <= 0:
            errors.append("STOP_LOSS debe ser mayor a 0")

        if errors:
            for e in errors:
                print(f"[CONFIG ERROR] {e}")
            raise ValueError(f"Configuracion invalida: {len(errors)} errores encontrados")

        return True

    def is_paper_mode(self) -> bool:
        """Verificar si estamos en modo paper trading"""
        return self.MODE.lower() == "paper"

    def __repr__(self):
        return (
            f"Config(mode={self.MODE}, capital={self.INITIAL_CAPITAL}, "
            f"max_positions={self.MAX_POSITIONS}, tp={self.TAKE_PROFIT}%, "
            f"sl={self.STOP_LOSS}%)"
        )
