# briefing_icon_types.py
# Canonical mapping for FS2 briefing icon types.
#
# FSIF is strict: authors MUST use the exact canonical string values
# documented here for icons[*].type. No aliases, case variations, or
# punctuation/spacing variants are accepted. Any non-canonical value
# should be treated as an error by callers.
#
# Icon types are split into two mutually-exclusive classifications:
#
#   NON_SHIP_ICON_TYPES  — landmarks/navigation markers that have no meaningful
#       ship class association. Authors must OMIT display_class for these.
#       The converter will emit the safe default $class: Terran NavBuoy.
#
#   SHIP_ICON_TYPES      — all other icon types that represent actual spacecraft.
#       Authors MUST author display_class with a valid, non-NavBuoy ship class.

from typing import Dict

# Canonical name -> ID mapping (exact spellings)
ICON_TYPE_ID_BY_NAME: Dict[str, int] = {
    "Fighter": 0,
    "Fighter Wing": 1,
    "Cargo": 2,
    "Cargo Wing": 3,
    "Science Cruiser": 4,          # alias ID 30 in FS2, but 4 is canonical here
    "Science Cruiser Wing": 5,
    "Capital Ship": 6,
    "Planet": 7,
    "Asteroid Field": 8,
    "Waypoint": 9,
    "Support Ship": 10,
    "Freighter (no cargo)": 11,
    "Freighter (has cargo)": 12,
    "Freighter Wing (no cargo)": 13,
    "Freighter Wing (has cargo)": 14,
    "Installation": 15,
    "Bomber": 16,
    "Bomber Wing": 17,
    "Cruiser": 18,                 # alias ID 28 in FS2, but 18 is canonical here
    "Cruiser Wing": 19,
    "Unknown": 20,
    "Unknown Wing": 21,
    "Player Fighter": 22,
    "Player Fighter Wing": 23,
    "Player Bomber": 24,
    "Player Bomber Wing": 25,
    "Small Planet": 26,
    "Transport Wing": 27,
    "Transport": 29,               # alias ID 34 in FS2, but 29 is canonical here
    "Supercapital Ship": 31,
    "Sentry Gun": 32,
    "Jump Node": 33,
}

# Reverse map: ID -> canonical name
ICON_TYPE_NAME_BY_ID: Dict[int, str] = {v: k for k, v in ICON_TYPE_ID_BY_NAME.items()}


def parse_icon_type(name) -> int:
    """Public entry point used by the loader.

    Expects an exact canonical string; raises ValueError for anything
    else so the caller can decide how to handle the error.
    """
    if not isinstance(name, str):
        raise ValueError(f"Icon type must be a canonical string; got {name!r}")
    key = name.strip()
    if not key:
        raise ValueError("Empty icon type name")
    if key not in ICON_TYPE_ID_BY_NAME:
        raise ValueError(f"Unknown briefing icon type: '{name}'")
    return ICON_TYPE_ID_BY_NAME[key]


def canonical_name_for_id(type_id: int) -> str:
    """Return the canonical name for a numeric FS2 icon type ID.

    If the ID is not recognized, the numeric value is returned as a
    string so the writer can still emit something meaningful.
    """
    return ICON_TYPE_NAME_BY_ID.get(int(type_id), str(type_id))


# ---------------------------------------------------------------------------
# Icon type classification sets
# ---------------------------------------------------------------------------

# Non-ship icon types: represent landmarks, navigation points, or celestial
# objects. These icons have no meaningful ship class display.
# Authors MUST omit display_class for these icon types.
NON_SHIP_ICON_TYPES: frozenset = frozenset({
    "Waypoint",
    "Jump Node",
    "Planet",
    "Small Planet",
    "Asteroid Field",
    "Unknown",
    "Unknown Wing",
})

# Ship icon types: all canonical icon types that represent actual spacecraft.
# Authors MUST explicitly author display_class with a valid, non-NavBuoy ship class.
SHIP_ICON_TYPES: frozenset = frozenset(
    set(ICON_TYPE_ID_BY_NAME.keys()) - NON_SHIP_ICON_TYPES
)
