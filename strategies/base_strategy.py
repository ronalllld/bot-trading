"""
Clase abstracta base para todas las estrategias de trading
Define la interfaz que todas las estrategias deben implementar
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional


class BaseStrategy(ABC):
    """Clase base abstracta para estrategias de trading"""

    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    @abstractmethod
    def analyze(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Analizar datos y generar senal de trading

        Args:
            df: DataFrame con datos OHLCV
            indicators: Diccionario con indicadores calculados

        Returns:
            dict con: {"action": "buy"/"sell"/"hold", "score": 0.0-1.0, "reason": str}
        """
        pass

    def is_enabled(self) -> bool:
        """Verificar si la estrategia esta habilitada"""
        return self.enabled

    def enable(self):
        """Habilitar estrategia"""
        self.enabled = True

    def disable(self):
        """Deshabilitar estrategia"""
        self.enabled = False

    def __repr__(self):
        status = "ON" if self.enabled else "OFF"
        return f"{self.name}Strategy({status})"
