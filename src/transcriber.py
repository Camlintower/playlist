import os
import re
from faster_whisper import WhisperModel
from src.subtitle_styles import get_style_config

def write_chunked_ass_lines(f, start_s: float, end_s: float, text: str, chunk_size: int, style_name: str, effect_func):
    """Interpolates line-level timestamps into word-level chunks for VTT/LRC."""
    words = text.split()
    if not words:
        return
        
    if len(words) <= chunk_size or chunk_size >= 5:
        dur_ms = int((end_s - start_s) * 1000)
        formatted_text = effect_func(text, dur_ms)
        f.write(f"Dialogue: 0,{format_ass_time(start_s)},{format_ass_time(end_s)},{style_name},,0,0,0,,{formatted_text}\n")
        return
        
    total_words = len(words)
    time_per_word = (end_s - start_s) / total_words
    
    for i in range(0, total_words, chunk_size):
        chunk = words[i:i+chunk_size]
        chunk_text = " ".join(chunk)
        
        chunk_start = start_s + (i * time_per_word)
        chunk_end = start_s + ((i + len(chunk)) * time_per_word)
        
        dur_ms = int((chunk_end - chunk_start) * 1000)
        if dur_ms <= 0: dur_ms = 100
        
        formatted_text = effect_func(chunk_text, dur_ms)
        f.write(f"Dialogue: 0,{format_ass_time(chunk_start)},{format_ass_time(chunk_end)},{style_name},,0,0,0,,{formatted_text}\n")

def time_to_seconds(t_str: str) -> float:
    if not t_str: return 0.0
    parts = t_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(t_str)

def parse_vtt_to_ass(vtt_path: str, output_path: str = "lyrics.ass", font_name: str = "Anton", size_preset: str = "Medium (50%)", layout_mode: str = "2-3 Word Chunk", video_ratio: str = "9:16 (Vertical/Reels)", start_offset: str = None):
    """Parses a downloaded YouTube VTT subtitle file into ASS subtitles."""
    print(f"Parsing YouTube VTT subtitles from {vtt_path}...")
    
    offset_s = time_to_seconds(start_offset) if start_offset else 0.0
    
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    parsed_lines = []
    time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')
    
    current_start = 0.0
    current_end = 0.0
    current_text = []
    
    def time_to_sec(t_str):
        h, m, s = t_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
        
    for line in lines:
        line = line.strip()
        match = time_pattern.search(line)
        if match:
            if current_text:
                text = " ".join(current_text).replace('♪', '').replace('</c>', '').strip()
                # Remove common VTT alignment tags if any exist
                text = re.sub(r'<[^>]+>', '', text)
                if text and not text.startswith('(') and not text.startswith('['):
                    parsed_lines.append((current_start, current_end, text))
            current_start = time_to_sec(match.group(1)) - offset_s
            current_end = time_to_sec(match.group(2)) - offset_s
            
            # Skip if the entire subtitle is before our start time
            if current_end < 0:
                current_text = []
                continue
                
            # Clamp start to 0 if it overlaps the cut
            if current_start < 0:
                current_start = 0.0
                
            current_text = []
        elif line and not line.startswith("WEBVTT") and not line.startswith("Kind:") and not line.startswith("Language:"):
            current_text.append(line)
            
    if current_text:
        text = " ".join(current_text).replace('♪', '').replace('</c>', '').strip()
        text = re.sub(r'<[^>]+>', '', text)
        if text and not text.startswith('(') and not text.startswith('['):
            parsed_lines.append((current_start, current_end, text))
            
    if not parsed_lines:
        return False, []
        
    # Deduplicate and merge rolling / incremental YouTube auto-captions
    merged_lines = []
    prev_s, prev_e, prev_txt = parsed_lines[0]
    for s, e, txt in parsed_lines[1:]:
        if txt.startswith(prev_txt) or prev_txt in txt:
            prev_e = max(prev_e, e)
            prev_txt = txt
        elif s - prev_e < 0.5 and (prev_e - prev_s < 2.5):
            prev_e = max(prev_e, e)
            prev_txt = f"{prev_txt} {txt}".strip()
        else:
            if prev_e - prev_s >= 0.8: # keep cues that last at least 0.8s
                merged_lines.append((prev_s, prev_e, prev_txt))
            prev_s, prev_e, prev_txt = s, e, txt
    merged_lines.append((prev_s, prev_e, prev_txt))
    parsed_lines = merged_lines
        
    style_def, chunk_size, effect_func = get_style_config(font_name, size_preset, layout_mode, video_ratio)
    ass_header = get_ass_header(style_def, video_ratio)
    style_name = "DynamicStyle"
    sentence_timings = []
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for start_s, end_s, text in parsed_lines:
            # Cap duration to prevent frozen subtitles
            if end_s - start_s > 5.0:
                end_s = start_s + 5.0
                
            sentence_timings.append((start_s, end_s, text))
            write_chunked_ass_lines(f, start_s, end_s, text, chunk_size, style_name, effect_func)
            
    print(f"VTT Subtitles written to {output_path}")
    return True, sentence_timings

