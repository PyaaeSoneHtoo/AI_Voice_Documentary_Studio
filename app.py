"""
AI Voice Documentary Studio — Main Web Application
Combines FreeLLMAPI (token intelligence) and VoiceStudio (voice cloning/TTS) for end-to-end documentary production.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from PIL import Image

import config
from core.llm_gateway import FreeLLMAPIGateway
from core.voice_studio_client import VoiceStudioClient, NARRATOR_PRESETS
from core.story_architect import StoryArchitect, DOCUMENTARY_PRESETS
from core.visual_engine import VisualEngine, STYLE_PRESETS
from core.audio_library import BGM_TRACKS
from core.pipeline import run_documentary_pipeline

# ── Streamlit Page Configuration ──
st.set_page_config(
    page_title="AI Voice Documentary Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .badge-online {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-fallback {
        background-color: #451a03;
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }
    .scene-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "current_script" not in st.session_state:
    st.session_state.current_script = DOCUMENTARY_PRESETS["The Lost City of Atlantis: Submerged Secrets"]

if "rendered_result" not in st.session_state:
    st.session_state.rendered_result = None

# Initialize Clients
llm_gateway = FreeLLMAPIGateway()
voice_client = VoiceStudioClient()
story_architect = StoryArchitect(gateway=llm_gateway)

# Health Checks
llm_online, llm_msg = llm_gateway.check_health()
voice_online, voice_msg = voice_client.check_health()

# Header
st.markdown('<div class="main-title">🎬 AI Voice Documentary Studio</div>', unsafe_allow_html=True)
st.caption("Powered by **FreeLLMAPI** (87+ Free LLM Providers) & **VoiceStudio** (Zero-Shot Voice Cloning & Audio Engine)")

# Status Pills
col_s1, col_s2, col_s3 = st.columns([1, 1, 1.5])
with col_s1:
    if llm_online:
        st.markdown(f'<div class="badge-online">🧠 FreeLLMAPI: {llm_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="badge-fallback">🧠 FreeLLMAPI: Offline (Direct/Heuristic)</div>', unsafe_allow_html=True)

with col_s2:
    if voice_online:
        st.markdown(f'<div class="badge-online">🎙️ VoiceStudio: {voice_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="badge-fallback">🎙️ Voice Engine: Edge-TTS Active</div>', unsafe_allow_html=True)

with col_s3:
    st.markdown('<div style="color: #94a3b8; font-size: 0.85rem; padding-top: 4px;">Zero API Cost · 1080p Cinema Video · Voice Cloning</div>', unsafe_allow_html=True)

st.divider()

# ── Sidebar Controls ──
with st.sidebar:
    st.header("⚙️ Studio Settings")
    
    st.subheader("1. Topic & Preset")
    preset_choice = st.selectbox(
        "Choose Preset or Custom:",
        ["Custom Topic..."] + list(DOCUMENTARY_PRESETS.keys())
    )
    
    custom_topic = ""
    if preset_choice == "Custom Topic...":
        custom_topic = st.text_input("Enter Documentary Topic:", "The Secrets of the Samurai in Feudal Japan")
        num_scenes = st.slider("Number of Scenes:", 2, 6, 4)
    else:
        st.session_state.current_script = DOCUMENTARY_PRESETS[preset_choice]
        num_scenes = len(st.session_state.current_script["scenes"])

    st.subheader("2. Narrator & Voice Cloning")
    available_voices = voice_client.get_available_voices()
    voice_options = {v["name"]: v["id"] for v in available_voices}
    selected_voice_name = st.selectbox("Select Narrator Voice:", list(voice_options.keys()))
    selected_voice_id = voice_options[selected_voice_name]

    # Voice Cloning Upload
    with st.expander("🎙️ Clone a New Voice"):
        st.caption("Upload a 5–30s clean voice sample (.wav) to create an instant VoiceStudio clone:")
        uploaded_voice = st.file_uploader("Upload reference audio:", type=["wav", "mp3"])
        if uploaded_voice:
            clone_name = st.text_input("Voice Name (e.g., my_voice):", "custom_clone")
            if st.button("Save & Clone Voice"):
                save_path = config.VOICES_DIR / f"{clone_name.strip().lower().replace(' ', '_')}.wav"
                with open(save_path, "wb") as f:
                    f.write(uploaded_voice.read())
                st.success(f"Voice saved to assets/voices! Refreshing...")
                st.rerun()

    st.subheader("3. Visual Style & Aspect Ratio")
    style_choice = st.selectbox("Cinematic Visual Style:", list(STYLE_PRESETS.keys()))
    aspect_choice = st.selectbox("Aspect Ratio:", list(config.ASPECT_RATIOS.keys()))

    st.subheader("4. Background Music")
    bgm_options = {b["name"]: b["id"] for b in BGM_TRACKS}
    selected_bgm_name = st.selectbox("Soundtrack:", list(bgm_options.keys()))
    selected_bgm_id = bgm_options[selected_bgm_name]
    bgm_vol = st.slider("BGM Volume Ducking:", 0.0, 0.4, 0.12, 0.02)

    st.divider()
    with st.expander("🔧 Advanced Gateway Endpoints"):
        st.text_input("FreeLLMAPI Base URL:", config.FREELLMAPI_BASE_URL, disabled=True)
        st.text_input("VoiceStudio Base URL:", config.VOICESTUDIO_BASE_URL, disabled=True)


# ── Main Tabs ──
tab1, tab2, tab3 = st.tabs(["📜 Script & Scene Planner", "🖼️ Visual & Voice Previews", "🚀 Video Production"])

# TAB 1: SCRIPT PLANNER
with tab1:
    st.subheader("Documentary Narrative & Script")
    
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("✨ Generate with FreeLLMAPI", use_container_width=True, type="primary"):
            target_topic = custom_topic if preset_choice == "Custom Topic..." else preset_choice
            with st.spinner("FreeLLMAPI is orchestrating your documentary script..."):
                script = story_architect.generate_script(
                    topic=target_topic,
                    target_scenes=num_scenes,
                    voice_id=selected_voice_id,
                    style_name=style_choice
                )
                st.session_state.current_script = script
                st.success("Script generated successfully!")
                st.rerun()

    st.markdown(f"### **{st.session_state.current_script.get('title', 'Documentary Title')}**")
    st.caption(f"Category: {st.session_state.current_script.get('category', 'General')}")

    # Display editable scenes
    scenes = st.session_state.current_script.get("scenes", [])
    for idx, scene in enumerate(scenes):
        with st.container():
            st.markdown(f'<div class="scene-card">', unsafe_allow_html=True)
            col_c1, col_c2 = st.columns([1, 4])
            with col_c1:
                st.markdown(f"**Scene {scene.get('scene_num', idx+1)}**")
                st.caption(f"Motion: `{scene.get('camera_motion', 'zoom_in')}`")
                st.caption(f"Speaker: {scene.get('speaker', 'Lead Narrator')}")
            with col_c2:
                scene["title"] = st.text_input(f"Title (Scene {idx+1})", scene.get("title", ""), key=f"title_{idx}")
                scene["narration"] = st.text_area(f"Narration Script (Scene {idx+1})", scene.get("narration", ""), key=f"narr_{idx}", height=75)
                scene["visual_prompt"] = st.text_area(f"Visual Generation Prompt (Scene {idx+1})", scene.get("visual_prompt", ""), key=f"vis_{idx}", height=65)
            st.markdown("</div>", unsafe_allow_html=True)


# TAB 2: VISUAL & VOICE PREVIEWS
with tab2:
    st.subheader("Scene Visuals & Voiceover Previews")
    st.caption("Inspect and test individual scene assets before full rendering:")

    for idx, scene in enumerate(st.session_state.current_script.get("scenes", [])):
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            st.markdown(f"#### Scene {idx+1}: {scene.get('title', '')}")
            st.write(scene.get("narration", ""))
            
            # Instant Voice Preview Button
            if st.button(f"🔊 Preview Voiceover (Scene {idx+1})", key=f"btn_audio_{idx}"):
                with st.spinner("Synthesizing audio..."):
                    preview_audio = config.TEMP_DIR / f"preview_scene_{idx+1}.mp3"
                    voice_client.generate_narration(scene.get("narration", ""), selected_voice_id, preview_audio)
                    st.audio(str(preview_audio))
        
        with col_p2:
            # Instant Image Preview Button
            if st.button(f"🎨 Generate Image Preview (Scene {idx+1})", key=f"btn_img_{idx}"):
                with st.spinner("Rendering visual prompt with FLUX..."):
                    vis_engine = VisualEngine()
                    preview_img = vis_engine.generate_scene_image(
                        scene.get("visual_prompt", ""),
                        scene_num=idx+1,
                        style_name=style_choice,
                        aspect_ratio_key=aspect_choice
                    )
                    st.image(str(preview_img), use_container_width=True)


# TAB 3: VIDEO PRODUCTION
with tab3:
    st.subheader("Final Video Production")
    st.write("Render the complete documentary: synchronizes speech, applies Ken Burns motion, ducks background music, and encodes full MP4.")

    if st.button("🎬 Render Full Documentary Video", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def on_progress(stage: str, prog: float, msg: str):
            progress_bar.progress(prog)
            status_text.info(f"**[{stage}]** {msg}")

        try:
            result = run_documentary_pipeline(
                script=st.session_state.current_script,
                visual_style=style_choice,
                aspect_ratio=aspect_choice,
                default_voice=selected_voice_id,
                bgm_track=selected_bgm_id,
                bgm_volume=bgm_vol,
                progress_callback=on_progress
            )
            st.session_state.rendered_result = result
            st.success(f"🎉 Production Complete in {result['elapsed_seconds']:.1f} seconds!")
        except Exception as err:
            st.error(f"Render failed: {err}")

    # Video Player
    if st.session_state.rendered_result:
        res = st.session_state.rendered_result
        video_file = res["video_path"]
        
        st.divider()
        st.subheader("📽️ Finished Documentary")
        st.video(video_file)

        col_d1, col_d2 = st.columns([1, 3])
        with col_d1:
            with open(video_file, "rb") as f:
                st.download_button(
                    label="⬇️ Download MP4 Video",
                    data=f,
                    file_name=Path(video_file).name,
                    mime="video/mp4",
                    type="primary"
                )
        with col_d2:
            st.caption(f"Duration: {res['total_duration']:.1f}s | Scenes: {res['scenes_count']} | Path: `{video_file}`")
