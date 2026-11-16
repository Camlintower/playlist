import os
import shutil
import requests
import re

def get_clips(keyword: str, count: int = 5, pexels_key: str = None, source: str = "Pexels") -> list[str]:
    output_dir = "clips"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    downloaded_clips = []
    
    if source == "Pixabay":
        print(f"[Scraper] Querying Pixabay for: '{keyword}'...")
        
        def fetch_pixabay(q: str) -> list[str]:
            q_formatted = q.replace(' ', '+')
            url = f"https://pixabay.com/videos/search/{q_formatted}/"
            try:
                req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                if req.status_code == 200:
                    return list(set(re.findall(r'https://cdn\.pixabay\.com/video/[^"]+\.mp4', req.text)))
            except:
                pass
            return []
            
        links = fetch_pixabay(keyword)
        
        # If full complex query fails, split the keywords and pool clips!
        if not links:
            print("[Scraper] Full query yielded 0 results. Pooling clips from individual keywords...")
            words = keyword.split()
            for w in words:
                if len(w) > 2:
                    w_links = fetch_pixabay(w)
                    for l in w_links:
                        if l not in links:
                            links.append(l)
                    if len(links) >= count:
                        break
                        
        for i, link in enumerate(links[:count]):
            clip_path = os.path.join(output_dir, f"clip_{i}.mp4")
            try:
                with requests.get(link, stream=True) as r, open(clip_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                downloaded_clips.append(clip_path)
            except Exception as e:
                print(f"[Scraper] Error downloading Pixabay clip: {e}")
            
    if not downloaded_clips and pexels_key:
        print("[Scraper] Querying Pexels API...")
        
        # Pexels requires shorter tag-like queries, so we use just the base keyword if NLP made it too long
        query = keyword if len(keyword.split()) <= 4 else " ".join(keyword.split()[:2])
        headers = {"Authorization": pexels_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}&orientation=portrait"
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
                for i, video in enumerate(videos):
                    video_files = video.get("video_files", [])
                    hd_files = [f for f in video_files if f.get("quality") == "hd"]
                    target_file = hd_files[0] if hd_files else (video_files[0] if video_files else None)
                    if target_file:
                        link = target_file.get("link")
                        clip_path = os.path.join(output_dir, f"fallback_clip_{i}.mp4")
                        with requests.get(link, stream=True) as r, open(clip_path, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                        downloaded_clips.append(clip_path)
        except Exception as e:
            print(f"[Scraper] Pexels API Error: {e}")
            
    print(f"[Scraper] Successfully fetched {len(downloaded_clips)} clips total.")
    return downloaded_clips

if __name__ == "__main__":
    pass
