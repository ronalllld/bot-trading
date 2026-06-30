"""
Parametros de configuracion para las estrategias de trading
"""


class StrategyConfig:
    """Configuracion de parametros de estrategias"""

    # --- RSI ---
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30       # Nivel de sobreventa
    RSI_OVERBOUGHT = 70     # Nivel de sobrecompra

    # --- MACD ---
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9

    # --- Bollinger Bands ---
    BB_PERIOD = 20
    BB_STD_DEV = 2.0

    # --- EMA ---
    EMA_FAST = 9
    EMA_MEDIUM = 21
    EMA_SLOW = 50
    EMA_VERY_SLOW = 200

    # --- Volumen ---
    VOLUME_MA_PERIOD = 20

    # --- ATR ---
    ATR_PERIOD = 14

    # --- Senales combinadas ---
    # Pesos para la estrategia combinada (deben sumar 1.0)
    WEIGHT_RSI = 0.30
    WEIGHT_MACD = 0.30
    WEIGHT_BB = 0.20
    WEIGHT_VOLUME = 0.20

    # Umbral minimo para ejecutar operacion
    BUY_THRESHOLD = 0.7
    SELL_THRESHOLD = 0.7

    # Estrategias disponibles
    AVAILABLE_STRATEGIES = ["rsi", "macd", "bollinger", "combined"]
    DEFAULT_STRATEGY = "combined"
