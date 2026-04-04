import re

def calculate_briefing_camera_height(delta_x: float, delta_z: float) -> float:
    """
    Calculate the height (and effective width) of the FSO briefing camera 
    given the bounding box dimensions of the briefing icons.
    
    The calculation uses a tight bounding box, constrained by the FSO 
    briefing camera aspect ratio (2.5) and FOV. It ensures a safety 
    factor of 15% (1.15) and clamps the minimum height to 1000.0.
    """
    target_ratio = 2.5
    final_width = max(delta_x, target_ratio * delta_z)
    cam_h = final_width * 1.15
    return max(cam_h, 1000.0)

def slugify_filename(s: str) -> str:
    """
    Convert an arbitrary string into a safe filename stem.
    
    Note: The FSO engine requires voice filenames to be < 30 characters total 
    (including the .wav extension). This function only sanitizes the string; 
    callers are responsible for truncating the result to enforce length limits.
    """
    try:
        s = str(s).strip().lower()
    except Exception:
        s = ""
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "line"

def ensure_wav_extension(name: str) -> str:
    """Ensure a non-empty .wav filename."""
    try:
        name = (str(name) or "").strip()
    except Exception:
        name = ""
    if not name:
        return "voice.wav"
    if not name.lower().endswith(".wav"):
        name = name + ".wav"
    return name
