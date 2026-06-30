"""
Pagina de Configuracion - Ajustar parametros del bot
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from config.config import Config
from config.strategy_config import StrategyConfig
from config.exchange_config import ExchangeConfig

st.set_page_config(page_title="Configuracion", page_icon="⚙️", layout="wide")

st.title("⚙️ Configuracion del Bot")
st.divider()

config = Config()

# --- Trading ---
st.subheader("Trading")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Parametros Actuales**")
    st.markdown(f"- **Modo:** `{config.MODE}`")
    st.markdown(f"- **Capital Inicial:** ${config.INITIAL_CAPITAL:.2f}")
    st.markdown(f"- **Riesgo por Trade:** {config.RISK_PER_TRADE}%")
    st.markdown(f"- **Max Posiciones:** {config.MAX_POSITIONS}")
    st.markdown(f"- **Tamano Posicion:** {config.POSITION_SIZE_PERCENTAGE}%")

with col2:
    st.markdown("**Limites de Riesgo**")
    st.markdown(f"- **Take Profit:** {config.TAKE_PROFIT}%")
    st.markdown(f"- **Stop Loss:** {config.STOP_LOSS}%")
    st.markdown(f"- **Perdida Diaria Max:** {config.MAX_DAILY_LOSS}%")
    st.markdown(f"- **Max Trades/Dia:** {config.MAX_DAILY_TRADES}")
    st.markdown(f"- **Timeframe:** {config.TIMEFRAME}")

st.divider()

# --- Estrategias ---
st.subheader("Estrategias")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Estrategias Disponibles**")
    for s in StrategyConfig.AVAILABLE_STRATEGIES:
        default = " (por defecto)" if s == StrategyConfig.DEFAULT_STRATEGY else ""
        st.markdown(f"- `{s}`{default}")

with col2:
    st.markdown("**Pesos de la Estrategia Combinada**")
    st.markdown(f"- RSI: {StrategyConfig.WEIGHT_RSI * 100:.0f}%")
    st.markdown(f"- MACD: {StrategyConfig.WEIGHT_MACD * 100:.0f}%")
    st.markdown(f"- Bollinger: {StrategyConfig.WEIGHT_BB * 100:.0f}%")
    st.markdown(f"- Volumen: {StrategyConfig.WEIGHT_VOLUME * 100:.0f}%")

st.divider()

# --- Indicadores ---
st.subheader("Parametros de Indicadores")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**RSI**")
    st.markdown(f"- Periodo: {StrategyConfig.RSI_PERIOD}")
    st.markdown(f"- Sobreventa: {StrategyConfig.RSI_OVERSOLD}")
    st.markdown(f"- Sobrecompra: {StrategyConfig.RSI_OVERBOUGHT}")

with col2:
    st.markdown("**MACD**")
    st.markdown(f"- Fast: {StrategyConfig.MACD_FAST}")
    st.markdown(f"- Slow: {StrategyConfig.MACD_SLOW}")
    st.markdown(f"- Signal: {StrategyConfig.MACD_SIGNAL}")

with col3:
    st.markdown("**Bollinger Bands**")
    st.markdown(f"- Periodo: {StrategyConfig.BB_PERIOD}")
    st.markdown(f"- Desviacion: {StrategyConfig.BB_STD_DEV}")

st.divider()

# --- Pares ---
st.subheader("Pares de Trading Permitidos")
pairs_text = ", ".join(ExchangeConfig.ALLOWED_PAIRS)
st.code(pairs_text)

st.markdown(f"**Filtros de Mercado:**")
st.markdown(f"- Volumen Minimo 24h: ${ExchangeConfig.MIN_VOLUME_24H:,.0f}")
st.markdown(f"- Spread Maximo: {ExchangeConfig.MAX_SPREAD_PERCENTAGE}%")
st.markdown(f"- Orden Minima: ${ExchangeConfig.MIN_ORDER_USDT}")

st.divider()

# --- Conexiones ---
st.subheader("Estado de Conexiones")
col1, col2, col3 = st.columns(3)

with col1:
    api_configured = bool(config.KUCOIN_API_KEY)
    st.markdown(f"**KuCoin API:** {'🟢 Configurada' if api_configured else '🔴 No configurada'}")

with col2:
    tg_configured = bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)
    st.markdown(f"**Telegram:** {'🟢 Configurado' if tg_configured else '🔴 No configurado'}")

with col3:
    email_configured = bool(config.SMTP_USER and config.SMTP_PASSWORD)
    st.markdown(f"**Email:** {'🟢 Configurado' if email_configured else '🔴 No configurado'}")

st.divider()
st.info(
    "Para modificar la configuracion, edita el archivo `.env` en la raiz del proyecto "
    "y reinicia el bot. Los cambios toman efecto al reiniciar."
)
