import os
import argparse
import glob
import yt_dlp

# Import internal modules
from config import PEXELS_API_KEY
from src.audio_extractor import download_audio, extract_beat_times
from src.lyrics_verifier import fetch_synced_lyrics
from src.transcriber import transcribe_audio, parse_vtt_to_ass
from src.nlp_processor import determine_aesthetic
from src.local_library import get_local_clips
from src.video_assembler import assemble_video, burn_subtitles

def cleanup_old_reels(max_reels=3, pattern="output_reel_*.mp4"):
    """Maintains a First-In-First-Out (FIFO) queue of generated reels, keeping at most max_reels."""
    existing_reels = glob.glob(pattern)
    if len(existing_reels) >= max_reels:
        # Sort by creation / modification time (oldest first)
        existing_reels.sort(key=os.path.getmtime)
        # Delete excess oldest reels to ensure at most max_reels - 1 exist before creating a new one
        num_to_delete = len(existing_reels) - max_reels + 1
        for old_reel in existing_reels[:num_to_delete]:
            try:
                print(f"FIFO Cleanup: Removing oldest reel {old_reel}...")
                os.remove(old_reel)
            except Exception as e:
                print(f"Error removing {old_reel}: {e}")

def get_next_output_name(base_name="output_reel", ext=".mp4"):
    cleanup_old_reels(max_reels=3)
    counter = 1
    while True:
        filename = f"{base_name}_{counter}{ext}"
        if not os.path.exists(filename):
            return filename
        counter += 1

def cleanup_temp_files():
    print("Cleaning up temporary files...")
    files_to_delete = ["audio_clip.webm", "audio_clip.mp3", "audio_clip_trimmed.mp3", "lyrics.ass", "stitched_video.mp4"]
    for vtt in glob.glob("audio_clip*.vtt"):
        files_to_delete.append(vtt)
        
    for f in files_to_delete:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists("clips"):
        import shutil
        shutil.rmtree("clips")

def generate_reel(url: str, song_title_override: str = None, start_time: str = None, end_time: str = None, 
                  font_name: str = "Anton", size_preset: str = "Medium (50%)", layout_mode: str = "2-3 Word Chunk", 
                  filter_style: str = "None", video_ratio: str = "9:16 (Vertical/Reels)",
                  aesthetic_override: str = "Auto-Detect (NLP)"):
    
    print(f"\n--- Starting Generation for: {url} ---")
    
    # 1. Download Audio
    print("\n--- Step 1: Downloading audio ---")
    start_t = start_time.replace(".", ":") if start_time else None
    end_t = end_time.replace(".", ":") if end_time else None
    audio_path = download_audio(url, start_time=start_t, end_time=end_t)
    
    # 2. Transcribe Audio & Verify Lyrics
    print("\n--- Step 2: Processing Lyrics ---")
    song_title = "Unknown Song"
    
    if song_title_override:
        song_title = song_title_override
        print(f"Using manual song title override: {song_title}")
    else:
        print("Fetching song metadata...")
        ydl_opts = {
            'quiet': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web_creator', 'mweb']
                }
            }
        }
        browsers = ['firefox', 'chrome', 'edge']
        info = None
        
        if os.name == 'nt':
            for browser in browsers:
                ydl_opts['cookiesfrombrowser'] = (browser,)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        if info: break
                    except:
                        pass
                        
        if not info:
            if 'cookiesfrombrowser' in ydl_opts:
                del ydl_opts['cookiesfrombrowser']
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                except:
                    pass
                    
        if info:
            song_title = info.get('title', "Unknown")
            print(f"Detected song title: {song_title}")
            
    print("Extracting perfectly synced subtitles using Whisper AI and verifying with LRC...")
    lrc_text = fetch_synced_lyrics(song_title) if song_title != "Unknown Song" else None
    ass_path, sentence_timings = transcribe_audio(
        audio_path, 
        lrc_text=lrc_text, 
        font_name=font_name, 
        size_preset=size_preset, 
        layout_mode=layout_mode, 
        video_ratio=video_ratio, 
        start_offset=start_time
    )
    
    # Extract overall lyrics text for NLP processing
    full_lyrics = " ".join([t[2] for t in sentence_timings])
    
    if aesthetic_override == "Auto-Detect (NLP)":
        selected_aesthetic = determine_aesthetic(full_lyrics)
    else:
        selected_aesthetic = aesthetic_override
        print(f"[Override] Bypassing NLP. Forcing aesthetic: {selected_aesthetic}")
    
    # 3. Pull Visuals
    print(f"\n--- Step 3: Pulling aesthetic clips for '{selected_aesthetic}' ---")
    if selected_aesthetic == "pinterest_edit_clips":
        print(f"Using local clips from {selected_aesthetic} folder...")
        clip_paths = get_local_clips(selected_aesthetic, count=20)
    else:
        print("Using dynamic API to fetch clips on the fly...")
        from src.scraper import get_clips
        from config import PEXELS_API_KEY
        
        search_query = selected_aesthetic
        if aesthetic_override == "Auto-Detect (NLP)":
            from src.nlp_processor import extract_keywords
            search_query = extract_keywords(full_lyrics)
            print(f"NLP Extracted Search Query: {search_query}")
            
        clip_paths = get_clips(keyword=search_query, count=10, pexels_key=PEXELS_API_KEY, source="Pexels")
        
    if not clip_paths:
        raise Exception(f"Failed to find or download any video clips for '{selected_aesthetic}'!")
        
    # 4. Assemble Video
    print("\n--- Step 4: Assembling video and applying filters ---")
    stitched_video = assemble_video(audio_path, clip_paths, sentence_timings, filter_style=filter_style, video_ratio=video_ratio)
    
    # 5. Burn Subtitles
    print("\n--- Step 5: Burning subtitles ---")
    final_output = get_next_output_name()
    burn_subtitles(stitched_video, ass_path, final_output)
    
    # 7. Cleanup
    cleanup_temp_files()
    
    print(f"\nDone! Final reel saved to: {os.path.abspath(final_output)}")
    return os.path.abspath(final_output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Reel Creator")
    parser.add_argument("--url", type=str, required=True, help="YouTube or SoundCloud URL")
    parser.add_argument("--start", type=str, default=None, help="Start time (e.g. 1.18 or 01:18)")
    parser.add_argument("--end", type=str, default=None, help="End time (e.g. 2.10 or 02:10)")
    parser.add_argument("--aesthetic", type=str, default="Auto-Detect (NLP)", help="Force aesthetic folder")
    args = parser.parse_args()
    
    generate_reel(args.url, start_time=args.start, end_time=args.end, aesthetic_override=args.aesthetic)
