"""
Validaciones de datos para el sistema de trading
"""

from loguru import logger


class Validators:
    """Validaciones para operaciones de trading"""

    @staticmethod
    def validate_symbol(symbol: str, allowed_pairs: list) -> bool:
        """Validar que el par de trading sea permitido"""
        if symbol not in allowed_pairs:
            logger.warning(f"Par {symbol} no esta en la lista de permitidos")
            return False
        return True

    @staticmethod
    def validate_order_size(amount_usdt: float, min_order: float = 5.0) -> bool:
        """Validar que el tamano de la orden cumpla el minimo"""
        if amount_usdt < min_order:
            logger.warning(f"Orden de ${amount_usdt:.2f} menor al minimo ${min_order:.2f}")
            return False
        return True

    @staticmethod
    def validate_balance(balance: float, required: float) -> bool:
        """Validar que hay balance suficiente"""
        if balance < required:
            logger.warning(f"Balance insuficiente: ${balance:.2f} < ${required:.2f}")
            return False
        return True

    @staticmethod
    def validate_positions_limit(current_positions: int, max_positions: int) -> bool:
        """Validar que no se exceda el limite de posiciones"""
        if current_positions >= max_positions:
            logger.warning(f"Limite de posiciones alcanzado: {current_positions}/{max_positions}")
            return False
        return True

    @staticmethod
    def validate_daily_loss(current_loss: float, max_loss: float) -> bool:
        """Validar que no se exceda la perdida diaria maxima"""
        if abs(current_loss) >= max_loss:
            logger.warning(f"Perdida diaria maxima alcanzada: {abs(current_loss):.2f}% >= {max_loss}%")
            return False
        return True

    @staticmethod
    def validate_daily_trades(current_trades: int, max_trades: int) -> bool:
        """Validar que no se exceda el limite de trades diarios"""
        if current_trades >= max_trades:
            logger.warning(f"Limite de trades diarios alcanzado: {current_trades}/{max_trades}")
            return False
        return True

    @staticmethod
    def validate_spread(bid: float, ask: float, max_spread: float = 0.5) -> bool:
        """Validar que el spread sea aceptable"""
        if bid == 0:
            return False
        spread = ((ask - bid) / bid) * 100
        if spread > max_spread:
            logger.warning(f"Spread demasiado alto: {spread:.2f}% > {max_spread}%")
            return False
        return True

    @staticmethod
    def validate_market_data(data, min_candles: int = 50) -> bool:
        """Validar que los datos de mercado sean suficientes"""
        if data is None or len(data) < min_candles:
            logger.warning(f"Datos de mercado insuficientes: {len(data) if data is not None else 0} < {min_candles}")
            return False
        return True
