"""
Gestion automatica de stop-loss
Monitorea posiciones y ejecuta ventas cuando se alcanza el stop loss
"""

from loguru import logger
from config.config import Config
from database.models import Trade


class StopLossManager:
    """Gestionar stop-loss automatico para posiciones abiertas"""

    def __init__(self, config: Config):
        self.config = config
        self.trailing_activated = {}  # {trade_id: highest_price}

    def calculate_stop_loss(self, entry_price: float) -> float:
        """Calcular precio de stop loss"""
        return entry_price * (1 - self.config.STOP_LOSS / 100)

    def should_trigger_stop_loss(self, trade: Trade, current_price: float) -> bool:
        """Verificar si se debe activar el stop loss"""
        if trade.stop_loss and current_price <= trade.stop_loss:
            logger.warning(
                f"STOP LOSS activado para {trade.symbol}: "
                f"Precio ${current_price:.4f} <= SL ${trade.stop_loss:.4f}"
            )
            return True
        return False

    def update_trailing_stop(self, trade: Trade, current_price: float,
                              activation_pct: float = 1.0,
                              trail_pct: float = None) -> float:
        """
        Actualizar trailing stop loss
        Se activa cuando la ganancia supera activation_pct
        Luego sigue al precio a una distancia de trail_pct
        """
        if trail_pct is None:
            trail_pct = self.config.STOP_LOSS

        trade_id = trade.trade_id
        gain_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100

        # Activar trailing solo si la ganancia supera el umbral
        if gain_pct < activation_pct:
            return trade.stop_loss or self.calculate_stop_loss(trade.entry_price)

        # Actualizar precio maximo
        if trade_id not in self.trailing_activated:
            self.trailing_activated[trade_id] = current_price
            logger.info(f"Trailing stop ACTIVADO para {trade.symbol} (ganancia: {gain_pct:.2f}%)")
        else:
            self.trailing_activated[trade_id] = max(
                self.trailing_activated[trade_id], current_price
            )

        # Calcular nuevo stop loss basado en el maximo
        highest = self.trailing_activated[trade_id]
        new_sl = highest * (1 - trail_pct / 100)

        # Solo subir el stop loss, nunca bajarlo
        current_sl = trade.stop_loss or 0
        return max(new_sl, current_sl)

    def clear_trailing(self, trade_id: str):
        """Limpiar trailing stop de un trade cerrado"""
        self.trailing_activated.pop(trade_id, None)
