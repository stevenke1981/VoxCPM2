"""Basic Text-to-Speech panel."""

from __future__ import annotations

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.panels.base_panel import GeneratorPanel
from app.utils.config_manager import ConfigManager
from app.utils.i18n import t
from app.utils.translator import (
    PRESET_MAP,
    apply_preset,
    needs_translation,
    target_lang_display,
)

# Ordered preset list for the dropdown
_LANG_PRESETS = list(PRESET_MAP.keys())


class TTSPanel(GeneratorPanel):
    """
    Mode 1 — Plain TTS.

    The user types text in any of the 30 supported languages and clicks
    Generate.  An optional accent/gender preset can be selected; for foreign-
    language presets the text is automatically translated before synthesis.
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
            mode="tts",
            engine=engine,
            player=player,
            config=config,
            status_cb=status_cb,
            **kwargs,
        )

    def _build_input_section(self) -> None:
        f = self._input_frame
        f.grid_columnconfigure(0, weight=1)

        # ── Accent / gender preset ────────────────────────────────────────────
        self._lbl(f, t("tts.lang_hint_label")).grid(
            row=0, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        hint_row = ctk.CTkFrame(f, fg_color="transparent")
        hint_row.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="ew")
        hint_row.grid_columnconfigure(0, weight=1)

        self._preset_var = ctk.StringVar(value="女聲普通話")
        self._preset_box = ctk.CTkComboBox(
            hint_row,
            variable=self._preset_var,
            values=[""] + _LANG_PRESETS,
            width=220,
            command=self._on_preset_select,
        )
        self._preset_box.grid(row=0, column=0, sticky="w")

        # Auto-translate toggle (shown/hidden depending on preset)
        self._translate_var = ctk.BooleanVar(value=True)
        self._translate_chk = ctk.CTkCheckBox(
            hint_row,
            variable=self._translate_var,
            text="",
            width=20,
            checkbox_width=18,
            checkbox_height=18,
        )
        self._translate_chk.grid(row=0, column=1, padx=(10, 4))

        self._translate_lbl = ctk.CTkLabel(
            hint_row,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#4e9af1",
            anchor="w",
        )
        self._translate_lbl.grid(row=0, column=2, sticky="w")

        # Tip text (updates when preset changes)
        self._hint_tip = ctk.CTkLabel(
            f,
            text=t("tts.lang_hint_tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            anchor="w",
        )
        self._hint_tip.grid(row=2, column=0, padx=24, pady=(0, 8), sticky="w")

        # Initialise translate indicator
        self._on_preset_select("女聲普通話")

        # ── Text to synthesise ────────────────────────────────────────────────
        self._lbl(f, t("tts.input_label")).grid(
            row=3, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        self._text = self._textbox(f, height=120)
        self._text.grid(row=4, column=0, padx=24, pady=(0, 0), sticky="ew")
        self._text.insert(
            "0.0",
            "VoxCPM2 帶來多語言支援、創意聲音設計和可控聲音複製功能。",
        )

        ctk.CTkLabel(
            f,
            text=t("tts.tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            justify="left",
            anchor="w",
        ).grid(row=5, column=0, padx=24, pady=(8, 4), sticky="w")

    def _get_gen_kwargs(self) -> dict:
        text = self._text.get("1.0", "end").strip()
        if not text:
            raise ValueError(t("tts.error_empty"))

        preset = self._preset_var.get().strip()
        translate_on = self._translate_var.get()
        text = apply_preset(text, preset, translate_enabled=translate_on)

        return {"text": text}

    def _on_preset_select(self, value: str) -> None:
        self._preset_var.set(value)
        if needs_translation(value):
            lang = target_lang_display(value)
            self._translate_lbl.configure(text=f"自動翻譯為 {lang}")
            self._translate_chk.grid()
            self._translate_lbl.grid()
        else:
            self._translate_lbl.configure(text="")
            self._translate_chk.grid_remove()
            self._translate_lbl.grid_remove()
