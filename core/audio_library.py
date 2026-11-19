"""
Audio Library — Cinematic Background Music & Ambience Management
"""

import math
import struct
import wave
from pathlib import Path
from typing import List, Dict

import config

BGM_TRACKS = [
    {
        "id": "cinematic_drone",
        "name": "🌌 Cosmic & Cinematic Ambient Drone (Deep Mystery)",
        "file": "cinematic_drone.wav",
        "genre": "Ambient / Drone",
        "default_volume": 0.15
    },
    {
        "id": "mystery_abyss",
        "name": "🌊 Abyssal Depth (Subtle Tension & Echoes)",
        "file": "mystery_abyss.wav",
        "genre": "Mystery / Drama",
        "default_volume": 0.12
    },
    {
        "id": "none",
        "name": "🔇 None (Narration Only)",
        "file": "",
        "genre": "Speech Only",
        "default_volume": 0.0
    }
]


def ensure_default_bgm_tracks():
    """Generates synthetic ambient audio tracks if files don't already exist."""
    config.BGM_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Check cinematic_drone.wav
    drone_path = config.BGM_DIR / "cinematic_drone.wav"
    if not drone_path.exists() or drone_path.stat().st_size == 0:
        _synthesize_ambient_drone(drone_path, duration=30.0, base_freq=55.0)

    # 2. Check mystery_abyss.wav
    abyss_path = config.BGM_DIR / "mystery_abyss.wav"
    if not abyss_path.exists() or abyss_path.stat().st_size == 0:
        _synthesize_ambient_drone(abyss_path, duration=30.0, base_freq=42.0)


def _synthesize_ambient_drone(path: Path, duration: float = 30.0, base_freq: float = 55.0):
    """Procedurally generates a warm, cinematic ambient drone WAV."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(n_samples):
            t = float(i) / sample_rate
            
            # Layer harmonics with slow LFO modulation
            lfo = 0.5 + 0.5 * math.sin(2 * math.pi * 0.1 * t)
            harm1 = math.sin(2 * math.pi * base_freq * t)
            harm2 = 0.5 * math.sin(2 * math.pi * (base_freq * 1.5) * t)
            harm3 = 0.25 * math.sin(2 * math.pi * (base_freq * 2.01) * t)
            
            sample_val = (harm1 + harm2 + harm3) * 0.25 * lfo
            # Soft fade-in and fade-out
            if t < 2.0:
                sample_val *= (t / 2.0)
            elif t > (duration - 2.0):
                sample_val *= ((duration - t) / 2.0)

            int_val = int(max(-32767, min(32767, sample_val * 32767)))
            # Left & Right
            frames.extend(struct.pack("<hh", int_val, int_val))
            
        wav_file.writeframes(frames)


# Ensure default BGM tracks are available
ensure_default_bgm_tracks()
