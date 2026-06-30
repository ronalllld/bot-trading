"""
Calculo de indicadores tecnicos
RSI, MACD, Bollinger Bands, EMA, ATR, Volumen
Usa pandas-ta para los calculos
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from loguru import logger

from config.strategy_config import StrategyConfig


class TechnicalIndicators:
    """Calcular todos los indicadores tecnicos necesarios"""

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calcular RSI (Relative Strength Index)"""
        if period is None:
            period = StrategyConfig.RSI_PERIOD
        try:
            rsi = ta.rsi(df["close"], length=period)
            return rsi
        except Exception as e:
            logger.error(f"Error calculando RSI: {e}")
            return pd.Series(dtype=float)

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = None,
                       slow: int = None, signal: int = None) -> dict:
        """Calcular MACD (Moving Average Convergence Divergence)"""
        if fast is None:
            fast = StrategyConfig.MACD_FAST
        if slow is None:
            slow = StrategyConfig.MACD_SLOW
        if signal is None:
            signal = StrategyConfig.MACD_SIGNAL
        try:
            macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
            if macd is not None and not macd.empty:
                cols = macd.columns.tolist()
                return {
                    "macd": macd[cols[0]],          # Linea MACD
                    "signal": macd[cols[1]],        # Linea de senal
                    "histogram": macd[cols[2]],     # Histograma
                }
            return {"macd": pd.Series(dtype=float), "signal": pd.Series(dtype=float),
                    "histogram": pd.Series(dtype=float)}
        except Exception as e:
            logger.error(f"Error calculando MACD: {e}")
            return {"macd": pd.Series(dtype=float), "signal": pd.Series(dtype=float),
                    "histogram": pd.Series(dtype=float)}

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = None,
                                   std: float = None) -> dict:
        """Calcular Bandas de Bollinger"""
        if period is None:
            period = StrategyConfig.BB_PERIOD
        if std is None:
            std = StrategyConfig.BB_STD_DEV
        try:
            bb = ta.bbands(df["close"], length=period, std=std)
            if bb is not None and not bb.empty:
                cols = bb.columns.tolist()
                return {
                    "lower": bb[cols[0]],       # Banda inferior
                    "middle": bb[cols[1]],      # Banda media (SMA)
                    "upper": bb[cols[2]],       # Banda superior
                    "bandwidth": bb[cols[3]] if len(cols) > 3 else pd.Series(dtype=float),
                    "percent_b": bb[cols[4]] if len(cols) > 4 else pd.Series(dtype=float),
                }
            return {"lower": pd.Series(dtype=float), "middle": pd.Series(dtype=float),
                    "upper": pd.Series(dtype=float), "bandwidth": pd.Series(dtype=float),
                    "percent_b": pd.Series(dtype=float)}
        except Exception as e:
            logger.error(f"Error calculando Bollinger Bands: {e}")
            return {"lower": pd.Series(dtype=float), "middle": pd.Series(dtype=float),
                    "upper": pd.Series(dtype=float), "bandwidth": pd.Series(dtype=float),
                    "percent_b": pd.Series(dtype=float)}

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
        """Calcular EMA (Exponential Moving Average)"""
        try:
            return ta.ema(df["close"], length=period)
        except Exception as e:
            logger.error(f"Error calculando EMA({period}): {e}")
            return pd.Series(dtype=float)

    @staticmethod
    def calculate_all_emas(df: pd.DataFrame) -> dict:
        """Calcular todas las EMAs configuradas"""
        return {
            "ema_fast": TechnicalIndicators.calculate_ema(df, StrategyConfig.EMA_FAST),
            "ema_medium": TechnicalIndicators.calculate_ema(df, StrategyConfig.EMA_MEDIUM),
            "ema_slow": TechnicalIndicators.calculate_ema(df, StrategyConfig.EMA_SLOW),
            "ema_very_slow": TechnicalIndicators.calculate_ema(df, StrategyConfig.EMA_VERY_SLOW),
        }

    @staticmethod
    def calculate_volume_average(df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calcular media movil del volumen"""
        if period is None:
            period = StrategyConfig.VOLUME_MA_PERIOD
        try:
            return ta.sma(df["volume"], length=period)
        except Exception as e:
            logger.error(f"Error calculando volumen promedio: {e}")
            return pd.Series(dtype=float)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calcular ATR (Average True Range) - Volatilidad"""
        if period is None:
            period = StrategyConfig.ATR_PERIOD
        try:
            return ta.atr(df["high"], df["low"], df["close"], length=period)
        except Exception as e:
            logger.error(f"Error calculando ATR: {e}")
            return pd.Series(dtype=float)

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14,
                              d_period: int = 3) -> dict:
        """Calcular Oscilador Estocastico"""
        try:
            stoch = ta.stoch(df["high"], df["low"], df["close"],
                             k=k_period, d=d_period)
            if stoch is not None and not stoch.empty:
                cols = stoch.columns.tolist()
                return {
                    "k": stoch[cols[0]],
                    "d": stoch[cols[1]],
                }
            return {"k": pd.Series(dtype=float), "d": pd.Series(dtype=float)}
        except Exception as e:
            logger.error(f"Error calculando Estocastico: {e}")
            return {"k": pd.Series(dtype=float), "d": pd.Series(dtype=float)}

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> dict:
        """Calcular todos los indicadores de una vez"""
        indicators = {}

        indicators["rsi"] = TechnicalIndicators.calculate_rsi(df)
        indicators["macd"] = TechnicalIndicators.calculate_macd(df)
        indicators["bollinger"] = TechnicalIndicators.calculate_bollinger_bands(df)
        indicators["emas"] = TechnicalIndicators.calculate_all_emas(df)
        indicators["volume_ma"] = TechnicalIndicators.calculate_volume_average(df)
        indicators["atr"] = TechnicalIndicators.calculate_atr(df)

        return indicators