def parse_lrc_to_ass(lrc_text: str, output_path: str = "lyrics.ass", font_name: str = "Anton", size_preset: str = "Medium (50%)", layout_mode: str = "2-3 Word Chunk", video_ratio: str = "9:16 (Vertical/Reels)", start_offset: str = None):
    """Parses standard LRC format into ASS subtitles with selected style."""
    lines = lrc_text.strip().split('\n')
    
    offset_s = time_to_seconds(start_offset) if start_offset else 0.0
    
    parsed_lines = []
    # Strictly match ONLY valid LRC timestamp lines: [mm:ss.xx] or [mm:ss.xxx]
    # This prevents metadata tags like [ar:], [al:], [作曲:...] from slipping in
    timestamp_pattern = re.compile(r'^\[(\d{2}):(\d{2}\.\d{2,3})\](.*)')
    
    # Patterns to strip: section headers like [Chorus], [Verse 1], etc.
    section_tag_pattern = re.compile(r'^\[.*\]\s*$')
    
    # Meaningless filler sounds to skip
    filler_words = {"uh", "uh-huh", "mhm", "mm", "hmm", "ah", "ooh", "oh", "la", "na", "yeah", "woah", "hey"}
    
    for line in lines:
        match = timestamp_pattern.match(line.strip())
        if match:
            m = int(match.group(1))
            s = float(match.group(2))
            text = match.group(3).strip()
            
            # Skip empty or section annotation lines
            if not text or section_tag_pattern.match(text):
                continue
            
            # Skip lines that are pure filler (all words are filler sounds)
            words_in_line = set(re.findall(r'\b\w+\b', text.lower()))
            if words_in_line and words_in_line.issubset(filler_words):
                continue
                
            # Skip very short lines (1-2 chars, likely garbled)
            if len(text) <= 2:
                continue
                
            # Skip lines containing Chinese/Japanese/Korean characters
            # These are metadata injected by Asian lyrics providers (e.g. 作曲：...)
            if re.search(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', text):
                continue
                
            total_s = (m * 60 + s) - offset_s
            if total_s >= -2.0: # allow slight overlap for the first lyric
                if total_s < 0: total_s = 0.0
                parsed_lines.append((total_s, text))
                
    if not parsed_lines:
        return False, []
        
    style_def, chunk_size, effect_func = get_style_config(font_name, size_preset, layout_mode, video_ratio)
    ass_header = get_ass_header(style_def, video_ratio)
    style_name = "DynamicStyle"
    
    sentence_timings = []
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for i, (start_s, text) in enumerate(parsed_lines):
            end_s = parsed_lines[i+1][0] if i+1 < len(parsed_lines) else start_s + 4.0
            # Cap duration to 5 seconds max if there's a long gap
            if end_s - start_s > 5.0:
                end_s = start_s + 5.0
                
            sentence_timings.append((start_s, end_s, text))
            write_chunked_ass_lines(f, start_s, end_s, text, chunk_size, style_name, effect_func)
            
    print(f"LRC Subtitles written to {output_path}")
    return True, sentence_timings

def get_ass_header(style_def: str, video_ratio: str = "9:16 (Vertical/Reels)") -> str:
    is_landscape = "16:9" in video_ratio
    is_square = "1:1" in video_ratio
    x = 1920 if is_landscape else 1080
    y = 1080 if is_landscape else (1080 if is_square else 1920)
    
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {x}
PlayResY: {y}
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
    header += style_def
    header += "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    return header


def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02}:{s:05.2f}"

