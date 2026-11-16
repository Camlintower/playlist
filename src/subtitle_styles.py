import os

def get_available_fonts():
    """Returns a list of all custom fonts we support and have downloaded."""
    return [
        "Permanent Marker", "Pacifico", "Bebas Neue", "Sedgwick Ave Display", "Anton",
        "Vast Shadow", "Bowlby One", "Comic Relief", "Special Elite", "Lavishly Yours",
        "Notable", "Rock Salt", "Jim Nightshade", "Bangers", "Oswald"
    ]

def get_style_config(font_name: str, size_preset: str, layout_mode: str, video_ratio: str):
    """
    Dynamically generates the ASS style, chunk size, and effect function based on modular inputs.
    Returns: (style_definition_string, chunk_size, apply_effect_func)
    """
    # 1. Determine Resolution Multiplier based on Video Ratio
    is_landscape = "16:9" in video_ratio
    is_square = "1:1" in video_ratio
    
    # ASS Coordinate System
    res_x = 1920 if is_landscape else 1080
    res_y = 1080 if is_landscape else (1080 if is_square else 1920)
    
    # 2. Calculate Strict Margins to Force Exact Screen Percentage Width
    if "Small" in size_preset: # 25% width
        target_width = res_x * 0.25
        base_size = int(target_width / 4) # rough estimate for 4-5 chars
        margin_v = int(res_y * 0.15)
    elif "Medium" in size_preset: # 50% width
        target_width = res_x * 0.50
        base_size = int(target_width / 4)
        margin_v = int(res_y * 0.10)
    else: # Fill (75% width)
        target_width = res_x * 0.75
        base_size = int(target_width / 4)
        margin_v = int(res_y * 0.08)
        
    # Scale font size down slightly if it's a full sentence so it fits vertically
    if "Sentence" in layout_mode:
        base_size = int(base_size * 0.6)
        
    # Calculate Left/Right margins to enforce the target_width bounding box
    margin_l_r = int((res_x - target_width) / 2)
    
    # 3. Determine Alignment & Layout Parameters
    if "Sentence" in layout_mode:
        align = 2 # Bottom-Center
        chunk_size = 10
        margins = f"{margin_l_r},{margin_l_r},{margin_v}"
    elif "2-3 Word" in layout_mode:
        align = 5 # Center
        chunk_size = 3
        # Center text uses the same strict bounding box
        margins = f"{margin_l_r},{margin_l_r},{margin_v}"
    else: # 1-Word Pop
        align = 5 # Center
        chunk_size = 1
        # 1-Word usually doesn't wrap, but we enforce margins just in case
        margins = f"{margin_l_r},{margin_l_r},{margin_v}"
        
    # 3. Build the ASS Style String
    # Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    
    # We'll use a clean white text with dark outline by default, but we can make it pop more
    # based on the font style. For gritty fonts, add more shadow.
    WHITE = "&H00FFFFFF"
    BLACK = "&H00000000"
    TRANS_BLACK = "&H80000000"
    
    outline = "4" if "Small" in size_preset else ("6" if "Medium" in size_preset else "9")
    shadow = "4"
    
    # Some fonts like "Vast Shadow" already have a shadow, so keep outline small
    if font_name in ["Vast Shadow", "Notable", "Bebas Neue"]:
        outline = "2"
        shadow = "6"
        
    style_def = f"Style: DynamicStyle,{font_name},{base_size},{WHITE},{BLACK},{BLACK},{TRANS_BLACK},-1,0,0,0,100,100,0,0,1,{outline},{shadow},{align},{margins},1\n"
    
    # 4. Generate the Animation Effect
    def effect_func(text, dur):
        if "1-Word" in layout_mode:
            # TikTok Pop in
            return f"{{\\fad(50,50)\\fscx130\\fscy130\\t(0,100,\\fscx100\\fscy100)}}{text}"
        elif "2-3 Word" in layout_mode:
            # Slight bounce
            return f"{{\\fad(100,100)\\fscx105\\fscy105\\t(0,150,\\fscx100\\fscy100)\\q1}}{text}"
        else:
            # Full sentence: just fade and wrap
            return f"{{\\fad(200,200)\\q1}}{text}"
            
    return style_def, chunk_size, effect_func
