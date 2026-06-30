"""
Dashboard principal con Streamlit
Pagina de Overview con metricas generales
"""

import sys
from pathlib import Path

# Agregar raiz del proyecto al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone

from config.config import Config
from database.db_manager import DatabaseManager

# --- Configuracion de la pagina ---
st.set_page_config(
    page_title="Trading Bot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Inicializar componentes ---
@st.cache_resource
def get_db():
    config = Config()
    db = DatabaseManager(config.DB_PATH)
    import asyncio
    asyncio.run(db.initialize())
    return db, config

db, config = get_db()


def main():
    """Pagina principal - Overview"""
    st.title("🤖 Trading Bot Pro - Dashboard")
    st.markdown(f"**Modo:** `{config.MODE}` | **Timeframe:** `{config.TIMEFRAME}` | **Estrategia:** `combined`")
    st.divider()

    # --- Metricas principales ---
    stats = db.get_trading_stats()
    open_trades = db.get_open_trades()
    daily_pnl = db.get_daily_pnl()
    daily_pnl_pct = db.get_daily_pnl_percentage(config.INITIAL_CAPITAL)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        balance = config.INITIAL_CAPITAL + stats.get("total_pnl", 0)
        st.metric("Balance Total", f"${balance:.2f}",
                  delta=f"${stats.get('total_pnl', 0):.2f}")

    with col2:
        st.metric("P&L Diario", f"${daily_pnl:.2f}",
                  delta=f"{daily_pnl_pct:.2f}%")

    with col3:
        st.metric("Posiciones Abiertas",
                  f"{len(open_trades)}/{config.MAX_POSITIONS}")

    with col4:
        st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")

    with col5:
        st.metric("Total Trades", stats.get("total_trades", 0))

    st.divider()

    # --- Graficos ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Evolucion del Balance")
        history = db.get_balance_history(hours=24)
        if history:
            df_history = pd.DataFrame([h.to_dict() for h in history])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_history["timestamp"],
                y=df_history["balance"],
                mode="lines+markers",
                name="Balance",
                line=dict(color="#00d4aa", width=2),
                fill="tozeroy",
                fillcolor="rgba(0,212,170,0.1)",
            ))
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Tiempo",
                yaxis_title="Balance (USDT)",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de balance aun. El bot guardara snapshots periodicamente.")

    with col_right:
        st.subheader("Distribucion de Resultados")
        closed_trades = db.get_closed_trades(limit=50)
        if closed_trades:
            pnls = [t.pnl for t in closed_trades]
            fig = px.histogram(
                x=pnls, nbins=20,
                labels={"x": "P&L (USDT)", "y": "Cantidad"},
                color_discrete_sequence=["#00d4aa"],
            )
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin trades cerrados aun.")

    # --- Posiciones Abiertas ---
    st.subheader("Posiciones Abiertas")
    if open_trades:
        data = []
        for t in open_trades:
            data.append({
                "Par": t.symbol,
                "Precio Entrada": f"${t.entry_price:.4f}",
                "Cantidad": f"{t.quantity:.8f}",
                "Inversion": f"${t.investment:.2f}",
                "Stop Loss": f"${t.stop_loss:.4f}" if t.stop_loss else "N/A",
                "Take Profit": f"${t.take_profit:.4f}" if t.take_profit else "N/A",
                "Estrategia": t.strategy,
                "Desde": t.entry_time.strftime("%H:%M:%S") if t.entry_time else "N/A",
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No hay posiciones abiertas")

    # --- Ultimos Trades ---
    st.subheader("Ultimos Trades Cerrados")
    recent = db.get_closed_trades(limit=10)
    if recent:
        data = []
        for t in recent:
            pnl_sign = "+" if t.pnl > 0 else ""
            data.append({
                "Par": t.symbol,
                "Entrada": f"${t.entry_price:.4f}",
                "Salida": f"${t.exit_price:.4f}" if t.exit_price else "N/A",
                "P&L": f"{pnl_sign}${t.pnl:.4f}",
                "P&L %": f"{pnl_sign}{t.pnl_percentage:.2f}%",
                "Razon": t.exit_reason or "N/A",
                "Estrategia": t.strategy,
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("Sin historial de trades")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Control del Bot")
        st.markdown(f"**Estado:** {'🟢 Activo' if config.MODE else '🔴 Inactivo'}")
        st.markdown(f"**Capital:** ${config.INITIAL_CAPITAL:.2f}")
        st.markdown(f"**TP:** {config.TAKE_PROFIT}% | **SL:** {config.STOP_LOSS}%")

        st.divider()
        st.header("Estadisticas")
        st.markdown(f"- **Profit Factor:** {stats.get('profit_factor', 0):.2f}")
        st.markdown(f"- **Mejor Trade:** ${stats.get('best_trade', 0):.4f}")
        st.markdown(f"- **Peor Trade:** ${stats.get('worst_trade', 0):.4f}")
        st.markdown(f"- **Avg Win:** ${stats.get('avg_win', 0):.4f}")
        st.markdown(f"- **Avg Loss:** ${stats.get('avg_loss', 0):.4f}")

        st.divider()
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()


if __name__ == "__main__":
    main()
