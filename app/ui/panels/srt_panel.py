"""SRT Batch Synthesis panel."""

from __future__ import annotations

import logging
import os
import threading
import tkinter.filedialog as fd
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import customtkinter as ctk
import numpy as np
import soundfile as sf

from app.core.tts_engine import TTSEngine
from app.utils.config_manager import ConfigManager
from app.utils.constants import WAV_DIR
from app.utils.i18n import t
from app.utils.srt_parser import SRTEntry, load_srt, ms_to_filename_part
from app.utils.translator import (
    PRESET_MAP,
    apply_preset,
    needs_translation,
    target_lang_display,
)

logger = logging.getLogger(__name__)

_LANG_PRESETS = list(PRESET_MAP.keys())

# Colour map for status badges
_STATUS_COLOURS = {
    "pending":     "#555577",
    "generating":  "#4e9af1",
    "done":        "#2ecc71",
    "error":       "#e05252",
    "skipped":     "#666666",
}


class _EntryRow:
    """Holds widgets for one SRT entry row in the scrollable list."""

    __slots__ = ("entry", "var", "row_frame", "status_lbl")

    def __init__(
        self,
        entry: SRTEntry,
        var: ctk.BooleanVar,
        row_frame: ctk.CTkFrame,
        status_lbl: ctk.CTkLabel,
    ) -> None:
        self.entry = entry
        self.var = var
        self.row_frame = row_frame
        self.status_lbl = status_lbl


