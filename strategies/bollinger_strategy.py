"""
Estrategia basada en Bandas de Bollinger
Compra cuando el precio toca banda inferior, vende en banda superior
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy


class BollingerStrategy(BaseStrategy):
    """Estrategia de trading basada en Bandas de Bollinger"""

    def __init__(self):
        super().__init__("Bollinger")

    def analyze(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Senal de COMPRA: Precio <= Banda inferior (rebote potencial)
        Senal de VENTA: Precio >= Banda superior (posible retroceso)
        """
        bb = indicators.get("bollinger", {})
        lower = bb.get("lower")
        upper = bb.get("upper")
        middle = bb.get("middle")

        if lower is None or lower.empty or upper is None or upper.empty:
            return {"action": "hold", "score": 0.0, "reason": "Datos BB insuficientes"}

        current_price = float(df["close"].iloc[-1])
        prev_price = float(df["close"].iloc[-2])
        lower_band = float(lower.iloc[-1])
        upper_band = float(upper.iloc[-1])
        middle_band = float(middle.iloc[-1]) if middle is not None and not middle.empty else 0

        # --- Precio toca o cruza banda inferior -> COMPRA ---
        if current_price <= lower_band:
            score = 0.85

            # Bonus si el precio rebota (cerro mas alto que abrio en la vela)
            if current_price > float(df["open"].iloc[-1]):
                score += 0.1

            score = min(score, 1.0)
            return {
                "action": "buy",
                "score": score,
                "reason": f"Precio (${current_price:.2f}) en banda inferior (${lower_band:.2f})",
            }

        # --- Precio cerca de banda inferior ---
        elif current_price <= lower_band * 1.005:
            return {
                "action": "buy",
                "score": 0.6,
                "reason": f"Precio cerca de banda inferior",
            }

        # --- Precio toca o cruza banda superior -> VENTA ---
        elif current_price >= upper_band:
            score = 0.85

            if current_price < float(df["open"].iloc[-1]):
                score += 0.1

            score = min(score, 1.0)
            return {
                "action": "sell",
                "score": score,
                "reason": f"Precio (${current_price:.2f}) en banda superior (${upper_band:.2f})",
            }

        # --- Precio cerca de banda superior ---
        elif current_price >= upper_band * 0.995:
            return {
                "action": "sell",
                "score": 0.6,
                "reason": f"Precio cerca de banda superior",
            }

        return {"action": "hold", "score": 0.0, "reason": "Precio dentro de bandas"}
