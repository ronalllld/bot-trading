"""
Estrategia combinada multi-indicador
Usa sistema de puntuacion ponderado con RSI, MACD, Bollinger y Volumen
Esta es la estrategia principal y recomendada
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy
from analysis.signal_generator import SignalGenerator


class CombinedStrategy(BaseStrategy):
    """Estrategia combinada que usa multiples indicadores con pesos"""

    def __init__(self):
        super().__init__("Combined")
        self.signal_generator = SignalGenerator()

    def analyze(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Sistema de puntuacion combinado:
        - RSI: 30% del peso
        - MACD: 30% del peso
        - Bollinger Bands: 20% del peso
        - Volumen: 20% del peso

        Compra si score > 0.7, Venta si score > 0.7
        """
        signal = self.signal_generator.generate_signal(df, indicators)

        reason_parts = []
        details = signal.get("details", {})

        for key in ["rsi", "macd", "bollinger", "volume"]:
            if key in details and isinstance(details[key], str):
                reason_parts.append(details[key])

        reason = " | ".join(reason_parts) if reason_parts else "Analisis combinado"

        return {
            "action": signal["action"],
            "score": signal["score"],
            "reason": reason,
            "details": details,
        }
