"""Voice Design panel — generate a novel voice from a text description."""

from __future__ import annotations

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.panels.base_panel import GeneratorPanel
from app.utils.config_manager import ConfigManager
from app.utils.i18n import t


_EXAMPLE_DESC = "A young woman, gentle and sweet voice, speaking in a calm pace"
_EXAMPLE_TEXT = "Hello! Welcome to VoxCPM2 Studio. How may I assist you today?"

_PRESETS = [
    # Female voices
    "A young woman, gentle and sweet voice",
    "A professional female narrator, clear and neutral",
    "A warm middle-aged woman, soothing and motherly",
    "An energetic young woman, bright and enthusiastic",
    "A calm elderly woman, wise and soft-spoken",
    "A seductive female voice, low and breathy",
    "A cheerful girl, innocent and lively",
    "A stern businesswoman, confident and direct",
    "A whispering female voice, intimate and hushed",
    "A dramatic female voice, theatrical and expressive",
    # Male voices
    "A middle-aged man, deep and authoritative tone",
    "An elderly gentleman, warm and reassuring",
    "A cheerful young man, energetic and fast-paced",
    "A baritone male narrator, rich and resonant",
    "A young man, casual and friendly",
    "A gruff old man, raspy and weathered",
    "A news anchor male voice, clear and professional",
    "A soft-spoken young man, gentle and thoughtful",
    "A boisterous man, loud and jovial",
    "A mysterious male voice, low and deliberate",
    # Multilingual / accented
    "A Mandarin-accented English speaker, clear enunciation",
    "A British English accent, polished and refined",
    "A Southern American drawl, relaxed and warm",
    "A French-accented English speaker, elegant and musical",
    "A Japanese-accented voice, precise and polite",
    # Special / character
    "A robot voice, slightly metallic and monotone",
    "An excited sports commentator, fast and dramatic",
    "A sleepy voice, slow and drowsy",
    "A storyteller, rich and expressive",
    "A documentary narrator, calm and authoritative",
]


class VoiceDesignPanel(GeneratorPanel):
    """
    Mode 2 — Voice Design.

    Generates a novel voice purely from a natural-language description —
    no reference audio required.  The description is automatically wrapped
    in parentheses and prepended to the synthesis text.
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
            title=t("vd.title"),
            mode="voice_design",
            engine=engine,
            player=player,
            config=config,
            status_cb=status_cb,
            **kwargs,
        )

    def _build_input_section(self) -> None:
        f = self._input_frame
        f.grid_columnconfigure(0, weight=1)

        # ── Voice description ─────────────────────────────────────────────────
        self._lbl(f, t("vd.desc_label")).grid(
            row=0, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        desc_frame = ctk.CTkFrame(f, fg_color="transparent")
        desc_frame.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="ew")
        desc_frame.grid_columnconfigure(0, weight=1)

        self._desc = ctk.CTkEntry(
            desc_frame,
            height=38,
            placeholder_text=t("vd.desc_placeholder"),
            font=ctk.CTkFont(size=13),
        )
        self._desc.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._desc.insert(0, _EXAMPLE_DESC)

        # Preset dropdown
        self._preset_var = ctk.StringVar(value=t("vd.presets"))
        preset_menu = ctk.CTkComboBox(
            desc_frame,
            variable=self._preset_var,
            values=_PRESETS,
            width=200,
            command=self._on_preset_select,
        )
        preset_menu.grid(row=0, column=1)

        ctk.CTkLabel(
            f, text=t("vd.desc_tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            justify="left", anchor="w",
        ).grid(row=2, column=0, padx=24, pady=(0, 10), sticky="w")

        # ── Text to synthesise ────────────────────────────────────────────────
        self._lbl(f, t("vd.text_label")).grid(
            row=3, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        self._text = self._textbox(f, height=100)
        self._text.grid(row=4, column=0, padx=24, pady=(0, 0), sticky="ew")
        self._text.insert("0.0", _EXAMPLE_TEXT)

        ctk.CTkLabel(
            f,
            text=t("vd.gen_tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            anchor="w",
        ).grid(row=5, column=0, padx=24, pady=(6, 0), sticky="w")

    def _get_gen_kwargs(self) -> dict:
        desc = self._desc.get().strip()
        text = self._text.get("1.0", "end").strip()

        if not desc:
            raise ValueError(t("vd.error_no_desc"))
        if not text:
            raise ValueError(t("vd.error_no_text"))

        # VoxCPM2 convention: embed description in leading parentheses
        combined = f"({desc}){text}"
        return {"text": combined}

    def _on_preset_select(self, value: str) -> None:
        if value and value != t("vd.presets"):
            self._desc.delete(0, "end")
            self._desc.insert(0, value)
