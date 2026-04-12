"""SRT subtitle file parser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SRTEntry:
    """One subtitle block parsed from an SRT file."""

    index: int
    start_time: str   # "HH:MM:SS,mmm"
    end_time: str     # "HH:MM:SS,mmm"
    start_ms: int     # start offset in milliseconds
    end_ms: int       # end offset in milliseconds
    text: str         # plain text (newlines joined to space)


_SRT_BLOCK = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n"
    r"((?:.+\n?)+?)(?:\n\n|\Z)",
    re.MULTILINE,
)


def time_to_ms(time_str: str) -> int:
    """Convert ``HH:MM:SS,mmm`` (or ``.mmm``) to milliseconds."""
    time_str = time_str.replace(".", ",")
    hms, ms = time_str.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)


def ms_to_filename_part(ms: int) -> str:
    """Convert milliseconds to a filename-safe time string ``00m01s500ms``."""
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1_000
    ms %= 1_000
    if h:
        return f"{h:02d}h{m:02d}m{s:02d}s{ms:03d}ms"
    return f"{m:02d}m{s:02d}s{ms:03d}ms"


def parse_srt(content: str) -> list[SRTEntry]:
    """
    Parse SRT file content into a list of :class:`SRTEntry` objects.

    Handles Windows (CRLF) and Unix (LF) line endings, UTF-8 BOM, and
    both ``,`` and ``.`` as the millisecond separator.

    Raises:
        ValueError: If no valid SRT blocks are found.
    """
    # Normalise line endings and strip BOM
    content = content.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    # Ensure file ends with double newline so the last block is matched
    if not content.endswith("\n\n"):
        content += "\n\n"

    entries: list[SRTEntry] = []
    for m in _SRT_BLOCK.finditer(content):
        idx = int(m.group(1))
        start_str = m.group(2).replace(".", ",")
        end_str = m.group(3).replace(".", ",")
        raw_text = m.group(4).strip()
        # Strip HTML tags sometimes present in SRT (e.g. <i>, <b>)
        clean_text = re.sub(r"<[^>]+>", "", raw_text)
        # Join multi-line text into a single line
        clean_text = " ".join(clean_text.splitlines()).strip()
        if not clean_text:
            continue
        entries.append(
            SRTEntry(
                index=idx,
                start_time=start_str,
                end_time=end_str,
                start_ms=time_to_ms(start_str),
                end_ms=time_to_ms(end_str),
                text=clean_text,
            )
        )

    if not entries:
        raise ValueError("No valid SRT entries found in the file.")

    return sorted(entries, key=lambda e: e.start_ms)


def load_srt(path: str | Path) -> list[SRTEntry]:
    """Read and parse an SRT file from *path*."""
    content = Path(path).read_text(encoding="utf-8-sig")
    return parse_srt(content)
