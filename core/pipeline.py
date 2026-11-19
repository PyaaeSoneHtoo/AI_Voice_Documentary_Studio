"""
Documentary Pipeline — End-to-End Orchestrator
Coordinates FreeLLMAPI intelligence, VoiceStudio voice cloning/synthesis, visual generation, and video composition.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import config
from core.llm_gateway import FreeLLMAPIGateway
from core.voice_studio_client import VoiceStudioClient
from core.visual_engine import VisualEngine
from core.video_composer import VideoComposer

logger = logging.getLogger("DocuStudio.Pipeline")


def run_documentary_pipeline(
    script: Dict[str, Any],
    visual_style: str = "Cinematic Photorealism (Universal)",
    aspect_ratio: str = "16:9 (YouTube & Cinematic Landscape)",
    default_voice: str = "david-attenborough",
    bgm_track: str = "cinematic_drone",
    bgm_volume: float = 0.12,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> Dict[str, Any]:
    """
    Executes the complete AI documentary production pipeline:
    1. Synthesizes scene speech (VoiceStudio / Edge-TTS)
    2. Generates scene imagery (Pollinations / Procedural)
    3. Renders animated camera motion clips and mixes final video
    """
    start_time = time.time()
    voice_client = VoiceStudioClient()
    visual_engine = VisualEngine()
    composer = VideoComposer()

    scenes = script.get("scenes", [])
    total_scenes = len(scenes)
    if total_scenes == 0:
        raise ValueError("Script contains no scenes to render.")

    def _notify(stage: str, prog: float, msg: str):
        if progress_callback:
            progress_callback(stage, prog, msg)
        logger.info(f"[{stage}] ({int(prog*100)}%): {msg}")

    _notify("Initializing", 0.05, f"Starting production for '{script.get('title', 'Documentary')}'...")

    scene_assets: List[Dict[str, Any]] = []

    # Step 1 & 2: Generate Audio & Visuals for each scene
    for idx, scene in enumerate(scenes):
        scene_num = scene.get("scene_num", idx + 1)
        narration = scene.get("narration", "")
        visual_prompt = scene.get("visual_prompt", "")
        voice_id = scene.get("voice", default_voice)
        camera_motion = scene.get("camera_motion", "zoom_in")

        base_prog = 0.1 + (idx / total_scenes) * 0.55

        # Audio generation
        _notify("Voice Synthesis", base_prog, f"Synthesizing voice for Scene {scene_num}/{total_scenes}...")
        audio_path = config.TEMP_DIR / f"scene_{scene_num:02d}.mp3"
        duration = voice_client.generate_narration(narration, voice_id, audio_path)

        # Visual generation
        _notify("Visual Generation", base_prog + (0.55 / total_scenes) * 0.5, f"Rendering visual for Scene {scene_num}/{total_scenes}...")
        img_path = visual_engine.generate_scene_image(
            prompt=visual_prompt,
            scene_num=scene_num,
            style_name=visual_style,
            aspect_ratio_key=aspect_ratio
        )

        scene_assets.append({
            "scene_num": scene_num,
            "title": scene.get("title", f"Scene {scene_num}"),
            "audio_path": audio_path,
            "image_path": img_path,
            "duration": duration,
            "camera_motion": camera_motion,
            "narration": narration
        })

    # Step 3: Video Assembly & Ken Burns Motion
    _notify("Video Assembly", 0.70, "Applying Ken Burns camera motion & rendering scene clips...")
    
    final_video_path = composer.compose_documentary(
        script=script,
        scene_assets=scene_assets,
        bgm_track_id=bgm_track,
        bgm_volume=bgm_volume,
        aspect_ratio_key=aspect_ratio
    )

    elapsed = time.time() - start_time
    total_audio_duration = sum(a["duration"] for a in scene_assets)

    _notify("Complete", 1.0, f"Documentary produced successfully in {elapsed:.1f}s!")

    return {
        "status": "success",
        "video_path": str(final_video_path),
        "total_duration": total_audio_duration,
        "elapsed_seconds": elapsed,
        "scenes_count": total_scenes,
        "scene_assets": scene_assets
    }
