"""
Estrategia basada en MACD (Moving Average Convergence Divergence)
Cruces de linea MACD con linea de senal
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy
from config.strategy_config import StrategyConfig


class MACDStrategy(BaseStrategy):
    """Estrategia de trading basada en MACD"""

    def __init__(self):
        super().__init__("MACD")

    def analyze(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Senal de COMPRA: MACD cruza encima de senal + histograma positivo + precio > EMA50
        Senal de VENTA: MACD cruza debajo de senal
        """
        macd_data = indicators.get("macd", {})
        emas = indicators.get("emas", {})

        macd_line = macd_data.get("macd")
        signal_line = macd_data.get("signal")
        histogram = macd_data.get("histogram")

        if (macd_line is None or macd_line.empty or len(macd_line) < 2 or
                signal_line is None or signal_line.empty):
            return {"action": "hold", "score": 0.0, "reason": "Datos MACD insuficientes"}

        current_macd = float(macd_line.iloc[-1])
        prev_macd = float(macd_line.iloc[-2])
        current_signal = float(signal_line.iloc[-1])
        prev_signal = float(signal_line.iloc[-2])
        current_hist = float(histogram.iloc[-1]) if histogram is not None and not histogram.empty else 0

        current_price = float(df["close"].iloc[-1])
        ema_slow = emas.get("ema_slow")

        # --- Cruce alcista: MACD cruza por encima de senal ---
        if prev_macd <= prev_signal and current_macd > current_signal:
            score = 0.8

            # Bonus: histograma positivo
            if current_hist > 0:
                score += 0.1

            # Bonus: precio por encima de EMA50
            if ema_slow is not None and not ema_slow.empty:
                if current_price > float(ema_slow.iloc[-1]):
                    score += 0.1

            score = min(score, 1.0)
            return {
                "action": "buy",
                "score": score,
                "reason": f"Cruce alcista MACD (hist={current_hist:.4f})",
            }

        # --- Cruce bajista: MACD cruza por debajo de senal ---
        elif prev_macd >= prev_signal and current_macd < current_signal:
            score = 0.8

            if current_hist < 0:
                score += 0.1

            if ema_slow is not None and not ema_slow.empty:
                if current_price < float(ema_slow.iloc[-1]):
                    score += 0.1

            score = min(score, 1.0)
            return {
                "action": "sell",
                "score": score,
                "reason": f"Cruce bajista MACD (hist={current_hist:.4f})",
            }

        return {"action": "hold", "score": 0.0, "reason": "MACD sin cruce"}
