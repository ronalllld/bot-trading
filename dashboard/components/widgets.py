"""
Widgets personalizados para el dashboard
"""

import streamlit as st


def metric_card(label: str, value: str, delta: str = None,
                delta_color: str = "normal"):
    """Crear tarjeta de metrica personalizada"""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def status_badge(label: str, active: bool):
    """Mostrar badge de estado"""
    emoji = "🟢" if active else "🔴"
    status = "Activo" if active else "Inactivo"
    st.markdown(f"{emoji} **{label}:** {status}")


def pnl_display(pnl: float, pnl_pct: float = None):
    """Mostrar P&L con formato y color"""
    sign = "+" if pnl > 0 else ""
    color = "green" if pnl >= 0 else "red"
    text = f"{sign}${pnl:.4f}"
    if pnl_pct is not None:
        text += f" ({sign}{pnl_pct:.2f}%)"
    st.markdown(f":{color}[{text}]")
