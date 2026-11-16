import streamlit as st
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from main import generate_reel
from src.subtitle_styles import get_available_fonts

st.set_page_config(page_title="Reel Generator", page_icon="🎬", layout="wide")

st.title("🎬 Aesthetic Reel Generator")
st.markdown("Turn any song into a high-quality vertical aesthetic reel.")

with st.form("reel_form"):
    url = st.text_input("🔗 Song URL (YouTube / SoundCloud)", placeholder="https://youtu.be/...")
    song_title_override = st.text_input("🎵 Song Title (For Lyrics Search)", placeholder="e.g., The Weeknd - Starboy (Leave blank to auto-detect)")
    
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.text_input("⏳ Start Time (Optional)", placeholder="e.g., 01:15")
    with col2:
        end_time = st.text_input("⌛ End Time (Optional)", placeholder="e.g., 01:45")
        
    col3, col4, col_size = st.columns([2, 1, 1])
    with col3:
        filter_style = st.selectbox("🎨 Filter", ["None", "Vintage Grain", "Cinematic Dark"])
    with col4:
        video_ratio = st.selectbox("📱 Output Ratio", ["9:16 (Vertical/Reels)", "1:1 (Square)", "16:9 (Landscape)"])
    with col_size:
        aesthetic_override = st.selectbox("📂 Aesthetic", ["pinterest_edit_clips", "Auto-Detect (NLP)", "dark_grunge", "retro_vhs", "cyber_neon", "nature_moody"])
        
    st.markdown("### 📝 Typography Settings")
    t_col1, t_col_btn, t_col2, t_col3 = st.columns([3, 1, 3, 3])
    
    with t_col1:
        font_name = st.selectbox("🔤 Font", get_available_fonts())
    with t_col_btn:
        st.write("")
        st.write("")
        refresh_btn = st.form_submit_button("🔄 Refresh")
    with t_col2:
        size_preset = st.selectbox("📏 Size", ["Small (25%)", "Medium (50%)", "Fill (75%)"], index=1)
    with t_col3:
        layout_mode = st.selectbox("📐 Layout", ["1-Word Pop", "2-3 Word Chunk", "Full Sentence Wrap"], index=1)
        
    # Live Font Preview
    font_url = font_name.replace(" ", "+")
    css_class = f"font-preview-{font_url.replace('+', '-')}"
    preview_html = f"""
    <link href="https://fonts.googleapis.com/css2?family={font_url}&display=swap" rel="stylesheet">
    <style>
    .{css_class} {{
        font-family: '{font_name}', sans-serif;
        font-size: 40px;
        text-align: center;
        padding: 20px;
        background: #1e1e1e;
        color: white;
        border-radius: 8px;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px #000;
        border: 1px solid #333;
    }}
    </style>
    <div class="{css_class}">{font_name}</div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)
    
    submit = st.form_submit_button("✨ Generate Reel", type="primary", use_container_width=True)
    
if submit:
    if not url:
        st.error("Please enter a URL.")
    else:
        # Validate timestamps
        valid_times = True
        if start_time and end_time:
            def time_to_sec(t_str):
                t_str = t_str.replace('.', ':')
                parts = t_str.split(':')
                if len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
                elif len(parts) == 2: return int(parts[0])*60 + float(parts[1])
                return float(t_str)
            try:
                if time_to_sec(end_time) <= time_to_sec(start_time):
                    st.error("⚠️ Error: End Time must be greater than Start Time!")
                    valid_times = False
            except:
                pass
                
        if valid_times:
            with st.spinner("Generating reel... this may take a minute."):
                try:
                    output_video = generate_reel(
                        url=url, 
                        song_title_override=song_title_override if song_title_override else None,
                        start_time=start_time if start_time else None,
                        end_time=end_time if end_time else None,
                        font_name=font_name,
                        size_preset=size_preset,
                        layout_mode=layout_mode,
                        filter_style=filter_style,
                        video_ratio=video_ratio,
                        aesthetic_override=aesthetic_override
                    )
                    
                    st.success(f"Reel Generated Successfully: `{os.path.basename(output_video)}`")
                    st.video(output_video)
                    
                    with open(output_video, "rb") as file:
                        video_bytes = file.read()
                        st.download_button(
                            label="⬇️ Download Generated Reel",
                            data=video_bytes,
                            file_name=os.path.basename(output_video),
                            mime="video/mp4",
                            type="primary",
                            use_container_width=True
                        )
                except Exception as e:
                    import traceback
                    st.error(f"An error occurred: {e}")
                    st.code(traceback.format_exc())
