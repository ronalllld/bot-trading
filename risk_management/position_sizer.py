"""
Calculo del tamano de posicion
Determina cuanto invertir en cada trade basado en el capital y riesgo
"""

from loguru import logger
from config.config import Config
from config.exchange_config import ExchangeConfig


class PositionSizer:
    """Calcular tamano optimo de posicion para cada trade"""

    def __init__(self, config: Config):
        self.config = config

    def calculate_position_size(self, available_balance: float,
                                 current_price: float = 0) -> dict:
        """
        Calcular tamano de posicion usando Fixed Percentage
        Capital: $10 USDT -> 50% = $5 por trade
        """
        # Porcentaje del balance a invertir
        percentage = self.config.POSITION_SIZE_PERCENTAGE / 100
        position_usdt = available_balance * percentage

        # Verificar minimo del exchange
        min_order = ExchangeConfig.MIN_ORDER_USDT
        if position_usdt < min_order:
            logger.warning(
                f"Posicion ${position_usdt:.2f} menor al minimo ${min_order}. "
                f"Se requiere balance >= ${min_order / percentage:.2f}"
            )
            return {
                "valid": False,
                "amount_usdt": 0,
                "quantity": 0,
                "reason": f"Posicion menor al minimo (${min_order})",
            }

        # Calcular cantidad de crypto
        quantity = position_usdt / current_price if current_price > 0 else 0

        result = {
            "valid": True,
            "amount_usdt": round(position_usdt, 2),
            "quantity": quantity,
            "percentage_used": self.config.POSITION_SIZE_PERCENTAGE,
            "available_balance": available_balance,
        }

        logger.debug(
            f"Position size: ${position_usdt:.2f} USDT "
            f"({self.config.POSITION_SIZE_PERCENTAGE}% de ${available_balance:.2f})"
        )
        return result

    def can_open_position(self, available_balance: float,
                           open_positions: int) -> bool:
        """Verificar si se puede abrir una nueva posicion"""
        # Verificar limite de posiciones
        if open_positions >= self.config.MAX_POSITIONS:
            logger.debug(f"Limite de posiciones alcanzado: {open_positions}/{self.config.MAX_POSITIONS}")
            return False

        # Verificar balance minimo
        percentage = self.config.POSITION_SIZE_PERCENTAGE / 100
        required = ExchangeConfig.MIN_ORDER_USDT
        if available_balance * percentage < required:
            logger.debug(f"Balance insuficiente para nueva posicion")
            return False

        return True

    def get_max_positions_for_balance(self, balance: float) -> int:
        """Calcular cuantas posiciones se pueden abrir con el balance actual"""
        percentage = self.config.POSITION_SIZE_PERCENTAGE / 100
        position_size = balance * percentage
        if position_size < ExchangeConfig.MIN_ORDER_USDT:
            return 0

        max_by_balance = int(balance / (ExchangeConfig.MIN_ORDER_USDT / percentage))
        return min(max_by_balance, self.config.MAX_POSITIONS)
