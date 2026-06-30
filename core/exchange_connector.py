"""
Conexion con el exchange Binance usando CCXT
Maneja autenticacion, balance, tickers y ordenes
"""

import ccxt
import asyncio
import time
from typing import Optional
from loguru import logger

from config.config import Config
from config.exchange_config import ExchangeConfig


class ExchangeConnector:
    """Conector principal con Binance via CCXT"""

    def __init__(self, config: Config):
        self.config = config
        self.exchange: Optional[ccxt.binance] = None
        self.connected = False
        self._last_request_time = 0
        self._request_interval = 1.0 / ExchangeConfig.MAX_REQUESTS_PER_SECOND

    async def connect(self):
        """Inicializar conexion con Binance"""
        try:
            exchange_params = {
                "apiKey": self.config.BINANCE_API_KEY,
                "secret": self.config.BINANCE_API_SECRET,
                "timeout": ExchangeConfig.REQUEST_TIMEOUT,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",
                },
            }

            if self.config.is_paper_mode():
                logger.info("Modo PAPER TRADING activado (ordenes simuladas)")

            self.exchange = ccxt.binance(exchange_params)

            # Cargar mercados
            await asyncio.to_thread(self.exchange.load_markets)
            self.connected = True
            logger.info(f"Conectado a Binance - Mercados cargados: {len(self.exchange.markets)}")

        except ccxt.AuthenticationError as e:
            logger.error(f"Error de autenticacion con Binance: {e}")
            raise
        except ccxt.NetworkError as e:
            logger.error(f"Error de red al conectar con Binance: {e}")
            raise
        except Exception as e:
            logger.error(f"Error al conectar con Binance: {e}")
            raise

    async def _rate_limit(self):
        """Controlar rate limiting manualmente"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._request_interval:
            await asyncio.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()

    async def get_balance(self) -> dict:
        """Obtener balance de la cuenta"""
        try:
            await self._rate_limit()
            balance = await asyncio.to_thread(self.exchange.fetch_balance)
            return {
                "USDT": balance.get("USDT", {}).get("free", 0.0),
                "total": balance.get("total", {}),
                "free": balance.get("free", {}),
                "used": balance.get("used", {}),
            }
        except Exception as e:
            logger.error(f"Error al obtener balance: {e}")
            return {"USDT": 0.0, "total": {}, "free": {}, "used": {}}

    async def fetch_ticker(self, symbol: str) -> dict:
        """Obtener ticker (precio actual) de un par"""
        try:
            await self._rate_limit()
            ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
            return {
                "symbol": symbol,
                "bid": ticker.get("bid", 0),
                "ask": ticker.get("ask", 0),
                "last": ticker.get("last", 0),
                "volume": ticker.get("quoteVolume", 0),
                "high": ticker.get("high", 0),
                "low": ticker.get("low", 0),
                "change": ticker.get("percentage", 0),
            }
        except Exception as e:
            logger.error(f"Error al obtener ticker de {symbol}: {e}")
            return {}

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "5m",
                          limit: int = None) -> list:
        """Obtener datos OHLCV (velas)"""
        if limit is None:
            limit = ExchangeConfig.OHLCV_LIMIT
        try:
            await self._rate_limit()
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv, symbol, timeframe, None, limit
            )
            return ohlcv  # [[timestamp, open, high, low, close, volume], ...]
        except Exception as e:
            logger.error(f"Error al obtener OHLCV de {symbol}: {e}")
            return []

    async def create_market_order(self, symbol: str, side: str, amount: float) -> dict:
        """Crear orden de mercado (compra/venta)"""
        try:
            await self._rate_limit()
            logger.info(f"Ejecutando orden {side.upper()} {symbol} - Cantidad: {amount}")

            if self.config.is_paper_mode():
                # En paper trading, simular la orden
                ticker = await self.fetch_ticker(symbol)
                price = ticker.get("last", 0)
                return {
                    "id": f"paper_{symbol}_{side}_{int(time.time())}",
                    "symbol": symbol,
                    "side": side,
                    "type": "market",
                    "amount": amount,
                    "price": price,
                    "cost": amount * price if side == "sell" else price * amount,
                    "filled": amount,
                    "status": "closed",
                    "paper": True,
                }

            order = await asyncio.to_thread(
                self.exchange.create_market_order, symbol, side, amount
            )
            logger.info(f"Orden ejecutada: {order.get('id')} - {side} {symbol}")
            return order

        except ccxt.InsufficientFunds as e:
            logger.error(f"Fondos insuficientes para {side} {symbol}: {e}")
            return {}
        except ccxt.InvalidOrder as e:
            logger.error(f"Orden invalida {side} {symbol}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error al crear orden {side} {symbol}: {e}")
            return {}

    async def create_limit_order(self, symbol: str, side: str,
                                  amount: float, price: float) -> dict:
        """Crear orden limitada"""
        try:
            await self._rate_limit()

            if self.config.is_paper_mode():
                return {
                    "id": f"paper_limit_{symbol}_{side}",
                    "symbol": symbol,
                    "side": side,
                    "type": "limit",
                    "amount": amount,
                    "price": price,
                    "status": "open",
                    "paper": True,
                }

            order = await asyncio.to_thread(
                self.exchange.create_limit_order, symbol, side, amount, price
            )
            return order
        except Exception as e:
            logger.error(f"Error al crear orden limitada: {e}")
            return {}

    async def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancelar una orden abierta"""
        try:
            await self._rate_limit()
            await asyncio.to_thread(self.exchange.cancel_order, order_id, symbol)
            logger.info(f"Orden cancelada: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error al cancelar orden {order_id}: {e}")
            return False

    async def get_open_orders(self, symbol: str = None) -> list:
        """Obtener ordenes abiertas"""
        try:
            await self._rate_limit()
            orders = await asyncio.to_thread(self.exchange.fetch_open_orders, symbol)
            return orders
        except Exception as e:
            logger.error(f"Error al obtener ordenes abiertas: {e}")
            return []

    async def get_market_info(self, symbol: str) -> dict:
        """Obtener informacion del mercado (minimos, precision)"""
        try:
            if symbol in self.exchange.markets:
                market = self.exchange.markets[symbol]
                return {
                    "symbol": symbol,
                    "min_amount": market.get("limits", {}).get("amount", {}).get("min", 0),
                    "min_cost": market.get("limits", {}).get("cost", {}).get("min", 0),
                    "price_precision": market.get("precision", {}).get("price", 8),
                    "amount_precision": market.get("precision", {}).get("amount", 8),
                    "active": market.get("active", False),
                }
            return {}
        except Exception as e:
            logger.error(f"Error al obtener info de mercado {symbol}: {e}")
            return {}

    async def get_trading_fees(self, symbol: str) -> dict:
        """Obtener comisiones de trading"""
        try:
            await self._rate_limit()
            fees = await asyncio.to_thread(self.exchange.fetch_trading_fee, symbol)
            return {
                "maker": fees.get("maker", 0.001),
                "taker": fees.get("taker", 0.001),
            }
        except Exception:
            return {"maker": 0.001, "taker": 0.001}

    async def close(self):
        """Cerrar conexion con el exchange"""
        if self.exchange:
            try:
                await asyncio.to_thread(self.exchange.close)
            except Exception:
                pass
            self.connected = False
            logger.info("Conexion con Binance cerrada")
