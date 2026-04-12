"""Manages generation history — saves WAV files and persists metadata."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 500  # hard cap to keep history.json manageable


class HistoryEntry:
    """Immutable snapshot of one generation result."""

    __slots__ = (
        "id", "timestamp", "mode", "text",
        "filename", "sample_rate", "duration",
    )

    def __init__(
        self,
        *,
        id: str,
        timestamp: str,
        mode: str,
        text: str,
        filename: str,
        sample_rate: int,
        duration: float,
    ) -> None:
        self.id = id
        self.timestamp = timestamp
        self.mode = mode
        self.text = text
        self.filename = filename
        self.sample_rate = sample_rate
        self.duration = duration

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "text": self.text,
            "filename": self.filename,
            "sample_rate": self.sample_rate,
            "duration": round(self.duration, 3),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        return cls(
            id=d["id"],
            timestamp=d["timestamp"],
            mode=d.get("mode", "tts"),
            text=d.get("text", ""),
            filename=d["filename"],
            sample_rate=d.get("sample_rate", 48000),
            duration=d.get("duration", 0.0),
        )


class HistoryManager:
    """
    Thread-safe manager for generation history.

    Saves each audio generation as a WAV file under *wav_dir* and keeps
    a ``history.json`` index alongside the files.

    Usage::

        hm = HistoryManager()
        entry = hm.save(wav_array, sr=48000, text="Hello", mode="tts")
        entries = hm.entries   # newest-first list of HistoryEntry
        hm.delete(entry.id)
    """

    def __init__(
        self,
        wav_dir: str | Path = "./wav-files",
        on_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self._wav_dir = Path(wav_dir)
        self._history_file = self._wav_dir / "history.json"
        self._entries: List[HistoryEntry] = []
        self._lock = threading.Lock()
        self._on_change = on_change

        self._wav_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def save(
        self,
        wav: np.ndarray,
        sr: int,
        text: str,
        mode: str,
    ) -> HistoryEntry:
        """
        Write *wav* to disk and prepend an entry to the history.

        Returns the new :class:`HistoryEntry`.
        """
        import soundfile as sf  # type: ignore[import]

        ts = datetime.now()
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        ts_file = ts.strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:6]
        filename = self._wav_dir / f"{mode}_{ts_file}_{short_id}.wav"

        # Write WAV
        try:
            sf.write(str(filename), wav, sr)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to save history WAV %s: %s", filename, exc)
            raise

        duration = len(wav) / sr
        entry = HistoryEntry(
            id=uuid.uuid4().hex,
            timestamp=ts_str,
            mode=mode,
            text=text,
            filename=str(filename),
            sample_rate=sr,
            duration=duration,
        )

        with self._lock:
            self._entries.insert(0, entry)
            if len(self._entries) > _MAX_ENTRIES:
                self._entries = self._entries[:_MAX_ENTRIES]

        self._persist()
        logger.info("History saved: %s  (%.2f s)", filename.name, duration)

        if self._on_change:
            try:
                self._on_change()
            except Exception:  # noqa: BLE001
                pass

        return entry

    def delete(self, entry_id: str) -> None:
        """Remove entry by *entry_id* and delete its WAV file if present."""
        with self._lock:
            target = next((e for e in self._entries if e.id == entry_id), None)
            if target is None:
                return
            self._entries = [e for e in self._entries if e.id != entry_id]

        # Delete WAV outside lock to avoid holding it during I/O
        wav_path = Path(target.filename)
        if wav_path.exists():
            try:
                wav_path.unlink()
                logger.info("Deleted WAV: %s", wav_path.name)
            except OSError as exc:
                logger.warning("Could not delete WAV %s: %s", wav_path, exc)

        self._persist()
        if self._on_change:
            try:
                self._on_change()
            except Exception:  # noqa: BLE001
                pass

    def clear_all(self) -> None:
        """Delete all entries and their WAV files."""
        with self._lock:
            to_delete = list(self._entries)
            self._entries = []

        for entry in to_delete:
            wav_path = Path(entry.filename)
            if wav_path.exists():
                try:
                    wav_path.unlink()
                except OSError:
                    pass

        self._persist()
        if self._on_change:
            try:
                self._on_change()
            except Exception:  # noqa: BLE001
                pass

    @property
    def entries(self) -> List[HistoryEntry]:
        """Newest-first snapshot of all entries."""
        with self._lock:
            return list(self._entries)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._history_file.exists():
            return
        try:
            data = json.loads(self._history_file.read_text(encoding="utf-8"))
            entries = [HistoryEntry.from_dict(d) for d in data if isinstance(d, dict)]
            # Only keep entries whose WAV file still exists
            valid = [e for e in entries if Path(e.filename).exists()]
            if len(valid) < len(entries):
                logger.info(
                    "Pruned %d missing WAV(s) from history", len(entries) - len(valid)
                )
            with self._lock:
                self._entries = valid
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load history: %s", exc)

    def _persist(self) -> None:
        with self._lock:
            data = [e.to_dict() for e in self._entries]
        try:
            self._history_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Could not save history.json: %s", exc)
