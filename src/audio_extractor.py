import os
import subprocess
import yt_dlp
import librosa
import numpy as np

def download_audio(url: str, start_time: str = None, end_time: str = None, output_path: str = "audio_clip") -> str:
    """Downloads audio from a URL using yt-dlp."""
    print(f"Downloading audio from {url}...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}.%(ext)s',
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'vtt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'noplaylist': True,
    }
    
    # Try multiple browsers to find one with active YouTube cookies to bypass bot checks
    browsers = ['chrome', 'edge', 'firefox', 'brave', 'opera']
    success = False
    
    for browser in browsers:
        ydl_opts['cookiesfrombrowser'] = (browser,)
        print(f"Attempting to download audio using {browser} cookies...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            success = True
            break
        except Exception as e:
            print(f"Failed with {browser} cookies: {e}")
            
    if not success:
        # Final fallback without cookies
        print("All cookie attempts failed, trying without cookies...")
        if 'cookiesfrombrowser' in ydl_opts:
            del ydl_opts['cookiesfrombrowser']
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
    final_output = f"{output_path}.mp3"
    
    if start_time and end_time:
        print(f"Clipping audio from {start_time} to {end_time}...")
        trimmed_output = f"{output_path}_trimmed.mp3"
        import shutil
        ffmpeg_cmd = shutil.which("ffmpeg") or os.path.abspath("ffmpeg.exe")
        # Removing '-c copy' is critical here! Stream copying MP3s with -ss causes inaccurate cuts 
        # at frame boundaries, which completely knocks the precisely calculated subtitles out of sync.
        subprocess.run([ffmpeg_cmd, "-y", "-i", final_output, "-ss", start_time, "-to", end_time, trimmed_output], check=True)
        return trimmed_output
        
    return final_output

def extract_beat_times(audio_path: str) -> list[float]:
    """Extracts beat timestamps from an audio file using librosa."""
    print(f"Extracting beats from {audio_path}...")
    
    # Load audio
    y, sr = librosa.load(audio_path)
    
    # Track beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    
    # Convert frames to time
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    print(f"Detected tempo: {tempo[0] if isinstance(tempo, np.ndarray) else tempo} BPM")
    print(f"Extracted {len(beat_times)} beat timestamps.")
    
    return beat_times.tolist()

if __name__ == "__main__":
    pass
