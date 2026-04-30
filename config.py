import os
from langdetect import DetectorFactory

DetectorFactory.seed = 0

# ── Load .env file if present (local development) ────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on environment variables

# ── API Keys (loaded from environment variables) ─────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
HF_API_KEY     = os.getenv("HF_API_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
MODEL_ID       = os.getenv("MODEL_ID", "sarvam-30b")
STT_MODEL      = os.getenv("STT_MODEL", "saarika:v2.5")

# ── API Endpoints ─────────────────────────────────────────
SARVAM_API           = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_TRANSLATE_API = "https://api.sarvam.ai/v1/translate"
SARVAM_STT_URL       = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL       = "https://api.sarvam.ai/text-to-speech"

# ── TTS Settings ──────────────────────────────────────────
TTS_MODEL            = "bulbul:v3"
TTS_SPEAKER          = "shubh"          # default voice (gender-neutral, works all languages)
TTS_SAMPLE_RATE      = 22050

# ── App Settings ──────────────────────────────────────────
DATA_FOLDER        = "data"
CHUNK_SIZE         = 800
CHUNK_OVERLAP      = 150
MAX_CONTEXT_CHUNKS = 3

# ── Language Maps ─────────────────────────────────────────
LANGUAGE_MAP = {
    'en': 'English', 'hi': 'Hindi',  'te': 'Telugu',
    'ta': 'Tamil',   'kn': 'Kannada','ml': 'Malayalam',
    'mr': 'Marathi', 'gu': 'Gujarati','bn': 'Bengali',
    'pa': 'Punjabi', 'ur': 'Urdu',   'or': 'Odia',
    'as': 'Assamese',
}

# ── Language code → Sarvam TTS BCP-47 code ────────────────
# Bulbul v3 supports: hi-IN, bn-IN, ta-IN, te-IN, gu-IN,
#                     kn-IN, ml-IN, mr-IN, pa-IN, od-IN, en-IN
TTS_LANGUAGE_MAP = {
    'hi': 'hi-IN', 'te': 'te-IN', 'ta': 'ta-IN',
    'kn': 'kn-IN', 'ml': 'ml-IN', 'mr': 'mr-IN',
    'bn': 'bn-IN', 'gu': 'gu-IN', 'pa': 'pa-IN',
    'or': 'od-IN', 'en': 'en-IN',
    # fallback for unsupported (Urdu, Assamese, etc.) → English voice
}

INDIC_SCRIPT_RANGES = {
    'hi': (0x0900, 0x097F), 'mr': (0x0900, 0x097F),
    'te': (0x0C00, 0x0C7F), 'ta': (0x0B80, 0x0BFF),
    'kn': (0x0C80, 0x0CFF), 'ml': (0x0D00, 0x0D7F),
    'gu': (0x0A80, 0x0AFF), 'bn': (0x0980, 0x09FF),
    'pa': (0x0A00, 0x0A7F), 'or': (0x0B00, 0x0B7F),
    'as': (0x0980, 0x09FF), 'ur': (0x0600, 0x06FF),
}
