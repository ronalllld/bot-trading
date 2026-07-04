"""
Pagina de Historial - Todos los trades cerrados
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from config.config import Config
from database.db_manager import DatabaseManager

st.set_page_config(page_title="Historial", page_icon="📜", layout="wide")

@st.cache_resource
def get_db():
    config = Config()
    db = DatabaseManager(config.DB_PATH)
    import asyncio
    asyncio.run(db.initialize())
    return db, config

db, config = get_db()

st.title("📜 Historial de Trades")
st.divider()

# Obtener trades cerrados
closed_trades = db.get_closed_trades(limit=500)

if not closed_trades:
    st.info("Sin historial de trades cerrados.")
else:
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        symbols = list(set(t.symbol for t in closed_trades))
        filter_symbol = st.selectbox("Filtrar por par", ["Todos"] + sorted(symbols))
    with col2:
        filter_result = st.selectbox("Resultado", ["Todos", "Ganadores", "Perdedores"])
    with col3:
        strategies = list(set(t.strategy for t in closed_trades if t.strategy))
        filter_strategy = st.selectbox("Estrategia", ["Todas"] + sorted(strategies))

    # Aplicar filtros
    filtered = closed_trades
    if filter_symbol != "Todos":
        filtered = [t for t in filtered if t.symbol == filter_symbol]
    if filter_result == "Ganadores":
        filtered = [t for t in filtered if t.pnl > 0]
    elif filter_result == "Perdedores":
        filtered = [t for t in filtered if t.pnl <= 0]
    if filter_strategy != "Todas":
        filtered = [t for t in filtered if t.strategy == filter_strategy]

    # Estadisticas de los trades filtrados
    st.divider()
    if filtered:
        wins = [t for t in filtered if t.pnl > 0]
        losses = [t for t in filtered if t.pnl <= 0]
        total_pnl = sum(t.pnl for t in filtered)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Trades", len(filtered))
        c2.metric("Ganadores", len(wins))
        c3.metric("Perdedores", len(losses))
        c4.metric("Win Rate", f"{len(wins)/len(filtered)*100:.1f}%" if filtered else "0%")
        sign = "+" if total_pnl > 0 else ""
        c5.metric("P&L Total", f"{sign}${total_pnl:.4f}")

    # Curva de Equity
    st.subheader("Curva de Equity")
    equity = [config.INITIAL_CAPITAL]
    for t in reversed(filtered):
        equity.append(equity[-1] + t.pnl)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=equity, mode="lines",
        name="Equity",
        line=dict(color="#00d4aa", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.1)",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Balance (USDT)",
        template="plotly_dark",
    )
    st.plotly_chart(fig, width='stretch')

    # Tabla de trades
    st.subheader("Detalle de Trades")
    data = []
    for t in filtered:
        pnl_sign = "+" if t.pnl > 0 else ""
        data.append({
            "Par": t.symbol,
            "Entrada": f"${t.entry_price:.4f}",
            "Salida": f"${t.exit_price:.4f}" if t.exit_price else "N/A",
            "Cantidad": f"{t.quantity:.8f}",
            "Inversion": f"${t.investment:.2f}",
            "P&L": f"{pnl_sign}${t.pnl:.4f}",
            "P&L %": f"{pnl_sign}{t.pnl_percentage:.2f}%",
            "Razon": t.exit_reason or "N/A",
            "Estrategia": t.strategy,
            "Fecha Entrada": t.entry_time.strftime("%Y-%m-%d %H:%M") if t.entry_time else "N/A",
            "Fecha Salida": t.exit_time.strftime("%Y-%m-%d %H:%M") if t.exit_time else "N/A",
        })

    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch', hide_index=True)

    # Boton exportar CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Exportar a CSV",
        data=csv,
        file_name="trades_history.csv",
        mime="text/csv",
    )

if st.button("🔄 Actualizar", width='stretch'):
    st.rerun()
