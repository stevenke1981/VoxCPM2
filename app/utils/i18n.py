"""Minimal i18n module for VoxCPM2 Studio.

Usage::

    from app.utils.i18n import t, init

    init("zh-TW")        # called once at startup
    print(t("nav.tts"))  # "文字轉語音"
"""

from __future__ import annotations

from typing import Dict

# ── Translation tables ────────────────────────────────────────────────────────

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh-TW": {
        # Navigation
        "nav.tts":          "文字轉語音",
        "nav.voice_design": "聲音設計",
        "nav.cloning":      "聲音複製",
        "nav.ultimate":     "極致複製",
        "nav.settings":     "設定",

        # Main window
        "app.subtitle":           "Studio",
        "app.model_not_loaded":   "  ○  未載入",
        "app.welcome":            "歡迎使用 {app} — 請在設定中載入模型以開始使用。",

        # Settings panel
        "settings.title":                  "⚙️  設定與模型",
        "settings.model_section":          "模型",
        "settings.model_placeholder":      "HuggingFace 模型 ID 或本地路徑",
        "settings.load_model":             "載入模型",
        "settings.loading":                "載入中 …",
        "settings.unload":                 "卸載",
        "settings.denoiser":               "載入降噪頭（提升品質，增加顯存）",
        "settings.model_not_loaded_badge": "  ○  模型未載入  ",
        "settings.model_loaded_badge":     "  ●  模型已載入  |  SR = {sr} Hz  ",
        "settings.starting_load":          "開始下載 / 載入 …",
        "settings.model_load_success":     "✓ 模型載入成功",
        "settings.model_unloaded":         "模型已卸載。",
        "settings.model_unloaded_status":  "模型已卸載",
        "settings.model_load_error":       "載入錯誤：{msg}",
        "settings.synthesis_params":       "合成參數",
        "settings.cfg_label":              "CFG 值",
        "settings.cfg_tooltip":            "無分類器引導強度。值越高越接近描述。",
        "settings.steps_label":            "推理步數",
        "settings.steps_tooltip":          "擴散步數。步數越多品質越好但速度越慢。",
        "settings.output_dir":             "預設輸出目錄",
        "settings.model_cache_dir":        "模型快取目錄",
        "settings.model_cache_placeholder":"./models（相對於專案根目錄）",
        "settings.browse":                 "瀏覽",
        "settings.save":                   "💾  儲存所有設定",
        "settings.saved":                  "設定已儲存。",
        "settings.language":               "介面語言",
        "settings.restart_required":       "語言已變更，請重新啟動應用程式。",

        # Base / generator panel
        "panel.generate":           "🎙️  生成",
        "panel.model_not_loaded":   "⚠️  模型未載入 — 請前往設定並點擊「載入模型」。",
        "panel.generating":         "⏳  正在生成音訊 …",
        "panel.done_status":        "✓  {dur:.2f} 秒  |  {sr} Hz",
        "panel.generated_status":   "已生成 {dur:.2f} 秒，{sr} Hz",
        "panel.error_status":       "錯誤：{msg}",

        # TTS panel
        "tts.title":           "🎙️  文字轉語音",
        "tts.input_label":     "待合成文字：",
        "tts.lang_hint_label": "語言 / 口音提示（可選）：",
        "tts.lang_hint_tip":   "ℹ️  加入括號提示可引導模型使用指定口音，例如：(普通話) 或 (台灣腔)",
        "tts.tip":             "ℹ️  VoxCPM2 自動偵測輸入語言。\n    支援 30 種語言 + 9 種中文方言。",
        "tts.error_empty":     "請輸入待合成的文字。",

        # Voice Design panel
        "vd.title":           "🎨  聲音設計",
        "vd.desc_label":      "聲音描述：",
        "vd.desc_placeholder":"例如：年輕女性，溫柔甜美的聲音",
        "vd.presets":         "預設",
        "vd.desc_tip":        "描述性別、年齡、音調、情感、語速、口音…\n例如：「年輕女性，溫柔甜美的聲音，平靜的語速」",
        "vd.text_label":      "待合成文字：",
        "vd.gen_tip":         "ℹ️  提示：生成 1–3 次以找到最佳聲音匹配。",
        "vd.error_no_desc":   "請輸入聲音描述。",
        "vd.error_no_text":   "請輸入待合成的文字。",

        # Cloning panel
        "clone.title":            "🔁  可控聲音複製",
        "clone.ref_label":        "參考音訊（WAV）：",
        "clone.ref_placeholder":  "選擇 .wav 檔案 …",
        "clone.browse":           "瀏覽",
        "clone.ref_tip":          "ℹ️  任何乾淨的 WAV 檔案（5–30 秒）效果均佳。",
        "clone.style_label":      "風格控制（可選）：",
        "clone.style_examples":   "範例 …",
        "clone.style_placeholder":"例如：普通話  或  (稍快，愉悅音調)",
        "clone.text_label":       "待合成文字：",
        "clone.error_no_ref":     "請選擇參考音訊檔案。",
        "clone.error_no_text":    "請輸入待合成的文字。",
        "clone.browse_ref_title": "選擇參考音訊",

        # Ultimate clone panel
        "ultimate.title":             "⭐  極致聲音複製",
        "ultimate.ref_label":         "參考 + 提示音訊（WAV）：",
        "ultimate.ref_placeholder":   "選擇說話者參考 .wav …",
        "ultimate.browse":            "瀏覽",
        "ultimate.ref_tip":           "ℹ️  建議參考音訊與提示音訊使用相同檔案。\n    5–30 秒、背景噪音最少的音訊效果最佳。",
        "ultimate.transcript_label":  "參考音訊的文字稿：",
        "ultimate.transcript_placeholder": "在此輸入參考音訊中說話的確切文字。",
        "ultimate.transcript_warning":"⚠️  文字稿必須與參考音訊完全一致，以獲得最高保真度。",
        "ultimate.text_label":        "待合成文字：",
        "ultimate.error_no_ref":      "請選擇參考音訊檔案。",
        "ultimate.error_no_transcript":"請輸入參考音訊的文字稿。",
        "ultimate.error_no_text":     "請輸入待合成的文字。",
        "ultimate.browse_ref_title":  "選擇參考音訊",

        # Audio control bar
        "audio.play":         "▶  播放",
        "audio.stop":         "■  停止",
        "audio.save":         "💾  儲存",
        "audio.vol":          "音量：",
        "audio.duration_empty":"時長：—",
        "audio.duration_val": "時長：{dur:.2f} 秒",
        "audio.save_title":   "儲存音訊",
        "audio.save_error":   "儲存錯誤",

        # History panel
        "nav.history":              "歷史紀錄",
        "history.title":            "🕘  歷史紀錄",
        "history.empty":            "尚無合成紀錄",
        "history.empty_hint":       "合成音訊後將自動儲存於此",
        "history.count":            "{n} 筆紀錄",
        "history.clear_all":        "清除全部",
        "history.play":             "▶",
        "history.stop":             "■",
        "history.delete":           "🗑",
        "history.mode.tts":         "TTS",
        "history.mode.voice_design":"聲音設計",
        "history.mode.clone":       "複製",
        "history.mode.ultimate":    "極致",
        "history.auto_saved":       "已自動儲存：{filename}",
        "history.load_error":       "無法載入音訊：{msg}",

        # Dialogs
        "dialog.browse_out":  "選擇輸出目錄",
        "dialog.browse_cache":"選擇模型快取目錄",
    },

    "en": {
        # Navigation
        "nav.tts":          "Text-to-Speech",
        "nav.voice_design": "Voice Design",
        "nav.cloning":      "Clone Voice",
        "nav.ultimate":     "Ultimate Clone",
        "nav.settings":     "Settings",

        # Main window
        "app.subtitle":           "Studio",
        "app.model_not_loaded":   "  ○  Not loaded",
        "app.welcome":            "Welcome to {app} — Load the model from Settings to begin.",

        # Settings panel
        "settings.title":                  "⚙️  Settings & Model",
        "settings.model_section":          "Model",
        "settings.model_placeholder":      "HuggingFace model id or local path",
        "settings.load_model":             "Load Model",
        "settings.loading":                "Loading …",
        "settings.unload":                 "Unload",
        "settings.denoiser":               "Load denoiser head  (improves quality, +VRAM)",
        "settings.model_not_loaded_badge": "  ○  Model not loaded  ",
        "settings.model_loaded_badge":     "  ●  Model loaded  |  SR = {sr} Hz  ",
        "settings.starting_load":          "Starting download / load …",
        "settings.model_load_success":     "✓ Model loaded successfully",
        "settings.model_unloaded":         "Model unloaded.",
        "settings.model_unloaded_status":  "Model unloaded",
        "settings.model_load_error":       "Load error: {msg}",
        "settings.synthesis_params":       "Synthesis Parameters",
        "settings.cfg_label":              "CFG Value",
        "settings.cfg_tooltip":            "Classifier-free guidance scale.  Higher = closer to description.",
        "settings.steps_label":            "Inference Steps",
        "settings.steps_tooltip":          "Diffusion steps.  More steps = better quality but slower.",
        "settings.output_dir":             "Default Output Directory",
        "settings.model_cache_dir":        "Model Cache Directory",
        "settings.model_cache_placeholder":"./models  (relative to project root)",
        "settings.browse":                 "Browse",
        "settings.save":                   "💾  Save All Settings",
        "settings.saved":                  "Settings saved.",
        "settings.language":               "Interface Language",
        "settings.restart_required":       "Language changed. Please restart the application.",

        # Base / generator panel
        "panel.generate":           "🎙️  Generate",
        "panel.model_not_loaded":   "⚠️  Model not loaded — open Settings and click 'Load Model'.",
        "panel.generating":         "⏳  Generating audio …",
        "panel.done_status":        "✓  {dur:.2f} s  |  {sr} Hz",
        "panel.generated_status":   "Generated {dur:.2f} s at {sr} Hz",
        "panel.error_status":       "Error: {msg}",

        # TTS panel
        "tts.title":           "🎙️  Text-to-Speech",
        "tts.input_label":     "Text to synthesise:",
        "tts.lang_hint_label": "Language / Accent Hint (optional):",
        "tts.lang_hint_tip":   "ℹ️  A parenthesis prefix guides the accent, e.g. (Mandarin) or (British English)",
        "tts.tip":             "ℹ️  VoxCPM2 automatically detects the input language.\n    Supports 30 languages + 9 Chinese dialects.",
        "tts.error_empty":     "Please enter text to synthesise.",

        # Voice Design panel
        "vd.title":           "🎨  Voice Design",
        "vd.desc_label":      "Voice Description:",
        "vd.desc_placeholder":"e.g.   A young woman, gentle and sweet voice",
        "vd.presets":         "Presets",
        "vd.desc_tip":        "Describe gender, age, tone, emotion, pace, accent …\ne.g. 'A young woman, gentle and sweet voice, calm pace'",
        "vd.text_label":      "Text to Synthesise:",
        "vd.gen_tip":         "ℹ️  Tip: generate 1–3 times to find the best voice match.",
        "vd.error_no_desc":   "Please enter a voice description.",
        "vd.error_no_text":   "Please enter text to synthesise.",

        # Cloning panel
        "clone.title":            "🔁  Controllable Voice Cloning",
        "clone.ref_label":        "Reference Audio (WAV):",
        "clone.ref_placeholder":  "Select a .wav file …",
        "clone.browse":           "Browse",
        "clone.ref_tip":          "ℹ️  Any clean WAV file (5–30 s) works well.",
        "clone.style_label":      "Style Control  (optional):",
        "clone.style_examples":   "Examples …",
        "clone.style_placeholder":"e.g.  Mandarin  or  (slightly faster, cheerful tone)",
        "clone.text_label":       "Text to Synthesise:",
        "clone.error_no_ref":     "Please select a reference audio file.",
        "clone.error_no_text":    "Please enter text to synthesise.",
        "clone.browse_ref_title": "Select reference audio",

        # Ultimate clone panel
        "ultimate.title":             "⭐  Ultimate Voice Cloning",
        "ultimate.ref_label":         "Reference + Prompt Audio (WAV):",
        "ultimate.ref_placeholder":   "Select the speaker reference .wav …",
        "ultimate.browse":            "Browse",
        "ultimate.ref_tip":           "ℹ️  Use the same clean WAV clip for both reference and prompt.\n    5–30 s with minimal background noise gives best results.",
        "ultimate.transcript_label":  "Transcript of the Reference Audio:",
        "ultimate.transcript_placeholder": "Type the exact words spoken in the reference audio here.",
        "ultimate.transcript_warning":"⚠️  The transcript must match the reference audio verbatim for maximum fidelity.",
        "ultimate.text_label":        "Text to Synthesise:",
        "ultimate.error_no_ref":      "Please select a reference audio file.",
        "ultimate.error_no_transcript":"Please enter the transcript of the reference audio.",
        "ultimate.error_no_text":     "Please enter text to synthesise.",
        "ultimate.browse_ref_title":  "Select reference audio",

        # Audio control bar
        "audio.play":         "▶  Play",
        "audio.stop":         "■  Stop",
        "audio.save":         "💾  Save",
        "audio.vol":          "Vol:",
        "audio.duration_empty":"Duration: —",
        "audio.duration_val": "Duration: {dur:.2f} s",
        "audio.save_title":   "Save audio",
        "audio.save_error":   "Save error",

        # History panel
        "nav.history":              "History",
        "history.title":            "🕘  History",
        "history.empty":            "No recordings yet",
        "history.empty_hint":       "Generated audio will appear here automatically",
        "history.count":            "{n} recording(s)",
        "history.clear_all":        "Clear All",
        "history.play":             "▶",
        "history.stop":             "■",
        "history.delete":           "🗑",
        "history.mode.tts":         "TTS",
        "history.mode.voice_design":"Design",
        "history.mode.clone":       "Clone",
        "history.mode.ultimate":    "Ultimate",
        "history.auto_saved":       "Auto-saved: {filename}",
        "history.load_error":       "Cannot load audio: {msg}",

        # Dialogs
        "dialog.browse_out":  "Select output directory",
        "dialog.browse_cache":"Select model cache directory",
    },
}

SUPPORTED_LOCALES = list(_TRANSLATIONS.keys())

# ── Runtime state ─────────────────────────────────────────────────────────────

_current_locale: str = "zh-TW"


def init(locale: str) -> None:
    """Set the active locale.  Call once before building any UI."""
    global _current_locale
    if locale in _TRANSLATIONS:
        _current_locale = locale
    else:
        _current_locale = "zh-TW"


def t(key: str, **kwargs: object) -> str:
    """Return the translated string for *key*, formatted with *kwargs*."""
    table = _TRANSLATIONS.get(_current_locale, _TRANSLATIONS["zh-TW"])
    text = table.get(key)
    if text is None:
        # Fall back to English, then the key itself
        text = _TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def current_locale() -> str:
    return _current_locale
