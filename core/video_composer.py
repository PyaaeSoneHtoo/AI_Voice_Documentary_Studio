"""
Video Composer — Dynamic Camera Motion, Subtitles & FFmpeg Assembly
Generates Ken Burns camera motion clips, Burns subtitles, mixes audio, and renders final MP4.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

import config

logger = logging.getLogger("DocuStudio.Composer")


class VideoComposer:
    def __init__(self, output_dir: Path = config.VIDEOS_DIR, temp_dir: Path = config.TEMP_DIR):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def compose_documentary(
        self,
        script: Dict[str, Any],
        scene_assets: List[Dict[str, Any]],
        bgm_track_id: str = "cinematic_drone",
        bgm_volume: float = 0.12,
        aspect_ratio_key: str = "16:9 (YouTube & Cinematic Landscape)"
    ) -> Path:
        """
        Takes prepared scene assets (images, audio durations), builds animated scene clips,
        generates subtitles, mixes background music, and renders the final documentary video.
        """
        ratio_info = config.ASPECT_RATIOS.get(aspect_ratio_key, config.ASPECT_RATIOS["16:9 (YouTube & Cinematic Landscape)"])
        width = ratio_info["width"]
        height = ratio_info["height"]
        fps = config.DEFAULT_FPS

        # 1. Build individual scene video clips
        scene_clips: List[Path] = []
        total_duration = 0.0

        for idx, asset in enumerate(scene_assets):
            scene_num = asset["scene_num"]
            image_path = Path(asset["image_path"])
            audio_path = Path(asset["audio_path"])
            duration = max(asset.get("duration", 5.0), 3.0)
            total_duration += duration
            motion = asset.get("camera_motion", "zoom_in")

            clip_path = self.temp_dir / f"clip_{scene_num:02d}.mp4"
            self._render_scene_clip(image_path, audio_path, duration, width, height, fps, motion, clip_path)
            scene_clips.append(clip_path)

        # 2. Create concatenation manifest
        concat_file = self.temp_dir / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                # Format for FFmpeg concat: file 'C:/path/clip_01.mp4'
                f.write(f"file '{clip.as_posix()}'\n")

        # 3. Concatenate video clips into merged video
        merged_video = self.temp_dir / "merged_scenes.mp4"
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(merged_video)
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        # 4. Mix Background Music (if selected)
        final_video_name = f"doc_{int(total_duration)}s_{script.get('title', 'documentary')[:25].strip().replace(' ', '_')}.mp4"
        final_video_name = "".join(c for c in final_video_name if c.isalnum() or c in "._-")
        final_output_path = self.output_dir / final_video_name

        bgm_path = self._resolve_bgm_path(bgm_track_id)
        if bgm_path and bgm_volume > 0:
            self._mix_bgm(merged_video, bgm_path, bgm_volume, total_duration, final_output_path)
        else:
            # Copy directly
            if final_output_path.exists():
                final_output_path.unlink()
            merged_video.rename(final_output_path)

        logger.info(f"Documentary rendering complete -> {final_output_path}")
        return final_output_path

    def _render_scene_clip(
        self,
        image_path: Path,
        audio_path: Path,
        duration: float,
        width: int,
        height: int,
        fps: int,
        motion: str,
        out_path: Path
    ):
        """
        Applies Ken Burns camera motion (pan/zoom) to an image and merges it with scene narration.
        """
        frames = int(duration * fps)

        # Build Ken Burns zoompan filter
        # zoompan takes duration in frames: d=frames
        if motion == "zoom_out":
            # Start zoomed at 1.15, zoom out to 1.0
            zoom_filter = f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.15/{frames}))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}"
        elif motion == "pan_left":
            # Subtle pan from right to left with slight zoom
            zoom_filter = f"zoompan=z='1.1':x='if(lte(on,1),iw*0.1,max(0,x-(iw*0.1/{frames})))':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}"
        elif motion == "pan_right":
            # Subtle pan from left to right with slight zoom
            zoom_filter = f"zoompan=z='1.1':x='if(lte(on,1),0,min(iw*0.1,x+(iw*0.1/{frames})))':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}"
        else:
            # Default: smooth zoom_in (1.0 -> 1.15)
            zoom_filter = f"zoompan=z='min(max(zoom,pzoom)+0.15/{frames},1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{zoom_filter}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{duration:.3f}",
            "-shortest",
            str(out_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg scene render failed: {res.stderr}")
            # Fallback simple render without zoompan if complex filter fails
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-pix_fmt", "yuv420p",
                "-vf", f"scale={width}:{height}",
                "-c:a", "aac",
                "-t", f"{duration:.3f}",
                str(out_path)
            ]
            subprocess.run(cmd_fallback, check=True)

    def _mix_bgm(self, video_path: Path, bgm_path: Path, bgm_vol: float, total_dur: float, out_path: Path):
        """Ducks and mixes background music under dialogue narration."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-stream_loop", "-1",
            "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume={bgm_vol:.3f}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_dur:.3f}",
            str(out_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _resolve_bgm_path(self, track_id: str) -> Optional[Path]:
        """Resolves file path for selected BGM track."""
        if track_id == "none":
            return None
        candidate = config.BGM_DIR / f"{track_id}.wav"
        if candidate.exists():
            return candidate
        default_candidate = config.BGM_DIR / "cinematic_drone.wav"
        if default_candidate.exists():
            return default_candidate
        return None
