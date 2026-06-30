"""
Configuracion especifica del exchange Binance
"""


class ExchangeConfig:
    """Parametros de configuracion para Binance"""

    # Exchange ID para CCXT
    EXCHANGE_ID = "binance"

    # Rate limits
    MAX_REQUESTS_PER_SECOND = 10
    REQUEST_TIMEOUT = 30000  # milisegundos

    # Pares permitidos para operar
    ALLOWED_PAIRS = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "XRP/USDT",
        "ADA/USDT",
        "DOGE/USDT",
        "TRX/USDT",
        "SHIB/USDT",
        "SOL/USDT",
        "DOT/USDT",
        "AVAX/USDT",
        "LINK/USDT",
        "ATOM/USDT",
        "LTC/USDT",
        "MATIC/USDT",
    ]

    # Filtros de mercado
    MIN_VOLUME_24H = 1_000_000  # Volumen minimo en USDT
    MAX_SPREAD_PERCENTAGE = 0.5  # Spread maximo permitido
    MIN_ORDER_USDT = 5.0  # Orden minima en USDT (minimo Binance ~5 USDT)

    # Timeframes soportados
    VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"]

    # Cantidad de velas a obtener para analisis
    OHLCV_LIMIT = 200
