"""
Sistema de backtesting historico
Permite probar estrategias con datos pasados
"""

import pandas as pd
from typing import List
from loguru import logger

from analysis.technical_indicators import TechnicalIndicators
from analysis.signal_generator import SignalGenerator
from config.config import Config


class Backtester:
    """Realizar backtesting de estrategias con datos historicos"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.signal_generator = SignalGenerator()
        self.results = []

    def run_backtest(self, df: pd.DataFrame, symbol: str = "TEST/USDT",
                     initial_capital: float = None) -> dict:
        """
        Ejecutar backtesting sobre datos historicos
        df: DataFrame con columnas OHLCV
        """
        if initial_capital is None:
            initial_capital = self.config.INITIAL_CAPITAL

        capital = initial_capital
        position = None  # {"entry_price", "quantity", "entry_idx"}
        trades = []
        equity_curve = [capital]

        take_profit_pct = self.config.TAKE_PROFIT / 100
        stop_loss_pct = self.config.STOP_LOSS / 100
        position_size_pct = self.config.POSITION_SIZE_PERCENTAGE / 100

        # Calcular indicadores para todo el dataset
        indicators = TechnicalIndicators.calculate_all_indicators(df)

        # Iterar sobre cada vela (empezar despues de tener suficientes datos)
        start_idx = 50
        for i in range(start_idx, len(df)):
            current_price = float(df["close"].iloc[i])
            current_time = df.index[i]

            # Si tenemos posicion abierta, verificar TP/SL
            if position:
                tp_price = position["entry_price"] * (1 + take_profit_pct)
                sl_price = position["entry_price"] * (1 - stop_loss_pct)

                if current_price >= tp_price:
                    # Take Profit
                    pnl = (current_price - position["entry_price"]) * position["quantity"]
                    capital += position["investment"] + pnl
                    trades.append({
                        "symbol": symbol,
                        "entry_price": position["entry_price"],
                        "exit_price": current_price,
                        "quantity": position["quantity"],
                        "investment": position["investment"],
                        "pnl": pnl,
                        "pnl_pct": (pnl / position["investment"]) * 100,
                        "exit_reason": "tp",
                        "entry_time": position["entry_time"],
                        "exit_time": current_time,
                    })
                    position = None

                elif current_price <= sl_price:
                    # Stop Loss
                    pnl = (current_price - position["entry_price"]) * position["quantity"]
                    capital += position["investment"] + pnl
                    trades.append({
                        "symbol": symbol,
                        "entry_price": position["entry_price"],
                        "exit_price": current_price,
                        "quantity": position["quantity"],
                        "investment": position["investment"],
                        "pnl": pnl,
                        "pnl_pct": (pnl / position["investment"]) * 100,
                        "exit_reason": "sl",
                        "entry_time": position["entry_time"],
                        "exit_time": current_time,
                    })
                    position = None

            # Si no tenemos posicion, buscar senales de compra
            if position is None:
                # Crear sub-dataframe hasta el punto actual
                sub_indicators = self._slice_indicators(indicators, i)
                signal = self.signal_generator.generate_signal(df.iloc[:i+1], sub_indicators)

                if signal["action"] == "buy" and capital > 0:
                    investment = capital * position_size_pct
                    if investment >= 5.0:  # Minimo $5
                        quantity = investment / current_price
                        capital -= investment
                        position = {
                            "entry_price": current_price,
                            "quantity": quantity,
                            "investment": investment,
                            "entry_time": current_time,
                        }

            # Registrar equity
            pos_value = 0
            if position:
                pos_value = position["quantity"] * current_price
            equity_curve.append(capital + pos_value)

        # Cerrar posicion abierta al final
        if position:
            final_price = float(df["close"].iloc[-1])
            pnl = (final_price - position["entry_price"]) * position["quantity"]
            capital += position["investment"] + pnl
            trades.append({
                "symbol": symbol,
                "entry_price": position["entry_price"],
                "exit_price": final_price,
                "quantity": position["quantity"],
                "investment": position["investment"],
                "pnl": pnl,
                "pnl_pct": (pnl / position["investment"]) * 100,
                "exit_reason": "end",
                "entry_time": position["entry_time"],
                "exit_time": df.index[-1],
            })

        # Calcular metricas
        return self._calculate_metrics(trades, equity_curve, initial_capital, capital)

    def _slice_indicators(self, indicators: dict, idx: int) -> dict:
        """Obtener indicadores hasta un indice especifico"""
        sliced = {}
        sliced["rsi"] = indicators["rsi"].iloc[:idx+1] if indicators["rsi"] is not None else pd.Series(dtype=float)

        sliced["macd"] = {}
        for key in ["macd", "signal", "histogram"]:
            series = indicators["macd"].get(key)
            sliced["macd"][key] = series.iloc[:idx+1] if series is not None else pd.Series(dtype=float)

        sliced["bollinger"] = {}
        for key in ["lower", "middle", "upper", "bandwidth", "percent_b"]:
            series = indicators["bollinger"].get(key)
            sliced["bollinger"][key] = series.iloc[:idx+1] if series is not None else pd.Series(dtype=float)

        sliced["volume_ma"] = indicators["volume_ma"].iloc[:idx+1] if indicators["volume_ma"] is not None else pd.Series(dtype=float)

        sliced["emas"] = {}
        for key, series in indicators.get("emas", {}).items():
            sliced["emas"][key] = series.iloc[:idx+1] if series is not None else pd.Series(dtype=float)

        sliced["atr"] = indicators["atr"].iloc[:idx+1] if indicators["atr"] is not None else pd.Series(dtype=float)

        return sliced

    def _calculate_metrics(self, trades: list, equity_curve: list,
                           initial_capital: float, final_capital: float) -> dict:
        """Calcular metricas de rendimiento del backtest"""
        if not trades:
            return {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate": 0, "total_pnl": 0, "total_return_pct": 0,
                "max_drawdown": 0, "profit_factor": 0, "sharpe_ratio": 0,
                "trades": [], "equity_curve": equity_curve,
            }

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        total_wins = sum(t["pnl"] for t in wins)
        total_losses = abs(sum(t["pnl"] for t in losses))

        # Max Drawdown
        peak = equity_curve[0]
        max_dd = 0
        for val in equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        # Sharpe Ratio (simplificado)
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1] > 0:
                ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                returns.append(ret)

        import numpy as np
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0

        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": (len(wins) / len(trades) * 100) if trades else 0,
            "total_pnl": final_capital - initial_capital,
            "total_return_pct": ((final_capital - initial_capital) / initial_capital * 100),
            "avg_win": (total_wins / len(wins)) if wins else 0,
            "avg_loss": (total_losses / len(losses)) if losses else 0,
            "best_trade": max((t["pnl"] for t in trades), default=0),
            "worst_trade": min((t["pnl"] for t in trades), default=0),
            "max_drawdown": max_dd,
            "profit_factor": (total_wins / total_losses) if total_losses > 0 else float("inf"),
            "sharpe_ratio": sharpe,
            "trades": trades,
            "equity_curve": equity_curve,
        }
