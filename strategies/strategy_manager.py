"""
Gestor y selector de estrategias
Permite activar/desactivar y cambiar estrategias en tiempo de ejecucion
"""

import pandas as pd
from typing import Dict, Optional
from loguru import logger

from strategies.base_strategy import BaseStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.combined_strategy import CombinedStrategy
from config.strategy_config import StrategyConfig


class StrategyManager:
    """Gestionar multiples estrategias de trading"""

    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.active_strategy: str = StrategyConfig.DEFAULT_STRATEGY
        self._register_strategies()

    def _register_strategies(self):
        """Registrar todas las estrategias disponibles"""
        self.strategies = {
            "rsi": RSIStrategy(),
            "macd": MACDStrategy(),
            "bollinger": BollingerStrategy(),
            "combined": CombinedStrategy(),
        }
        logger.info(f"Estrategias registradas: {list(self.strategies.keys())}")

    def get_strategy(self, name: str = None) -> Optional[BaseStrategy]:
        """Obtener una estrategia por nombre"""
        if name is None:
            name = self.active_strategy
        return self.strategies.get(name)

    def set_active_strategy(self, name: str):
        """Cambiar la estrategia activa"""
        if name in self.strategies:
            self.active_strategy = name
            logger.info(f"Estrategia activa cambiada a: {name}")
        else:
            logger.error(f"Estrategia '{name}' no encontrada")

    def analyze(self, df: pd.DataFrame, indicators: dict,
                strategy_name: str = None) -> dict:
        """Ejecutar analisis con la estrategia seleccionada"""
        strategy = self.get_strategy(strategy_name)
        if strategy is None:
            return {"action": "hold", "score": 0.0, "reason": "Estrategia no disponible"}

        if not strategy.is_enabled():
            return {"action": "hold", "score": 0.0, "reason": f"Estrategia {strategy.name} deshabilitada"}

        return strategy.analyze(df, indicators)

    def analyze_all(self, df: pd.DataFrame, indicators: dict) -> dict:
        """Ejecutar analisis con todas las estrategias habilitadas"""
        results = {}
        for name, strategy in self.strategies.items():
            if strategy.is_enabled():
                results[name] = strategy.analyze(df, indicators)
        return results

    def enable_strategy(self, name: str):
        """Habilitar una estrategia"""
        if name in self.strategies:
            self.strategies[name].enable()

    def disable_strategy(self, name: str):
        """Deshabilitar una estrategia"""
        if name in self.strategies:
            self.strategies[name].disable()

    def get_available_strategies(self) -> list:
        """Obtener lista de estrategias disponibles"""
        return [
            {"name": name, "enabled": s.is_enabled()}
            for name, s in self.strategies.items()
        ]
