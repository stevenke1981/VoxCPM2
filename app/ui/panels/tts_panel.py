"""Basic Text-to-Speech panel."""

from __future__ import annotations

import threading

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

_LANG_PRESETS = list(PRESET_MAP.keys())


class TTSPanel(GeneratorPanel):
    """
    Mode 1 — Plain TTS.

    Left textbox : input text.
    Right textbox: translated / final text.

    「翻譯」button translates immediately (async) and fills the right box.
    「生成」uses whatever is in the right box (or left box if no translation).
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
        self._translating = False
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

    # ── Input section ─────────────────────────────────────────────────────────

    def _build_input_section(self) -> None:
        f = self._input_frame
        f.grid_columnconfigure(0, weight=1)

        # ── Preset row ────────────────────────────────────────────────────────
        self._lbl(f, t("tts.lang_hint_label")).grid(
            row=0, column=0, padx=24, pady=(0, 4), sticky="w"
        )

        preset_row = ctk.CTkFrame(f, fg_color="transparent")
        preset_row.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="ew")

        self._preset_var = ctk.StringVar(value="女聲普通話")
        self._preset_box = ctk.CTkComboBox(
            preset_row,
            variable=self._preset_var,
            values=[""] + _LANG_PRESETS,
            width=200,
            command=self._on_preset_select,
        )
        self._preset_box.grid(row=0, column=0, padx=(0, 10))

        # 「翻譯」button — visible only for foreign presets
        self._translate_btn = ctk.CTkButton(
            preset_row,
            text="🌐  翻譯",
            width=90, height=32,
            font=ctk.CTkFont(size=12),
            fg_color="#2a3a5e", hover_color="#1f2d4a",
            command=self._do_translate,
        )
        self._translate_btn.grid(row=0, column=1, padx=(0, 8))

        # Translation status label
        self._translate_lbl = ctk.CTkLabel(
            preset_row, text="",
            font=ctk.CTkFont(size=12), text_color="#4e9af1", anchor="w",
        )
        self._translate_lbl.grid(row=0, column=2, sticky="w")

        # Tip
        ctk.CTkLabel(
            f,
            text=t("tts.lang_hint_tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            anchor="w",
        ).grid(row=2, column=0, padx=24, pady=(0, 8), sticky="w")

        # Initialise visibility
        self._on_preset_select("女聲普通話")

        # ── Two-column text area ──────────────────────────────────────────────
        cols = ctk.CTkFrame(f, fg_color="transparent")
        cols.grid(row=3, column=0, padx=24, pady=(0, 0), sticky="ew")
        cols.grid_columnconfigure(0, weight=1)
        cols.grid_columnconfigure(1, weight=1)

        # Left header
        ctk.CTkLabel(
            cols, text=t("tts.input_label"),
            font=ctk.CTkFont(size=13), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 2))

        # Right header + copy button
        right_hdr = ctk.CTkFrame(cols, fg_color="transparent")
        right_hdr.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 2))
        right_hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            right_hdr, text=t("tts.translated_label"),
            font=ctk.CTkFont(size=13), anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            right_hdr, text=t("tts.copy_btn"), width=60, height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#2a3a5e", hover_color="#1f2d4a",
            command=self._copy_translated,
        ).grid(row=0, column=1, sticky="e")

        # Left textbox — original input
        self._text = self._textbox(cols, height=130)
        self._text.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self._text.insert(
            "0.0",
            "VoxCPM2 帶來多語言支援、創意聲音設計和可控聲音複製功能。",
        )

        # Right textbox — translated / final text (editable)
        self._translated = self._textbox(cols, height=130)
        self._translated.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        self._translated.configure(text_color="#88ccff")

        ctk.CTkLabel(
            f,
            text=t("tts.tip"),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            justify="left", anchor="w",
        ).grid(row=4, column=0, padx=24, pady=(8, 4), sticky="w")

    # ── Preset / translate UI ─────────────────────────────────────────────────

    def _on_preset_select(self, value: str) -> None:
        self._preset_var.set(value)
        if needs_translation(value):
            lang = target_lang_display(value)
            self._translate_lbl.configure(text=f"→ {lang}")
            self._translate_btn.grid()
            self._translate_lbl.grid()
        else:
            self._translate_lbl.configure(text="")
            self._translate_btn.grid_remove()
            self._translate_lbl.grid_remove()
            # Clear right box when switching back to Chinese preset
            self._translated.delete("1.0", "end")

    # ── Translate button ──────────────────────────────────────────────────────

    def _do_translate(self) -> None:
        """Translate the left box text and show result in the right box."""
        if self._translating:
            return
        text = self._text.get("1.0", "end").strip()
        if not text:
            return
        preset = self._preset_var.get().strip()
        if not needs_translation(preset):
            return

        self._translating = True
        self._translate_btn.configure(state="disabled", text="翻譯中…")
        self._translate_lbl.configure(text="")

        threading.Thread(
            target=self._translate_worker,
            args=(text, preset),
            daemon=True,
            name="TTSTranslatePreview",
        ).start()

    def _translate_worker(self, text: str, preset: str) -> None:
        try:
            result = apply_preset(text, preset, translate_enabled=True)
            self.after(0, lambda: self._on_translate_done(result))
        except ConnectionError as exc:
            self.after(0, lambda: self._on_translate_error(str(exc)))
        except Exception as exc:  # noqa: BLE001
            self.after(0, lambda: self._on_translate_error(str(exc)))

    def _on_translate_done(self, result: str) -> None:
        self._translating = False
        self._translate_btn.configure(state="normal", text="🌐  翻譯")
        lang = target_lang_display(self._preset_var.get())
        self._translate_lbl.configure(text=f"→ {lang}")
        self._update_translated(result)

    def _on_translate_error(self, msg: str) -> None:
        self._translating = False
        self._translate_btn.configure(state="normal", text="🌐  翻譯")
        self._translate_lbl.configure(text=f"⚠ {msg}", text_color="#e05252")

    # ── Generation ────────────────────────────────────────────────────────────

    def _on_generate(self) -> None:
        """Override: run translation + synthesis together in background thread."""
        if self._is_generating:
            return
        if not self._engine.is_loaded:
            self._set_status(t("panel.model_not_loaded"), error=True)
            return

        raw_text = self._text.get("1.0", "end").strip()
        if not raw_text:
            self._set_status(f"⚠️  {t('tts.error_empty')}", error=True)
            return

        preset = self._preset_var.get().strip()
        cfg_value = float(self._config.get("cfg_value", 2.0))
        steps = int(self._config.get("inference_timesteps", 10))

        # If right box already has (manually edited) translated text, use it
        right_text = self._translated.get("1.0", "end").strip()
        # Only reuse right box if it looks like a translation result
        # (i.e. it was filled in and the preset requires translation)
        use_right = bool(right_text) and needs_translation(preset)

        self._last_kwargs = {"text": raw_text}
        self._is_generating = True
        self._gen_btn.configure(state="disabled")
        self._set_status(t("panel.generating"))
        self._start_progress_animation()

        threading.Thread(
            target=self._worker_with_translation,
            args=(raw_text, preset, cfg_value, steps, right_text if use_right else None),
            daemon=True,
            name="TTSSynthesisWorker",
        ).start()

    def _worker_with_translation(
        self,
        raw_text: str,
        preset: str,
        cfg_value: float,
        steps: int,
        pre_translated: str | None,
    ) -> None:
        try:
            if pre_translated:
                # Right box was already filled — use it directly
                final_text = pre_translated
            else:
                # Translate (or just apply hint) now
                final_text = apply_preset(raw_text, preset, translate_enabled=True)
                # Show translated result in right box
                captured = final_text
                self.after(0, lambda: self._update_translated(captured))

            self._last_kwargs["text"] = final_text

            wav = self._engine.generate(
                text=final_text,
                cfg_value=cfg_value,
                inference_timesteps=steps,
            )
            self.after(0, lambda: self._on_done(wav))
        except ConnectionError as exc:
            msg = str(exc)
            self.after(0, lambda: self._on_error(msg))
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            self.after(0, lambda: self._on_error(msg))

    def _get_gen_kwargs(self) -> dict:
        # Not used — _on_generate is fully overridden above
        return {}

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_translated(self, text: str) -> None:
        self._translated.delete("1.0", "end")
        self._translated.insert("1.0", text)

    def _copy_translated(self) -> None:
        content = self._translated.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self._status_cb(t("tts.copied"))
