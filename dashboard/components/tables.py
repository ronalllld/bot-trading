"""
Componentes de tablas de datos para el dashboard
"""

import pandas as pd
from typing import List
from database.models import Trade


def trades_to_dataframe(trades: List[Trade]) -> pd.DataFrame:
    """Convertir lista de trades a DataFrame para display"""
    if not trades:
        return pd.DataFrame()

    data = []
    for t in trades:
        pnl_sign = "+" if t.pnl and t.pnl > 0 else ""
        data.append({
            "Par": t.symbol,
            "Lado": t.side.upper(),
            "Entrada": f"${t.entry_price:.4f}",
            "Salida": f"${t.exit_price:.4f}" if t.exit_price else "-",
            "Cantidad": f"{t.quantity:.8f}",
            "Inversion": f"${t.investment:.2f}",
            "P&L": f"{pnl_sign}${t.pnl:.4f}" if t.pnl else "-",
            "P&L %": f"{pnl_sign}{t.pnl_percentage:.2f}%" if t.pnl_percentage else "-",
            "Estado": t.status,
            "Razon": t.exit_reason or "-",
            "Estrategia": t.strategy,
        })

    return pd.DataFrame(data)


def positions_to_dataframe(positions: List[dict]) -> pd.DataFrame:
    """Convertir posiciones con P&L a DataFrame"""
    if not positions:
        return pd.DataFrame()

    data = []
    for p in positions:
        trade = p["trade"]
        pnl_sign = "+" if p["pnl"] > 0 else ""
        data.append({
            "Par": trade.symbol,
            "Precio Entrada": f"${trade.entry_price:.4f}",
            "Precio Actual": f"${p['current_price']:.4f}",
            "P&L": f"{pnl_sign}${p['pnl']:.4f}",
            "P&L %": f"{pnl_sign}{p['pnl_percentage']:.2f}%",
            "Valor Actual": f"${p['current_value']:.2f}",
            "Dist. TP": f"{p['distance_to_tp']:.2f}%",
            "Dist. SL": f"{p['distance_to_sl']:.2f}%",
        })

    return pd.DataFrame(data)
