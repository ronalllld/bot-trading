"""
Tests unitarios de estrategias de trading
"""

import pytest
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.technical_indicators import TechnicalIndicators
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.combined_strategy import CombinedStrategy
from strategies.strategy_manager import StrategyManager


def generate_sample_ohlcv(n: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    prices = [100.0]
    for _ in range(n - 1):
        prices.append(max(prices[-1] + np.random.normal(0, 1), 1))
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


class TestRSIStrategy:
    def test_analyze_returns_valid_signal(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        strategy = RSIStrategy()
        result = strategy.analyze(df, indicators)
        assert "action" in result
        assert "score" in result
        assert result["action"] in ["buy", "sell", "hold"]
        assert 0 <= result["score"] <= 1

    def test_strategy_name(self):
        strategy = RSIStrategy()
        assert strategy.name == "RSI"

    def test_enable_disable(self):
        strategy = RSIStrategy()
        assert strategy.is_enabled()
        strategy.disable()
        assert not strategy.is_enabled()
        strategy.enable()
        assert strategy.is_enabled()


class TestMACDStrategy:
    def test_analyze_returns_valid_signal(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        strategy = MACDStrategy()
        result = strategy.analyze(df, indicators)
        assert "action" in result
        assert result["action"] in ["buy", "sell", "hold"]

    def test_strategy_name(self):
        strategy = MACDStrategy()
        assert strategy.name == "MACD"


class TestBollingerStrategy:
    def test_analyze_returns_valid_signal(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        strategy = BollingerStrategy()
        result = strategy.analyze(df, indicators)
        assert "action" in result
        assert result["action"] in ["buy", "sell", "hold"]


class TestCombinedStrategy:
    def test_analyze_returns_valid_signal(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        strategy = CombinedStrategy()
        result = strategy.analyze(df, indicators)
        assert "action" in result
        assert "score" in result

    def test_score_range(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        strategy = CombinedStrategy()
        result = strategy.analyze(df, indicators)
        assert 0 <= result["score"] <= 1


class TestStrategyManager:
    def test_available_strategies(self):
        manager = StrategyManager()
        available = manager.get_available_strategies()
        names = [s["name"] for s in available]
        assert "rsi" in names
        assert "macd" in names
        assert "bollinger" in names
        assert "combined" in names

    def test_set_active_strategy(self):
        manager = StrategyManager()
        manager.set_active_strategy("rsi")
        assert manager.active_strategy == "rsi"

    def test_analyze(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        manager = StrategyManager()
        result = manager.analyze(df, indicators)
        assert "action" in result

    def test_analyze_all(self):
        df = generate_sample_ohlcv()
        indicators = TechnicalIndicators.calculate_all_indicators(df)
        manager = StrategyManager()
        results = manager.analyze_all(df, indicators)
        assert len(results) == 4
