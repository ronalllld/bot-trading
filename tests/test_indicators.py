"""
Tests unitarios de indicadores tecnicos
"""

import pytest
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.technical_indicators import TechnicalIndicators


def generate_sample_ohlcv(n: int = 200, start_price: float = 100.0) -> pd.DataFrame:
    """Generar datos OHLCV de ejemplo para tests"""
    np.random.seed(42)
    prices = [start_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 1)
        prices.append(max(prices[-1] + change, 1))

    data = {
        "open": [p + np.random.uniform(-0.5, 0.5) for p in prices],
        "high": [p + abs(np.random.normal(0, 1)) for p in prices],
        "low": [p - abs(np.random.normal(0, 1)) for p in prices],
        "close": prices,
        "volume": [np.random.uniform(1000, 10000) for _ in prices],
    }
    df = pd.DataFrame(data)
    df.index = pd.date_range("2024-01-01", periods=n, freq="5min")
    return df


class TestRSI:
    """Tests para calculo de RSI"""

    def test_rsi_returns_series(self):
        df = generate_sample_ohlcv()
        rsi = TechnicalIndicators.calculate_rsi(df)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(df)

    def test_rsi_range(self):
        df = generate_sample_ohlcv()
        rsi = TechnicalIndicators.calculate_rsi(df)
        valid = rsi.dropna()
        assert all(0 <= v <= 100 for v in valid)

    def test_rsi_custom_period(self):
        df = generate_sample_ohlcv()
        rsi = TechnicalIndicators.calculate_rsi(df, period=7)
        valid = rsi.dropna()
        assert len(valid) > 0

    def test_rsi_empty_data(self):
        df = pd.DataFrame({"close": []})
        rsi = TechnicalIndicators.calculate_rsi(df)
        assert isinstance(rsi, pd.Series)


class TestMACD:
    """Tests para calculo de MACD"""

    def test_macd_returns_dict(self):
        df = generate_sample_ohlcv()
        macd = TechnicalIndicators.calculate_macd(df)
        assert isinstance(macd, dict)
        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd

    def test_macd_values(self):
        df = generate_sample_ohlcv()
        macd = TechnicalIndicators.calculate_macd(df)
        assert len(macd["macd"]) == len(df)

    def test_macd_custom_params(self):
        df = generate_sample_ohlcv()
        macd = TechnicalIndicators.calculate_macd(df, fast=8, slow=21, signal=5)
        assert len(macd["macd"]) > 0


class TestBollingerBands:
    """Tests para calculo de Bandas de Bollinger"""

    def test_bb_returns_dict(self):
        df = generate_sample_ohlcv()
        bb = TechnicalIndicators.calculate_bollinger_bands(df)
        assert isinstance(bb, dict)
        assert "lower" in bb
        assert "middle" in bb
        assert "upper" in bb

    def test_bb_upper_greater_than_lower(self):
        df = generate_sample_ohlcv()
        bb = TechnicalIndicators.calculate_bollinger_bands(df)
        upper = bb["upper"].dropna()
        lower = bb["lower"].dropna()
        for u, l in zip(upper, lower):
            assert u >= l

    def test_bb_custom_params(self):
        df = generate_sample_ohlcv()
        bb = TechnicalIndicators.calculate_bollinger_bands(df, period=10, std=1.5)
        assert len(bb["middle"].dropna()) > 0


class TestEMA:
    """Tests para calculo de EMA"""

    def test_ema_returns_series(self):
        df = generate_sample_ohlcv()
        ema = TechnicalIndicators.calculate_ema(df, period=9)
        assert isinstance(ema, pd.Series)

    def test_all_emas(self):
        df = generate_sample_ohlcv()
        emas = TechnicalIndicators.calculate_all_emas(df)
        assert "ema_fast" in emas
        assert "ema_medium" in emas
        assert "ema_slow" in emas
        assert "ema_very_slow" in emas


class TestAllIndicators:
    """Tests para calculo de todos los indicadores"""

    def test_calculate_all(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "bollinger" in indicators
        assert "emas" in indicators
        assert "volume_ma" in indicators
        assert "atr" in indicators

    def test_atr_positive(self):
        df = generate_sample_ohlcv()
        atr = TechnicalIndicators.calculate_atr(df)
        valid = atr.dropna()
        assert all(v >= 0 for v in valid)
