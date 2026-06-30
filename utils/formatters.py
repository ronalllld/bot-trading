"""
Formateadores de datos para presentacion
"""


class Formatters:
    """Formatear datos para display y notificaciones"""

    @staticmethod
    def format_price(price: float, decimals: int = 2) -> str:
        """Formatear precio con separadores de miles"""
        if price >= 1:
            return f"${price:,.{decimals}f}"
        else:
            # Para precios muy pequenos, usar mas decimales
            return f"${price:.8f}"

    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Formatear porcentaje con signo"""
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.{decimals}f}%"

    @staticmethod
    def format_quantity(quantity: float, symbol: str = "") -> str:
        """Formatear cantidad de crypto"""
        if quantity >= 1:
            return f"{quantity:.4f} {symbol}".strip()
        else:
            return f"{quantity:.8f} {symbol}".strip()

    @staticmethod
    def format_pnl(pnl: float) -> str:
        """Formatear P&L con color emoji"""
        sign = "+" if pnl > 0 else ""
        emoji = "🟢" if pnl >= 0 else "🔴"
        return f"{emoji} {sign}${pnl:.2f}"

    @staticmethod
    def format_trade_message(trade_data: dict) -> str:
        """Formatear mensaje de trade para notificaciones"""
        side_emoji = "🟢 COMPRA" if trade_data["side"] == "buy" else "🔴 VENTA"
        msg = (
            f"{side_emoji} EJECUTADA\n"
            f"Par: {trade_data['symbol']}\n"
            f"Precio: ${trade_data['price']:,.2f}\n"
            f"Cantidad: {trade_data['quantity']:.8f}\n"
            f"Inversion: ${trade_data['investment']:.2f}\n"
        )
        if trade_data.get("stop_loss"):
            msg += f"Stop Loss: ${trade_data['stop_loss']:,.2f}\n"
        if trade_data.get("take_profit"):
            msg += f"Take Profit: ${trade_data['take_profit']:,.2f}\n"
        return msg

    @staticmethod
    def format_sell_message(trade_data: dict) -> str:
        """Formatear mensaje de venta para notificaciones"""
        reason = trade_data.get("exit_reason", "MANUAL").upper()
        pnl = trade_data.get("pnl", 0)
        pnl_pct = trade_data.get("pnl_percentage", 0)
        emoji = "🟢" if pnl >= 0 else "🔴"
        sign = "+" if pnl > 0 else ""

        msg = (
            f"{emoji} VENTA - {reason}\n"
            f"Par: {trade_data['symbol']}\n"
            f"Entrada: ${trade_data['entry_price']:,.2f}\n"
            f"Salida: ${trade_data['exit_price']:,.2f}\n"
            f"{'Ganancia' if pnl >= 0 else 'Perdida'}: {sign}${pnl:.2f} ({sign}{pnl_pct:.2f}%)\n"
        )
        if trade_data.get("duration"):
            msg += f"Duracion: {trade_data['duration']}\n"
        return msg

    @staticmethod
    def format_daily_summary(data: dict) -> str:
        """Formatear resumen diario"""
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        pnl = data.get("pnl", 0)
        pnl_pct = data.get("pnl_percentage", 0)
        sign = "+" if pnl > 0 else ""

        return (
            f"📊 RESUMEN DEL DIA\n"
            f"Trades: {total} ({wins}W / {losses}L)\n"
            f"Win Rate: {win_rate:.1f}%\n"
            f"P&L: {sign}${pnl:.2f} ({sign}{pnl_pct:.1f}%)\n"
            f"Balance: ${data.get('balance', 0):.2f}"
        )
