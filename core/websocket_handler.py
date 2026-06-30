"""
Manejo de datos en tiempo real via WebSocket
Permite recibir precios en streaming para monitoreo de posiciones
"""

import asyncio
import json
from typing import Callable
from loguru import logger

try:
    import websockets
except ImportError:
    websockets = None


class WebSocketHandler:
    """Manejar conexiones WebSocket con KuCoin para datos en tiempo real"""

    WS_PUBLIC_URL = "wss://ws-api-spot.kucoin.com"

    def __init__(self):
        self.ws = None
        self.running = False
        self.callbacks = {}
        self._ping_task = None

    async def connect(self, token: str = None):
        """Conectar al WebSocket de KuCoin"""
        if websockets is None:
            logger.warning("Libreria websockets no disponible, usando polling")
            return

        try:
            url = self.WS_PUBLIC_URL
            if token:
                url = f"{url}?token={token}"

            self.ws = await websockets.connect(url)
            self.running = True
            logger.info("WebSocket conectado a KuCoin")

            self._ping_task = asyncio.create_task(self._keepalive())

        except Exception as e:
            logger.error(f"Error conectando WebSocket: {e}")
            self.running = False

    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """Suscribirse a actualizaciones de precio de un par"""
        kucoin_symbol = symbol.replace("/", "-")
        topic = f"/market/ticker:{kucoin_symbol}"

        if symbol not in self.callbacks:
            self.callbacks[symbol] = []
        self.callbacks[symbol].append(callback)

        if self.ws:
            subscribe_msg = {
                "id": str(id(callback)),
                "type": "subscribe",
                "topic": topic,
                "response": True,
            }
            await self.ws.send(json.dumps(subscribe_msg))
            logger.info(f"Suscrito a ticker de {symbol}")

    async def unsubscribe_ticker(self, symbol: str):
        """Desuscribirse de un par"""
        kucoin_symbol = symbol.replace("/", "-")
        topic = f"/market/ticker:{kucoin_symbol}"

        if self.ws:
            unsub_msg = {
                "id": "unsub",
                "type": "unsubscribe",
                "topic": topic,
            }
            await self.ws.send(json.dumps(unsub_msg))

        self.callbacks.pop(symbol, None)

    async def listen(self):
        """Escuchar mensajes del WebSocket"""
        if not self.ws:
            return

        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type", "")

                if msg_type == "message":
                    topic = data.get("topic", "")
                    ticker_data = data.get("data", {})

                    if "/market/ticker:" in topic:
                        kucoin_sym = topic.split(":")[-1]
                        symbol = kucoin_sym.replace("-", "/")

                        for callback in self.callbacks.get(symbol, []):
                            try:
                                await callback(symbol, ticker_data)
                            except Exception as e:
                                logger.error(f"Error en callback de {symbol}: {e}")

        except Exception as e:
            if self.running:
                logger.error(f"Error en WebSocket listener: {e}")

    async def _keepalive(self):
        """Enviar ping periodico para mantener la conexion"""
        while self.running and self.ws:
            try:
                await asyncio.sleep(30)
                if self.ws:
                    ping_msg = {"id": "ping", "type": "ping"}
                    await self.ws.send(json.dumps(ping_msg))
            except Exception:
                break

    async def close(self):
        """Cerrar conexion WebSocket"""
        self.running = False
        if self._ping_task:
            self._ping_task.cancel()
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket cerrado")
