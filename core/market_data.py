"""
Obtencion y procesamiento de datos de mercado
Convierte datos crudos OHLCV en DataFrames de pandas
"""

import pandas as pd
from typing import List, Optional
from loguru import logger

from core.exchange_connector import ExchangeConnector
from config.exchange_config import ExchangeConfig


class MarketData:
    """Obtener y procesar datos de mercado"""

    def __init__(self, exchange: ExchangeConnector):
        self.exchange = exchange

    async def get_ohlcv_dataframe(self, symbol: str, timeframe: str = "5m",
                                   limit: int = None) -> Optional[pd.DataFrame]:
        """Obtener datos OHLCV como DataFrame de pandas"""
        if limit is None:
            limit = ExchangeConfig.OHLCV_LIMIT

        raw_data = await self.exchange.fetch_ohlcv(symbol, timeframe, limit)
        if not raw_data or len(raw_data) < 10:
            logger.warning(f"Datos insuficientes para {symbol}: {len(raw_data) if raw_data else 0} velas")
            return None

        df = pd.DataFrame(raw_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df = df.astype(float)
        return df

    async def get_current_price(self, symbol: str) -> float:
        """Obtener precio actual de un par"""
        ticker = await self.exchange.fetch_ticker(symbol)
        return ticker.get("last", 0.0)

    async def get_top_pairs_by_volume(self, limit: int = 20) -> List[dict]:
        """Obtener los pares con mayor volumen en 24h"""
        pairs_data = []

        for symbol in ExchangeConfig.ALLOWED_PAIRS:
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue

                volume_24h = ticker.get("volume", 0)
                if volume_24h >= ExchangeConfig.MIN_VOLUME_24H:
                    bid = ticker.get("bid", 0)
                    ask = ticker.get("ask", 0)

                    # Calcular spread
                    spread = 0.0
                    if bid > 0:
                        spread = ((ask - bid) / bid) * 100

                    if spread <= ExchangeConfig.MAX_SPREAD_PERCENTAGE:
                        pairs_data.append({
                            "symbol": symbol,
                            "price": ticker.get("last", 0),
                            "volume_24h": volume_24h,
                            "change_24h": ticker.get("change", 0),
                            "bid": bid,
                            "ask": ask,
                            "spread": spread,
                        })

            except Exception as e:
                logger.debug(f"Error al obtener ticker de {symbol}: {e}")
                continue

        # Ordenar por volumen descendente
        pairs_data.sort(key=lambda x: x["volume_24h"], reverse=True)
        return pairs_data[:limit]

    async def is_market_data_fresh(self, symbol: str, max_age_seconds: int = 30) -> bool:
        """Verificar que los datos de mercado estan actualizados"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return bool(ticker)
        except Exception:
            return False

    async def get_multiple_ohlcv(self, symbols: List[str], timeframe: str = "5m") -> dict:
        """Obtener OHLCV de multiples pares"""
        result = {}
        for symbol in symbols:
            df = await self.get_ohlcv_dataframe(symbol, timeframe)
            if df is not None:
                result[symbol] = df
        return result
