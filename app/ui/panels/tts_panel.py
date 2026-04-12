"""Basic Text-to-Speech panel."""

from __future__ import annotations

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.panels.base_panel import GeneratorPanel
from app.utils.config_manager import ConfigManager
from app.utils.i18n import t


class TTSPanel(GeneratorPanel):
    """
    Mode 1 — Plain TTS.

    The user types text in any of the 30 supported languages and clicks
    Generate.  No reference audio is required.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        engine: TTSEngine,
        player: AudioPlayer,
        config: ConfigManager,
        status_cb,
        **kwargs: object,
    ) -> None:
        super().__init__(
            master,
            title=t("tts.title"),
            engine=engine,
            player=player,
            config=config,
            status_cb=status_cb,
            **kwargs,
        )

    def _build_input_section(self) -> None:
        f = self._input_frame
        f.grid_columnconfigure(0, weight=1)

        self._lbl(f, t("tts.input_label")).grid(
            row=0, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        self._text = self._textbox(f, height=130)
        self._text.grid(row=1, column=0, padx=24, pady=(0, 0), sticky="ew")
        self._text.insert(
            "0.0",
            "VoxCPM2 brings multilingual support, creative voice design, "
            "and controllable voice cloning to the open-source community.",
        )

        ctk.CTkLabel(
            f,
            text=t("tts.tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, padx=24, pady=(8, 4), sticky="w")

    def _get_gen_kwargs(self) -> dict:
        text = self._text.get("1.0", "end").strip()
        if not text:
            raise ValueError(t("tts.error_empty"))
        return {"text": text}
