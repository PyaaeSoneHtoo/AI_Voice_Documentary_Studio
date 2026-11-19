"""
AI Voice Documentary Studio — Configuration & Environment Settings
Combines FreeLLMAPI (for zero-cost LLM intelligence) and VoiceStudio (for voice cloning/TTS).
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / "core"
ASSETS_DIR = BASE_DIR / "assets"
BGM_DIR = ASSETS_DIR / "bgm"
VOICES_DIR = ASSETS_DIR / "voices"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = OUTPUT_DIR / "temp"
VIDEOS_DIR = OUTPUT_DIR / "videos"

# Ensure all critical folders exist
for folder in [ASSETS_DIR, BGM_DIR, VOICES_DIR, OUTPUT_DIR, TEMP_DIR, VIDEOS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ── FreeLLMAPI Configuration (LLM Gateway) ──
# FreeLLMAPI aggregates 87+ free providers behind an OpenAI-compatible /v1 endpoint.
FREELLMAPI_BASE_URL = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")
FREELLMAPI_API_KEY = os.getenv("FREELLMAPI_API_KEY", "local")
FREELLMAPI_DEFAULT_MODEL = os.getenv("FREELLMAPI_DEFAULT_MODEL", "auto:smart")  # "auto:smart", "auto:fast", "auto"

# Direct Cloud Fallback (Optional, used if FreeLLMAPI is offline)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── VoiceStudio Configuration (Voice Cloning & Audio Synthesis) ──
# VoiceStudio runs locally providing zero-shot voice cloning and OpenAI-compatible audio endpoints.
VOICESTUDIO_BASE_URL = os.getenv("VOICESTUDIO_BASE_URL", "http://localhost:8000/v1")
VOICESTUDIO_API_KEY = os.getenv("VOICESTUDIO_API_KEY", "local")
VOICESTUDIO_DEFAULT_VOICE = os.getenv("VOICESTUDIO_DEFAULT_VOICE", "omnivoice")

# Fallback Edge-TTS Voices
DEFAULT_FALLBACK_VOICE = "en-US-ChristopherNeural"

# ── Visual & Rendering Settings ──
ASPECT_RATIOS = {
    "16:9 (YouTube & Cinematic Landscape)": {"width": 1920, "height": 1080, "ratio": "16:9"},
    "9:16 (TikTok, Reels, Shorts)": {"width": 1080, "height": 1920, "ratio": "9:16"},
    "2.39:1 (Anamorphic Cinema Widescreen)": {"width": 1920, "height": 804, "ratio": "2.39:1"}
}

DEFAULT_FPS = 30
DEFAULT_SCENE_DURATION = 6.0  # seconds if speech length is shorter
