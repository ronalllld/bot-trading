"""
Escaneo automatico del mercado
Identifica oportunidades de trading en multiples pares
"""

from typing import List
from loguru import logger

from core.market_data import MarketData
from analysis.technical_indicators import TechnicalIndicators
from analysis.signal_generator import SignalGenerator
from config.exchange_config import ExchangeConfig


class MarketScanner:
    """Escanear el mercado buscando oportunidades"""

    def __init__(self, market_data: MarketData):
        self.market_data = market_data
        self.signal_generator = SignalGenerator()

    async def scan_market(self, timeframe: str = "5m") -> List[dict]:
        """Escanear todos los pares y generar senales"""
        opportunities = []

        # Obtener pares con buen volumen
        pairs = await self.market_data.get_top_pairs_by_volume(limit=20)
        logger.info(f"Escaneando {len(pairs)} pares...")

        for pair_info in pairs:
            symbol = pair_info["symbol"]
            try:
                # Obtener datos OHLCV
                df = await self.market_data.get_ohlcv_dataframe(symbol, timeframe)
                if df is None or len(df) < 50:
                    continue

                # Calcular indicadores
                indicators = TechnicalIndicators.calculate_all_indicators(df)

                # Generar senal
                signal = self.signal_generator.generate_signal(df, indicators)

                if signal["action"] != "hold":
                    opportunity = {
                        "symbol": symbol,
                        "action": signal["action"],
                        "score": signal["score"],
                        "price": pair_info["price"],
                        "volume_24h": pair_info["volume_24h"],
                        "change_24h": pair_info["change_24h"],
                        "spread": pair_info["spread"],
                        "indicators": {
                            "rsi": float(indicators["rsi"].iloc[-1]) if len(indicators["rsi"]) > 0 else 0,
                            "macd_hist": float(indicators["macd"]["histogram"].iloc[-1]) if len(indicators["macd"]["histogram"]) > 0 else 0,
                        },
                        "details": signal.get("details", {}),
                    }
                    opportunities.append(opportunity)
                    logger.info(
                        f"Senal {signal['action'].upper()} en {symbol} - "
                        f"Score: {signal['score']:.2f} - Precio: ${pair_info['price']}"
                    )

            except Exception as e:
                logger.debug(f"Error escaneando {symbol}: {e}")
                continue

        # Ordenar por score descendente
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Encontradas {len(opportunities)} oportunidades")
        return opportunities

    async def quick_scan(self, symbols: List[str], timeframe: str = "5m") -> List[dict]:
        """Escaneo rapido de pares especificos"""
        results = []

        for symbol in symbols:
            try:
                df = await self.market_data.get_ohlcv_dataframe(symbol, timeframe)
                if df is None:
                    continue

                indicators = TechnicalIndicators.calculate_all_indicators(df)
                signal = self.signal_generator.generate_signal(df, indicators)

                results.append({
                    "symbol": symbol,
                    "action": signal["action"],
                    "score": signal["score"],
                    "price": float(df["close"].iloc[-1]),
                    "rsi": float(indicators["rsi"].iloc[-1]) if len(indicators["rsi"]) > 0 else 0,
                })

            except Exception as e:
                logger.debug(f"Error en quick_scan de {symbol}: {e}")

        return results
