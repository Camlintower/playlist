import os
import requests

def download_fonts():
    # Base directory for fonts
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    
    # Mapping of exact Github raw URLs for TTF files
    fonts_to_download = {
        "PermanentMarker-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/apache/permanentmarker/PermanentMarker-Regular.ttf",
        "Pacifico-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/pacifico/Pacifico-Regular.ttf",
        "BebasNeue-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf",
        "SedgwickAveDisplay-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/sedgwickavedisplay/SedgwickAveDisplay-Regular.ttf",
        "Anton-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf",
        "VastShadow-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/vastshadow/VastShadow-Regular.ttf",
        "BowlbyOne-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/bowlbyone/BowlbyOne-Regular.ttf",
        "ComicRelief.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/comicrelief/ComicRelief.ttf",
        "SpecialElite-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/apache/specialelite/SpecialElite-Regular.ttf",
        "LavishlyYours-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/lavishlyyours/LavishlyYours-Regular.ttf",
        "Notable-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notable/Notable-Regular.ttf",
        "RockSalt-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/apache/rocksalt/RockSalt-Regular.ttf",
        "JimNightshade-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/jimnightshade/JimNightshade-Regular.ttf",
        "Bangers-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/bangers/Bangers-Regular.ttf",
        "Oswald-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/static/Oswald-Regular.ttf"
    }
    
    print(f"Downloading fonts to {fonts_dir}...")
    for filename, url in fonts_to_download.items():
        filepath = os.path.join(fonts_dir, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Successfully downloaded {filename}")
                else:
                    print(f"Failed to download {filename} (Status: {response.status_code}). URL: {url}")
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
        else:
            print(f"{filename} already exists. Skipping.")
            
if __name__ == "__main__":
    download_fonts()
