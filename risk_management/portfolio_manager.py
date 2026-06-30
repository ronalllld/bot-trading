"""
Gestion del portafolio completo
Monitorea exposicion total, balance y rendimiento
"""

from typing import List
from loguru import logger
from config.config import Config
from database.db_manager import DatabaseManager
from database.models import Trade


class PortfolioManager:
    """Gestionar el portafolio completo del bot"""

    def __init__(self, config: Config, db: DatabaseManager):
        self.config = config
        self.db = db
        self.paused = False
        self.pause_reason = ""

    def get_portfolio_summary(self, current_balance: float,
                               open_trades: List[Trade] = None) -> dict:
        """Obtener resumen del portafolio"""
        if open_trades is None:
            open_trades = self.db.get_open_trades()

        # Calcular valor de posiciones abiertas
        total_invested = sum(t.investment for t in open_trades)
        total_exposure = (total_invested / self.config.INITIAL_CAPITAL * 100) if self.config.INITIAL_CAPITAL > 0 else 0

        # P&L diario
        daily_pnl = self.db.get_daily_pnl()
        daily_pnl_pct = self.db.get_daily_pnl_percentage(self.config.INITIAL_CAPITAL)

        # Estadisticas generales
        stats = self.db.get_trading_stats()

        return {
            "balance": current_balance,
            "initial_capital": self.config.INITIAL_CAPITAL,
            "total_invested": total_invested,
            "available": current_balance - total_invested,
            "exposure_pct": total_exposure,
            "open_positions": len(open_trades),
            "max_positions": self.config.MAX_POSITIONS,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "total_pnl": stats.get("total_pnl", 0),
            "win_rate": stats.get("win_rate", 0),
            "total_trades": stats.get("total_trades", 0),
            "paused": self.paused,
            "pause_reason": self.pause_reason,
        }

    def check_daily_limits(self) -> bool:
        """Verificar limites diarios, pausar bot si es necesario"""
        daily_pnl_pct = self.db.get_daily_pnl_percentage(self.config.INITIAL_CAPITAL)

        # Verificar perdida diaria maxima
        if daily_pnl_pct <= -self.config.MAX_DAILY_LOSS:
            self.paused = True
            self.pause_reason = f"Perdida diaria maxima alcanzada: {daily_pnl_pct:.2f}%"
            logger.warning(f"BOT PAUSADO: {self.pause_reason}")
            return False

        # Verificar limite de trades diarios
        daily_trades = self.db.count_daily_trades()
        if daily_trades >= self.config.MAX_DAILY_TRADES:
            self.paused = True
            self.pause_reason = f"Limite de trades diarios alcanzado: {daily_trades}"
            logger.warning(f"BOT PAUSADO: {self.pause_reason}")
            return False

        return True

    def can_trade(self) -> bool:
        """Verificar si el bot puede operar"""
        if self.paused:
            logger.debug(f"Bot pausado: {self.pause_reason}")
            return False
        return self.check_daily_limits()

    def pause(self, reason: str = "Manual"):
        """Pausar el bot"""
        self.paused = True
        self.pause_reason = reason
        logger.info(f"Bot PAUSADO: {reason}")

    def resume(self):
        """Reanudar el bot"""
        self.paused = False
        self.pause_reason = ""
        logger.info("Bot REANUDADO")

    def reset_daily(self):
        """Resetear limites diarios (llamar a medianoche)"""
        if self.paused and "diaria" in self.pause_reason.lower():
            self.resume()
            logger.info("Limites diarios reseteados")
