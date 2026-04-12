"""Basic Text-to-Speech panel."""

from __future__ import annotations

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.panels.base_panel import GeneratorPanel
from app.utils.config_manager import ConfigManager
from app.utils.i18n import t

# Language/accent preset hints — prepended as (hint) before the text
_LANG_PRESETS = [
    "",                         # none / auto-detect
    # 標準中文
    "普通話",
    "台灣腔普通話",
    "粵語",
    # 中文方言
    "四川話",
    "吳語",
    "閩南話",
    "東北話",
    "河南話",
    "陝西話",
    "山東話",
    "天津話",
    # 外語
    "Mandarin",
    "Cantonese",
    "English",
    "British English",
    "American English",
    "Japanese",
    "Korean",
]


class TTSPanel(GeneratorPanel):
    """
    Mode 1 — Plain TTS.

    The user types text in any of the 30 supported languages and clicks
    Generate.  An optional language/accent hint can be prepended as a
    parenthesis prefix to guide the model's pronunciation.
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

        # ── Language / accent hint ────────────────────────────────────────────
        self._lbl(f, t("tts.lang_hint_label")).grid(
            row=0, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        hint_row = ctk.CTkFrame(f, fg_color="transparent")
        hint_row.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="ew")
        hint_row.grid_columnconfigure(0, weight=1)

        self._lang_hint = ctk.CTkEntry(
            hint_row,
            height=34,
            placeholder_text="普通話  /  Mandarin  /  留空則自動偵測",
            font=ctk.CTkFont(size=12),
        )
        self._lang_hint.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        # Default to 普通話 for zh-TW locale
        self._lang_hint.insert(0, "普通話")

        self._preset_var = ctk.StringVar(value="▾")
        ctk.CTkComboBox(
            hint_row,
            variable=self._preset_var,
            values=_LANG_PRESETS,
            width=140,
            command=self._on_preset_select,
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            f,
            text=t("tts.lang_hint_tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            anchor="w",
        ).grid(row=2, column=0, padx=24, pady=(0, 8), sticky="w")

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

        hint = self._lang_hint.get().strip()
        if hint:
            text = f"({hint}){text}"

        return {"text": text}

    def _on_preset_select(self, value: str) -> None:
        self._lang_hint.delete(0, "end")
        self._lang_hint.insert(0, value)
