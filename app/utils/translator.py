"""Light translation helper using deep-translator (Google backend, no API key)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── Preset → (hint_text, target_lang_code) ───────────────────────────────────
# hint_text  : text prepended as (hint) before synthesis
# target_lang: ISO 639-1 code for translation; None = no translation (same language)

PRESET_MAP: dict[str, tuple[str, str | None]] = {
    # ── 中文（不翻譯，只改口音/性別）────────────────────────────────────────
    "女聲普通話":          ("女聲普通話",         None),
    "男聲普通話":          ("男聲普通話",         None),
    "女聲台灣腔普通話":    ("女聲台灣腔普通話",   None),
    "男聲台灣腔普通話":    ("男聲台灣腔普通話",   None),
    "女聲粵語":            ("女聲粵語",           None),
    "男聲粵語":            ("男聲粵語",           None),
    "女聲四川話":          ("女聲四川話",         None),
    "男聲四川話":          ("男聲四川話",         None),
    "女聲閩南話":          ("女聲閩南話",         None),
    "男聲閩南話":          ("男聲閩南話",         None),
    "女聲吳語":            ("女聲吳語",           None),
    "男聲吳語":            ("男聲吳語",           None),
    "男聲東北話":          ("男聲東北話",         None),
    "女聲東北話":          ("女聲東北話",         None),
    "男聲河南話":          ("男聲河南話",         None),
    "男聲陝西話":          ("男聲陝西話",         None),
    "男聲山東話":          ("男聲山東話",         None),
    "男聲天津話":          ("男聲天津話",         None),
    # ── 外語（需翻譯，使用中文標籤）──────────────────────────────────────────
    "女聲英語":            ("female English",         "en"),
    "男聲英語":            ("male English",           "en"),
    "女聲英式英語":        ("female British English", "en"),
    "男聲英式英語":        ("male British English",   "en"),
    "女聲美式英語":        ("female American English","en"),
    "男聲美式英語":        ("male American English",  "en"),
    "女聲日語":            ("female Japanese",        "ja"),
    "男聲日語":            ("male Japanese",          "ja"),
    "女聲韓語":            ("female Korean",          "ko"),
    "男聲韓語":            ("male Korean",            "ko"),
    "女聲法語":            ("female French",          "fr"),
    "男聲法語":            ("male French",            "fr"),
    "女聲德語":            ("female German",          "de"),
    "男聲德語":            ("male German",            "de"),
    "女聲西班牙語":        ("female Spanish",         "es"),
    "男聲西班牙語":        ("male Spanish",           "es"),
}

# Friendly display names for target languages
LANG_DISPLAY: dict[str, str] = {
    "en":    "英語",
    "ja":    "日語",
    "ko":    "韓語",
    "fr":    "法語",
    "de":    "德語",
    "es":    "西班牙語",
    "zh-CN": "中文（簡體）",
}


def needs_translation(preset: str) -> bool:
    """Return True if the preset requires translating the input text."""
    info = PRESET_MAP.get(preset)
    return info is not None and info[1] is not None


def target_lang_display(preset: str) -> str:
    """Return a human-readable name for the translation target language."""
    info = PRESET_MAP.get(preset)
    if info is None or info[1] is None:
        return ""
    return LANG_DISPLAY.get(info[1], info[1])


def check_network(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """Return True if the network is reachable (DNS port on Google)."""
    import socket
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return True
    except OSError:
        return False


def translate(text: str, target_lang: str) -> str:
    """
    Translate *text* to *target_lang* using Google Translate (via deep-translator).

    Args:
        text:        Source text (any language).
        target_lang: ISO 639-1 / BCP-47 code, e.g. ``"ja"``, ``"en"``, ``"ko"``.

    Returns:
        Translated string.

    Raises:
        ConnectionError: No network connection available.
    """
    if not check_network():
        raise ConnectionError("需要網路連線才能翻譯")
    try:
        from deep_translator import GoogleTranslator  # type: ignore[import]

        result: str = GoogleTranslator(source="auto", target=target_lang).translate(text)
        logger.info("Translated to %s: %r → %r", target_lang, text[:60], result[:60])
        return result
    except ConnectionError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Translation failed (%s)", exc)
        raise ConnectionError("需要網路連線才能翻譯") from exc


def apply_preset(text: str, preset: str, *, translate_enabled: bool = True) -> str:
    """
    Apply *preset* to *text*: translate if needed, then prepend the hint.

    Args:
        text:               Raw user text.
        preset:             Selected preset string (key in PRESET_MAP).
        translate_enabled:  If False, skip translation even for foreign presets.

    Returns:
        Final text ready for synthesis, e.g. ``"(female Japanese)こんにちは"``.
    """
    if not preset:
        return text

    info = PRESET_MAP.get(preset)
    if info is None:
        # Unknown preset — treat as raw hint
        return f"({preset}){text}"

    hint, target_lang = info

    if target_lang and translate_enabled:
        text = translate(text, target_lang)

    return f"({hint}){text}"
