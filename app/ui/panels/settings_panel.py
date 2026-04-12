"""Settings & Model Management panel."""

from __future__ import annotations

import threading
import tkinter.filedialog as fd
from typing import Callable

import customtkinter as ctk

from app.core.tts_engine import TTSEngine
from app.utils.config_manager import ConfigManager
from app.utils.constants import DEFAULT_CFG, DEFAULT_MODEL, DEFAULT_MODEL_CACHE_DIR, DEFAULT_STEPS
from app.utils.i18n import SUPPORTED_LOCALES, t


class SettingsPanel(ctk.CTkFrame):
    """
    Controls model loading / unloading and all synthesis parameters.

    Unlike the generator panels this does not inherit from GeneratorPanel
    because it does not produce audio directly.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        engine: TTSEngine,
        config: ConfigManager,
        status_cb: Callable[[str], None],
        on_model_state_change: Callable[[bool], None],
        **kwargs: object,
    ) -> None:
        super().__init__(master, **kwargs)
        self._engine = engine
        self._config = config
        self._status_cb = status_cb
        self._on_model_state_change = on_model_state_change
        self._is_loading = False

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        row = 0

        # Title
        ctk.CTkLabel(
            self,
            text=t("settings.title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).grid(row=row, column=0, padx=24, pady=(20, 16), sticky="w")
        row += 1

        # ── Model section ────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=t("settings.model_section"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=row, column=0, padx=24, pady=(0, 8), sticky="w")
        row += 1

        model_row = ctk.CTkFrame(self, fg_color="transparent")
        model_row.grid(row=row, column=0, padx=24, pady=(0, 6), sticky="ew")
        model_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._model_entry = ctk.CTkEntry(
            model_row, height=36,
            font=ctk.CTkFont(size=13),
            placeholder_text=t("settings.model_placeholder"),
        )
        self._model_entry.insert(0, self._config.get("model_name", DEFAULT_MODEL))
        self._model_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._load_btn = ctk.CTkButton(
            model_row, text=t("settings.load_model"), width=110, height=36,
            fg_color="#1a5276", hover_color="#2471a3",
            command=self._on_load,
        )
        self._load_btn.grid(row=0, column=1, padx=(0, 6))

        self._unload_btn = ctk.CTkButton(
            model_row, text=t("settings.unload"), width=80, height=36,
            fg_color="#6e2c00", hover_color="#922b21",
            command=self._on_unload,
            state="disabled",
        )
        self._unload_btn.grid(row=0, column=2)

        # ── Model cache directory ─────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=t("settings.model_cache_dir"),
            font=ctk.CTkFont(size=13),
            anchor="w",
        ).grid(row=row, column=0, padx=24, pady=(4, 4), sticky="w")
        row += 1

        cache_row = ctk.CTkFrame(self, fg_color="transparent")
        cache_row.grid(row=row, column=0, padx=24, pady=(0, 6), sticky="ew")
        cache_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._cache_entry = ctk.CTkEntry(
            cache_row, height=36,
            font=ctk.CTkFont(size=12),
            placeholder_text=t("settings.model_cache_placeholder"),
        )
        self._cache_entry.insert(0, self._config.get("model_cache_dir", DEFAULT_MODEL_CACHE_DIR))
        self._cache_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            cache_row, text=t("settings.browse"), width=84, height=36,
            command=self._browse_cache,
        ).grid(row=0, column=1)

        # Denoiser checkbox
        self._denoiser_var = ctk.BooleanVar(
            value=bool(self._config.get("load_denoiser", False))
        )
        ctk.CTkCheckBox(
            self,
            text=t("settings.denoiser"),
            variable=self._denoiser_var,
            font=ctk.CTkFont(size=12),
        ).grid(row=row, column=0, padx=24, pady=(0, 8), sticky="w")
        row += 1

        # Model status badge
        self._status_badge = ctk.CTkLabel(
            self,
            text=t("settings.model_not_loaded_badge"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#343444",
            corner_radius=6,
            text_color="#888888",
        )
        self._status_badge.grid(row=row, column=0, padx=24, pady=(0, 4), sticky="w")
        row += 1

        # Model log
        self._model_log = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            anchor="w",
        )
        self._model_log.grid(row=row, column=0, padx=26, pady=(0, 14), sticky="w")
        row += 1

        # ── Separator ────────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=2, fg_color="#33334a").grid(
            row=row, column=0, padx=24, pady=(0, 16), sticky="ew"
        )
        row += 1

        # ── Synthesis parameters ─────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=t("settings.synthesis_params"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=row, column=0, padx=24, pady=(0, 12), sticky="w")
        row += 1

        # CFG value
        row = self._add_slider(
            row,
            label=t("settings.cfg_label"),
            tooltip=t("settings.cfg_tooltip"),
            from_=1.0, to=5.0, steps=40,
            config_key="cfg_value",
            default=DEFAULT_CFG,
        )

        # Inference timesteps
        row = self._add_slider(
            row,
            label=t("settings.steps_label"),
            tooltip=t("settings.steps_tooltip"),
            from_=5, to=50, steps=45,
            config_key="inference_timesteps",
            default=DEFAULT_STEPS,
            is_int=True,
        )

        # ── Separator ────────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=2, fg_color="#33334a").grid(
            row=row, column=0, padx=24, pady=(4, 16), sticky="ew"
        )
        row += 1

        # ── Output directory ─────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=t("settings.output_dir"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=row, column=0, padx=24, pady=(0, 8), sticky="w")
        row += 1

        out_row = ctk.CTkFrame(self, fg_color="transparent")
        out_row.grid(row=row, column=0, padx=24, pady=(0, 4), sticky="ew")
        out_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._out_entry = ctk.CTkEntry(out_row, height=36, font=ctk.CTkFont(size=12))
        self._out_entry.insert(0, self._config.get("output_dir", "./output"))
        self._out_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            out_row, text=t("settings.browse"), width=84, height=36,
            command=self._browse_out,
        ).grid(row=0, column=1)

        # ── Separator ────────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=2, fg_color="#33334a").grid(
            row=row, column=0, padx=24, pady=(4, 16), sticky="ew"
        )
        row += 1

        # ── Language selector ─────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=t("settings.language"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=row, column=0, padx=24, pady=(0, 8), sticky="w")
        row += 1

        lang_row = ctk.CTkFrame(self, fg_color="transparent")
        lang_row.grid(row=row, column=0, padx=24, pady=(0, 4), sticky="ew")
        row += 1

        _LOCALE_LABELS = {"zh-TW": "繁體中文 (zh-TW)", "en": "English (en)"}
        current_lang = self._config.get("language", "zh-TW")
        self._lang_var = ctk.StringVar(value=_LOCALE_LABELS.get(current_lang, current_lang))

        ctk.CTkComboBox(
            lang_row,
            variable=self._lang_var,
            values=[_LOCALE_LABELS.get(loc, loc) for loc in SUPPORTED_LOCALES],
            width=220,
            command=self._on_language_change,
        ).grid(row=0, column=0)

        self._lang_note = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color="#e0a030",
            anchor="w",
        )
        self._lang_note.grid(row=row, column=0, padx=26, pady=(0, 8), sticky="w")
        row += 1

        # ── Save settings button ─────────────────────────────────────────────
        ctk.CTkButton(
            self,
            text=t("settings.save"),
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2d6a4f", hover_color="#3a8a63",
            command=self._save_settings,
        ).grid(row=row, column=0, padx=24, pady=(16, 24), sticky="w")

        # Sync button states to model state
        self._refresh_model_ui()

    def _add_slider(
        self,
        row: int,
        label: str,
        tooltip: str,
        from_: float,
        to: float,
        steps: int,
        config_key: str,
        default: float,
        is_int: bool = False,
    ) -> int:
        param_frame = ctk.CTkFrame(self, fg_color="transparent")
        param_frame.grid(row=row, column=0, padx=24, pady=(0, 12), sticky="ew")
        param_frame.grid_columnconfigure(1, weight=1)
        row += 1

        ctk.CTkLabel(
            param_frame, text=f"{label}:",
            font=ctk.CTkFont(size=13),
            width=170, anchor="w",
        ).grid(row=0, column=0)

        val = float(self._config.get(config_key, default))
        value_lbl = ctk.CTkLabel(
            param_frame,
            text=str(int(val)) if is_int else f"{val:.1f}",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=44,
        )
        value_lbl.grid(row=0, column=2, padx=(8, 0))

        slider = ctk.CTkSlider(
            param_frame,
            from_=from_, to=to,
            number_of_steps=steps,
        )
        slider.set(val)
        slider.grid(row=0, column=1, sticky="ew")

        def _on_slide(v: float) -> None:
            text = str(int(v)) if is_int else f"{v:.1f}"
            value_lbl.configure(text=text)
            self._config.set(config_key, int(v) if is_int else round(v, 2))

        slider.configure(command=_on_slide)

        # Tooltip (as small italic label below)
        ctk.CTkLabel(
            param_frame, text=tooltip,
            font=ctk.CTkFont(size=10),
            text_color="#556677",
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, sticky="w")

        return row

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_load(self) -> None:
        if self._is_loading or self._engine.is_loaded:
            return
        model_name = self._model_entry.get().strip() or DEFAULT_MODEL
        cache_dir = self._cache_entry.get().strip() or DEFAULT_MODEL_CACHE_DIR
        self._config.set("model_name", model_name)
        self._config.set("model_cache_dir", cache_dir)
        self._config.set("load_denoiser", self._denoiser_var.get())
        self._is_loading = True
        self._load_btn.configure(state="disabled", text=t("settings.loading"))
        self._set_log(t("settings.starting_load"))
        threading.Thread(
            target=self._load_worker,
            args=(model_name, self._denoiser_var.get(), cache_dir),
            daemon=True,
            name="ModelLoader",
        ).start()

    def _load_worker(self, model_name: str, load_denoiser: bool, cache_dir: str) -> None:
        try:
            self._engine.load_model(
                model_name=model_name,
                load_denoiser=load_denoiser,
                cache_dir=cache_dir,
                progress_callback=lambda m: self.after(0, lambda: self._set_log(m)),
            )
            self.after(0, self._on_load_success)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            self.after(0, lambda: self._on_load_error(msg))

    def _on_load_success(self) -> None:
        self._is_loading = False
        self._refresh_model_ui()
        self._status_cb(t("settings.model_load_success"))
        self._on_model_state_change(True)

    def _on_load_error(self, msg: str) -> None:
        self._is_loading = False
        self._load_btn.configure(state="normal", text=t("settings.load_model"))
        self._set_log(f"✗ {msg}")
        self._status_cb(t("settings.model_load_error", msg=msg))

    def _on_unload(self) -> None:
        self._engine.unload_model()
        self._refresh_model_ui()
        self._set_log(t("settings.model_unloaded"))
        self._status_cb(t("settings.model_unloaded_status"))
        self._on_model_state_change(False)

    def _browse_cache(self) -> None:
        path = fd.askdirectory(title=t("dialog.browse_cache"))
        if path:
            self._cache_entry.delete(0, "end")
            self._cache_entry.insert(0, path)
            self._config.set("model_cache_dir", path)

    def _browse_out(self) -> None:
        path = fd.askdirectory(title=t("dialog.browse_out"))
        if path:
            self._out_entry.delete(0, "end")
            self._out_entry.insert(0, path)
            self._config.set("output_dir", path)

    def _on_language_change(self, display_value: str) -> None:
        # Map display label back to locale code
        _LABEL_TO_LOCALE = {"繁體中文 (zh-TW)": "zh-TW", "English (en)": "en"}
        locale = _LABEL_TO_LOCALE.get(display_value, display_value)
        self._config.set("language", locale)
        self._lang_note.configure(text=t("settings.restart_required"))

    def _save_settings(self) -> None:
        self._config.set("output_dir", self._out_entry.get().strip())
        self._config.set("model_cache_dir", self._cache_entry.get().strip())
        self._config.save()
        self._status_cb(t("settings.saved"))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_log(self, msg: str) -> None:
        self._model_log.configure(text=msg)

    def _refresh_model_ui(self) -> None:
        loaded = self._engine.is_loaded
        if loaded:
            self._status_badge.configure(
                text=t("settings.model_loaded_badge", sr=self._engine.sample_rate),
                text_color="#2ecc71",
                fg_color="#1a3a27",
            )
            self._load_btn.configure(state="disabled", text=t("settings.load_model"))
            self._unload_btn.configure(state="normal")
        else:
            self._status_badge.configure(
                text=t("settings.model_not_loaded_badge"),
                text_color="#888888",
                fg_color="#343444",
            )
            self._load_btn.configure(state="normal", text=t("settings.load_model"))
            self._unload_btn.configure(state="disabled")
