# How to Seed Your Local Library with Pinterest & TikTok

I have installed `yt-dlp` and `gallery-dl` in your virtual environment. You can use these powerful CLI tools to instantly clone entire boards or profiles into your local library.

## Option 1: Clone a Pinterest Board (`yt-dlp`)
If you find a public Pinterest board full of aesthetic edits (e.g., `https://www.pinterest.com/username/board-name/`), simply run:
```bash
.\venv\Scripts\yt-dlp -P "assets/clips/dark_grunge" "https://www.pinterest.com/username/board-name/"
```
*This will download every video on that board directly into your local folder!*

## Option 2: Clone a TikTok Profile (`gallery-dl`)
If you find a TikTok creator who posts great aesthetic clips, you can clone their entire profile:
```bash
.\venv\Scripts\gallery-dl --directory "assets/clips/cyber_neon" "https://www.tiktok.com/@username"
```

## How to use them with the Generator
Once you download clips into the `assets/clips/` subfolders, the **Semantic Vibe Router** (or the Aesthetic Override dropdown in the Streamlit UI) will instantly detect them and randomly stitch 20 of them together for your next reel!
