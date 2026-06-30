"""
Estrategia basada en RSI (Relative Strength Index)
Compra en sobreventa, vende en sobrecompra
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy
from config.strategy_config import StrategyConfig


class RSIStrategy(BaseStrategy):
    """Estrategia de trading basada en RSI"""

    def __init__(self):
        super().__init__("RSI")

    def analyze(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Senal de COMPRA: RSI < 30, Volumen > promedio, EMA9 > EMA21
        Senal de VENTA: RSI > 70
        """
        rsi = indicators.get("rsi")
        volume_ma = indicators.get("volume_ma")
        emas = indicators.get("emas", {})

        if rsi is None or rsi.empty or len(rsi) < 2:
            return {"action": "hold", "score": 0.0, "reason": "Datos RSI insuficientes"}

        current_rsi = float(rsi.iloc[-1])
        current_volume = float(df["volume"].iloc[-1])
        avg_volume = float(volume_ma.iloc[-1]) if volume_ma is not None and not volume_ma.empty else 0

        ema_fast = emas.get("ema_fast")
        ema_medium = emas.get("ema_medium")

        # --- Senal de COMPRA ---
        if current_rsi < StrategyConfig.RSI_OVERSOLD:
            score = 0.8

            # Bonus por volumen alto
            if avg_volume > 0 and current_volume > avg_volume:
                score += 0.1

            # Bonus por tendencia alcista (EMA9 > EMA21)
            if (ema_fast is not None and not ema_fast.empty and
                    ema_medium is not None and not ema_medium.empty):
                if float(ema_fast.iloc[-1]) > float(ema_medium.iloc[-1]):
                    score += 0.1

            score = min(score, 1.0)
            return {
                "action": "buy",
                "score": score,
                "reason": f"RSI sobreventa ({current_rsi:.1f})",
            }

        # --- Senal de VENTA ---
        elif current_rsi > StrategyConfig.RSI_OVERBOUGHT:
            score = 0.8

            if avg_volume > 0 and current_volume > avg_volume:
                score += 0.1

            if (ema_fast is not None and not ema_fast.empty and
                    ema_medium is not None and not ema_medium.empty):
                if float(ema_fast.iloc[-1]) < float(ema_medium.iloc[-1]):
                    score += 0.1

            score = min(score, 1.0)
            return {
                "action": "sell",
                "score": score,
                "reason": f"RSI sobrecompra ({current_rsi:.1f})",
            }

        return {"action": "hold", "score": 0.0, "reason": f"RSI neutral ({current_rsi:.1f})"}
