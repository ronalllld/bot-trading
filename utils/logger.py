"""
Sistema de logging avanzado con loguru
Registra en consola y archivos rotativos
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_level: str = "INFO", log_dir: str = None):
    """Configurar el sistema de logging"""
    # Remover handler por defecto
    logger.remove()

    # Formato para consola
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>"
    )

    # Formato para archivos
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{module}:{function}:{line} | "
        "{message}"
    )

    # Handler de consola
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
    )

    # Handler de archivo general
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(exist_ok=True)

    logger.add(
        str(log_dir / "bot_{time:YYYY-MM-DD}.log"),
        format=file_format,
        level=log_level,
        rotation="00:00",      # Rotar a medianoche
        retention="30 days",   # Mantener 30 dias
        compression="zip",
        encoding="utf-8",
    )

    # Handler de errores separado
    logger.add(
        str(log_dir / "errors_{time:YYYY-MM-DD}.log"),
        format=file_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    # Handler de trades
    logger.add(
        str(log_dir / "trades_{time:YYYY-MM-DD}.log"),
        format=file_format,
        level="INFO",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        filter=lambda record: "TRADE" in record["message"],
        encoding="utf-8",
    )

    logger.info(f"Logger configurado - Nivel: {log_level}")
    return logger
