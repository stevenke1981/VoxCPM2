"""Thread-safe audio player backed by sounddevice."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    Loads a float32 numpy audio array and exposes ``play`` / ``stop`` / ``save``.

    Playback runs in a daemon thread so it never blocks the GUI.

    Example::

        player = AudioPlayer()
        player.load(wav, sample_rate=48000)
        player.play(volume=0.9)
        # later …
        player.stop()
        player.save_to_file("output.wav")
    """

    def __init__(self) -> None:
        self._wav: Optional[np.ndarray] = None
        self._sample_rate: int = 48000
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def has_audio(self) -> bool:
        return self._wav is not None

    @property
    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def wav(self) -> Optional[np.ndarray]:
        """Read-only view of the loaded audio array."""
        return self._wav

    @property
    def duration(self) -> float:
        """Duration in seconds; 0.0 if no audio is loaded."""
        if self._wav is None:
            return 0.0
        return len(self._wav) / self._sample_rate

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, wav: np.ndarray, sample_rate: int) -> None:
        """
        Store audio for later playback.  Stops any active playback first.

        Args:
            wav:         1-D or 2-D float32 array.  Stereo arrays are mixed
                         to mono automatically.
            sample_rate: Sample rate in Hz.
        """
        self.stop()
        with self._lock:
            wav = np.atleast_1d(wav)
            if wav.ndim > 1:
                wav = wav.mean(axis=-1)           # (N, C) → (N,)
            wav = wav.astype(np.float32, copy=False)
            # Hard-clip to [-1, 1] to prevent sounddevice clipping errors
            np.clip(wav, -1.0, 1.0, out=wav)
            self._wav = wav
            self._sample_rate = int(sample_rate)

    def play(
        self,
        volume: float = 1.0,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Start non-blocking playback.

        Args:
            volume:      Scalar multiplier applied before playback [0, 1].
            on_finished: Optional zero-argument callback invoked when playback
                         ends (either naturally or via ``stop()``).
                         Called from the worker thread — use ``widget.after()``
                         if it touches the GUI.
        """
        if not self.has_audio:
            return
        self.stop()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker,
            args=(float(volume), on_finished),
            daemon=True,
            name="AudioPlayer-worker",
        )
        self._thread.start()

    def stop(self) -> None:
        """Interrupt active playback and wait for the worker to exit."""
        try:
            import sounddevice as sd  # type: ignore[import]
            sd.stop()
        except Exception:  # noqa: BLE001
            pass
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def load_file(self, path: str) -> None:
        """
        Load audio from a WAV file on disk.

        Args:
            path: Path to a WAV file.

        Raises:
            FileNotFoundError: File does not exist.
            RuntimeError:      soundfile is not installed or read fails.
        """
        from pathlib import Path as _Path

        if not _Path(path).exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        try:
            import soundfile as sf  # type: ignore[import]

            wav, sr = sf.read(str(path), dtype="float32", always_2d=False)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Could not read audio file: {exc}") from exc

        self.load(wav, int(sr))

    def save_to_file(self, path: str) -> None:
        """
        Write the loaded audio to *path* as a WAV file.

        Args:
            path: Destination file path (must end in ``.wav``).

        Raises:
            RuntimeError: No audio loaded.
            OSError:      File write error.
        """
        if not self.has_audio:
            raise RuntimeError("No audio loaded — nothing to save.")

        import soundfile as sf  # type: ignore[import]

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            sf.write(str(dest), self._wav, self._sample_rate)

        logger.info("Saved %s  (%.1f s)", dest, self.duration)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _worker(
        self,
        volume: float,
        on_finished: Optional[Callable[[], None]],
    ) -> None:
        try:
            import sounddevice as sd  # type: ignore[import]

            with self._lock:
                wav = self._wav.copy()
                sr = self._sample_rate

            if volume != 1.0:
                wav = wav * max(0.0, min(1.0, volume))

            sd.play(wav, sr)
            # Wait until end-of-stream OR stop() sets the event
            while not self._stop_event.is_set():
                if not sd.get_stream().active:
                    break
                self._stop_event.wait(timeout=0.05)

            sd.stop()

        except Exception as exc:  # noqa: BLE001
            logger.error("Playback error: %s", exc)
        finally:
            if on_finished:
                try:
                    on_finished()
                except Exception:  # noqa: BLE001
                    pass
