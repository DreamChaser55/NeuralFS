import os
import re
import math
from pathlib import Path

def sanitize_path(arg: str) -> str:
    """
    Conservative path normalization:
    - Remove one symmetric outer quote layer if present.
    - Expand ~ and environment variables.
    - Preserve embedded spaces and valid characters.
    - Return a normalized path string appropriate for the current OS.
    """
    if not arg:
        return ""

    p = str(arg).strip()
    if len(p) >= 2 and ((p[0] == '"' and p[-1] == '"') or (p[0] == "'" and p[-1] == "'")):
        p = p[1:-1]

    p = os.path.expandvars(os.path.expanduser(p))
    return str(Path(p))

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

def compute_facing_orientation(source_pos, target_pos):
    """Compute a 9-float orientation matrix that points a ship's nose at *target_pos*
    from *source_pos*, using the same algorithm as FSO's ``vm_vector_2_matrix``
    (forward-only form, default up = world +Y).

    Row convention (FRED / FS2 ``$Orientation``):

    * row 1 ``[m00, m01, m02]`` = right (rvec)
    * row 2 ``[m10, m11, m12]`` = up   (uvec)
    * row 3 ``[m20, m21, m22]`` = nose/forward (fvec)

    For level targets (same Y as source) the result is identical to the
    FSIF Authoring Guide yaw-only formula::

        orientation: [fz, 0.0, -fx, 0.0, 1.0, 0.0, fx, 0.0, fz]

    Raises:
        ValueError: if *source_pos* and *target_pos* are at the same position
            (zero-length forward vector, no meaningful facing direction possible).
    """
    dx = float(target_pos[0]) - float(source_pos[0])
    dy = float(target_pos[1]) - float(source_pos[1])
    dz = float(target_pos[2]) - float(source_pos[2])
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-9:
        raise ValueError(
            "source and target are at the same position "
            "(or too close to compute a meaningful facing direction)."
        )

    # ---- Forward / nose (row 3) ----
    zx, zy, zz = dx / length, dy / length, dz / length

    # ---- Right (row 1) ----
    horiz_len = math.sqrt(zx * zx + zz * zz)
    if horiz_len < 1e-9:
        # Forward is straight up (+Y) or straight down (-Y).
        # Choose right = world +X; up is derived from cross(forward, right).
        xx, xy, xz = 1.0, 0.0, 0.0
        # up = z × x
        yx = zy * xz - zz * xy   # = 0
        yy = zz * xx - zx * xz   # = 0
        yz = zx * xy - zy * xx   # = -zy  (= ∓1)
        y_len = math.sqrt(yx * yx + yy * yy + yz * yz)
        if y_len < 1e-9:
            yx, yy, yz = 0.0, 0.0, 1.0
        else:
            yx, yy, yz = yx / y_len, yy / y_len, yz / y_len
    else:
        # Non-vertical: right = normalize(zz, 0, -zx)  — FSO formula
        xx, xy, xz = zz / horiz_len, 0.0, -zx / horiz_len
        # up = z × x
        yx = zy * xz - zz * xy
        yy = zz * xx - zx * xz
        yz = zx * xy - zy * xx
        y_len = math.sqrt(yx * yx + yy * yy + yz * yz)
        if y_len > 1e-9:
            yx, yy, yz = yx / y_len, yy / y_len, yz / y_len
        else:
            yx, yy, yz = 0.0, 1.0, 0.0

    return [xx, xy, xz, yx, yy, yz, zx, zy, zz]


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