def parse_lrc_lines(lrc_text):
    """Parses LRC into a list of (timestamp_seconds, line_text)."""
    lines = []
    pattern = re.compile(r'^\[(\d{2}):(\d{2}\.\d{2,3})\](.*)')
    for line in lrc_text.strip().split('\n'):
        m = pattern.match(line.strip())
        if m:
            mins = int(m.group(1))
            secs = float(m.group(2))
            text = m.group(3).strip()
            if text and not (text.startswith('[') and text.endswith(']')):
                lines.append((mins * 60 + secs, text))
    return lines

def fuzzy_find_lrc_window(whisper_text: str, lrc_lines: list):
    """
    Finds the exact slice of LRC lines that corresponds to the transcribed audio clip.
    Returns: (matched_lrc_lines, best_score)
    """
    if not whisper_text or not lrc_lines:
        return [], 0.0

    def norm(s):
        return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()

    clean_trans = norm(whisper_text)
    trans_words = clean_trans.split()
    if not trans_words:
        return [], 0.0

    import difflib
    best_score = 0.0
    best_range = (0, 0)
    max_window = min(len(lrc_lines), 20)
    
    for i in range(len(lrc_lines)):
        for j in range(i + 1, min(len(lrc_lines) + 1, i + max_window + 1)):
            window_text = norm(" ".join(line[1] for line in lrc_lines[i:j]))
            score = difflib.SequenceMatcher(None, clean_trans, window_text).ratio()
            if score > best_score:
                best_score = score
                best_range = (i, j)
                
    if best_score >= 0.50:
        # Also ensure at least 25% of unique words match to avoid matching random dialogue to song lyrics
        matched_slice = lrc_lines[best_range[0]:best_range[1]]
        matched_words = set(norm(" ".join(l[1] for l in matched_slice)).split())
        trans_word_set = set(clean_trans.split())
        word_overlap = len(trans_word_set.intersection(matched_words)) / max(len(trans_word_set), 1)
        if word_overlap >= 0.25:
            return matched_slice, best_score
    return [], 0.0

