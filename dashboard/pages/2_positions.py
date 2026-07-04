"""
Pagina de Posiciones - Detalle de posiciones abiertas
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from config.config import Config
from database.db_manager import DatabaseManager

st.set_page_config(page_title="Posiciones", page_icon="📈", layout="wide")

@st.cache_resource
def get_db():
    config = Config()
    db = DatabaseManager(config.DB_PATH)
    import asyncio
    asyncio.run(db.initialize())
    return db, config

db, config = get_db()

st.title("📈 Posiciones Activas")
st.divider()

open_trades = db.get_open_trades()

if not open_trades:
    st.info("No hay posiciones abiertas actualmente.")
else:
    for trade in open_trades:
        with st.expander(f"📍 {trade.symbol} - Entrada: ${trade.entry_price:.4f}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Precio Entrada", f"${trade.entry_price:.4f}")
            with col2:
                st.metric("Cantidad", f"{trade.quantity:.8f}")
            with col3:
                st.metric("Inversion", f"${trade.investment:.2f}")
            with col4:
                st.metric("Estrategia", trade.strategy)

            # Niveles TP/SL visualizados
            if trade.stop_loss and trade.take_profit:
                fig = go.Figure()

                # Linea de entrada
                fig.add_hline(y=trade.entry_price, line_dash="solid",
                              line_color="white", annotation_text="Entrada")
                # Take Profit
                fig.add_hline(y=trade.take_profit, line_dash="dash",
                              line_color="green", annotation_text=f"TP: ${trade.take_profit:.4f}")
                # Stop Loss
                fig.add_hline(y=trade.stop_loss, line_dash="dash",
                              line_color="red", annotation_text=f"SL: ${trade.stop_loss:.4f}")

                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=20, b=20),
                    yaxis_title="Precio",
                    template="plotly_dark",
                    yaxis=dict(range=[
                        trade.stop_loss * 0.998,
                        trade.take_profit * 1.002
                    ]),
                )
                st.plotly_chart(fig, width='stretch')

            # Info adicional
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Stop Loss:** ${trade.stop_loss:.4f}" if trade.stop_loss else "**SL:** N/A")
                st.markdown(f"**Take Profit:** ${trade.take_profit:.4f}" if trade.take_profit else "**TP:** N/A")
            with col_b:
                st.markdown(f"**Abierta desde:** {trade.entry_time.strftime('%Y-%m-%d %H:%M:%S') if trade.entry_time else 'N/A'}")
                st.markdown(f"**Order ID:** `{trade.exchange_order_id or 'N/A'}`")

# Resumen
st.divider()
st.subheader("Resumen")
total_invested = sum(t.investment for t in open_trades)
exposure = (total_invested / config.INITIAL_CAPITAL * 100) if config.INITIAL_CAPITAL > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Invertido", f"${total_invested:.2f}")
with col2:
    st.metric("Exposicion", f"{exposure:.1f}%")
with col3:
    st.metric("Posiciones", f"{len(open_trades)}/{config.MAX_POSITIONS}")

if st.button("🔄 Actualizar", width='stretch'):
    st.rerun()
