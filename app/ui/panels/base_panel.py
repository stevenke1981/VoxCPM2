"""GeneratorPanel — shared base class for all TTS generation panels."""

from __future__ import annotations

import threading
from typing import Callable, Optional

import customtkinter as ctk
import numpy as np

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.widgets.audio_control_bar import AudioControlBar
from app.ui.widgets.waveform_canvas import WaveformCanvas
from app.utils.config_manager import ConfigManager
from app.utils.constants import WAVEFORM_H
from app.utils.i18n import t


class GeneratorPanel(ctk.CTkFrame):
    """
    Abstract base class for the four generation panels.

    Subclasses must implement:
    - ``_build_input_section()``: add widgets to ``self._input_frame``
    - ``_get_gen_kwargs() -> dict``: return keyword arguments for
      :meth:`~app.core.tts_engine.TTSEngine.generate`

    The base class provides:
    - A titled collapsible *input* section
    - ▶ Generate button with busy state, progress bar, status label
    - WaveformCanvas (drawn after generation)
    - AudioControlBar (enabled after generation)
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        title: str,
        engine: TTSEngine,
        player: AudioPlayer,
        config: ConfigManager,
        status_cb: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        super().__init__(master, **kwargs)
        self._title = title
        self._engine = engine
        self._player = player
        self._config = config
        self._status_cb = status_cb
        self._is_generating = False

        self.grid_columnconfigure(0, weight=1)

        self._build_title()
        self._build_input_container()
        self._build_input_section()        # subclass hook
        self._build_generate_section()
        self._build_output_section()

    # ── Subclass hooks ────────────────────────────────────────────────────────

    def _build_input_section(self) -> None:
        """Override: populate self._input_frame with panel-specific widgets."""
        raise NotImplementedError

    def _get_gen_kwargs(self) -> dict:
        """
        Override: return keyword arguments for ``TTSEngine.generate()``.

        Raise :class:`ValueError` with a user-friendly message if the inputs
        are invalid.
        """
        raise NotImplementedError

    # ── Layout builders ───────────────────────────────────────────────────────

    def _build_title(self) -> None:
        ctk.CTkLabel(
            self,
            text=self._title,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="w")

    def _build_input_container(self) -> None:
        self._input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._input_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self._input_frame.grid_columnconfigure(0, weight=1)

    def _build_generate_section(self) -> None:
        gen_frame = ctk.CTkFrame(self, fg_color="transparent")
        gen_frame.grid(row=2, column=0, padx=24, pady=(0, 4), sticky="ew")
        gen_frame.grid_columnconfigure(0, weight=1)

        self._gen_btn = ctk.CTkButton(
            gen_frame,
            text=t("panel.generate"),
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_generate,
        )
        self._gen_btn.grid(row=0, column=0, sticky="ew")

        self._status_lbl = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
            anchor="w",
        )
        self._status_lbl.grid(row=3, column=0, padx=26, pady=(2, 0), sticky="w")

        self._progress = ctk.CTkProgressBar(self)
        self._progress.grid(row=4, column=0, padx=24, pady=(4, 12), sticky="ew")
        self._progress.set(0)

    def _build_output_section(self) -> None:
        sep = ctk.CTkFrame(self, height=2, fg_color="#33334a")
        sep.grid(row=5, column=0, padx=24, pady=(4, 12), sticky="ew")

        self._waveform = WaveformCanvas(self, height=WAVEFORM_H)
        self._waveform.grid(row=6, column=0, padx=24, pady=(0, 10), sticky="ew")

        self._audio_bar = AudioControlBar(self, player=self._player)
        self._audio_bar.grid(row=7, column=0, padx=24, pady=(0, 24), sticky="ew")

    # ── Generation flow ───────────────────────────────────────────────────────

    def _on_generate(self) -> None:
        if self._is_generating:
            return
        if not self._engine.is_loaded:
            self._set_status(t("panel.model_not_loaded"), error=True)
            return

        try:
            kwargs = self._get_gen_kwargs()
        except ValueError as exc:
            self._set_status(f"⚠️  {exc}", error=True)
            return

        # Read synthesis params from config
        kwargs.setdefault("cfg_value", float(self._config.get("cfg_value", 2.0)))
        kwargs.setdefault(
            "inference_timesteps", int(self._config.get("inference_timesteps", 10))
        )

        self._is_generating = True
        self._gen_btn.configure(state="disabled")
        self._set_status(t("panel.generating"))
        self._progress.set(0.35)

        threading.Thread(
            target=self._worker,
            args=(kwargs,),
            daemon=True,
            name=f"{self.__class__.__name__}-worker",
        ).start()

    def _worker(self, kwargs: dict) -> None:
        try:
            wav = self._engine.generate(**kwargs)
            self.after(0, lambda: self._on_done(wav))
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            self.after(0, lambda: self._on_error(msg))

    def _on_done(self, wav: np.ndarray) -> None:
        self._is_generating = False
        self._gen_btn.configure(state="normal")
        self._progress.set(1.0)

        sr = self._engine.sample_rate
        dur = len(wav) / sr
        self._set_status(t("panel.done_status", dur=dur, sr=sr))
        self._status_cb(t("panel.generated_status", dur=dur, sr=sr))

        self._player.load(wav, sr)
        self._waveform.draw_waveform(wav)
        self._audio_bar.set_has_audio(True)

    def _on_error(self, msg: str) -> None:
        self._is_generating = False
        self._gen_btn.configure(state="normal")
        self._progress.set(0)
        self._set_status(f"✗  {msg}", error=True)
        self._status_cb(t("panel.error_status", msg=msg))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, *, error: bool = False) -> None:
        color = "#e05252" if error else "#aaaaaa"
        self._status_lbl.configure(text=msg, text_color=color)

    @staticmethod
    def _lbl(parent: ctk.CTkBaseClass, text: str, **kw: object) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=13),
            anchor="w",
            **kw,  # type: ignore[arg-type]
        )

    @staticmethod
    def _textbox(parent: ctk.CTkBaseClass, height: int = 100) -> ctk.CTkTextbox:
        tb = ctk.CTkTextbox(parent, height=height, wrap="word")
        return tb
