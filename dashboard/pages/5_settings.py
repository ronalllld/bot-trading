"""
Pagina de Configuracion - Ajustar parametros del bot sin redeploy
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from config.config import Config
from config.strategy_config import StrategyConfig
from config.exchange_config import ExchangeConfig
from config.settings_manager import load_settings, save_settings

st.set_page_config(page_title="Configuracion", page_icon="⚙️", layout="wide")

st.title("⚙️ Configuracion del Bot")
st.divider()

config = Config()

# --- SECCION EDITABLE ---
st.subheader("Ajustar Parametros")
st.info("Los cambios aplican en el proximo ciclo del bot (5 segundos). No requiere redeploy.")

current = load_settings(config.DATA_DIR)

with st.form("settings_form"):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Capital y Posiciones**")
        new_capital = st.number_input(
            "Capital inicial (USDT)",
            min_value=5.0,
            max_value=100000.0,
            value=float(current["INITIAL_CAPITAL"]),
            step=1.0,
            help="El capital base que el bot usa para calcular el tamaño de cada trade.",
        )
        new_max_pos = st.number_input(
            "Max posiciones simultaneas",
            min_value=1,
            max_value=10,
            value=int(current["MAX_POSITIONS"]),
            step=1,
            help="Cuantos trades abiertos puede tener el bot al mismo tiempo.",
        )
        new_pos_pct = st.slider(
            "% del capital por trade",
            min_value=10,
            max_value=100,
            value=int(current["POSITION_SIZE_PERCENTAGE"]),
            step=5,
            help="Que porcentaje del capital se invierte en cada trade.",
        )

    with col2:
        st.markdown("**Riesgo**")
        new_tp = st.number_input(
            "Take Profit (%)",
            min_value=0.5,
            max_value=50.0,
            value=float(current["TAKE_PROFIT"]),
            step=0.5,
            help="El bot vende cuando el precio sube este porcentaje desde la entrada.",
        )
        new_sl = st.number_input(
            "Stop Loss (%)",
            min_value=0.1,
            max_value=20.0,
            value=float(current["STOP_LOSS"]),
            step=0.1,
            help="El bot vende cuando el precio cae este porcentaje desde la entrada.",
        )

        trade_usdt = new_capital * (new_pos_pct / 100)
        st.markdown("**Simulacion con estos valores:**")
        st.markdown(f"- Por trade: **${trade_usdt:.2f} USDT**")
        st.markdown(f"- Ganancia si TP: **+${trade_usdt * new_tp / 100:.2f}**")
        st.markdown(f"- Perdida si SL: **-${trade_usdt * new_sl / 100:.2f}**")
        st.markdown(f"- Max invertido: **${trade_usdt * new_max_pos:.2f}** ({new_max_pos} trades)")

    submitted = st.form_submit_button("💾 Guardar cambios", use_container_width=True, type="primary")

if submitted:
    new_settings = {
        "INITIAL_CAPITAL": new_capital,
        "POSITION_SIZE_PERCENTAGE": float(new_pos_pct),
        "MAX_POSITIONS": new_max_pos,
        "TAKE_PROFIT": new_tp,
        "STOP_LOSS": new_sl,
    }
    if save_settings(config.DATA_DIR, new_settings):
        st.success("Configuracion guardada. El bot aplicara los cambios en el proximo ciclo.")
    else:
        st.error("Error al guardar. Revisa los permisos del directorio /app/data/")

st.divider()

# --- SECCION DE LECTURA ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Estrategias")
    st.markdown("**Disponibles**")
    for s in StrategyConfig.AVAILABLE_STRATEGIES:
        default = " (activa)" if s == StrategyConfig.DEFAULT_STRATEGY else ""
        st.markdown(f"- `{s}`{default}")

    st.markdown("**Pesos de la Estrategia Combinada**")
    st.markdown(f"- RSI: {StrategyConfig.WEIGHT_RSI * 100:.0f}%")
    st.markdown(f"- MACD: {StrategyConfig.WEIGHT_MACD * 100:.0f}%")
    st.markdown(f"- Bollinger: {StrategyConfig.WEIGHT_BB * 100:.0f}%")
    st.markdown(f"- Volumen: {StrategyConfig.WEIGHT_VOLUME * 100:.0f}%")

with col2:
    st.subheader("Indicadores")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**RSI**")
        st.markdown(f"- Periodo: {StrategyConfig.RSI_PERIOD}")
        st.markdown(f"- Sobreventa: {StrategyConfig.RSI_OVERSOLD}")
        st.markdown(f"- Sobrecompra: {StrategyConfig.RSI_OVERBOUGHT}")
    with col_b:
        st.markdown("**MACD**")
        st.markdown(f"- Fast: {StrategyConfig.MACD_FAST}")
        st.markdown(f"- Slow: {StrategyConfig.MACD_SLOW}")
        st.markdown(f"- Signal: {StrategyConfig.MACD_SIGNAL}")
    with col_c:
        st.markdown("**Bollinger**")
        st.markdown(f"- Periodo: {StrategyConfig.BB_PERIOD}")
        st.markdown(f"- Desviacion: {StrategyConfig.BB_STD_DEV}")

st.divider()

# --- Pares ---
st.subheader("Pares de Trading Permitidos")
st.code(", ".join(ExchangeConfig.ALLOWED_PAIRS))
st.markdown(f"- Volumen Minimo 24h: ${ExchangeConfig.MIN_VOLUME_24H:,.0f}")
st.markdown(f"- Spread Maximo: {ExchangeConfig.MAX_SPREAD_PERCENTAGE}%")
st.markdown(f"- Orden Minima: ${ExchangeConfig.MIN_ORDER_USDT}")

st.divider()

# --- Estado de conexiones ---
st.subheader("Estado de Conexiones")
col1, col2, col3 = st.columns(3)
with col1:
    api_ok = bool(config.BINANCE_API_KEY)
    st.markdown(f"**Binance API:** {'🟢 Configurada' if api_ok else '🔴 No configurada'}")
with col2:
    tg_ok = bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)
    st.markdown(f"**Telegram:** {'🟢 Configurado' if tg_ok else '🔴 No configurado'}")
with col3:
    email_ok = bool(config.SMTP_USER and config.SMTP_PASSWORD)
    st.markdown(f"**Email:** {'🟢 Configurado' if email_ok else '🔴 No configurado'}")
