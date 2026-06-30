"""
Calculo de indicadores tecnicos
RSI, MACD, Bollinger Bands, EMA, ATR, Volumen
Implementados con pandas/numpy puro sin dependencias externas
"""

import pandas as pd
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
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
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
            ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
            ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            return {
                "macd": macd_line,
                "signal": signal_line,
                "histogram": histogram,
            }
        except Exception as e:
            logger.error(f"Error calculando MACD: {e}")
            return {
                "macd": pd.Series(dtype=float),
                "signal": pd.Series(dtype=float),
                "histogram": pd.Series(dtype=float),
            }

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = None,
                                   std: float = None) -> dict:
        """Calcular Bandas de Bollinger"""
        if period is None:
            period = StrategyConfig.BB_PERIOD
        if std is None:
            std = StrategyConfig.BB_STD_DEV
        try:
            middle = df["close"].rolling(period).mean()
            std_dev = df["close"].rolling(period).std()
            upper = middle + std * std_dev
            lower = middle - std * std_dev
            bandwidth = (upper - lower) / middle
            percent_b = (df["close"] - lower) / (upper - lower)
            return {
                "lower": lower,
                "middle": middle,
                "upper": upper,
                "bandwidth": bandwidth,
                "percent_b": percent_b,
            }
        except Exception as e:
            logger.error(f"Error calculando Bollinger Bands: {e}")
            return {
                "lower": pd.Series(dtype=float),
                "middle": pd.Series(dtype=float),
                "upper": pd.Series(dtype=float),
                "bandwidth": pd.Series(dtype=float),
                "percent_b": pd.Series(dtype=float),
            }

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
        """Calcular EMA (Exponential Moving Average)"""
        try:
            return df["close"].ewm(span=period, adjust=False).mean()
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
            return df["volume"].rolling(period).mean()
        except Exception as e:
            logger.error(f"Error calculando volumen promedio: {e}")
            return pd.Series(dtype=float)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calcular ATR (Average True Range) - Volatilidad"""
        if period is None:
            period = StrategyConfig.ATR_PERIOD
        try:
            tr = pd.concat([
                df["high"] - df["low"],
                (df["high"] - df["close"].shift()).abs(),
                (df["low"] - df["close"].shift()).abs(),
            ], axis=1).max(axis=1)
            return tr.ewm(com=period - 1, min_periods=period).mean()
        except Exception as e:
            logger.error(f"Error calculando ATR: {e}")
            return pd.Series(dtype=float)

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14,
                              d_period: int = 3) -> dict:
        """Calcular Oscilador Estocastico"""
        try:
            lowest_low = df["low"].rolling(k_period).min()
            highest_high = df["high"].rolling(k_period).max()
            k = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low)
            d = k.rolling(d_period).mean()
            return {"k": k, "d": d}
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
