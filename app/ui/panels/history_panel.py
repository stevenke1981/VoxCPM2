"""History panel — scrollable list of past generation entries."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.utils.history_manager import HistoryEntry, HistoryManager
from app.utils.i18n import t

logger = logging.getLogger(__name__)

# ── Mode badge colours ─────────────────────────────────────────────────────────
_MODE_COLOURS: dict[str, tuple[str, str]] = {
    # (fg_color, text_color)
    "tts":          ("#1a5276", "#5dade2"),
    "voice_design": ("#4a235a", "#bb8fce"),
    "clone":        ("#1e4d2b", "#58d68d"),
    "ultimate":     ("#7d6608", "#f4d03f"),
}
_MODE_DEFAULT = ("#333344", "#aaaaaa")


def _mode_label(mode: str) -> str:
    key = f"history.mode.{mode}"
    return t(key)


def _mode_colours(mode: str) -> tuple[str, str]:
    return _MODE_COLOURS.get(mode, _MODE_DEFAULT)


class HistoryPanel(ctk.CTkFrame):
    """
    Displays past generation entries from :class:`~app.utils.history_manager.HistoryManager`.

    Call :meth:`refresh` to rebuild the list (e.g. after a new entry is added
    or when the panel becomes visible).
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        history: HistoryManager,
        player: AudioPlayer,
        status_cb: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        super().__init__(master, **kwargs)
        self._history = history
        self._player = player
        self._status_cb = status_cb
        self._playing_id: Optional[str] = None  # id of entry currently playing
        self._play_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_list_area()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=t("history.title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._count_lbl = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#667788",
        )
        self._count_lbl.grid(row=0, column=1, padx=(8, 0))

        ctk.CTkButton(
            header,
            text=t("history.clear_all"),
            width=90, height=28,
            font=ctk.CTkFont(size=12),
            fg_color="#6e2c00", hover_color="#922b21",
            command=self._on_clear_all,
        ).grid(row=0, column=2, padx=(8, 0))

    def _build_list_area(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#16162a",
            corner_radius=8,
        )
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Rebuild the entire entry list from history manager."""
        # Destroy old widgets
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._play_buttons.clear()
        self._playing_id = None

        entries = self._history.entries
        n = len(entries)
        self._count_lbl.configure(text=t("history.count", n=n) if n else "")

        if not entries:
            self._build_empty_state()
            return

        for row, entry in enumerate(entries):
            self._build_card(self._scroll, entry, row)

    def prepend_entry(self, entry: HistoryEntry) -> None:
        """
        Prepend a single new card without rebuilding the entire list.
        Faster than :meth:`refresh` for real-time updates.
        """
        # Shift existing cards down
        for widget in self._scroll.winfo_children():
            info = widget.grid_info()
            if info:
                widget.grid(row=int(info["row"]) + 1, column=0, **{
                    k: v for k, v in info.items() if k not in ("row", "column", "in")
                })

        self._build_card(self._scroll, entry, 0)

        n = self._history.count
        self._count_lbl.configure(text=t("history.count", n=n))

    # ── Card builder ──────────────────────────────────────────────────────────

    def _build_empty_state(self) -> None:
        ctk.CTkLabel(
            self._scroll,
            text=t("history.empty"),
            font=ctk.CTkFont(size=14),
            text_color="#556677",
        ).grid(row=0, column=0, pady=(40, 4))

        ctk.CTkLabel(
            self._scroll,
            text=t("history.empty_hint"),
            font=ctk.CTkFont(size=11),
            text_color="#445566",
        ).grid(row=1, column=0, pady=(0, 40))

    def _build_card(
        self, parent: ctk.CTkScrollableFrame, entry: HistoryEntry, row: int
    ) -> None:
        card = ctk.CTkFrame(parent, fg_color="#1e1e32", corner_radius=8)
        card.grid(row=row, column=0, padx=4, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # ── Mode badge ────────────────────────────────────────────────────────
        fg, tc = _mode_colours(entry.mode)
        ctk.CTkLabel(
            card,
            text=f" {_mode_label(entry.mode)} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=fg,
            text_color=tc,
            corner_radius=4,
            width=58,
        ).grid(row=0, column=0, padx=(10, 8), pady=(10, 2), sticky="nw")

        # ── Info column ───────────────────────────────────────────────────────
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, padx=(0, 8), pady=(8, 8), sticky="ew")
        info.grid_columnconfigure(0, weight=1)

        # Timestamp + duration row
        meta_row = ctk.CTkFrame(info, fg_color="transparent")
        meta_row.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            meta_row,
            text=entry.timestamp,
            font=ctk.CTkFont(size=11),
            text_color="#778899",
        ).grid(row=0, column=0, sticky="w")

        dur_text = f"  {entry.duration:.2f}s  {entry.sample_rate // 1000}kHz"
        ctk.CTkLabel(
            meta_row,
            text=dur_text,
            font=ctk.CTkFont(size=11),
            text_color="#556677",
        ).grid(row=0, column=1, padx=(8, 0), sticky="w")

        # Text preview
        preview = entry.text.replace("\n", " ")
        if len(preview) > 72:
            preview = preview[:69] + "…"
        ctk.CTkLabel(
            info,
            text=preview,
            font=ctk.CTkFont(size=12),
            text_color="#cccccc",
            anchor="w",
            wraplength=520,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Filename (small)
        ctk.CTkLabel(
            info,
            text=Path(entry.filename).name,
            font=ctk.CTkFont(size=10),
            text_color="#445566",
            anchor="w",
        ).grid(row=2, column=0, sticky="w")

        # ── Action buttons ────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=(0, 10), pady=8, sticky="ns")

        play_btn = ctk.CTkButton(
            btn_frame,
            text=t("history.play"),
            width=36, height=30,
            font=ctk.CTkFont(size=14),
            fg_color="#1a3a5c", hover_color="#2a5a8c",
            command=lambda e=entry: self._on_play(e),
        )
        play_btn.grid(row=0, column=0, pady=(0, 4))
        self._play_buttons[entry.id] = play_btn

        ctk.CTkButton(
            btn_frame,
            text=t("history.delete"),
            width=36, height=30,
            font=ctk.CTkFont(size=14),
            fg_color="#3a1010", hover_color="#6e2c00",
            command=lambda e=entry: self._on_delete(e),
        ).grid(row=1, column=0)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_play(self, entry: HistoryEntry) -> None:
        # If this entry is already playing, stop it
        if self._playing_id == entry.id and self._player.is_playing:
            self._player.stop()
            self._set_play_icon(entry.id, playing=False)
            self._playing_id = None
            return

        # Stop previous playback
        if self._playing_id:
            self._set_play_icon(self._playing_id, playing=False)
        self._player.stop()
        self._playing_id = entry.id

        try:
            self._player.load_file(entry.filename)
        except Exception as exc:  # noqa: BLE001
            logger.error("History load error: %s", exc)
            self._status_cb(t("history.load_error", msg=str(exc)))
            self._playing_id = None
            return

        self._set_play_icon(entry.id, playing=True)
        self._player.play(
            on_finished=lambda: self.after(0, lambda: self._on_play_finished(entry.id))
        )

    def _on_play_finished(self, entry_id: str) -> None:
        if self._playing_id == entry_id:
            self._set_play_icon(entry_id, playing=False)
            self._playing_id = None

    def _set_play_icon(self, entry_id: str, *, playing: bool) -> None:
        btn = self._play_buttons.get(entry_id)
        if btn and btn.winfo_exists():
            btn.configure(
                text=t("history.stop") if playing else t("history.play"),
                fg_color="#1a3a5c" if not playing else "#3a1a1a",
            )

    def _on_delete(self, entry: HistoryEntry) -> None:
        # Stop playback if this entry is playing
        if self._playing_id == entry.id:
            self._player.stop()
            self._playing_id = None
        self._history.delete(entry.id)
        self.refresh()

    def _on_clear_all(self) -> None:
        self._player.stop()
        self._playing_id = None
        self._history.clear_all()
        self.refresh()