def align_whisper_to_verified(whisper_words, lrc_text):
    """
    Aligns Whisper detected words with verified lyrics from LRC.
    1. Finds the exact matching window of lyrics in the song.
    2. Maps verified words only within that window onto Whisper's frame-perfect audio timestamps.
    3. Eliminates rapid flickering by never cramming un-spoken words into milliseconds.
    """
    if not whisper_words:
        return []
    if not lrc_text:
        return whisper_words

    lrc_lines = parse_lrc_lines(lrc_text)
    if not lrc_lines:
        return whisper_words

    whisper_transcript = " ".join([w.word for w in whisper_words])
    matched_lines, score = fuzzy_find_lrc_window(whisper_transcript, lrc_lines)
    
    if not matched_lines:
        print("LRC lyrics found, but no matching section for this audio clip. Using Whisper transcripts.")
        return whisper_words
        
    print(f"Matched verified LRC lyrics window (confidence: {score*100:.1f}%):")
    for t, txt in matched_lines:
        print(f"  [{t:.2f}s] {txt}")

    # Extract verified words ONLY from the matched window
    v_words = []
    for _, txt in matched_lines:
        v_words.extend(txt.split())

    def norm(w):
        return re.sub(r'[^a-z0-9]', '', w.lower())

    v_norm = [norm(w) for w in v_words]
    w_norm = [norm(w.word) for w in whisper_words]

    import difflib
    matcher = difflib.SequenceMatcher(None, w_norm, v_norm)
    aligned_words = []

    class AlignedWord:
        def __init__(self, start, end, word):
            self.start = float(start)
            self.end = float(end)
            self.word = word

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                aligned_words.append(AlignedWord(whisper_words[i].start, whisper_words[i].end, v_words[j]))
        elif tag == 'replace':
            # Whisper misheard words or split/merged syllables
            start_t = whisper_words[i1].start
            end_t = whisper_words[i2 - 1].end
            v_chunk = v_words[j1:j2]
            dur = max(end_t - start_t, 0.2 * len(v_chunk))
            t_per_word = dur / len(v_chunk)
            for idx, v_w in enumerate(v_chunk):
                aligned_words.append(AlignedWord(start_t + (idx * t_per_word), start_t + ((idx + 1) * t_per_word), v_w))
        elif tag == 'delete':
            # Filler sound or background noise picked up by Whisper
            pass
        elif tag == 'insert':
            # Verified lyrics have a word Whisper missed inside the matched window
            prev_end = whisper_words[i1 - 1].end if i1 > 0 else (whisper_words[0].start - 0.5)
            next_start = whisper_words[i1].start if i1 < len(whisper_words) else (prev_end + 1.0)
            gap = next_start - prev_end
            v_chunk = v_words[j1:j2]
            min_dur = 0.2 * len(v_chunk)
            actual_dur = max(gap, min_dur)
            t_per_word = actual_dur / len(v_chunk)
            base_t = max(prev_end, 0.0)
            for idx, v_w in enumerate(v_chunk):
                w_start = base_t + (idx * t_per_word)
                w_end = base_t + ((idx + 1) * t_per_word)
                aligned_words.append(AlignedWord(w_start, w_end, v_w))

    return aligned_words if aligned_words else whisper_words

def transcribe_audio(audio_path: str, output_ass: str = "lyrics.ass", lrc_text: str = None, font_name: str = "Anton", size_preset: str = "Medium (50%)", layout_mode: str = "2-3 Word Chunk", video_ratio: str = "9:16 (Vertical/Reels)", start_offset: str = None):
    """Transcribes audio using Whisper AI, and optionally corrects text using verified LRC lyrics."""
    print(f"Transcribing {audio_path} using Whisper AI for perfect timing...")
            
    print(f"Transcribing {audio_path} using Whisper AI...")
    device = "cpu"
    compute_type = "int8"
    
    model = WhisperModel("small", device=device, compute_type=compute_type)
    segments, info = model.transcribe(audio_path, word_timestamps=True)
    segments_list = list(segments)
    
    style_def, chunk_size, effect_func = get_style_config(font_name, size_preset, layout_mode, video_ratio)
    ass_header = get_ass_header(style_def, video_ratio)
    style_name = "DynamicStyle"
    
    # Extract flat list of all whisper words
    all_whisper_words = []
    for segment in segments_list:
        all_whisper_words.extend(segment.words)
        
    # Align and correct text if we have verified lyrics
    if lrc_text:
        print("Aligning Whisper timestamps with verified LRC text...")
        final_words = align_whisper_to_verified(all_whisper_words, lrc_text)
    else:
        final_words = all_whisper_words
        
    sentence_timings = []
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_header)
        
        for i in range(0, len(final_words), chunk_size):
            chunk = final_words[i:i+chunk_size]
            if not chunk: continue
            
            start_time_val = chunk[0].start
            end_time_val = chunk[-1].end
            
            start_time_str = format_ass_time(start_time_val)
            end_time_str = format_ass_time(end_time_val)
            
            dur_ms = int((end_time_val - start_time_val) * 1000)
            if dur_ms <= 0: dur_ms = 100
            
            # Handle both object attributes (Whisper word) and aligned tuples
            text = " ".join([w.word.strip() for w in chunk])
            sentence_timings.append((start_time_val, end_time_val, text))
            
            formatted_text = effect_func(text, dur_ms)
            f.write(f"Dialogue: 0,{start_time_str},{end_time_str},{style_name},,0,0,0,,{formatted_text}\n")
            
    print(f"Subtitles written to {output_ass}")
    return output_ass, sentence_timings

if __name__ == "__main__":
    pass
