# Automated Aesthetic Video Pipeline - Project History & Architecture

This document serves as a comprehensive record of the development journey, technical decisions, architectures tested, and future roadmaps for the Automated Aesthetic Video Generator project.

---

## 1. Project Goal
To build a fully automated Python pipeline that takes a YouTube song URL and automatically generates a short-form, highly aesthetic vertical video (Reel/TikTok/Short) featuring:
- Time-synced lyrics with dynamic animations (ASS subtitles).
- A sequence of aesthetic background video clips perfectly cut to match the vocal boundaries of the lyrics.
- Dynamic visual searches based on the thematic mood of the song's lyrics.

---

## 2. Core Architecture Pipeline
The current working pipeline executes in the following sequence:

1. **Audio Extraction (`audio_extractor.py`)**: Uses `yt-dlp` to download the best audio from the provided YouTube link and optionally trims it using `ffmpeg`. (Fixed Windows `PermissionError` by saving to a new `_trimmed.mp3` file rather than replacing the locked file).
2. **Transcription & Sync (`transcriber.py`)**: Uses the `syncedlyrics` library to fetch verified time-synced `.lrc` lyrics from Spotify/Musixmatch. It converts these timestamps into precise sentence-level boundaries.
3. **NLP Vibe Extraction (`nlp_processor.py`)**: Analyzes the raw text of the lyrics, strips out common stop words, and determines the top thematic keywords (e.g., "monster", "redemption").
4. **Visual Scraper (`scraper.py`)**: Searches and downloads vertical stock video clips matching the user's base keyword combined with the NLP-extracted vibe.
5. **Subtitle Styling (`subtitle_styles.py`)**: Uses `pysubs2` to generate an `.ass` (Advanced SubStation Alpha) subtitle file. Supports multiple highly customized font styles, primary/secondary colors, drop shadows, and Karaoke timing effects.
6. **Video Assembly (`video_assembler.py`)**: Uses `moviepy` to stitch the downloaded background clips together. The clips are precisely cut at the exact timestamps where the lyric sentences change, rather than at random intervals. Finally, `ffmpeg` burns the `.ass` subtitles onto the video.

---

## 3. Video Scraping: Approaches & Outcomes

A significant portion of development was dedicated to finding the highest quality source for aesthetic, edgy, and retro visual clips. We tried multiple sources, facing heavy anti-bot security:

### ❌ Pinterest (Playwright Web Scraping)
- **Goal:** Scrape Pinterest for "aesthetic retro rock" videos, as Pinterest has the best user-curated content.
- **Approach 1 (Basic Headless):** Blocked by a mandatory login wall overlay that prevented search result loading.
- **Approach 2 (Automated Login):** Attempted to use Playwright to type in username and password. Pinterest detected the headless browser and permanently disabled (grayed-out) the "Log in" button.
- **Approach 3 (Session Cookie Injection):** Passed the user's live `_pinterest_sess` cookie from their actual browser into the Playwright context. Pinterest still flagged the session mismatch and threw a hard wall.
- **Conclusion:** Pinterest API v5 explicitly forbids mass media downloading, and their frontend is heavily guarded by Cloudflare/bot-detection. Abandoned.

### ❌ YouTube Shorts (`yt-dlp`)
- **Goal:** Use `ytsearch` to find "#shorts aesthetic edits".
- **Outcome:** The dynamic NLP search queries (e.g., "monster searching redemption whos") were too complex for YouTube, yielding 0 results. When simplified, the downloaded clips were often low-quality, contained streamers, or already had baked-in text lyrics.
- **Conclusion:** Unreliable video quality and style. Removed from app.

### ❌ Pixabay (Regex HTML Scraping)
- **Goal:** Scrape the free Pixabay video search pages directly using `requests` and RegEx.
- **Outcome:** Initially worked in isolated tests, but Pixabay recently upgraded their Cloudflare protection, resulting in a permanent `403 Forbidden` block for automated Python HTTP requests.

### ✅ Pexels API (Currently Active)
- **Goal:** Use the official Pexels API with an authorized API key.
- **Outcome:** Works flawlessly. Scrapes 20 HD, cinematic vertical clips. We implemented logic to automatically truncate complex NLP queries down to 2 words so the Pexels tagging engine doesn't fail.
- **Limitation:** While high-quality, Pexels is "stock footage" and lacks the edgy, heavily edited VHS/retro vibe found on Pinterest.

---

## 4. The Future Paradigm: Local Curated Clip Library
Due to the unreliability of web scraping and the "stock" nature of APIs, we brainstormed a professional architecture shift: **The Local Clip Library**.

### How it will work:
1. **Curated Folders:** The user downloads 100+ high-quality aesthetic clips manually (from Pinterest, TikTok, etc.) and categorizes them into local folders (e.g., `assets/clips/dark_grunge`, `assets/clips/neon_cyberpunk`).
2. **Semantic NLP Router:** The `nlp_processor.py` will be upgraded to analyze the lyrics and score them against predefined "Vibes". It will automatically select the local folder that best matches the song's emotion.
3. **Random Selection:** The pipeline will randomly select 20 unique clips from the chosen local folder and assemble them.

**Benefits:**
- **0% Failure Rate:** No network timeouts, 403 errors, or API rate limits.
- **Instant Speed:** Eliminates the 20-30 second wait time for downloading 20 video clips.
- **100% Quality Control:** Every clip in the final video is guaranteed to be perfectly on-brand and highly aesthetic because it was hand-picked by the user.

---

## 5. Next Steps
- Review the `implementation_plan.md` for the Local Clip Library transition.
- Refactor `scraper.py` into `local_library.py`.
- Upgrade `subtitle_styles.py` to support even more aggressive, chaotic typography animations (as requested by the user: "crazy animation fonts, letter tracking, wrapping").
