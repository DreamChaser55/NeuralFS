import re

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
