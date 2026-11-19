"""
Story Architect — Cinematic Documentary Script & Scene Planner
Leverages FreeLLMAPI to orchestrate multi-scene documentaries with structured cinematic metadata.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional

from core.llm_gateway import FreeLLMAPIGateway

logger = logging.getLogger("DocuStudio.Story")

DOCUMENTARY_PRESETS = {
    "The Lost City of Atlantis: Submerged Secrets": {
        "title": "The Lost City of Atlantis: Submerged Secrets",
        "category": "Ancient History & Deep Sea Mystery",
        "default_voice": "david-attenborough",
        "default_style": "Historical Epic & Ancient Civilization",
        "scenes": [
            {
                "scene_num": 1,
                "title": "The Golden Metropolis",
                "speaker": "Lead Narrator",
                "voice": "david-attenborough",
                "narration": "More than two thousand years ago, the philosopher Plato wrote of an empire beyond the Pillars of Hercules—a civilization of unimaginable wealth, advanced engineering, and boundless power.",
                "visual_prompt": "Monumental ancient city of Atlantis with concentric rings of water and land, golden temples, marble palaces, ancient triremes sailing through grand canals, sun rays breaking through majestic clouds, 8k cinematic photorealism",
                "camera_motion": "zoom_in"
            },
            {
                "scene_num": 2,
                "title": "The Cataclysm of the Deep",
                "speaker": "Lead Narrator",
                "voice": "david-attenborough",
                "narration": "In a single day and night of catastrophic misfortune, violent earthquakes shook the tectonic plates. Towering tsunamis swept through the marble corridors, swallowing the golden towers into the abyssal depths.",
                "visual_prompt": "Cataclysmic ocean tsunami crashing violently over towering ancient Greek marble towers and bronze statues, dramatic stormy skies with lightning, dark churning waves, cinematic devastation",
                "camera_motion": "pan_right"
            },
            {
                "scene_num": 3,
                "title": "Ruins in the Abyssal Blue",
                "speaker": "Deep Ocean Explorer",
                "voice": "morgan-freeman",
                "narration": "Modern deep-sea submersibles scanning the Atlantic seabed have revealed anomalous geometric structures—colossal megalithic columns standing silent under thousands of feet of crushing water.",
                "visual_prompt": "Deep sea research submarine with bright xenon headlights illuminating submerged megalithic stone pillars and statues covered in coral on the dark ocean floor, bioluminescent marine life, eerie atmospheric blue haze",
                "camera_motion": "zoom_out"
            },
            {
                "scene_num": 4,
                "title": "An Eternal Legend",
                "speaker": "Lead Narrator",
                "voice": "david-attenborough",
                "narration": "Whether a moral allegory or a submerged historical truth, Atlantis remains humanity's greatest reminder: that even the mightiest empires can vanish beneath the tides of time.",
                "visual_prompt": "Panoramic sunset over the endless deep ocean, calm glittering waves reflecting golden sunlight, ethereal outline of an ancient sunken city faintly visible beneath translucent crystal water",
                "camera_motion": "pan_left"
            }
        ]
    },
    "The James Webb Cosmic Journey: Edge of the Universe": {
        "title": "The James Webb Cosmic Journey: Edge of the Universe",
        "category": "Space Exploration & Astrophysics",
        "default_voice": "astronomer-carl",
        "default_style": "Space & Cosmic Odyssey",
        "scenes": [
            {
                "scene_num": 1,
                "title": "The Golden Eye of Humanity",
                "speaker": "Astrophysicist Narrator",
                "voice": "astronomer-carl",
                "narration": "One million miles from Earth, hanging suspended in the cold vacuum of space, humanity's greatest optical marvel unfolded its eighteen beryllium-gold mirrors.",
                "visual_prompt": "James Webb Space Telescope floating majestically in deep space at L2 Lagrange point, golden hexagonal mirrors reflecting the distant sun and Earth, deep cosmic background of stars and nebulae, photorealistic 8k",
                "camera_motion": "zoom_in"
            },
            {
                "scene_num": 2,
                "title": "Piercing the Cosmic Dawn",
                "speaker": "Astrophysicist Narrator",
                "voice": "astronomer-carl",
                "narration": "Peering through dense clouds of interstellar dust with infrared vision, Webb captured the first primordial galaxies born just three hundred million years after the Big Bang.",
                "visual_prompt": "Deep space field showing glowing spiral galaxies, colorful cosmic dust, swirling stellar nurseries glowing in vibrant infrared crimson and gold, ultra high definition deep field",
                "camera_motion": "zoom_out"
            },
            {
                "scene_num": 3,
                "title": "The Pillars of Creation Reborn",
                "speaker": "Lead Narrator",
                "voice": "morgan-freeman",
                "narration": "Within the Eagle Nebula, towering columns of cold hydrogen gas and dust continue to birth newborn stars, sculpting cosmic cathedrals across trillions of miles.",
                "visual_prompt": "Iconic Pillars of Creation in Eagle Nebula rendered in breathtaking infrared detail, towering fingers of celestial gas illuminated by newborn blue stars, glowing edges, majestic cosmic scale",
                "camera_motion": "pan_right"
            },
            {
                "scene_num": 4,
                "title": "Looking Back into Infinity",
                "speaker": "Astrophysicist Narrator",
                "voice": "astronomer-carl",
                "narration": "Every photon captured by this golden observatory is a message from the deep past—proving that we are the cosmos experiencing itself, gazing back at the dawn of existence.",
                "visual_prompt": "A breathtaking cosmic view from the edge of the universe, billions of interconnected galactic filaments resembling neural networks, brilliant bursts of light in the infinite void",
                "camera_motion": "zoom_in"
            }
        ]
    },
    "The Secrets of the Deep: Earth's Final Frontier": {
        "title": "The Secrets of the Deep: Earth's Final Frontier",
        "category": "Nature & Marine Biology",
        "default_voice": "david-attenborough",
        "default_style": "Cinematic Photorealism (Universal)",
        "scenes": [
            {
                "scene_num": 1,
                "title": "Beyond the Sunlit Shallows",
                "speaker": "Lead Narrator",
                "voice": "david-attenborough",
                "narration": "We know more about the craters on the moon than the abyssal trenches of our own planet. Below two hundred meters, the last rays of sunlight fade, giving way to the Midnight Zone.",
                "visual_prompt": "Sunlight fading into deep indigo and black ocean water, silhouette of a whale diving into the deep abyss, shimmering surface far above, eerie beautiful marine atmosphere, 8k",
                "camera_motion": "zoom_out"
            },
            {
                "scene_num": 2,
                "title": "Living Lights of the Abyss",
                "speaker": "Marine Biologist",
                "voice": "cinematic-jenny",
                "narration": "In total darkness, life creates its own illumination. Bizarre siphonophores, glowing jellyfish, and deep-sea anglers pulse with bioluminescent neon hues.",
                "visual_prompt": "Bioluminescent deep sea creatures glowing with vibrant sapphire, emerald, and violet lights against pitch black abyssal waters, transparent floating jellyfish, macro detail, cinematic lighting",
                "camera_motion": "zoom_in"
            },
            {
                "scene_num": 3,
                "title": "The Mariana Trench",
                "speaker": "Lead Narrator",
                "voice": "david-attenborough",
                "narration": "At nearly thirty-six thousand feet deep in the Mariana Trench, the pressure exceeds eight tons per square inch. Yet even here, life thrives along hydrothermal vents.",
                "visual_prompt": "Black smoker hydrothermal vent erupting mineral-rich hot plumes on the deep seafloor, deep sea robotic rover scanning giant tube worms and ghost white crabs, cinematic contrast",
                "camera_motion": "pan_left"
            },
            {
                "scene_num": 4,
                "title": "The Heart of Our World",
                "speaker": "Lead Narrator",
                "voice": "david-attenborough",
                "narration": "The deep ocean holds ninety-five percent of Earth's living space—a vast, silent kingdom that regulates our climate and guards the greatest mysteries of life.",
                "visual_prompt": "Serene wide ocean landscape with underwater coral reef glowing under twilight water, shafts of soft moonlight penetrating the crystal waves, peaceful cinematic masterpiece",
                "camera_motion": "zoom_in"
            }
        ]
    }
}


class StoryArchitect:
    def __init__(self, gateway: Optional[FreeLLMAPIGateway] = None):
        self.gateway = gateway or FreeLLMAPIGateway()

    def generate_script(
        self,
        topic: str,
        target_scenes: int = 4,
        voice_id: str = "david-attenborough",
        style_name: str = "Cinematic Photorealism (Universal)",
        genre: str = "Historical Documentary"
    ) -> Dict[str, Any]:
        """
        Plans and generates a cinematic documentary script using FreeLLMAPI.
        Falls back to heuristic architecture if offline.
        """
        clean_topic = topic.strip()

        system_prompt = (
            "You are an elite BBC Natural History and National Geographic documentary filmmaker and scriptwriter. "
            "Write an evocative, award-winning documentary script based on the user's prompt. "
            "CRITICAL: You must return ONLY raw valid JSON without markdown codeblocks or extra text. "
            "JSON structure:\n"
            "{\n"
            '  "title": "Captivating Documentary Title",\n'
            '  "category": "Genre / Theme",\n'
            '  "scenes": [\n'
            "    {\n"
            '      "scene_num": 1,\n'
            '      "title": "Chapter 1: The Title",\n'
            '      "speaker": "Lead Narrator",\n'
            f'      "voice": "{voice_id}",\n'
            '      "narration": "Poetic, engaging 2-3 sentence narration for this scene.",\n'
            '      "visual_prompt": "Highly detailed 8k cinematic photorealistic prompt describing lighting, camera lens, mood, and environment.",\n'
            '      "camera_motion": "zoom_in | zoom_out | pan_left | pan_right"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Topic: {clean_topic}\n"
            f"Number of Scenes: {target_scenes}\n"
            f"Genre / Tone: {genre}\n"
            f"Visual Style: {style_name}\n\n"
            f"Produce exactly {target_scenes} sequential scenes that build narrative tension from beginning to resolution."
        )

        try:
            raw_response = self.gateway.chat_complete(system_prompt, user_prompt, model="auto:smart")
            parsed = self._extract_json(raw_response)
            if parsed and "scenes" in parsed and len(parsed["scenes"]) > 0:
                parsed["default_voice"] = voice_id
                parsed["default_style"] = style_name
                logger.info(f"Successfully generated documentary script for '{clean_topic}' with {len(parsed['scenes'])} scenes.")
                return parsed
        except Exception as e:
            logger.warning(f"FreeLLMAPI script generation failed ({e}). Using intelligent heuristic fallback.")

        # Heuristic fallback
        return self._generate_heuristic(clean_topic, target_scenes, voice_id, style_name, genre)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON object from raw LLM output."""
        try:
            # Strip markdown formatting
            cleaned = re.sub(r"^```(json)?", "", text.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            
            # Find outermost braces
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start:end+1])
        except Exception:
            pass
        return None

    def _generate_heuristic(
        self,
        topic: str,
        target_scenes: int,
        voice_id: str,
        style_name: str,
        genre: str
    ) -> Dict[str, Any]:
        """Deterministic high-quality cinematic script generator for offline operation."""
        title = topic.title()
        templates = [
            ("The Genesis & The World Before", "zoom_in",
             f"For generations, {title} remained an enigma—an elusive chapter in the grand tapestry of our world. To uncover its truth, we must journey back to where the legend first emerged.",
             f"Cinematic establishing wide shot of {title}, dramatic golden sunrise horizon, volumetric god rays, majestic cinematic atmosphere, 8k documentary photograph"),
            ("The Turning Point of Discovery", "pan_right",
             f"As explorers and researchers probed deeper into {title}, shocking discoveries challenged conventional wisdom, sparking debates that resonated across continents.",
             f"Intense detailed cinematic shot illustrating the mysteries of {title}, moody chiaroscuro lighting, historic textures, 35mm film grain aesthetic"),
            ("The Revelation Beneath the Surface", "zoom_out",
             f"Modern investigations have revealed intricate secrets hidden within {title}, shedding light on aspects of human history and science that time had almost forgotten.",
             f"Macro breathtaking visual exploration of {title}, crystalline details, cinematic color grading, atmospheric depth of field, National Geographic style"),
            ("The Enduring Legacy", "pan_left",
             f"Today, {title} endures as a powerful testament to our collective curiosity—an immortal reminder of the mysteries that continue to shape our universe.",
             f"Panoramic sunset over the horizon reflecting the profound legacy of {title}, soft golden reflections on water, serene and epic cinematic composition")
        ]

        scenes = []
        for i in range(min(target_scenes, len(templates))):
            tmpl = templates[i]
            scenes.append({
                "scene_num": i + 1,
                "title": f"Chapter {i + 1}: {tmpl[0]}",
                "speaker": "Lead Narrator",
                "voice": voice_id,
                "narration": tmpl[2],
                "visual_prompt": tmpl[3],
                "camera_motion": tmpl[1]
            })

        return {
            "title": f"{title}: An Untold Chronicle",
            "category": genre,
            "default_voice": voice_id,
            "default_style": style_name,
            "scenes": scenes
        }
