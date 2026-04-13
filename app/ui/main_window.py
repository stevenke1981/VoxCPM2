"""MainWindow — root CustomTkinter window with sidebar navigation."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.core.tts_engine import TTSEngine
from app.ui.panels.cloning_panel import CloningPanel
from app.ui.panels.history_panel import HistoryPanel
from app.ui.panels.settings_panel import SettingsPanel
from app.ui.panels.srt_panel import SRTPanel
from app.ui.panels.tts_panel import TTSPanel
from app.ui.panels.ultimate_clone_panel import UltimateClonePanel
from app.ui.panels.voice_design_panel import VoiceDesignPanel
from app.utils.config_manager import ConfigManager
from app.utils.constants import (
    APP_NAME,
    APP_VERSION,
    MIN_H,
    MIN_W,
    NAV_ITEMS,
    PANEL_CLONING,
    PANEL_HISTORY,
    PANEL_SETTINGS,
    PANEL_SRT,
    PANEL_TTS,
    PANEL_ULTIMATE,
    PANEL_VOICE_DESIGN,
    SIDEBAR_WIDTH,
    WAV_DIR,
)
from app.utils.history_manager import HistoryEntry, HistoryManager
from app.utils.i18n import t

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class MainWindow(ctk.CTk):
    """
    Root application window.

    Layout::

        ┌──────────────────┬───────────────────────────────┐
        │   sidebar (fixed) │   content area (expands)      │
        │   nav buttons    │   one panel shown at a time   │
        │   model badge    │                               │
        ├──────────────────┴───────────────────────────────┤
        │   status bar (full width)                        │
        └──────────────────────────────────────────────────┘
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry(f"{MIN_W}x{MIN_H}")
        self.minsize(MIN_W, MIN_H)

        # ── Shared services ───────────────────────────────────────────────────
        self._engine = TTSEngine()
        self._player = AudioPlayer()
        self._config = config if config is not None else ConfigManager()
        self._history = HistoryManager(wav_dir=WAV_DIR)

        # ── Layout ────────────────────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._build_status_bar()

        # ── Show default panel & wire close ──────────────────────────────────
        self._show_panel(PANEL_TTS)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Auto-load model if enabled ────────────────────────────────────────
        if self._config.get("auto_load_model", False):
            self.after(500, self._panels[PANEL_SETTINGS].trigger_auto_load)  # type: ignore[attr-defined]

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        self._sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, corner_radius=0)
        self._sidebar.grid(row=0, column=0, rowspan=1, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._sidebar.grid_columnconfigure(0, weight=1)
        self._sidebar.grid_rowconfigure(9, weight=1)   # spacer

        # App logo / title
        ctk.CTkLabel(
            self._sidebar,
            text="VoxCPM2",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#4e9af1",
        ).grid(row=0, column=0, padx=16, pady=(20, 2), sticky="w")

        ctk.CTkLabel(
            self._sidebar,
            text=t("app.subtitle"),
            font=ctk.CTkFont(size=13),
            text_color="#667788",
        ).grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        # ── Nav buttons ───────────────────────────────────────────────────────
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for i, (icon, label_key, panel_id) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {t(label_key)}",
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#2a2a3e",
                font=ctk.CTkFont(size=13),
                command=lambda pid=panel_id: self._show_panel(pid),
            )
            btn.grid(row=2 + i, column=0, padx=8, pady=2, sticky="ew")
            self._nav_btns[panel_id] = btn

        # ── Model status badge (bottom of sidebar) ────────────────────────────
        self._model_badge = ctk.CTkLabel(
            self._sidebar,
            text=t("app.model_not_loaded"),
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            fg_color="#252535",
            corner_radius=6,
            anchor="w",
        )
        self._model_badge.grid(row=10, column=0, padx=12, pady=(8, 20), sticky="ew")

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content_area(self) -> None:
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="#1c1c2c")
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        gen_common = dict(
            master=self._content,
            engine=self._engine,
            player=self._player,
            config=self._config,
            status_cb=self._set_status,
            history=self._history,
            on_history_entry=self._on_new_history_entry,
            fg_color="#1c1c2c",
            corner_radius=0,
        )

        self._history_panel = HistoryPanel(
            master=self._content,
            history=self._history,
            player=self._player,
            status_cb=self._set_status,
            fg_color="#1c1c2c",
            corner_radius=0,
        )

        self._panels: dict[str, ctk.CTkFrame] = {
            PANEL_TTS:          TTSPanel(**gen_common),
            PANEL_VOICE_DESIGN: VoiceDesignPanel(**gen_common),
            PANEL_CLONING:      CloningPanel(**gen_common),
            PANEL_ULTIMATE:     UltimateClonePanel(**gen_common),
            PANEL_HISTORY:      self._history_panel,
            PANEL_SRT:          SRTPanel(
                master=self._content,
                engine=self._engine,
                config=self._config,
                status_cb=self._set_status,
                fg_color="#1c1c2c",
                corner_radius=0,
            ),
            PANEL_SETTINGS:     SettingsPanel(
                master=self._content,
                engine=self._engine,
                config=self._config,
                status_cb=self._set_status,
                on_model_state_change=self._on_model_state_change,
                fg_color="#1c1c2c",
                corner_radius=0,
            ),
        }

        # All panels occupy the same cell; only one is gridded at a time
        for panel in self._panels.values():
            panel.grid(row=0, column=0, sticky="nsew")
            panel.grid_remove()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_status_bar(self) -> None:
        bar = ctk.CTkFrame(
            self, height=26, corner_radius=0,
            fg_color="#14141e",
        )
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_propagate(False)

        self._status_lbl = ctk.CTkLabel(
            bar,
            text=t("app.welcome", app=APP_NAME),
            font=ctk.CTkFont(size=11),
            text_color="#667788",
            anchor="w",
        )
        self._status_lbl.grid(row=0, column=0, padx=12, pady=3, sticky="w")

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_panel(self, panel_id: str) -> None:
        for pid, panel in self._panels.items():
            if pid == panel_id:
                panel.grid()
            else:
                panel.grid_remove()

        # Refresh history panel whenever it becomes visible
        if panel_id == PANEL_HISTORY:
            self._history_panel.refresh()

        # Highlight active nav button
        for pid, btn in self._nav_btns.items():
            if pid == panel_id:
                btn.configure(fg_color="#2a3a5e", text_color="#4e9af1")
            else:
                btn.configure(fg_color="transparent", text_color="#cccccc")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        """Update the status bar (called from any thread via after())."""
        self.after(0, lambda: self._status_lbl.configure(text=msg))

    def _on_model_state_change(self, loaded: bool) -> None:
        """Called by SettingsPanel when model loads or unloads."""
        if loaded:
            sr = self._engine.sample_rate
            self._model_badge.configure(
                text=f"  ●  Loaded  {sr} Hz",
                text_color="#2ecc71",
                fg_color="#1a3a27",
            )
        else:
            self._model_badge.configure(
                text=t("app.model_not_loaded"),
                text_color="#888888",
                fg_color="#252535",
            )

    def _on_new_history_entry(self, entry: HistoryEntry) -> None:
        """Prepend new entry to the history panel (called on main thread)."""
        self._history_panel.prepend_entry(entry)

    def _on_close(self) -> None:
        """Graceful shutdown: stop playback, save config, destroy window."""
        self._player.stop()
        self._config.save()
        self.destroy()
