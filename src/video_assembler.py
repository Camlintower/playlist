import os
import subprocess
import random
import shutil

def get_ffmpeg_binary():
    return shutil.which("ffmpeg") or os.path.abspath("ffmpeg.exe")

def get_ffprobe_binary():
    return shutil.which("ffprobe") or os.path.abspath("ffprobe.exe")

def get_video_duration(clip_path):
    ffprobe_exe = get_ffprobe_binary()
    cmd = [ffprobe_exe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", clip_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def assemble_video(audio_path: str, clip_paths: list[str], sentence_timings: list, output_path: str = "stitched_video.mp4", filter_style: str = "None", video_ratio: str = "9:16 (Vertical/Reels)"):
    print(f"Assembling video using FFmpeg (Filter: {filter_style}, Ratio: {video_ratio})...")
    
    if not clip_paths:
        raise ValueError("No video clips provided.")
        
    ffmpeg_exe = get_ffmpeg_binary()
    audio_duration = get_video_duration(audio_path)
    if audio_duration == 0.0:
        audio_duration = sentence_timings[-1][1] if sentence_timings else 30.0
    
    # We will pick cuts at sentence boundaries
    cut_points = [0.0]
    for start, _, _ in sentence_timings:
        # Prevent rapid-fire cuts less than 1.5 seconds
        if start - cut_points[-1] >= 1.5:
            cut_points.append(start)
            
    if cut_points[-1] < audio_duration:
        cut_points.append(audio_duration)
        
    temp_files = []
    clip_index = 0
    
    # Map ratio selection to FFmpeg scale/crop dimensions
    ratio_map = {
        "9:16 (Vertical/Reels)": (1080, 1920),
        "1:1 (Square)": (1080, 1080),
        "16:9 (Landscape)": (1920, 1080),
    }
    w, h = ratio_map.get(video_ratio, (1080, 1920))
    base_vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    
    if filter_style == "Vintage Grain":
        # Warm tint, noise, slight fade
        vf = f"{base_vf},colorchannelmixer=rr=1.1:gg=1.0:bb=0.9,noise=alls=8:allf=t,eq=brightness=-0.02:contrast=1.05:saturation=0.9"
    elif filter_style == "Cinematic Dark":
        # Moody, high contrast, low brightness
        vf = f"{base_vf},eq=brightness=-0.05:contrast=1.1:saturation=0.8"
    else:
        vf = base_vf
        
    for i in range(len(cut_points) - 1):
        start_time = cut_points[i]
        end_time = cut_points[i+1]
        duration = end_time - start_time
        
        source_clip = clip_paths[clip_index % len(clip_paths)]
        clip_index += 1
        
        temp_out = f"temp_seg_{i}.mp4"
        temp_files.append(temp_out)
        
        cmd = [
            ffmpeg_exe, "-y",
            "-i", source_clip,
            "-t", str(duration),
            "-an",
            "-r", "30",
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            temp_out
        ]
        
        print(f"Processing segment {i+1}/{len(cut_points)-1} with duration {duration}...")
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        except subprocess.CalledProcessError as e:
            print(f"FFMPEG ERROR on segment {i}: {e.stderr}")
            raise
        
    with open("segments.txt", "w") as f:
        for t in temp_files:
            f.write(f"file '{t}'\n")
            
    print("Concatenating segments...")
    concat_cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "segments.txt",
        "-i", audio_path,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    subprocess.run(concat_cmd, check=True)
    
    # Cleanup temp files
    for t in temp_files:
        if os.path.exists(t):
            os.remove(t)
    if os.path.exists("segments.txt"):
        os.remove("segments.txt")
        
    return output_path

def burn_subtitles(video_path: str, ass_path: str, final_output: str = "output_reel.mp4"):
    print(f"Burning subtitles from {ass_path} into {video_path}...")
    
    ffmpeg_exe = get_ffmpeg_binary()
    ass_path_escaped = os.path.basename(ass_path)
    
    # Use relative path to avoid FFmpeg choking on the "D:" colon in Windows absolute paths
    fonts_dir = "assets/fonts"
    
    command = [
        ffmpeg_exe, "-y", "-i", video_path, 
        "-vf", f"ass='{ass_path_escaped}':fontsdir='{fonts_dir}'", 
        "-c:v", "libx264", "-preset", "fast", "-c:a", "copy", 
        final_output
    ]
    
    subprocess.run(command, check=True)
    return final_output

if __name__ == "__main__":
    pass
