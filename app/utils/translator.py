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
    # ── 外語（需翻譯）────────────────────────────────────────────────────────
    "female Mandarin":          ("female Mandarin",        "zh-CN"),
    "male Mandarin":            ("male Mandarin",          "zh-CN"),
    "female Cantonese":         ("female Cantonese",       "zh-CN"),
    "male Cantonese":           ("male Cantonese",         "zh-CN"),
    "female English":           ("female English",         "en"),
    "male English":             ("male English",           "en"),
    "female British English":   ("female British English", "en"),
    "male British English":     ("male British English",   "en"),
    "female American English":  ("female American English","en"),
    "male American English":    ("male American English",  "en"),
    "female Japanese":          ("female Japanese",        "ja"),
    "male Japanese":            ("male Japanese",          "ja"),
    "female Korean":            ("female Korean",          "ko"),
    "male Korean":              ("male Korean",            "ko"),
}

# Friendly display names for target languages
LANG_DISPLAY: dict[str, str] = {
    "en":    "English",
    "ja":    "日語",
    "ko":    "韓語",
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


def translate(text: str, target_lang: str) -> str:
    """
    Translate *text* to *target_lang* using Google Translate (via deep-translator).

    Args:
        text:        Source text (any language).
        target_lang: ISO 639-1 / BCP-47 code, e.g. ``"ja"``, ``"en"``, ``"ko"``.

    Returns:
        Translated string, or the original text if translation fails.
    """
    try:
        from deep_translator import GoogleTranslator  # type: ignore[import]

        result: str = GoogleTranslator(source="auto", target=target_lang).translate(text)
        logger.info("Translated to %s: %r → %r", target_lang, text[:60], result[:60])
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Translation failed (%s), using original text: %s", exc, text[:60])
        return text


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