class SRTPanel(ctk.CTkFrame):
    """
    Mode 5 — SRT Batch Synthesis.

    Import a SubRip (.srt) subtitle file, select entries, then
    synthesise each one.  Output filenames embed the subtitle
    start-timestamp so the clips can be placed on a timeline or
    merged automatically.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        engine: TTSEngine,
        config: ConfigManager,
        status_cb,
        **kwargs: object,
    ) -> None:
        super().__init__(master, **kwargs)
        self._engine = engine
        self._config = config
        self._status_cb = status_cb

        self._entries: List[SRTEntry] = []
        self._rows: List[_EntryRow] = []
        self._output_dir: Optional[Path] = None
        self._stop_flag = threading.Event()
        self._is_running = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # entry list expands

        self._build_title()
        self._build_top_controls()
        self._build_entry_list()
        self._build_bottom_controls()

    # ── Layout builders ───────────────────────────────────────────────────────

    def _build_title(self) -> None:
        ctk.CTkLabel(
            self,
            text=t("srt.title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="w")

    def _build_top_controls(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        # ── SRT file row ──────────────────────────────────────────────────────
        ctk.CTkLabel(
            top, text=t("srt.file_label"),
            font=ctk.CTkFont(size=13), anchor="w",
        ).grid(row=0, column=0, padx=(0, 8), pady=(0, 4), sticky="w")

        file_row = ctk.CTkFrame(top, fg_color="transparent")
        file_row.grid(row=0, column=1, columnspan=2, pady=(0, 4), sticky="ew")
        file_row.grid_columnconfigure(0, weight=1)

        self._file_entry = ctk.CTkEntry(
            file_row, height=34, font=ctk.CTkFont(size=12),
            placeholder_text="*.srt",
        )
        self._file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            file_row, text=t("srt.browse"), width=84, height=34,
            command=self._browse_srt,
        ).grid(row=0, column=1)

        # ── Accent / gender preset ────────────────────────────────────────────
        ctk.CTkLabel(
            top, text=t("srt.lang_hint_label"),
            font=ctk.CTkFont(size=13), anchor="w",
        ).grid(row=1, column=0, padx=(0, 8), pady=(4, 4), sticky="w")

        hint_row = ctk.CTkFrame(top, fg_color="transparent")
        hint_row.grid(row=1, column=1, columnspan=2, pady=(4, 4), sticky="ew")
        hint_row.grid_columnconfigure(0, weight=0)

        self._preset_var = ctk.StringVar(value="女聲普通話")
        self._preset_box = ctk.CTkComboBox(
            hint_row,
            variable=self._preset_var,
            values=[""] + _LANG_PRESETS,
            width=220,
            command=self._on_preset_select,
        )
        self._preset_box.grid(row=0, column=0, padx=(0, 10))

        # Auto-translate toggle (shown for foreign-language presets only)
        self._translate_var = ctk.BooleanVar(value=True)
        self._translate_chk = ctk.CTkCheckBox(
            hint_row, variable=self._translate_var, text="",
            width=20, checkbox_width=18, checkbox_height=18,
        )
        self._translate_chk.grid(row=0, column=1, padx=(0, 4))

        self._translate_lbl = ctk.CTkLabel(
            hint_row, text="",
            font=ctk.CTkFont(size=12), text_color="#4e9af1", anchor="w",
        )
        self._translate_lbl.grid(row=0, column=2, sticky="w")

        self._on_preset_select("女聲普通話")

        # ── Parse button ──────────────────────────────────────────────────────
        self._parse_btn = ctk.CTkButton(
            top,
            text=t("srt.parse_btn"),
            height=36,
            command=self._parse_srt,
        )
        self._parse_btn.grid(row=2, column=0, columnspan=3, pady=(8, 0), sticky="w")

    def _build_entry_list(self) -> None:
        # Toolbar: Select All / Deselect All + entry count
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=2, column=0, padx=24, pady=(4, 4), sticky="ew")
        toolbar.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            toolbar, text=t("srt.select_all"), width=90, height=30,
            command=self._select_all,
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            toolbar, text=t("srt.deselect_all"), width=110, height=30,
            command=self._deselect_all,
        ).grid(row=0, column=1, padx=(0, 12))

        self._count_lbl = ctk.CTkLabel(
            toolbar, text="",
            font=ctk.CTkFont(size=12), text_color="#888888", anchor="w",
        )
        self._count_lbl.grid(row=0, column=2, sticky="w")

        # Scrollable frame for entry rows
        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#16162a",
            corner_radius=6,
            label_text="",
        )
        self._scroll_frame.grid(row=3, column=0, padx=24, pady=(0, 8), sticky="nsew")
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        # Placeholder label
        self._placeholder_lbl = ctk.CTkLabel(
            self._scroll_frame,
            text=t("srt.empty_hint"),
            font=ctk.CTkFont(size=12),
            text_color="#555566",
        )
        self._placeholder_lbl.grid(row=0, column=0, pady=30)

    def _build_bottom_controls(self) -> None:
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=4, column=0, padx=24, pady=(0, 16), sticky="ew")
        bot.grid_columnconfigure(3, weight=1)

        # Output directory label
        self._outdir_lbl = ctk.CTkLabel(
            bot, text="",
            font=ctk.CTkFont(size=11), text_color="#556677", anchor="w",
        )
        self._outdir_lbl.grid(row=0, column=0, columnspan=5, pady=(0, 6), sticky="w")

        # Progress label
        self._progress_lbl = ctk.CTkLabel(
            bot, text="",
            font=ctk.CTkFont(size=12), text_color="#888888", anchor="w",
        )
        self._progress_lbl.grid(row=1, column=0, columnspan=5, pady=(0, 6), sticky="w")

        # Progress bar
        self._progress = ctk.CTkProgressBar(bot)
        self._progress.grid(row=2, column=0, columnspan=5, pady=(0, 10), sticky="ew")
        self._progress.set(0)

        # Action buttons
        self._start_btn = ctk.CTkButton(
            bot, text=t("srt.start"), height=40, width=140,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_synthesis,
        )
        self._start_btn.grid(row=3, column=0, padx=(0, 8))

        self._stop_btn = ctk.CTkButton(
            bot, text=t("srt.stop"), height=40, width=100,
            fg_color="#553333", hover_color="#662222",
            command=self._stop_synthesis,
            state="disabled",
        )
        self._stop_btn.grid(row=3, column=1, padx=(0, 8))

        self._merge_btn = ctk.CTkButton(
            bot, text=t("srt.merge"), height=40, width=180,
            fg_color="#2a3a5e", hover_color="#1f2d4a",
            command=self._merge_audio,
        )
        self._merge_btn.grid(row=3, column=2)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse_srt(self) -> None:
        path = fd.askopenfilename(
            title="Open SRT File",
            filetypes=[
                ("SubRip subtitles", "*.srt"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._file_entry.delete(0, "end")
            self._file_entry.insert(0, path)

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

    def _parse_srt(self) -> None:
        path = self._file_entry.get().strip()
        if not path:
            self._status_cb(t("srt.error_no_file"))
            return

        try:
            self._entries = load_srt(path)
        except Exception as exc:
            self._status_cb(t("srt.error_parse", msg=str(exc)))
            return

        # Build timestamped output directory name
        stem = Path(path).stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_dir = Path(WAV_DIR) / f"srt_{stem}_{ts}"
        self._outdir_lbl.configure(
            text=f"{t('srt.output_dir')} {self._output_dir}"
        )

        self._rebuild_rows()
        self._status_cb(t("srt.parsed_ok", n=len(self._entries)))

    def _rebuild_rows(self) -> None:
        """Clear and repopulate the scrollable entry list."""
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._rows.clear()

        if not self._entries:
            ctk.CTkLabel(
                self._scroll_frame,
                text=t("srt.empty_hint"),
                font=ctk.CTkFont(size=12),
                text_color="#555566",
            ).grid(row=0, column=0, pady=30)
            self._count_lbl.configure(text="")
            return

        for i, entry in enumerate(self._entries):
            var = ctk.BooleanVar(value=True)
            row_frame = ctk.CTkFrame(
                self._scroll_frame,
                fg_color="#1e1e34" if i % 2 == 0 else "#1a1a2e",
                corner_radius=4,
            )
            row_frame.grid(row=i, column=0, pady=2, sticky="ew")
            row_frame.grid_columnconfigure(3, weight=1)

            # Checkbox
            ctk.CTkCheckBox(
                row_frame, variable=var, text="", width=24,
                checkbox_width=18, checkbox_height=18,
                command=self._update_count_label,
            ).grid(row=0, column=0, padx=(8, 4), pady=6)

            # Index
            ctk.CTkLabel(
                row_frame,
                text=f"{entry.index:04d}",
                font=ctk.CTkFont(size=11, family="Courier"),
                text_color="#667788",
                width=36, anchor="e",
            ).grid(row=0, column=1, padx=(0, 10))

            # Timestamp
            ts_text = f"{entry.start_time} → {entry.end_time}"
            ctk.CTkLabel(
                row_frame,
                text=ts_text,
                font=ctk.CTkFont(size=11, family="Courier"),
                text_color="#4e9af1",
                width=260, anchor="w",
            ).grid(row=0, column=2, padx=(0, 10))

            # Text preview
            preview = entry.text[:80] + ("…" if len(entry.text) > 80 else "")
            ctk.CTkLabel(
                row_frame,
                text=preview,
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).grid(row=0, column=3, padx=(0, 10), sticky="w")

            # Status badge
            status_lbl = ctk.CTkLabel(
                row_frame,
                text=t("srt.status_pending"),
                font=ctk.CTkFont(size=11),
                text_color=_STATUS_COLOURS["pending"],
                width=80, anchor="e",
            )
            status_lbl.grid(row=0, column=4, padx=(0, 10))

            self._rows.append(_EntryRow(entry, var, row_frame, status_lbl))

        self._update_count_label()

    def _update_count_label(self) -> None:
        selected = sum(1 for r in self._rows if r.var.get())
        total = len(self._rows)
        self._count_lbl.configure(text=f"{selected} / {total}")

    def _select_all(self) -> None:
        for r in self._rows:
            r.var.set(True)
        self._update_count_label()

    def _deselect_all(self) -> None:
        for r in self._rows:
            r.var.set(False)
        self._update_count_label()

    # ── Synthesis ─────────────────────────────────────────────────────────────

    def _start_synthesis(self) -> None:
        if self._is_running:
            return
        if not self._engine.is_loaded:
            self._status_cb(t("srt.error_no_model"))
            return
        if not self._entries:
            self._status_cb(t("srt.error_no_file"))
            return

        selected = [r for r in self._rows if r.var.get()]
        if not selected:
            self._status_cb(t("srt.error_no_entries"))
            return

        # Ensure output directory exists
        if self._output_dir is None:
            self._status_cb(t("srt.error_no_file"))
            return
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._stop_flag.clear()
        self._is_running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._progress.set(0)

        threading.Thread(
            target=self._synthesis_worker,
            args=(selected,),
            daemon=True,
            name="SRTSynthesisWorker",
        ).start()

    def _synthesis_worker(self, rows: List[_EntryRow]) -> None:
        total = len(rows)
        preset = self._preset_var.get().strip()
        translate_on = self._translate_var.get()

        cfg_value = float(self._config.get("cfg_value", 2.0))
        steps = int(self._config.get("inference_timesteps", 10))

        for i, row in enumerate(rows):
            if self._stop_flag.is_set():
                self.after(0, lambda r=row: r.status_lbl.configure(
                    text=t("srt.status_skipped"),
                    text_color=_STATUS_COLOURS["skipped"],
                ))
                continue

            # Mark as generating
            self.after(0, lambda r=row: r.status_lbl.configure(
                text=t("srt.status_generating"),
                text_color=_STATUS_COLOURS["generating"],
            ))
            self.after(0, lambda v=(i / total): self._progress.set(v))

            try:
                text = apply_preset(
                    row.entry.text, preset, translate_enabled=translate_on
                )

                wav = self._engine.generate(
                    text=text,
                    cfg_value=cfg_value,
                    inference_timesteps=steps,
                )
                sr = self._engine.sample_rate

                # Build filename: {index:04d}_{start_formatted}.wav
                fname = f"{row.entry.index:04d}_{ms_to_filename_part(row.entry.start_ms)}.wav"
                out_path = self._output_dir / fname  # type: ignore[operator]
                sf.write(str(out_path), wav, sr)

                self.after(0, lambda r=row: r.status_lbl.configure(
                    text=t("srt.status_done"),
                    text_color=_STATUS_COLOURS["done"],
                ))
            except Exception as exc:  # noqa: BLE001
                logger.error("SRT entry %d synthesis failed: %s", row.entry.index, exc)
                self.after(0, lambda r=row: r.status_lbl.configure(
                    text=t("srt.status_error"),
                    text_color=_STATUS_COLOURS["error"],
                ))

            done = i + 1
            self.after(0, lambda d=done, tot=total: (
                self._progress.set(d / tot),
                self._progress_lbl.configure(
                    text=t("srt.progress", done=d, total=tot)
                ),
            ))

        self.after(0, self._on_synthesis_done)

    def _on_synthesis_done(self) -> None:
        self._is_running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        done = sum(
            1 for r in self._rows
            if r.var.get() and
            r.status_lbl.cget("text") == t("srt.status_done")
        )
        msg = t("srt.synthesis_done", n=done)
        self._status_cb(msg)
        self._progress_lbl.configure(text=msg)

    def _stop_synthesis(self) -> None:
        self._stop_flag.set()
        self._stop_btn.configure(state="disabled")

    # ── Merge ─────────────────────────────────────────────────────────────────

    def _merge_audio(self) -> None:
        """Place each synthesised WAV at its subtitle start offset in a timeline."""
        if self._output_dir is None or not self._output_dir.exists():
            self._status_cb(t("srt.error_no_file"))
            return

        # Collect only rows marked as done
        done_rows = [
            r for r in self._rows
            if r.status_lbl.cget("text") == t("srt.status_done")
        ]
        if not done_rows:
            self._status_cb(t("srt.error_no_entries"))
            return

        threading.Thread(
            target=self._merge_worker,
            args=(done_rows,),
            daemon=True,
            name="SRTMergeWorker",
        ).start()

    def _merge_worker(self, rows: List[_EntryRow]) -> None:
        try:
            sr = self._engine.sample_rate

            # Determine total length from the last entry's end_ms
            max_end_ms = max(r.entry.end_ms for r in rows)
            # Add 1-second tail
            total_samples = int((max_end_ms + 1000) * sr / 1000)
            merged = np.zeros(total_samples, dtype=np.float32)

            for row in rows:
                fname = f"{row.entry.index:04d}_{ms_to_filename_part(row.entry.start_ms)}.wav"
                wav_path = self._output_dir / fname  # type: ignore[operator]
                if not wav_path.exists():
                    continue
                clip, file_sr = sf.read(str(wav_path), dtype="float32")
                if clip.ndim > 1:
                    clip = clip.mean(axis=1)
                offset = int(row.entry.start_ms * sr / 1000)
                end = offset + len(clip)
                if end > total_samples:
                    clip = clip[: total_samples - offset]
                    end = total_samples
                merged[offset:end] += clip

            # Normalise to prevent clipping
            peak = np.abs(merged).max()
            if peak > 1.0:
                merged /= peak

            out_path = self._output_dir / "_merged.wav"  # type: ignore[operator]
            sf.write(str(out_path), merged, sr)
            msg = t("srt.merged_saved", path=str(out_path))
            self.after(0, lambda: self._status_cb(msg))
            self.after(0, lambda: self._progress_lbl.configure(text=msg))
        except Exception as exc:  # noqa: BLE001
            logger.error("SRT merge failed: %s", exc)
            self.after(0, lambda: self._status_cb(f"Merge error: {exc}"))
