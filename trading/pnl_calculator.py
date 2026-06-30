"""
Calculo de Profit & Loss
Metricas avanzadas de rendimiento del trading
"""

import numpy as np
from typing import List
from database.models import Trade


class PnLCalculator:
    """Calcular metricas de rendimiento del trading"""

    @staticmethod
    def calculate_trade_pnl(entry_price: float, exit_price: float,
                            quantity: float, side: str = "buy") -> dict:
        """Calcular P&L de un trade individual"""
        if side == "buy":
            pnl = (exit_price - entry_price) * quantity
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl = (entry_price - exit_price) * quantity
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100

        return {"pnl": pnl, "pnl_percentage": pnl_pct}

    @staticmethod
    def calculate_unrealized_pnl(trade: Trade, current_price: float) -> dict:
        """Calcular P&L no realizado de una posicion abierta"""
        pnl = (current_price - trade.entry_price) * trade.quantity
        pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
        return {"pnl": pnl, "pnl_percentage": pnl_pct}

    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calcular Sharpe Ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        excess = [r - risk_free_rate for r in returns]
        avg = np.mean(excess)
        std = np.std(excess)
        if std == 0:
            return 0.0
        return float(avg / std * np.sqrt(252))

    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> float:
        """Calcular Max Drawdown en porcentaje"""
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return max_dd

    @staticmethod
    def calculate_profit_factor(trades: List[Trade]) -> float:
        """Calcular Profit Factor (ganancias brutas / perdidas brutas)"""
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @staticmethod
    def calculate_win_rate(trades: List[Trade]) -> float:
        """Calcular Win Rate en porcentaje"""
        if not trades:
            return 0.0
        winners = sum(1 for t in trades if t.pnl > 0)
        return (winners / len(trades)) * 100

    @staticmethod
    def get_performance_summary(trades: List[Trade],
                                 equity_curve: List[float] = None) -> dict:
        """Obtener resumen completo de rendimiento"""
        if not trades:
            return {
                "total_trades": 0, "win_rate": 0, "total_pnl": 0,
                "profit_factor": 0, "max_drawdown": 0, "sharpe_ratio": 0,
                "avg_win": 0, "avg_loss": 0, "best_trade": 0, "worst_trade": 0,
            }

        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]

        returns = []
        for t in trades:
            if t.investment > 0:
                returns.append(t.pnl / t.investment)

        result = {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": PnLCalculator.calculate_win_rate(trades),
            "total_pnl": sum(t.pnl for t in trades),
            "avg_win": (sum(t.pnl for t in wins) / len(wins)) if wins else 0,
            "avg_loss": (abs(sum(t.pnl for t in losses)) / len(losses)) if losses else 0,
            "best_trade": max((t.pnl for t in trades), default=0),
            "worst_trade": min((t.pnl for t in trades), default=0),
            "profit_factor": PnLCalculator.calculate_profit_factor(trades),
            "sharpe_ratio": PnLCalculator.calculate_sharpe_ratio(returns),
        }

        if equity_curve:
            result["max_drawdown"] = PnLCalculator.calculate_max_drawdown(equity_curve)

        return result
