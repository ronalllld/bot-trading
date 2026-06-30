"""
Modelos de base de datos usando SQLAlchemy
Define las tablas: trades, balance_history, system_logs
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Trade(Base):
    """Tabla de trades ejecutados"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False)  # ID unico generado
    symbol = Column(String(20), nullable=False)                 # Par de trading (BTC/USDT)
    side = Column(String(10), nullable=False)                   # buy / sell
    entry_price = Column(Float, nullable=False)                 # Precio de entrada
    exit_price = Column(Float, nullable=True)                   # Precio de salida
    quantity = Column(Float, nullable=False)                    # Cantidad de crypto
    investment = Column(Float, nullable=False)                  # Inversion en USDT
    pnl = Column(Float, default=0.0)                           # Ganancia/perdida en USDT
    pnl_percentage = Column(Float, default=0.0)                # Ganancia/perdida en %
    strategy = Column(String(50), default="combined")           # Estrategia usada
    entry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    exit_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="open")                # open / closed
    exit_reason = Column(String(20), nullable=True)            # tp / sl / manual / signal
    stop_loss = Column(Float, nullable=True)                   # Precio de stop loss
    take_profit = Column(Float, nullable=True)                 # Precio de take profit
    exchange_order_id = Column(String(100), nullable=True)      # ID de orden en exchange

    def __repr__(self):
        return (
            f"Trade(id={self.id}, symbol={self.symbol}, side={self.side}, "
            f"entry={self.entry_price}, status={self.status}, pnl={self.pnl})"
        )

    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "investment": self.investment,
            "pnl": self.pnl,
            "pnl_percentage": self.pnl_percentage,
            "strategy": self.strategy,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "status": self.status,
            "exit_reason": self.exit_reason,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }


class BalanceHistory(Base):
    """Historial de balance para graficos de equity"""
    __tablename__ = "balance_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    balance = Column(Float, nullable=False)
    positions_count = Column(Integer, default=0)
    daily_pnl = Column(Float, default=0.0)
    daily_pnl_percentage = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)

    def __repr__(self):
        return f"BalanceHistory(balance={self.balance}, daily_pnl={self.daily_pnl})"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "balance": self.balance,
            "positions_count": self.positions_count,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_percentage": self.daily_pnl_percentage,
            "total_pnl": self.total_pnl,
        }


class SystemLog(Base):
    """Logs del sistema para el dashboard"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    level = Column(String(20), nullable=False)    # info / warning / error
    message = Column(Text, nullable=False)
    module = Column(String(50), nullable=True)

    def __repr__(self):
        return f"SystemLog(level={self.level}, message={self.message[:50]})"
