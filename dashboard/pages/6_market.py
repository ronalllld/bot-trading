"""
Pagina de Mercado en Vivo - Scanner de pares en tiempo real
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import ccxt
import time

from config.config import Config
from config.exchange_config import ExchangeConfig
from analysis.technical_indicators import TechnicalIndicators
from analysis.signal_generator import SignalGenerator

st.set_page_config(page_title="Mercado en Vivo", page_icon="🔍", layout="wide")
st.title("🔍 Mercado en Vivo")
st.markdown("Scanner en tiempo real — se actualiza cada 30 segundos")
st.divider()

@st.cache_resource
def get_config():
    return Config()

config = get_config()

@st.cache_data(ttl=30)
def scan_market(_timestamp):
    """Escanear todos los pares y calcular indicadores"""
    try:
        exchange = ccxt.binance({
            "apiKey": config.BINANCE_API_KEY,
            "secret": config.BINANCE_API_SECRET,
            "enableRateLimit": True,
        })

        signal_gen = SignalGenerator()
        results = []

        for symbol in ExchangeConfig.ALLOWED_PAIRS:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, "5m", limit=200)
                if not ohlcv or len(ohlcv) < 50:
                    continue

                df = pd.DataFrame(
                    ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
                )

                indicators = TechnicalIndicators.calculate_all_indicators(df)
                signal = signal_gen.generate_signal(df, indicators)

                rsi_val = float(indicators["rsi"].iloc[-1]) if len(indicators["rsi"]) > 0 else 0
                macd_hist = float(indicators["macd"]["histogram"].iloc[-1]) if len(indicators["macd"]["histogram"]) > 0 else 0
                bb = indicators["bollinger"]
                price = float(df["close"].iloc[-1])
                lower = float(bb["lower"].iloc[-1]) if len(bb["lower"]) > 0 else 0
                upper = float(bb["upper"].iloc[-1]) if len(bb["upper"]) > 0 else 0
                details = signal.get("details", {})

                results.append({
                    "Par": symbol,
                    "Precio": price,
                    "RSI": round(rsi_val, 1),
                    "MACD Hist": round(macd_hist, 6),
                    "BB Lower": round(lower, 4),
                    "BB Upper": round(upper, 4),
                    "Score": round(details.get("buy_score", 0), 3),
                    "Señal": signal["action"].upper(),
                    "_score_num": signal.get("score", 0),
                    "_action": signal["action"],
                })
            except Exception:
                continue

        results.sort(key=lambda x: x["Score"], reverse=True)
        return results

    except Exception as e:
        st.error(f"Error conectando con Binance: {e}")
        return []


# --- Controles ---
col_refresh, col_info = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 Actualizar ahora", use_container_width=True):
        st.cache_data.clear()

with col_info:
    st.info(f"Umbral de entrada: **score >= {0.70}** | Timeframe: **5m** | Pares: **{len(ExchangeConfig.ALLOWED_PAIRS)}**")

# --- Escanear ---
with st.spinner("Escaneando mercado..."):
    timestamp = int(time.time() // 30)
    results = scan_market(timestamp)

if not results:
    st.warning("No se pudieron obtener datos del mercado.")
else:
    # --- Señales activas ---
    buy_signals = [r for r in results if r["_action"] == "buy"]
    sell_signals = [r for r in results if r["_action"] == "sell"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Pares escaneados", len(results))
    col2.metric("Señales BUY", len(buy_signals), delta=f"+{len(buy_signals)}" if buy_signals else None)
    col3.metric("Señales SELL", len(sell_signals))

    st.divider()

    # --- Tabla principal ---
    st.subheader("Scores por Par")

    df_display = pd.DataFrame([{
        "Par": r["Par"],
        "Precio": f"${r['Precio']:,.4f}",
        "RSI": r["RSI"],
        "MACD Hist": r["MACD Hist"],
        "BB Lower": f"${r['BB Lower']:,.4f}",
        "BB Upper": f"${r['BB Upper']:,.4f}",
        "Score": r["Score"],
        "Señal": r["Señal"],
    } for r in results])

    def color_signal(val):
        if val == "BUY":
            return "background-color: #1a4a2e; color: #00d4aa; font-weight: bold"
        elif val == "SELL":
            return "background-color: #4a1a1a; color: #ff4444; font-weight: bold"
        return ""

    def color_score(val):
        if val >= 0.70:
            return "background-color: #1a4a2e; color: #00d4aa; font-weight: bold"
        elif val >= 0.50:
            return "background-color: #3a3a1a; color: #ffdd44"
        return ""

    def color_rsi(val):
        if val < 30:
            return "color: #00d4aa; font-weight: bold"
        elif val > 70:
            return "color: #ff4444; font-weight: bold"
        return ""

    styled = df_display.style \
        .applymap(color_signal, subset=["Señal"]) \
        .applymap(color_score, subset=["Score"]) \
        .applymap(color_rsi, subset=["RSI"])

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # --- Barras de progreso por par ---
    st.divider()
    st.subheader("Proximidad al umbral de entrada (0.70)")

    for r in results:
        score = r["Score"]
        pct = min(score / 0.70, 1.0)
        label = f"{r['Par']} — Score: {score:.3f}"
        if r["_action"] == "buy":
            label += " 🟢 SEÑAL BUY"
        elif r["_action"] == "sell":
            label += " 🔴 SEÑAL SELL"

        col_label, col_bar = st.columns([2, 5])
        with col_label:
            st.markdown(f"**{r['Par']}**  \n`${r['Precio']:,.4f}` | RSI: {r['RSI']}")
        with col_bar:
            st.progress(pct, text=f"Score: {score:.3f} / 0.70")

    st.divider()
    st.caption(f"Ultima actualizacion: cada 30 segundos automaticamente. Presiona 'Actualizar ahora' para forzar.")
