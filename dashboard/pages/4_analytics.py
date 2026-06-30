"""
Pagina de Analiticas - Metricas avanzadas de rendimiento
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from config.config import Config
from database.db_manager import DatabaseManager
from trading.pnl_calculator import PnLCalculator

st.set_page_config(page_title="Analiticas", page_icon="📊", layout="wide")

@st.cache_resource
def get_db():
    config = Config()
    db = DatabaseManager(config.DB_PATH)
    import asyncio
    asyncio.run(db.initialize())
    return db, config

db, config = get_db()

st.title("📊 Analiticas Avanzadas")
st.divider()

closed_trades = db.get_closed_trades(limit=1000)

if not closed_trades:
    st.info("Sin datos suficientes para analiticas. Necesitas trades cerrados.")
else:
    # Calcular metricas avanzadas
    equity_curve = [config.INITIAL_CAPITAL]
    for t in reversed(closed_trades):
        equity_curve.append(equity_curve[-1] + t.pnl)

    performance = PnLCalculator.get_performance_summary(closed_trades, equity_curve)

    # --- Metricas principales ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sharpe Ratio", f"{performance.get('sharpe_ratio', 0):.2f}")
    with col2:
        st.metric("Max Drawdown", f"{performance.get('max_drawdown', 0):.2f}%")
    with col3:
        st.metric("Profit Factor", f"{performance.get('profit_factor', 0):.2f}")
    with col4:
        avg_win = performance.get("avg_win", 0)
        avg_loss = performance.get("avg_loss", 0)
        ratio = avg_win / avg_loss if avg_loss > 0 else 0
        st.metric("Avg Win / Avg Loss", f"{ratio:.2f}")

    st.divider()

    # --- Graficos ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribucion de P&L")
        pnls = [t.pnl for t in closed_trades]
        colors = ["#00d4aa" if p > 0 else "#ff4444" for p in pnls]
        fig = go.Figure(data=[go.Bar(y=pnls, marker_color=colors)])
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis_title="P&L (USDT)",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Histograma de Retornos (%)")
        pnl_pcts = [t.pnl_percentage for t in closed_trades]
        fig = px.histogram(
            x=pnl_pcts, nbins=30,
            labels={"x": "Retorno (%)", "y": "Frecuencia"},
            color_discrete_sequence=["#00d4aa"],
        )
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Heatmap de rendimiento por par ---
    st.subheader("Rendimiento por Par")
    pair_data = {}
    for t in closed_trades:
        if t.symbol not in pair_data:
            pair_data[t.symbol] = {"trades": 0, "pnl": 0, "wins": 0}
        pair_data[t.symbol]["trades"] += 1
        pair_data[t.symbol]["pnl"] += t.pnl
        if t.pnl > 0:
            pair_data[t.symbol]["wins"] += 1

    if pair_data:
        df_pairs = pd.DataFrame([
            {
                "Par": sym,
                "Trades": d["trades"],
                "P&L Total": f"${d['pnl']:.4f}",
                "Win Rate": f"{d['wins']/d['trades']*100:.1f}%" if d['trades'] > 0 else "0%",
                "P&L Numerico": d["pnl"],
            }
            for sym, d in pair_data.items()
        ])
        df_pairs = df_pairs.sort_values("P&L Numerico", ascending=False)
        st.dataframe(
            df_pairs[["Par", "Trades", "P&L Total", "Win Rate"]],
            use_container_width=True, hide_index=True,
        )

    # --- Performance por estrategia ---
    st.subheader("Rendimiento por Estrategia")
    strat_data = {}
    for t in closed_trades:
        s = t.strategy or "unknown"
        if s not in strat_data:
            strat_data[s] = {"trades": 0, "pnl": 0, "wins": 0}
        strat_data[s]["trades"] += 1
        strat_data[s]["pnl"] += t.pnl
        if t.pnl > 0:
            strat_data[s]["wins"] += 1

    if strat_data:
        df_strat = pd.DataFrame([
            {
                "Estrategia": s,
                "Trades": d["trades"],
                "P&L Total": f"${d['pnl']:.4f}",
                "Win Rate": f"{d['wins']/d['trades']*100:.1f}%",
            }
            for s, d in strat_data.items()
        ])
        st.dataframe(df_strat, use_container_width=True, hide_index=True)

    # --- Metricas detalladas ---
    st.divider()
    st.subheader("Metricas Detalladas")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Performance**")
        st.markdown(f"- Total Trades: {performance['total_trades']}")
        st.markdown(f"- Ganadores: {performance['winning_trades']}")
        st.markdown(f"- Perdedores: {performance['losing_trades']}")
        st.markdown(f"- Win Rate: {performance['win_rate']:.1f}%")

    with col2:
        st.markdown("**P&L**")
        st.markdown(f"- Total P&L: ${performance['total_pnl']:.4f}")
        st.markdown(f"- Mejor Trade: ${performance['best_trade']:.4f}")
        st.markdown(f"- Peor Trade: ${performance['worst_trade']:.4f}")
        st.markdown(f"- Avg Win: ${performance['avg_win']:.4f}")

    with col3:
        st.markdown("**Riesgo**")
        st.markdown(f"- Avg Loss: ${performance['avg_loss']:.4f}")
        st.markdown(f"- Sharpe: {performance.get('sharpe_ratio', 0):.2f}")
        st.markdown(f"- Max DD: {performance.get('max_drawdown', 0):.2f}%")
        st.markdown(f"- Profit Factor: {performance['profit_factor']:.2f}")

if st.button("🔄 Actualizar", use_container_width=True):
    st.rerun()
