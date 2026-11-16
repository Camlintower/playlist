import re

# This dictionary maps keywords to specific local aesthetic folders.
# The NLP engine will score the lyrics against these lists.
AESTHETIC_CATEGORIES = {
    "dark_grunge": ["dark", "monster", "blood", "pain", "night", "fear", "shadow", "goth", "rock", "metal", "slave"],
    "retro_vhs": ["memory", "past", "time", "nostalgia", "vintage", "old", "love", "heart", "yesterday", "dream"],
    "cyber_neon": ["future", "neon", "city", "fast", "car", "drive", "night", "light", "speed", "cyber"],
    "nature_moody": ["rain", "forest", "tree", "river", "cloud", "storm", "sky", "fog", "mountain", "ocean"]
}

def determine_aesthetic(lyrics: str) -> str:
    """
    Analyzes lyrics and returns the name of the most strongly matched aesthetic folder.
    """
    lyrics_lower = lyrics.lower()
    
    # Strip out non-alphanumeric characters to count pure words
    words = re.findall(r'\b\w+\b', lyrics_lower)
    
    scores = {category: 0 for category in AESTHETIC_CATEGORIES.keys()}
    
    for word in words:
        for category, keywords in AESTHETIC_CATEGORIES.items():
            if word in keywords:
                scores[category] += 1
                
    # Find the category with the highest score
    best_match = max(scores, key=scores.get)
    
    # If no keywords matched, default to dark_grunge or retro_vhs
    if scores[best_match] == 0:
        print("[NLP] No strong aesthetic detected, defaulting to retro_vhs.")
        return "retro_vhs"
        
    print(f"[NLP] Aesthetic Scores: {scores}")
    print(f"[NLP] Selected Aesthetic: '{best_match}'")
    
    return best_match
def extract_keywords(lyrics: str) -> str:
    """
    Extracts 2-4 prominent, meaningful keywords from the lyrics for dynamic API searches.
    """
    stop_words = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", 
                  "is", "am", "are", "was", "were", "be", "being", "been", "do", "does", "did", 
                  "have", "has", "had", "a", "an", "the", "and", "but", "if", "or", "because", 
                  "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", 
                  "between", "into", "through", "during", "before", "after", "above", "below", 
                  "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", 
                  "further", "then", "once", "here", "there", "when", "where", "why", "how", 
                  "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", 
                  "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", 
                  "t", "can", "will", "just", "don", "should", "now", "wanna", "gonna", "gotta",
                  "like", "yeah", "oh", "ooh", "ah", "la", "know", "got", "let", "make", "take",
                  "see", "say", "come", "go", "want", "tell", "need", "feel", "think", "never", 
                  "always", "cause", "back", "time", "way", "day", "night", "life", "love", "baby"}
                  
    words = re.findall(r'\b[a-z]{3,}\b', lyrics.lower())
    meaningful_words = [w for w in words if w not in stop_words]
    
    from collections import Counter
    counts = Counter(meaningful_words)
    top_words = [word for word, count in counts.most_common(3)]
    
    if not top_words:
        return "aesthetic cinematic"
        
    keyword_str = " ".join(top_words) + " aesthetic"
    print(f"[NLP] Extracted dynamic search keywords: '{keyword_str}'")
    return keyword_str

if __name__ == "__main__":
    test_lyrics = "I wanna be your slave I wanna be your master"
    print(determine_aesthetic(test_lyrics))
    print(extract_keywords(test_lyrics))
