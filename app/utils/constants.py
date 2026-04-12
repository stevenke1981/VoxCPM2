"""Application-wide constants for VoxCPM2 Studio."""

# ─── App metadata ────────────────────────────────────────────────────────────
APP_NAME = "VoxCPM2 Studio"
APP_VERSION = "1.0.0"

# ─── Default model ───────────────────────────────────────────────────────────
DEFAULT_MODEL = "openbmb/VoxCPM2"
DEFAULT_MODEL_CACHE_DIR = "./models"

# ─── Window geometry ─────────────────────────────────────────────────────────
MIN_W = 1120
MIN_H = 740
SIDEBAR_WIDTH = 230
WAVEFORM_H = 110

# ─── TTS parameters ──────────────────────────────────────────────────────────
DEFAULT_CFG = 2.0
DEFAULT_STEPS = 10
DEFAULT_VOLUME = 0.9

# ─── Panel IDs ───────────────────────────────────────────────────────────────
PANEL_TTS = "tts"
PANEL_VOICE_DESIGN = "voice_design"
PANEL_CLONING = "cloning"
PANEL_ULTIMATE = "ultimate"
PANEL_HISTORY = "history"
PANEL_SRT = "srt"
PANEL_SETTINGS = "settings"

# ─── History WAV output directory ────────────────────────────────────────────
WAV_DIR = "./wav-files"

# ─── Navigation items (icon, i18n_key, panel_id) ─────────────────────────────
NAV_ITEMS = [
    ("🎙️", "nav.tts",          PANEL_TTS),
    ("🎨", "nav.voice_design", PANEL_VOICE_DESIGN),
    ("🔁", "nav.cloning",      PANEL_CLONING),
    ("⭐", "nav.ultimate",     PANEL_ULTIMATE),
    ("🕘", "nav.history",      PANEL_HISTORY),
    ("📄", "nav.srt",         PANEL_SRT),
    ("⚙️", "nav.settings",    PANEL_SETTINGS),
]

# ─── Supported languages ─────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = [
    "Arabic", "Burmese", "Chinese", "Danish", "Dutch",
    "English", "Finnish", "French", "German", "Greek",
    "Hebrew", "Hindi", "Indonesian", "Italian", "Japanese",
    "Khmer", "Korean", "Lao", "Malay", "Norwegian",
    "Polish", "Portuguese", "Russian", "Spanish", "Swahili",
    "Swedish", "Tagalog", "Thai", "Turkish", "Vietnamese",
]

CHINESE_DIALECTS = [
    "四川话", "粤语", "吴语", "东北话", "河南话",
    "陕西话", "山东话", "天津话", "闽南话",
]

# ─── Audio ────────────────────────────────────────────────────────────────────
FALLBACK_SAMPLE_RATE = 48000

# ─── Config file ─────────────────────────────────────────────────────────────
CONFIG_FILENAME = "voxcpm2_studio.json"

# ─── Waveform colours (canvas hex) ───────────────────────────────────────────
WAVEFORM_BG = "#1a1a2e"
WAVEFORM_BAR = "#4e9af1"
WAVEFORM_BASELINE = "#334466"
