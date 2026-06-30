"""
Funciones auxiliares generales
"""

from datetime import datetime, timezone
import hashlib


class Helpers:
    """Funciones de utilidad general"""

    @staticmethod
    def timestamp_now() -> datetime:
        """Obtener timestamp actual en UTC"""
        return datetime.now(timezone.utc)

    @staticmethod
    def timestamp_to_str(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Convertir datetime a string"""
        return dt.strftime(fmt)

    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """Calcular cambio porcentual entre dos valores"""
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100

    @staticmethod
    def round_to_precision(value: float, precision: int = 8) -> float:
        """Redondear valor a precision especifica"""
        return round(value, precision)

    @staticmethod
    def generate_trade_id(symbol: str, side: str, timestamp: datetime) -> str:
        """Generar ID unico para un trade"""
        raw = f"{symbol}_{side}_{timestamp.isoformat()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Division segura que retorna default si denominador es 0"""
        if denominator == 0:
            return default
        return numerator / denominator

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Limitar valor entre minimo y maximo"""
        return max(min_val, min(value, max_val))

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Formatear duracion en formato legible"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = seconds / 60
            return f"{mins:.0f}min"
        else:
            hours = seconds / 3600
            mins = (seconds % 3600) / 60
            return f"{hours:.0f}h {mins:.0f}min"
