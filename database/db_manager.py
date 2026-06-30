"""
Gestor de base de datos SQLite con SQLAlchemy
Maneja conexiones, sesiones y operaciones CRUD
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from database.models import Base, Trade, BalanceHistory, SystemLog


class DatabaseManager:
    """Gestor centralizado de base de datos"""

    def __init__(self, db_path: str = None):
        """Inicializar conexion a la base de datos"""
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "trading_bot.db"
        self.db_path = str(db_path)
        self.engine = None
        self.SessionLocal = None

    async def initialize(self):
        """Crear engine, tablas y session factory"""
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Base de datos inicializada en {self.db_path}")

    def get_session(self) -> Session:
        """Obtener una sesion de base de datos"""
        return self.SessionLocal()

    # --- TRADES ---

    def save_trade(self, trade: Trade) -> Trade:
        """Guardar un trade nuevo"""
        with self.get_session() as session:
            session.add(trade)
            session.commit()
            session.refresh(trade)
            logger.info(f"TRADE guardado: {trade.symbol} {trade.side} @ {trade.entry_price}")
            return trade

    def update_trade(self, trade_id: str, **kwargs) -> Optional[Trade]:
        """Actualizar un trade existente"""
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if trade:
                for key, value in kwargs.items():
                    if hasattr(trade, key):
                        setattr(trade, key, value)
                session.commit()
                session.refresh(trade)
                logger.info(f"TRADE actualizado: {trade_id}")
            return trade

    def get_open_trades(self) -> List[Trade]:
        """Obtener todos los trades abiertos"""
        with self.get_session() as session:
            trades = session.query(Trade).filter(Trade.status == "open").all()
            # Detach de la sesion para uso externo
            session.expunge_all()
            return trades

    def get_trade_by_symbol(self, symbol: str) -> Optional[Trade]:
        """Obtener trade abierto por simbolo"""
        with self.get_session() as session:
            trade = (
                session.query(Trade)
                .filter(Trade.symbol == symbol, Trade.status == "open")
                .first()
            )
            if trade:
                session.expunge(trade)
            return trade

    def get_all_trades(self, limit: int = 100) -> List[Trade]:
        """Obtener historial de trades"""
        with self.get_session() as session:
            trades = (
                session.query(Trade)
                .order_by(Trade.entry_time.desc())
                .limit(limit)
                .all()
            )
            session.expunge_all()
            return trades

    def get_closed_trades(self, limit: int = 100) -> List[Trade]:
        """Obtener trades cerrados"""
        with self.get_session() as session:
            trades = (
                session.query(Trade)
                .filter(Trade.status == "closed")
                .order_by(Trade.exit_time.desc())
                .limit(limit)
                .all()
            )
            session.expunge_all()
            return trades

    def get_daily_trades(self) -> List[Trade]:
        """Obtener trades del dia actual"""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        with self.get_session() as session:
            trades = (
                session.query(Trade)
                .filter(Trade.entry_time >= today_start)
                .all()
            )
            session.expunge_all()
            return trades

    def get_daily_pnl(self) -> float:
        """Calcular P&L del dia"""
        daily_trades = self.get_daily_trades()
        return sum(t.pnl for t in daily_trades if t.status == "closed")

    def get_daily_pnl_percentage(self, initial_capital: float) -> float:
        """Calcular P&L del dia en porcentaje"""
        daily_pnl = self.get_daily_pnl()
        if initial_capital == 0:
            return 0.0
        return (daily_pnl / initial_capital) * 100

    def count_daily_trades(self) -> int:
        """Contar trades del dia"""
        return len(self.get_daily_trades())

    def close_trade(self, trade_id: str, exit_price: float, exit_reason: str) -> Optional[Trade]:
        """Cerrar un trade y calcular P&L"""
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                return None

            trade.exit_price = exit_price
            trade.exit_time = datetime.now(timezone.utc)
            trade.status = "closed"
            trade.exit_reason = exit_reason

            # Calcular P&L
            if trade.side == "buy":
                trade.pnl = (exit_price - trade.entry_price) * trade.quantity
                trade.pnl_percentage = ((exit_price - trade.entry_price) / trade.entry_price) * 100
            else:
                trade.pnl = (trade.entry_price - exit_price) * trade.quantity
                trade.pnl_percentage = ((trade.entry_price - exit_price) / trade.entry_price) * 100

            session.commit()
            session.refresh(trade)
            logger.info(
                f"TRADE cerrado: {trade.symbol} - PnL: ${trade.pnl:.4f} ({trade.pnl_percentage:.2f}%)"
            )
            session.expunge(trade)
            return trade

    # --- BALANCE HISTORY ---

    def save_balance_snapshot(self, balance: float, positions_count: int,
                              daily_pnl: float, daily_pnl_pct: float, total_pnl: float):
        """Guardar snapshot del balance actual"""
        with self.get_session() as session:
            snapshot = BalanceHistory(
                balance=balance,
                positions_count=positions_count,
                daily_pnl=daily_pnl,
                daily_pnl_percentage=daily_pnl_pct,
                total_pnl=total_pnl,
            )
            session.add(snapshot)
            session.commit()

    def get_balance_history(self, hours: int = 24) -> List[BalanceHistory]:
        """Obtener historial de balance"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        with self.get_session() as session:
            history = (
                session.query(BalanceHistory)
                .filter(BalanceHistory.timestamp >= since)
                .order_by(BalanceHistory.timestamp.asc())
                .all()
            )
            session.expunge_all()
            return history

    # --- SYSTEM LOGS ---

    def save_log(self, level: str, message: str, module: str = None):
        """Guardar log en base de datos"""
        with self.get_session() as session:
            log = SystemLog(level=level, message=message, module=module)
            session.add(log)
            session.commit()

    def get_recent_logs(self, limit: int = 50) -> List[SystemLog]:
        """Obtener logs recientes"""
        with self.get_session() as session:
            logs = (
                session.query(SystemLog)
                .order_by(SystemLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            session.expunge_all()
            return logs

    # --- ESTADISTICAS ---

    def get_trading_stats(self) -> dict:
        """Obtener estadisticas generales de trading"""
        closed_trades = self.get_closed_trades(limit=1000)

        if not closed_trades:
            return {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate": 0.0, "total_pnl": 0.0, "avg_win": 0.0,
                "avg_loss": 0.0, "best_trade": 0.0, "worst_trade": 0.0,
                "profit_factor": 0.0, "avg_pnl_percentage": 0.0,
            }

        wins = [t for t in closed_trades if t.pnl > 0]
        losses = [t for t in closed_trades if t.pnl <= 0]

        total_wins = sum(t.pnl for t in wins) if wins else 0
        total_losses = abs(sum(t.pnl for t in losses)) if losses else 0

        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": (len(wins) / len(closed_trades) * 100) if closed_trades else 0,
            "total_pnl": sum(t.pnl for t in closed_trades),
            "avg_win": (total_wins / len(wins)) if wins else 0,
            "avg_loss": (total_losses / len(losses)) if losses else 0,
            "best_trade": max((t.pnl for t in closed_trades), default=0),
            "worst_trade": min((t.pnl for t in closed_trades), default=0),
            "profit_factor": (total_wins / total_losses) if total_losses > 0 else float("inf"),
            "avg_pnl_percentage": (
                sum(t.pnl_percentage for t in closed_trades) / len(closed_trades)
            ),
        }

    async def close(self):
        """Cerrar conexion a la base de datos"""
        if self.engine:
            self.engine.dispose()
            logger.info("Conexion a base de datos cerrada")
