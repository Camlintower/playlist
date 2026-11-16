import os
import random

def get_local_clips(aesthetic_folder: str, count: int = 20) -> list[str]:
    """
    Reads video clips from a local aesthetic folder and returns a randomly sampled list.
    If the folder has fewer clips than requested, it repeats them to meet the count.
    """
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "clips", aesthetic_folder)
    
    if not os.path.exists(base_dir):
        print(f"[Local Library] Warning: Directory {base_dir} does not exist.")
        return []
        
    valid_extensions = ('.mp4', '.mov', '.mkv', '.webm')
    available_clips = [os.path.join(base_dir, f) for f in os.listdir(base_dir) if f.lower().endswith(valid_extensions)]
    
    if not available_clips:
        print(f"[Local Library] Error: No valid video clips found in {base_dir}.")
        return []
        
    print(f"[Local Library] Found {len(available_clips)} clips in '{aesthetic_folder}'.")
    
    selected_clips = []
    
    # Shuffle so every generation is unique
    random.shuffle(available_clips)
    
    # Fill the quota (gracefully loop if we run out of unique clips)
    while len(selected_clips) < count:
        for clip in available_clips:
            selected_clips.append(clip)
            if len(selected_clips) >= count:
                break
                
    print(f"[Local Library] Successfully selected {len(selected_clips)} clips for assembly.")
    return selected_clips
