"""AudioControlBar — play / stop / save buttons + volume slider."""

from __future__ import annotations

import tkinter.filedialog as fd
import tkinter.messagebox as mb
from typing import Optional

import customtkinter as ctk

from app.core.audio_player import AudioPlayer
from app.utils.i18n import t


class AudioControlBar(ctk.CTkFrame):
    """
    A compact row of playback controls that operate on a shared
    :class:`~app.core.audio_player.AudioPlayer` instance.

    **Thread safety**: All UI updates happen on the main thread via polling
    (``after``). The player itself runs its worker on a daemon thread.

    Usage::

        bar = AudioControlBar(frame, player=audio_player)
        bar.set_has_audio(True)   # enables buttons after generation
    """

    _POLL_MS = 100  # polling interval while playing

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        player: AudioPlayer,
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._player = player
        self._poll_id: Optional[str] = None
        self._build_ui()
        self.set_has_audio(False)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_has_audio(self, state: bool) -> None:
        """Enable or disable all controls depending on audio availability."""
        s = "normal" if state else "disabled"
        self._play_btn.configure(state=s)
        self._stop_btn.configure(state=s)
        self._save_btn.configure(state=s)
        if state and self._player.has_audio:
            dur = self._player.duration
            self._time_lbl.configure(text=t("audio.duration_val", dur=dur))
        else:
            self._time_lbl.configure(text=t("audio.duration_empty"))

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Stretch column 5 to push volume slider to the right
        for c in range(5):
            self.grid_columnconfigure(c, weight=0)
        self.grid_columnconfigure(5, weight=1)

        # ── Buttons ──────────────────────────────────────────────────────────
        self._play_btn = ctk.CTkButton(
            self, text=t("audio.play"),
            width=96, height=34,
            font=ctk.CTkFont(size=13),
            command=self._on_play,
        )
        self._play_btn.grid(row=0, column=0, padx=(0, 6))

        self._stop_btn = ctk.CTkButton(
            self, text=t("audio.stop"),
            width=96, height=34,
            font=ctk.CTkFont(size=13),
            fg_color="#4a4a5a", hover_color="#5a5a6a",
            command=self._on_stop,
        )
        self._stop_btn.grid(row=0, column=1, padx=(0, 6))

        self._save_btn = ctk.CTkButton(
            self, text=t("audio.save"),
            width=104, height=34,
            font=ctk.CTkFont(size=13),
            fg_color="#2d6a4f", hover_color="#3a8a63",
            command=self._on_save,
        )
        self._save_btn.grid(row=0, column=2, padx=(0, 20))

        # ── Volume ───────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text=t("audio.vol"),
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=3, padx=(0, 4))

        self._vol = ctk.CTkSlider(self, from_=0.0, to=1.0, width=110)
        self._vol.set(0.9)
        self._vol.grid(row=0, column=4)

        # ── Duration label ───────────────────────────────────────────────────
        self._time_lbl = ctk.CTkLabel(
            self, text=t("audio.duration_empty"),
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        )
        self._time_lbl.grid(row=0, column=5, padx=(16, 0), sticky="e")

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_play(self) -> None:
        if not self._player.has_audio:
            return
        volume = float(self._vol.get())
        self._play_btn.configure(state="disabled")
        self._player.play(
            volume=volume,
            on_finished=self._playback_finished_safe,
        )
        self._start_poll()

    def _on_stop(self) -> None:
        self._player.stop()
        self._stop_poll()
        self._play_btn.configure(state="normal")

    def _on_save(self) -> None:
        if not self._player.has_audio:
            return
        path = fd.asksaveasfilename(
            title=t("audio.save_title"),
            defaultextension=".wav",
            filetypes=[("WAV audio", "*.wav"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self._player.save_to_file(path)
        except Exception as exc:  # noqa: BLE001
            mb.showerror(t("audio.save_error"), str(exc))

    # ── Polling ───────────────────────────────────────────────────────────────

    def _start_poll(self) -> None:
        if self._poll_id is None:
            self._poll()

    def _poll(self) -> None:
        if self._player.is_playing:
            self._poll_id = self.after(self._POLL_MS, self._poll)
        else:
            self._poll_id = None
            self._play_btn.configure(state="normal")

    def _stop_poll(self) -> None:
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None

    def _playback_finished_safe(self) -> None:
        """Called from worker thread — marshal back to main thread."""
        self.after(0, lambda: self._play_btn.configure(state="normal"))
        self.after(0, self._stop_poll)
