"""
Tests de gestion de riesgo
"""

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import Config
from risk_management.position_sizer import PositionSizer
from risk_management.stop_loss_manager import StopLossManager
from risk_management.take_profit_manager import TakeProfitManager
from database.models import Trade


@pytest.fixture
def config():
    return Config()


class TestPositionSizer:
    def test_calculate_position_size(self, config):
        sizer = PositionSizer(config)
        result = sizer.calculate_position_size(10.0, current_price=50000)
        assert result["valid"] is True
        assert result["amount_usdt"] == 5.0  # 50% de $10
        assert result["quantity"] > 0

    def test_position_too_small(self, config):
        sizer = PositionSizer(config)
        result = sizer.calculate_position_size(3.0, current_price=50000)
        # 50% de $3 = $1.50 < $5 minimo
        assert result["valid"] is False

    def test_can_open_position(self, config):
        sizer = PositionSizer(config)
        assert sizer.can_open_position(10.0, open_positions=0) is True
        assert sizer.can_open_position(10.0, open_positions=2) is False

    def test_max_positions_for_balance(self, config):
        sizer = PositionSizer(config)
        max_pos = sizer.get_max_positions_for_balance(10.0)
        assert max_pos <= config.MAX_POSITIONS
        assert max_pos > 0


class TestStopLossManager:
    def test_calculate_stop_loss(self, config):
        sl_manager = StopLossManager(config)
        sl = sl_manager.calculate_stop_loss(100.0)
        # 1.5% por defecto
        assert sl == 98.5

    def test_should_trigger(self, config):
        sl_manager = StopLossManager(config)
        trade = Trade(
            trade_id="test", symbol="BTC/USDT", side="buy",
            entry_price=100, quantity=1, investment=100,
            stop_loss=98.5
        )
        assert sl_manager.should_trigger_stop_loss(trade, 98.0) is True
        assert sl_manager.should_trigger_stop_loss(trade, 99.0) is False

    def test_trailing_stop(self, config):
        sl_manager = StopLossManager(config)
        trade = Trade(
            trade_id="test_trail", symbol="BTC/USDT", side="buy",
            entry_price=100, quantity=1, investment=100,
            stop_loss=98.5
        )
        # Precio sube a 102 (>1% ganancia) -> trailing se activa
        new_sl = sl_manager.update_trailing_stop(trade, 102.0)
        assert new_sl >= 98.5  # El SL nunca baja


class TestTakeProfitManager:
    def test_calculate_take_profit(self, config):
        tp_manager = TakeProfitManager(config)
        tp = tp_manager.calculate_take_profit(100.0)
        # 3% por defecto
        assert tp == 103.0

    def test_should_trigger(self, config):
        tp_manager = TakeProfitManager(config)
        trade = Trade(
            trade_id="test", symbol="BTC/USDT", side="buy",
            entry_price=100, quantity=1, investment=100,
            take_profit=103.0
        )
        assert tp_manager.should_trigger_take_profit(trade, 104.0) is True
        assert tp_manager.should_trigger_take_profit(trade, 102.0) is False

    def test_risk_reward_ratio(self, config):
        tp_manager = TakeProfitManager(config)
        rr = tp_manager.calculate_risk_reward(100.0)
        assert rr["risk_reward_ratio"] == config.TAKE_PROFIT / config.STOP_LOSS
        assert rr["tp_price"] == 103.0
        assert rr["sl_price"] == 98.5


class TestDailyLoss:
    def test_max_daily_loss_config(self, config):
        assert config.MAX_DAILY_LOSS == 5.0
        assert config.MAX_DAILY_TRADES == 20
