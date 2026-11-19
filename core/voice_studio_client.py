"""
VoiceStudio Integration Client — Voice Cloning & Speech Synthesis Engine
Connects to VoiceStudio's local OpenAI-compatible audio API (/v1/audio/speech) with Edge-TTS fallback.
"""

import asyncio
import io
import json
import logging
import os
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import config

logger = logging.getLogger("DocuStudio.Voice")

# Curated Presets: VoiceStudio & Edge-TTS Mappings
NARRATOR_PRESETS = [
    {
        "id": "david-attenborough",
        "name": "Sir David (Legendary BBC Nature & Wildlife)",
        "voicestudio_voice": "david-nature",
        "edgetts_voice": "en-GB-RyanNeural",
        "gender": "Male",
        "accent": "British",
        "style": "Deep, Whispering, Wonder & Awe"
    },
    {
        "id": "morgan-freeman",
        "name": "Morgan (Deep, Authoritative & Epic Storyteller)",
        "voicestudio_voice": "morgan-deep",
        "edgetts_voice": "en-US-ChristopherNeural",
        "gender": "Male",
        "accent": "American",
        "style": "Gravitas, Cinematic, Wisdom"
    },
    {
        "id": "astronomer-carl",
        "name": "Carl (Cosmic Odyssey & Scientific Reflection)",
        "voicestudio_voice": "carl-cosmic",
        "edgetts_voice": "en-US-GuyNeural",
        "gender": "Male",
        "accent": "American",
        "style": "Poetic, Contemplative, Scientific"
    },
    {
        "id": "true-crime-noir",
        "name": "Eric (Dark Noir, True Crime & Secret History)",
        "voicestudio_voice": "noir-detective",
        "edgetts_voice": "en-US-EricNeural",
        "gender": "Male",
        "accent": "American",
        "style": "Intense, Atmospheric, Suspenseful"
    },
    {
        "id": "history-chronicle-sonia",
        "name": "Sonia (Regal Historian & Ancient Civilizations)",
        "voicestudio_voice": "sonia-regal",
        "edgetts_voice": "en-GB-SoniaNeural",
        "gender": "Female",
        "accent": "British",
        "style": "Scholarly, Articulate, Grand"
    },
    {
        "id": "cinematic-jenny",
        "name": "Jenny (Warm, Modern & Thoughtful Explorer)",
        "voicestudio_voice": "jenny-warm",
        "edgetts_voice": "en-US-JennyNeural",
        "gender": "Female",
        "accent": "American",
        "style": "Empathetic, Narrative, Clear"
    }
]


class VoiceStudioClient:
    def __init__(
        self,
        base_url: str = config.VOICESTUDIO_BASE_URL,
        api_key: str = config.VOICESTUDIO_API_KEY
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def check_health(self) -> Tuple[bool, str]:
        """Checks if local VoiceStudio backend is online and running."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status in (200, 204):
                    return True, "VoiceStudio Engine Online (OmniVoice / CosyVoice Active)"
        except Exception:
            pass

        # Also check root health
        try:
            req = urllib.request.Request(f"{self.base_url.replace('/v1', '')}/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status in (200, 204):
                    return True, "VoiceStudio Engine Online"
        except Exception:
            pass

        return False, "Offline (Using Edge-TTS fallback)"

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Returns preset narrator voices plus any custom cloned voices."""
        voices = list(NARRATOR_PRESETS)
        
        # Scan for user cloned voice samples in assets/voices
        custom_voice_dir = config.VOICES_DIR
        for audio_file in custom_voice_dir.glob("*.wav"):
            voice_id = f"custom-{audio_file.stem}"
            voices.insert(0, {
                "id": voice_id,
                "name": f"🎙️ Cloned: {audio_file.stem.replace('_', ' ').title()}",
                "voicestudio_voice": str(audio_file),
                "edgetts_voice": config.DEFAULT_FALLBACK_VOICE,
                "gender": "Custom Clone",
                "accent": "Original Audio",
                "style": "Exact Voice Clone (from reference audio)"
            })
        return voices

    def generate_narration(
        self,
        text: str,
        voice_id: str,
        output_filepath: Path,
        speech_rate: str = "+0%"
    ) -> float:
        """
        Synthesizes text into audio.
        Attempts VoiceStudio first; if offline, falls back seamlessly to Edge-TTS.
        Returns the duration of the audio in seconds.
        """
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Resolve voice metadata
        voice_preset = next((v for v in self.get_available_voices() if v["id"] == voice_id), None)
        if not voice_preset:
            voice_preset = NARRATOR_PRESETS[0]

        # 1. Try VoiceStudio /v1/audio/speech
        is_online, _ = self.check_health()
        if is_online:
            try:
                target_voice = voice_preset.get("voicestudio_voice", "omnivoice")
                payload = {
                    "model": "omnivoice",
                    "voice": target_voice,
                    "input": text,
                    "response_format": "mp3"
                }
                req = urllib.request.Request(
                    f"{self.base_url}/audio/speech",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    with open(output_filepath, "wb") as f:
                        f.write(resp.read())
                duration = self.get_audio_duration(output_filepath)
                logger.info(f"VoiceStudio synthesized {output_filepath.name} ({duration:.2f}s)")
                return duration
            except Exception as e:
                logger.warning(f"VoiceStudio synthesis failed ({e}). Falling back to Edge-TTS...")

        # 2. Fallback to Edge-TTS
        edge_voice = voice_preset.get("edgetts_voice", config.DEFAULT_FALLBACK_VOICE)
        duration = self._generate_with_edgetts(text, edge_voice, output_filepath, speech_rate)
        return duration

    def _generate_with_edgetts(
        self,
        text: str,
        voice: str,
        output_filepath: Path,
        rate: str = "+0%"
    ) -> float:
        """Generates voiceover using Microsoft Edge-TTS."""
        import edge_tts

        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(str(output_filepath))

        try:
            asyncio.run(_run())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_run())

        return self.get_audio_duration(output_filepath)

    @staticmethod
    def get_audio_duration(filepath: Path) -> float:
        """Determines the exact duration of an audio file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            # Fallback estimation based on file size for MP3 (approx 16KB/s for 128kbps)
            try:
                size = filepath.stat().st_size
                return max(3.0, size / 16000.0)
            except Exception:
                return 5.0
