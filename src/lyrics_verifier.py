import re
import urllib.request
import urllib.parse
import json
import syncedlyrics

# CJK Unicode ranges: Chinese, Japanese, Korean characters
CJK_PATTERN = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')

def clean_song_query(query: str) -> str:
    """Cleans YouTube video title junk to ensure high match rate on lyrics databases."""
    # Remove parenthetical tags like (Official Video), [Music Video], etc.
    q = re.sub(r'[\(\[\{].*?[\)\]\}]', ' ', query)
    # Remove common video keywords
    q = re.sub(r'(?i)\b(official|music|video|audio|lyrics?|visualizer|remix|hd|4k|feat\.?|ft\.?)\b.*', ' ', q)
    return " ".join(q.split())

def fetch_from_lrclib(search_term: str) -> str:
    """Fetches synced lyrics from the open-source LRCLIB API."""
    try:
        url = f"https://lrclib.net/api/search?q={urllib.parse.quote(search_term)}"
        req = urllib.request.Request(url, headers={"User-Agent": "AestheticReelGenerator/1.0 (https://github.com/)"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and isinstance(data, list):
                for item in data:
                    synced = item.get("syncedLyrics")
                    if synced:
                        print(f"Found synced lyrics on LRCLIB: {item.get('trackName')} by {item.get('artistName')}")
                        return synced
    except Exception as e:
        print(f"LRCLIB search error: {e}")
    return None

def fetch_synced_lyrics(search_term: str) -> str:
    """Fetches LRC (time-synced lyrics) from LRCLIB, Spotify, and Musixmatch."""
    cleaned_query = clean_song_query(search_term)
    print(f"Searching verified lyrics for '{search_term}' (Cleaned: '{cleaned_query}')...")
    
    # 1. Primary: LRCLIB (Open-source, free, instant)
    lrc = fetch_from_lrclib(cleaned_query)
    if lrc:
        return lrc
        
    if cleaned_query != search_term:
        lrc = fetch_from_lrclib(search_term)
        if lrc:
            return lrc
            
    # 2. Secondary: Spotify & Musixmatch via syncedlyrics
    for provider in ["Spotify", "Musixmatch"]:
        try:
            lrc = syncedlyrics.search(cleaned_query, providers=[provider])
            if lrc:
                print(f"Successfully found time-synced lyrics from {provider}!")
                return lrc
        except Exception:
            pass
            
    # 3. Fallback: Any provider in syncedlyrics
    try:
        lrc = syncedlyrics.search(cleaned_query)
        if lrc:
            print("Successfully found time-synced lyrics (fallback provider).")
            return lrc
    except Exception:
        pass
        
    print("No exact synced lyrics found. Falling back to AI transcription.")
    return None

if __name__ == "__main__":
    pass
