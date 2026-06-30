"""
Gestion automatica de take-profit
Monitorea posiciones y ejecuta ventas cuando se alcanza el objetivo de ganancia
"""

from loguru import logger
from config.config import Config
from database.models import Trade


class TakeProfitManager:
    """Gestionar take-profit automatico para posiciones abiertas"""

    def __init__(self, config: Config):
        self.config = config

    def calculate_take_profit(self, entry_price: float) -> float:
        """Calcular precio de take profit"""
        return entry_price * (1 + self.config.TAKE_PROFIT / 100)

    def should_trigger_take_profit(self, trade: Trade, current_price: float) -> bool:
        """Verificar si se debe activar el take profit"""
        if trade.take_profit and current_price >= trade.take_profit:
            logger.info(
                f"TAKE PROFIT activado para {trade.symbol}: "
                f"Precio ${current_price:.4f} >= TP ${trade.take_profit:.4f}"
            )
            return True
        return False

    def calculate_risk_reward(self, entry_price: float) -> dict:
        """Calcular ratio riesgo/recompensa"""
        tp = self.config.TAKE_PROFIT
        sl = self.config.STOP_LOSS
        ratio = tp / sl if sl > 0 else 0

        return {
            "take_profit_pct": tp,
            "stop_loss_pct": sl,
            "risk_reward_ratio": ratio,
            "tp_price": entry_price * (1 + tp / 100),
            "sl_price": entry_price * (1 - sl / 100),
        }
