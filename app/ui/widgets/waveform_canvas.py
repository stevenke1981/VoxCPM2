"""WaveformCanvas widget — draws PCM audio as a min/max bar waveform."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import customtkinter as ctk
import numpy as np

from app.utils.constants import WAVEFORM_BG, WAVEFORM_BAR, WAVEFORM_BASELINE


class WaveformCanvas(ctk.CTkFrame):
    """
    A resizable canvas that displays audio waveform as vertical amplitude bars.

    Usage::

        wf = WaveformCanvas(parent_frame, height=110)
        wf.draw_waveform(wav_array)  # must be called from main thread
        wf.clear()
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        height: int = 110,
        **kwargs: object,
    ) -> None:
        # Strip 'height' from kwargs so CTkFrame doesn't receive it twice
        kwargs.pop("height", None)
        super().__init__(master, height=height, corner_radius=8, **kwargs)

        self._wav: Optional[np.ndarray] = None

        self._canvas = tk.Canvas(
            self,
            bg=WAVEFORM_BG,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self._canvas.bind("<Configure>", self._on_resize)

    # ── Public ────────────────────────────────────────────────────────────────

    def draw_waveform(self, wav: np.ndarray) -> None:
        """
        Render *wav* as a min/max bar waveform.

        Args:
            wav: 1-D or 2-D float32 PCM array.  Stereo is averaged to mono.

        Must be called from the **main (GUI) thread**.
        """
        wav = np.atleast_1d(wav)
        if wav.ndim > 1:
            wav = wav.mean(axis=-1)
        self._wav = wav.astype(np.float32, copy=False)
        self._redraw()

    def clear(self) -> None:
        """Erase the waveform and show the baseline only."""
        self._wav = None
        self._canvas.delete("all")
        self._draw_baseline()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _on_resize(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._wav is not None:
            self._redraw()
        else:
            self._draw_baseline()

    def _draw_baseline(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 2 or h < 2:
            return
        mid = h // 2
        self._canvas.delete("all")
        self._canvas.create_line(
            0, mid, w, mid,
            fill=WAVEFORM_BASELINE, width=1, dash=(6, 4),
        )

    def _redraw(self) -> None:
        self._canvas.delete("all")
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()

        if w < 2 or h < 2 or self._wav is None:
            return

        wav = self._wav
        n = len(wav)
        if n == 0:
            self._draw_baseline()
            return

        # ── Down-sample: max absolute amplitude per pixel column ──────────────
        step = max(1, n // w)
        mid = h // 2
        margin = 6
        amp = (h - margin * 2) / 2

        # Draw vertical bars (min / max per column = typical DAW waveform)
        cols = min(w, n // step) if step > 0 else min(w, n)
        for i in range(cols):
            start = i * step
            end = min(start + step, n)
            chunk = wav[start:end]
            if chunk.size == 0:
                continue
            hi = float(chunk.max())
            lo = float(chunk.min())
            y_top = int(mid - hi * amp)
            y_bot = int(mid - lo * amp)
            y_top = max(margin, min(h - margin, y_top))
            y_bot = max(margin, min(h - margin, y_bot))
            self._canvas.create_line(i, y_top, i, y_bot, fill=WAVEFORM_BAR)

        # Baseline
        self._canvas.create_line(
            0, mid, w, mid,
            fill=WAVEFORM_BASELINE, width=1, dash=(6, 4),
        )
