"""Local user preferences for recently opened and favorite database files."""

import json
import os
from pathlib import Path

_APP_DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
_SETTINGS_PATH = _APP_DATA_ROOT / "BastionCommand" / "Viper" / "database_locations.json"
_MAX_RECENT_LOCATIONS = 10


def _normalized_path(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _read_settings() -> dict[str, list[str]]:
    try:
        raw_settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"favorites": [], "recent": []}

    return {
        key: [value for value in raw_settings.get(key, []) if isinstance(value, str)]
        for key in ("favorites", "recent")
    }


def _write_settings(settings: dict[str, list[str]]) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = _SETTINGS_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    temporary_path.replace(_SETTINGS_PATH)


def saved_database_paths() -> tuple[list[Path], list[Path]]:
    """Return saved favorite paths and recent paths, preserving display order."""
    settings = _read_settings()
    favorites = [Path(value) for value in settings["favorites"]]
    recent = [Path(value) for value in settings["recent"]]
    return favorites, recent


def is_favorite_database(path: Path) -> bool:
    normalized_path = _normalized_path(path)
    favorites, _recent = saved_database_paths()
    return any(_normalized_path(favorite) == normalized_path for favorite in favorites)


def remember_database(path: Path, favorite: bool) -> None:
    """Record a successfully opened database and optionally retain it as a favorite."""
    resolved_path = path.resolve()
    normalized_path = _normalized_path(resolved_path)
    settings = _read_settings()

    settings["recent"] = [
        value for value in settings["recent"] if _normalized_path(Path(value)) != normalized_path
    ]
    settings["recent"].insert(0, str(resolved_path))
    settings["recent"] = settings["recent"][:_MAX_RECENT_LOCATIONS]

    settings["favorites"] = [
        value for value in settings["favorites"] if _normalized_path(Path(value)) != normalized_path
    ]
    if favorite:
        settings["favorites"].insert(0, str(resolved_path))

    _write_settings(settings)


def remove_favorite_database(path: Path) -> None:
    """Remove a path from favorites while leaving it available in recent locations."""
    normalized_path = _normalized_path(path)
    settings = _read_settings()
    settings["favorites"] = [
        value for value in settings["favorites"] if _normalized_path(Path(value)) != normalized_path
    ]
    _write_settings(settings)