"""JSON-backed configuration manager."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.utils.constants import (
    CONFIG_FILENAME,
    DEFAULT_CFG,
    DEFAULT_MODEL,
    DEFAULT_MODEL_CACHE_DIR,
    DEFAULT_STEPS,
    DEFAULT_VOLUME,
)

logger = logging.getLogger(__name__)

_DEFAULTS: dict[str, Any] = {
    "model_name": DEFAULT_MODEL,
    "model_cache_dir": DEFAULT_MODEL_CACHE_DIR,
    "cfg_value": DEFAULT_CFG,
    "inference_timesteps": DEFAULT_STEPS,
    "load_denoiser": False,
    "output_dir": "./output",
    "volume": DEFAULT_VOLUME,
    "language": "zh-TW",
    "auto_load_model": False,
}


class ConfigManager:
    """
    Loads and persists settings in a JSON file next to the executable.

    Usage::

        cfg = ConfigManager()
        print(cfg.get("cfg_value"))   # 2.0
        cfg.set("cfg_value", 3.0)
        cfg.save()
    """

    def __init__(self, path: str | Path = CONFIG_FILENAME) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = dict(_DEFAULTS)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def save(self) -> None:
        """Write current settings to disk.  Silently no-ops on permission error."""
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Could not save config to %s: %s", self._path, exc)

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            loaded: dict[str, Any] = json.loads(
                self._path.read_text(encoding="utf-8")
            )
            # Only update known keys to guard against stale / malformed data
            for key in _DEFAULTS:
                if key in loaded:
                    self._data[key] = loaded[key]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load config from %s: %s", self._path, exc)
