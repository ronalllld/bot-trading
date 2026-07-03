"""
Gestion de configuracion dinamica del usuario
Lee y escribe user_settings.json en el directorio de datos persistente
"""

import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "INITIAL_CAPITAL": 10.0,
    "POSITION_SIZE_PERCENTAGE": 50.0,
    "MAX_POSITIONS": 2,
    "TAKE_PROFIT": 3.0,
    "STOP_LOSS": 1.5,
}


def _settings_path(data_dir: Path) -> Path:
    return data_dir / "user_settings.json"


def load_settings(data_dir: Path) -> dict:
    """Cargar configuracion del usuario o devolver defaults"""
    path = _settings_path(data_dir)
    if path.exists():
        try:
            with open(path, "r") as f:
                saved = json.load(f)
            return {**DEFAULT_SETTINGS, **saved}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(data_dir: Path, settings: dict) -> bool:
    """Guardar configuracion del usuario en disco"""
    path = _settings_path(data_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False
