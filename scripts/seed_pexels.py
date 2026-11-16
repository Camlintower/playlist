import os
import requests
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PEXELS_API_KEY
CATEGORIES = {
    "dark_grunge": ["dark aesthetic", "cyberpunk street", "grunge city"],
    "retro_vhs": ["vhs aesthetic", "80s retro", "grainy video"],
    "nature_moody": ["foggy forest", "rainy night", "dark clouds"],
    "cyber_neon": ["neon lights", "cyberpunk city", "synthwave"]
}

def seed_pexels():
    headers = {"Authorization": PEXELS_API_KEY}
    for folder, queries in CATEGORIES.items():
        save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "clips", folder)
        os.makedirs(save_dir, exist_ok=True)
        
        for query in queries:
            print(f"Fetching '{query}' for folder '{folder}'...")
            url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=15"
            try:
                response = requests.get(url, headers=headers).json()
                for video in response.get("videos", []):
                    # Grab highest quality mp4
                    video_files = video.get("video_files", [])
                    hd_files = [f for f in video_files if f.get("width", 0) >= 720]
                    if not hd_files:
                        continue
                    video_url = hd_files[0]["link"]
                    file_path = os.path.join(save_dir, f"pexels_{video['id']}.mp4")
                    
                    if not os.path.exists(file_path):
                        r = requests.get(video_url, stream=True)
                        with open(file_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                        print(f"  Downloaded: {file_path}")
            except Exception as e:
                print(f"Error fetching Pexels query '{query}': {e}")

if __name__ == "__main__":
    seed_pexels()
