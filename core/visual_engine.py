"""
Visual Engine — Photorealistic Image Generation & Cinematic Styling
Generates scene visuals using Pollinations AI (FLUX / Photorealism) with offline procedural fallbacks.
"""

import io
import logging
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

logger = logging.getLogger("DocuStudio.Visual")

STYLE_PRESETS = {
    "Cinematic Photorealism (Universal)": {
        "suffix": ", 8k resolution, cinematic lighting, shot on 35mm Arri Alexa lens, photorealistic, National Geographic documentary photography, award winning composition",
        "negative": "cartoon, 3d render, anime, blurry, low resolution, watermark, text, deformed"
    },
    "Historical 35mm Film Still (Kodak 500T)": {
        "suffix": ", authentic historical film still, Kodak Vision3 500T 35mm grain, vintage color grading, soft halation, archival documentary photo",
        "negative": "modern, digital, oversaturated, cartoon, CGI, plastic, text"
    },
    "Space & Cosmic Odyssey (Hubble/Webb)": {
        "suffix": ", James Webb Space Telescope ultra deep field, glowing celestial nebulae, star clusters, cosmic rays, breathtaking astrophysics photography, 8k",
        "negative": "earth, cartoon, blurry, low quality, oversaturated green"
    },
    "Dark Mystery & Crime Noir": {
        "suffix": ", moody chiaroscuro lighting, deep shadows, volumetric fog, dramatic high contrast, true crime documentary cinematography, film noir aesthetic",
        "negative": "bright, sunny, cheerful, cartoon, low quality"
    },
    "Ancient Oil Painting & Renaissance Epic": {
        "suffix": ", majestic classical oil painting, Rembrandt lighting, rich golden undertones, detailed brushwork, epic fine art masterpiece, museum quality",
        "negative": "photo, modern, digital render, 3d, pixelated, blur"
    },
    "Cyberpunk & High-Tech Futuristic": {
        "suffix": ", futuristic cyberpunk aesthetic, volumetric neon reflections, holographic displays, rain-slicked surfaces, blade runner 2049 cinematography, 8k",
        "negative": "vintage, medieval, cartoon, flat, blurry"
    }
}


class VisualEngine:
    def __init__(self, output_dir: Path = config.TEMP_DIR):
        self.output_dir = output_dir

    def generate_scene_image(
        self,
        prompt: str,
        scene_num: int,
        style_name: str = "Cinematic Photorealism (Universal)",
        aspect_ratio_key: str = "16:9 (YouTube & Cinematic Landscape)"
    ) -> Path:
        """
        Generates and saves a high-resolution image for a documentary scene.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / f"scene_{scene_num:02d}.jpg"

        # Resolve dimensions
        ratio_info = config.ASPECT_RATIOS.get(aspect_ratio_key, config.ASPECT_RATIOS["16:9 (YouTube & Cinematic Landscape)"])
        width = ratio_info["width"]
        height = ratio_info["height"]

        # Compose enhanced prompt
        style_info = STYLE_PRESETS.get(style_name, STYLE_PRESETS["Cinematic Photorealism (Universal)"])
        full_prompt = f"{prompt.strip()}{style_info['suffix']}"

        # 1. Attempt Pollinations AI (FLUX model, zero API key required)
        try:
            encoded_prompt = urllib.parse.quote(full_prompt)
            # Use 1280x720 or scaled dimensions for fast download, then resize to full
            dl_width = 1280 if width >= height else 720
            dl_height = int(dl_width * (height / width))
            
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={dl_width}&height={dl_height}&model=flux&nologo=true&seed={scene_num*137 + 42}"
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Docu-Studio/1.0"}
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                image_data = resp.read()
                img = Image.open(io.BytesIO(image_data)).convert("RGB")
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                img.save(out_path, "JPEG", quality=95)
                logger.info(f"Generated scene {scene_num} image via Pollinations FLUX -> {out_path.name}")
                return out_path
        except Exception as e:
            logger.warning(f"Pollinations generation failed ({e}). Creating procedural cinematic fallback.")

        # 2. Procedural Fallback
        self._generate_procedural_image(prompt, scene_num, width, height, out_path)
        return out_path

    def _generate_procedural_image(self, prompt: str, scene_num: int, width: int, height: int, out_path: Path):
        """Creates an atmospheric cinematic card if network is unavailable."""
        img = Image.new("RGB", (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Draw deep cinematic radial vignette
        for r in range(min(width, height) // 2, 0, -10):
            alpha = int(255 * (1 - r / (min(width, height) / 2)))
            fill = (max(0, 30 - alpha // 10), max(0, 41 - alpha // 8), max(0, 59 - alpha // 6))
            draw.ellipse(
                [(width // 2 - r, height // 2 - r), (width // 2 + r, height // 2 + r)],
                outline=fill,
                width=10
            )

        # Draw Title and Chapter Text
        text = f"SCENE {scene_num:02d}\n{prompt[:90]}..."
        draw.text((width // 2, height // 2), text, fill=(241, 245, 249), anchor="mm")
        img.save(out_path, "JPEG", quality=95)
