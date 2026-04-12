"""Ultimate Voice Cloning panel — highest fidelity with transcript."""

from __future__ import annotations

import tkinter.filedialog as fd

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.panels.base_panel import GeneratorPanel
from app.utils.config_manager import ConfigManager
from app.utils.i18n import t


_EXAMPLE_TEXT = "This is an ultimate cloning demonstration using VoxCPM2 Studio."


class UltimateClonePanel(GeneratorPanel):
    """
    Mode 4 — Ultimate Voice Cloning.

    Provide both the reference audio **and** its exact transcript for
    maximum timbre fidelity.  Passing the same clip to both reference and
    prompt fields gives the highest speaker similarity.
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
            title=t("ultimate.title"),
            engine=engine,
            player=player,
            config=config,
            status_cb=status_cb,
            **kwargs,
        )

    def _build_input_section(self) -> None:
        f = self._input_frame
        f.grid_columnconfigure(0, weight=1)

        # ── Prompt (reference) audio ──────────────────────────────────────────
        self._lbl(f, t("ultimate.ref_label")).grid(
            row=0, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        ref_row = ctk.CTkFrame(f, fg_color="transparent")
        ref_row.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="ew")
        ref_row.grid_columnconfigure(0, weight=1)

        self._ref_path = ctk.CTkEntry(
            ref_row, height=36,
            placeholder_text=t("ultimate.ref_placeholder"),
            font=ctk.CTkFont(size=12),
        )
        self._ref_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            ref_row, text=t("ultimate.browse"), width=84, height=36,
            command=self._browse_ref,
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            f,
            text=t("ultimate.ref_tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            justify="left", anchor="w",
        ).grid(row=2, column=0, padx=24, pady=(0, 10), sticky="w")

        # ── Transcript of the reference audio ────────────────────────────────
        self._lbl(f, t("ultimate.transcript_label")).grid(
            row=3, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        self._transcript = self._textbox(f, height=72)
        self._transcript.grid(row=4, column=0, padx=24, pady=(0, 4), sticky="ew")
        self._transcript.insert("0.0", t("ultimate.transcript_placeholder"))

        ctk.CTkLabel(
            f,
            text=t("ultimate.transcript_warning"),
            font=ctk.CTkFont(size=11),
            text_color="#aa7733",
            anchor="w",
        ).grid(row=5, column=0, padx=24, pady=(0, 10), sticky="w")

        # ── Text to synthesise ────────────────────────────────────────────────
        self._lbl(f, t("ultimate.text_label")).grid(
            row=6, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        self._text = self._textbox(f, height=90)
        self._text.grid(row=7, column=0, padx=24, sticky="ew")
        self._text.insert("0.0", _EXAMPLE_TEXT)

    def _get_gen_kwargs(self) -> dict:
        ref = self._ref_path.get().strip()
        if not ref:
            raise ValueError(t("ultimate.error_no_ref"))

        transcript = self._transcript.get("1.0", "end").strip()
        if not transcript:
            raise ValueError(t("ultimate.error_no_transcript"))

        text = self._text.get("1.0", "end").strip()
        if not text:
            raise ValueError(t("ultimate.error_no_text"))

        return {
            "text": text,
            "reference_wav_path": ref,
            "prompt_wav_path": ref,        # same clip → highest similarity
            "prompt_text": transcript,
        }

    def _browse_ref(self) -> None:
        path = fd.askopenfilename(
            title=t("ultimate.browse_ref_title"),
            filetypes=[
                ("WAV files", "*.wav"),
                ("All audio", "*.wav *.flac *.mp3"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._ref_path.delete(0, "end")
            self._ref_path.insert(0, path)
