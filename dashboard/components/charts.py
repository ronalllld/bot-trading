"""
Componentes de graficos interactivos con Plotly
"""

import plotly.graph_objects as go
import pandas as pd


def create_candlestick_chart(df: pd.DataFrame, title: str = "",
                              tp_price: float = None,
                              sl_price: float = None) -> go.Figure:
    """Crear grafico de velas japonesas"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color="#00d4aa",
        decreasing_line_color="#ff4444",
    )])

    if tp_price:
        fig.add_hline(y=tp_price, line_dash="dash", line_color="green",
                      annotation_text=f"TP: ${tp_price:.2f}")
    if sl_price:
        fig.add_hline(y=sl_price, line_dash="dash", line_color="red",
                      annotation_text=f"SL: ${sl_price:.2f}")

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def create_equity_curve(equity_data: list, title: str = "Curva de Equity") -> go.Figure:
    """Crear grafico de curva de equity"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=equity_data,
        mode="lines",
        name="Equity",
        line=dict(color="#00d4aa", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.1)",
    ))
    fig.update_layout(
        title=title,
        yaxis_title="Balance (USDT)",
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def create_pnl_bar_chart(pnls: list, title: str = "P&L por Trade") -> go.Figure:
    """Crear grafico de barras de P&L"""
    colors = ["#00d4aa" if p > 0 else "#ff4444" for p in pnls]
    fig = go.Figure(data=[go.Bar(y=pnls, marker_color=colors)])
    fig.update_layout(
        title=title,
        yaxis_title="P&L (USDT)",
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig
