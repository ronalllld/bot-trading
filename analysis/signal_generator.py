"""
Generacion y validacion de senales de trading
Sistema de puntuacion combinado de multiples indicadores
"""

import pandas as pd
from loguru import logger
from config.strategy_config import StrategyConfig


class SignalGenerator:
    """Generar senales de compra/venta basadas en indicadores"""

    def __init__(self):
        self.buy_threshold = StrategyConfig.BUY_THRESHOLD
        self.sell_threshold = StrategyConfig.SELL_THRESHOLD

    def generate_signal(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Generar senal combinada usando todos los indicadores
        Retorna: {"action": "buy"/"sell"/"hold", "score": 0.0-1.0, "details": {...}}
        """
        buy_score = 0.0
        sell_score = 0.0
        details = {}

        # --- RSI Score ---
        rsi_buy, rsi_sell, rsi_detail = self._evaluate_rsi(indicators.get("rsi"))
        buy_score += rsi_buy * StrategyConfig.WEIGHT_RSI
        sell_score += rsi_sell * StrategyConfig.WEIGHT_RSI
        details["rsi"] = rsi_detail

        # --- MACD Score ---
        macd_buy, macd_sell, macd_detail = self._evaluate_macd(indicators.get("macd", {}))
        buy_score += macd_buy * StrategyConfig.WEIGHT_MACD
        sell_score += macd_sell * StrategyConfig.WEIGHT_MACD
        details["macd"] = macd_detail

        # --- Bollinger Bands Score ---
        bb_buy, bb_sell, bb_detail = self._evaluate_bollinger(
            df, indicators.get("bollinger", {})
        )
        buy_score += bb_buy * StrategyConfig.WEIGHT_BB
        sell_score += bb_sell * StrategyConfig.WEIGHT_BB
        details["bollinger"] = bb_detail

        # --- Volume Score ---
        vol_buy, vol_sell, vol_detail = self._evaluate_volume(
            df, indicators.get("volume_ma")
        )
        buy_score += vol_buy * StrategyConfig.WEIGHT_VOLUME
        sell_score += vol_sell * StrategyConfig.WEIGHT_VOLUME
        details["volume"] = vol_detail

        # Determinar accion
        action = "hold"
        score = 0.0

        if buy_score >= self.buy_threshold:
            action = "buy"
            score = buy_score
        elif sell_score >= self.sell_threshold:
            action = "sell"
            score = sell_score

        details["buy_score"] = round(buy_score, 4)
        details["sell_score"] = round(sell_score, 4)

        return {"action": action, "score": round(score, 4), "details": details}

    def _evaluate_rsi(self, rsi: pd.Series) -> tuple:
        """Evaluar RSI - retorna (buy_score, sell_score, detail)"""
        if rsi is None or rsi.empty:
            return 0.0, 0.0, "sin datos"

        current_rsi = float(rsi.iloc[-1])
        buy_score = 0.0
        sell_score = 0.0

        if current_rsi < StrategyConfig.RSI_OVERSOLD:
            # Sobreventa fuerte -> senal de compra
            buy_score = 1.0
        elif current_rsi < 40:
            # Zona baja -> senal moderada de compra
            buy_score = 0.6
        elif current_rsi > StrategyConfig.RSI_OVERBOUGHT:
            # Sobrecompra fuerte -> senal de venta
            sell_score = 1.0
        elif current_rsi > 60:
            # Zona alta -> senal moderada de venta
            sell_score = 0.4

        return buy_score, sell_score, f"RSI={current_rsi:.1f}"

    def _evaluate_macd(self, macd_data: dict) -> tuple:
        """Evaluar MACD - retorna (buy_score, sell_score, detail)"""
        macd_line = macd_data.get("macd")
        signal_line = macd_data.get("signal")
        histogram = macd_data.get("histogram")

        if macd_line is None or macd_line.empty or len(macd_line) < 2:
            return 0.0, 0.0, "sin datos"

        current_macd = float(macd_line.iloc[-1])
        prev_macd = float(macd_line.iloc[-2])
        current_signal = float(signal_line.iloc[-1])
        prev_signal = float(signal_line.iloc[-2])
        current_hist = float(histogram.iloc[-1])

        buy_score = 0.0
        sell_score = 0.0

        # Cruce alcista: MACD cruza por encima de senal
        if prev_macd <= prev_signal and current_macd > current_signal:
            buy_score = 1.0
        elif current_hist > 0 and current_macd > current_signal:
            buy_score = 0.6

        # Cruce bajista: MACD cruza por debajo de senal
        if prev_macd >= prev_signal and current_macd < current_signal:
            sell_score = 1.0
        elif current_hist < 0 and current_macd < current_signal:
            sell_score = 0.6

        return buy_score, sell_score, f"MACD={current_macd:.4f} Hist={current_hist:.4f}"

    def _evaluate_bollinger(self, df: pd.DataFrame, bb_data: dict) -> tuple:
        """Evaluar Bollinger Bands - retorna (buy_score, sell_score, detail)"""
        lower = bb_data.get("lower")
        upper = bb_data.get("upper")

        if lower is None or lower.empty or upper is None or upper.empty:
            return 0.0, 0.0, "sin datos"

        current_price = float(df["close"].iloc[-1])
        lower_band = float(lower.iloc[-1])
        upper_band = float(upper.iloc[-1])

        buy_score = 0.0
        sell_score = 0.0

        # Precio cerca o por debajo de banda inferior -> compra
        if current_price <= lower_band:
            buy_score = 1.0
        elif current_price <= lower_band * 1.01:
            buy_score = 0.7

        # Precio cerca o por encima de banda superior -> venta
        if current_price >= upper_band:
            sell_score = 1.0
        elif current_price >= upper_band * 0.99:
            sell_score = 0.7

        return buy_score, sell_score, f"Precio={current_price:.2f} BB=[{lower_band:.2f}-{upper_band:.2f}]"

    def _evaluate_volume(self, df: pd.DataFrame, volume_ma: pd.Series) -> tuple:
        """Evaluar volumen - retorna (buy_score, sell_score, detail)"""
        if volume_ma is None or volume_ma.empty:
            return 0.0, 0.0, "sin datos"

        current_volume = float(df["volume"].iloc[-1])
        avg_volume = float(volume_ma.iloc[-1])

        if avg_volume == 0:
            return 0.0, 0.0, "volumen=0"

        volume_ratio = current_volume / avg_volume
        buy_score = 0.0
        sell_score = 0.0

        # Volumen alto confirma la tendencia
        if volume_ratio > 1.5:
            buy_score = 1.0
            sell_score = 1.0  # Confirma ambas direcciones
        elif volume_ratio > 1.0:
            buy_score = 0.6
            sell_score = 0.6

        return buy_score, sell_score, f"Vol_ratio={volume_ratio:.2f}"
