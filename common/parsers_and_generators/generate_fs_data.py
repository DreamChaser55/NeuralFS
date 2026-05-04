import re
from pathlib import Path
from typing import Set, Dict, List

# Paths
# This script is located in common/parsers_and_generators/
# Root is ../../
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOC_DIR = ROOT_DIR / "Documentation"
FSO_DOC_DIR = DOC_DIR / "FSO and fs2 format"
SEXP_DOC_DIR = DOC_DIR / "FSO SEXPs"
# Output to common/fs_data.py
OUTPUT_FILE = Path(__file__).resolve().parent.parent.parent / "common" / "fs_data.py"

def parse_tokens_reference():
    """Parses FSO_Tokens_Reference.md for various lists."""
    path = FSO_DOC_DIR / "FSO_Tokens_Reference.md"
    content = path.read_text(encoding="utf-8")
    
    data = {
        "teams": set(),
        "priorities": set(),
        "ai_classes": set(),
        "mission_music": set(),
        "briefing_music": set(),
        "nebula_patterns": set(),
        "nebula_poofs": set(),
        "suns": set(),
        "planets": set(),
        "nebulae_bitmaps": set(),
        "primary_weapons": set(),
        "secondary_weapons": set(),
        "anchors": set(),
        "arrival_methods": set(),
        "departure_methods": set(),
    }

    # Helper regexes
    # Sections usually start with ### or ####
    
    # Teams
    if match := re.search(r"### Teams\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("- "):
                data["teams"].add(line.strip()[2:].strip())

    # Priorities
    if match := re.search(r"### Message priorities\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("- "):
                val = line.strip()[2:].strip().strip('"')
                data["priorities"].add(val)
    
    # AI Classes
    if match := re.search(r"### AI Class values.*?\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("- "):
                data["ai_classes"].add(line.strip()[2:].strip())

    # Music
    if match := re.search(r"#### Mission Music:\n(.*?)\n\n#### Briefing Music:", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip():
                data["mission_music"].add(line.strip())
                
    if match := re.search(r"#### Briefing Music:\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip():
                data["briefing_music"].add(line.strip())

    # Nebula Patterns & Poofs
    if match := re.search(r"### Volumetric \(full\) nebula parameters\n(.*?)\n\n", content, re.DOTALL):
        block = match.group(1)
        for line in block.splitlines():
            if line.startswith("Pattern:"):
                parts = line.replace("Pattern:", "").split(",")
                data["nebula_patterns"].update(p.strip() for p in parts if p.strip())
            if line.startswith("Cloud Sprites:"):
                parts = line.replace("Cloud Sprites:", "").split(",")
                data["nebula_poofs"].update(p.strip() for p in parts if p.strip())
                
    # Weapons
    # Primary
    if match := re.search(r"- Primary Banks \(lasers\):\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("-"):
                parts = line.split(":", 1)[1].split(",")
                data["primary_weapons"].update(p.strip() for p in parts if p.strip())
    # Secondary
    if match := re.search(r"- Secondary Banks \(missiles\):\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("-"):
                parts = line.split(":", 1)[1].split(",")
                data["secondary_weapons"].update(p.strip() for p in parts if p.strip())

    # Background Bitmaps
    # Nebulae
    if match := re.search(r"- Nebulae .*?\n(.*?)\n\n- Planets:", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("-"):
                parts = line.split(":", 1)[1].split(",")
                data["nebulae_bitmaps"].update(p.strip() for p in parts if p.strip())
    
    # Planets
    if match := re.search(r"- Planets:\n(.*?)\n\n", content, re.DOTALL):
         data["planets"].update(p.strip() for p in match.group(1).split(",") if p.strip())

    # Suns
    if match := re.search(r"- Suns:\n(.*?)\n\n", content, re.DOTALL):
         data["suns"].update(p.strip() for p in match.group(1).split(",") if p.strip())

    # Wildcards / Anchors
    if match := re.search(r"## Wildcards and special literals\n\nLiterals:\n(.*?)\n\n", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if line.strip().startswith("-"):
                val = line.strip()[2:].strip().strip('"')
                data["anchors"].add(val)

    # Arrival / Departure Methods
    # Parse shared (both arrival and departure) methods first.
    # Only collect top-level list entries (exactly "- <token>"), not indented sub-bullets.
    if match := re.search(r"#### Arrival and Departure\n(.*?)(?=\n####|\n###|\Z)", content, re.DOTALL):
        for line in match.group(1).splitlines():
            # Top-level list entry: exactly two chars "- " at start (not indented)
            if re.match(r'^- \S', line):
                token = line[2:].strip()
                data["arrival_methods"].add(token)
                data["departure_methods"].add(token)

    # Arrival-only methods
    if match := re.search(r"#### Arrival-only\n(.*?)(?=\n####|\n###|\Z)", content, re.DOTALL):
        for line in match.group(1).splitlines():
            if re.match(r'^- \S', line):
                token = line[2:].strip()
                data["arrival_methods"].add(token)

    return data

def parse_ship_classes():
    path = FSO_DOC_DIR / "spacecraft-classes.md"
    classes = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- "):
            classes.add(line.strip()[2:].strip())
    return classes

def parse_dockpoints():
    path = FSO_DOC_DIR / "ship-dockpoint-names.md"
    docks = {}
    current_ship = None
    
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## "):
            current_ship = line[3:].strip()
            docks[current_ship] = set()
        elif line.startswith("- ") and current_ship:
            docks[current_ship].add(line[2:].strip())
        elif line.startswith("> (No docks)") and current_ship:
            pass # Keep empty set
            
    return docks

def parse_subsystems():
    subs_dir = FSO_DOC_DIR / "Ship subsystems"
    subsystems = {}
    
    for file_path in subs_dir.glob("*.md"):
        current_ship = None
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("## "):
                current_ship = line[3:].strip()
                subsystems[current_ship] = set()
            elif line.startswith("- ") and current_ship:
                subsystems[current_ship].add(line[2:].strip())
            elif line.startswith("> (No subsystems)") and current_ship:
                pass
                
    return subsystems

def parse_sexps():
    path = SEXP_DOC_DIR / "INDEX.md"
    operators = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Format: - `operator-name`
        match = re.match(r"-\s*`([^`]+)`", line)
        if match:
            operators.add(match.group(1))
    return operators

def parse_voices(doc_dir: Path, provider_folder: str) -> Set[str]:
    """
    Parses voice files from the given provider folder in Documentation directory.
    Supports both Google TTS and ElevenLabs TTS folder structures.
    """
    voices = set()
    tts_dir = doc_dir / provider_folder
    
    if not tts_dir.exists():
        return voices

    # Look for common voice file patterns
    files_to_check = ['male_voices.txt', 'female_voices.txt', 'voices.txt']
    
    for f_name in files_to_check:
        v_path = tts_dir / f_name
        if v_path.exists():
            try:
                with open(v_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        l = line.strip()
                        # Ignore comments and empty lines
                        if l and not l.startswith('#'):
                            # Handle characteristics (e.g. "Charon -- Informative")
                            name = l.split("--")[0].strip()
                            if name:
                                voices.add(name)
            except Exception as e:
                print(f"[Warning] Failed to read voice definition file {v_path}: {e}")
                
    return voices

def parse_secondary_capacities() -> Dict[str, List[int]]:
    path = ROOT_DIR / "FSIF_to_FS2_Converter" / "secondary_bank_capacities.md"
    capacities = {}
    
    if not path.exists():
        print(f"[Warning] Secondary capacities file not found: {path}")
        return capacities
        
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- "):
            parts = line[2:].split(":")
            if len(parts) == 2:
                ship = parts[0].strip()
                caps_str = parts[1].strip()
                if caps_str.startswith("[") and caps_str.endswith("]"):
                    caps = [int(x.strip()) for x in caps_str[1:-1].split(",") if x.strip().isdigit()]
                    capacities[ship] = caps
    return capacities

def parse_weapon_sizes() -> Dict[str, float]:
    path = ROOT_DIR / "FSIF_to_FS2_Converter" / "secondary_weapon_sizes.md"
    sizes = {}
    
    if not path.exists():
        print(f"[Warning] Secondary weapon sizes file not found: {path}")
        return sizes
        
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- "):
            parts = line[2:].split(":")
            if len(parts) == 2:
                weapon = parts[0].strip()
                try:
                    size = float(parts[1].strip())
                    sizes[weapon] = size
                except ValueError:
                    pass
    return sizes

def parse_hardpoints() -> Dict[str, Dict[str, int]]:
    path = FSO_DOC_DIR / "fighter_bomber_hardpoints.md"
    hardpoints = {}
    current_ship = None
    
    if not path.exists():
        print(f"[Warning] Hardpoints file not found: {path}")
        return hardpoints
        
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith("## "):
            current_ship = line[3:].strip()
            hardpoints[current_ship] = {"primary": 0, "secondary": 0}
        elif current_ship and line.startswith("- Primary:"):
            try:
                count = int(line.split(":")[1].strip())
                hardpoints[current_ship]["primary"] = count
            except ValueError:
                print(f"[Warning] Invalid primary count for {current_ship}: {line}")
        elif current_ship and line.startswith("- Secondary:"):
            try:
                count = int(line.split(":")[1].strip())
                hardpoints[current_ship]["secondary"] = count
            except ValueError:
                print(f"[Warning] Invalid secondary count for {current_ship}: {line}")
                
    return hardpoints

def parse_ship_bounding_boxes() -> Dict[str, Dict[str, List[float]]]:
    path = FSO_DOC_DIR / "ship_bounding_boxes.md"
    bounding_boxes = {}
    
    if not path.exists():
        print(f"[Warning] Ship bounding boxes file not found: {path}")
        return bounding_boxes
        
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    current_ship = None
    min_coords = None
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith("## Schema"):
            continue
            
        if line.startswith("## "):
            current_ship = line[3:].strip()
            min_coords = None
        elif current_ship:
            try:
                coords = [float(x.strip()) for x in line.split(",")]
                if len(coords) == 3:
                    if min_coords is None:
                        min_coords = coords
                    else:
                        bounding_boxes[current_ship] = {
                            "min": min_coords,
                            "max": coords
                        }
                        current_ship = None
                        min_coords = None
            except ValueError:
                print(f"[Warning] Invalid coordinate line for {current_ship}: {line}")
                
    return bounding_boxes

def generate_file():
    print("Parsing documentation...")
    tokens = parse_tokens_reference()
    ships = parse_ship_classes()
    docks = parse_dockpoints()
    subs = parse_subsystems()
    sexps = parse_sexps()
    sexps.add('goals') # Manually add 'goals' as it is a special top-level container not in INDEX.md
    
    voices_google = parse_voices(DOC_DIR, 'Google TTS')
    voices_elevenlabs = parse_voices(DOC_DIR, 'ElevenLabs TTS')
    voices_inworld = parse_voices(DOC_DIR, 'Inworld TTS')
    
    hardpoints = parse_hardpoints()
    sbank_capacities = parse_secondary_capacities()
    weapon_sizes = parse_weapon_sizes()
    bounding_boxes = parse_ship_bounding_boxes()
    
    # Combined collections
    backgrounds = tokens["suns"] | tokens["planets"] | tokens["nebulae_bitmaps"]
    weapons = tokens["primary_weapons"] | tokens["secondary_weapons"]
    
    print(f"Found {len(ships)} ships, {len(sexps)} SEXPs, {len(subs)} subsystem entries, "
          f"{len(voices_google)} Google voices, {len(voices_elevenlabs)} ElevenLabs voices, "
          f"{len(voices_inworld)} Inworld voices, {len(hardpoints)} hardpoint definitions.")
    
    def fmt_set(s):
        if not s: return "set()"
        # repr(list) gives ['A', 'B'], convert to {'A', 'B'}
        return repr(sorted(list(s))).replace("[", "{", 1).replace("]", "}", 1)

    # Write file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# fs_data.py\n")
        f.write("# Central repository for FSO token lists and allowed values.\n")
        f.write("# GENERATED FROM DOCUMENTATION. DO NOT EDIT MANUALLY.\n\n")
        
        f.write("from typing import Set\n\n")
        
        # Teams
        f.write("# Teams\n")
        f.write(f"ALLOWED_TEAMS = {fmt_set(tokens['teams'])}\n\n")
        
        # Priorities
        f.write("# Message Priorities\n")
        f.write(f"ALLOWED_PRIORITIES = {fmt_set(tokens['priorities'])}\n\n")
        
        # AI Classes
        f.write("# AI Classes\n")
        f.write(f"ALLOWED_AI_CLASSES = {fmt_set(tokens['ai_classes'])}\n\n")
        
        # Music
        f.write("# Music\n")
        f.write(f"ALLOWED_MUSIC_MISSION = {fmt_set(tokens['mission_music'])}\n\n")
        f.write(f"ALLOWED_MUSIC_BRIEFING = {fmt_set(tokens['briefing_music'])}\n\n")
        
        # Nebula
        f.write("# Nebula Patterns (Full Nebula)\n")
        f.write(f"ALLOWED_NEBULA_PATTERNS = {fmt_set(tokens['nebula_patterns'])}\n\n")
        f.write("# Nebula Poofs (Full Nebula)\n")
        f.write(f"ALLOWED_NEBULA_POOFS = {fmt_set(tokens['nebula_poofs'])}\n\n")
        
        # Backgrounds
        f.write("# Background Bitmaps - Suns\n")
        f.write(f"ALLOWED_SUNS = {fmt_set(tokens['suns'])}\n\n")
        f.write("# Background Bitmaps - Planets\n")
        f.write(f"ALLOWED_PLANETS = {fmt_set(tokens['planets'])}\n\n")
        f.write("# Background Bitmaps - Nebulae\n")
        f.write(f"ALLOWED_NEBULAE_BITMAPS = {fmt_set(tokens['nebulae_bitmaps'])}\n\n")
        f.write("# Combined Backgrounds\n")
        f.write("ALLOWED_BACKGROUNDS = ALLOWED_SUNS | ALLOWED_PLANETS | ALLOWED_NEBULAE_BITMAPS\n\n")
        
        # Anchors
        f.write("# Anchor Tokens (Wildcards)\n")
        f.write(f"ALLOWED_ANCHORS_TOKENS = {fmt_set(tokens['anchors'])}\n\n")

        # Arrival / Departure Methods
        f.write("# Arrival Methods (arrival_method field on ships and wings)\n")
        f.write(f"ALLOWED_ARRIVAL_METHODS = {fmt_set(tokens['arrival_methods'])}\n\n")
        f.write("# Departure Methods (departure_method field on ships and wings)\n")
        f.write(f"ALLOWED_DEPARTURE_METHODS = {fmt_set(tokens['departure_methods'])}\n\n")

        # Weapons
        f.write("# Weapons - Primary\n")
        f.write(f"ALLOWED_PRIMARY_WEAPONS = {fmt_set(tokens['primary_weapons'])}\n\n")
        f.write("# Weapons - Secondary\n")
        f.write(f"ALLOWED_SECONDARY_WEAPONS = {fmt_set(tokens['secondary_weapons'])}\n\n")
        f.write("# Combined Weapons\n")
        f.write("ALLOWED_WEAPONS = ALLOWED_PRIMARY_WEAPONS | ALLOWED_SECONDARY_WEAPONS\n\n")
        
        # Ship Classes
        f.write("# --- 1. Spacecraft Classes ---\n")
        f.write(f"ALLOWED_SHIP_CLASSES = {fmt_set(ships)}\n\n")
        
        # Dockpoints
        f.write("# --- 2. Dockpoints (Mapping Class -> Set of Points) ---\n")
        f.write("ALLOWED_DOCKPOINTS = {\n")
        for ship, pts in sorted(docks.items()):
            if pts:
                f.write(f"    {ship!r}: {fmt_set(pts)},\n")
        f.write("}\n\n")
        
        # Subsystems
        f.write("# --- 3. Subsystems (Mapping Class -> Set of Subsystems) ---\n")
        f.write("# Note: \"Pilot\" is virtual and always allowed, handled separately in logic.\n")
        f.write("# Only listing critical subsystems typically targeted by SEXPs.\n")
        f.write("ALLOWED_SUBSYSTEMS = {\n")
        for ship, sub_set in sorted(subs.items()):
            if sub_set:
                f.write(f"    {ship!r}: {fmt_set(sub_set)},\n")
        f.write("}\n\n")
        
        # SEXPs
        f.write("# --- 4. SEXP Operators ---\n")
        f.write("# Exhaustive list of standard FSO/Retail SEXP operators.\n")
        f.write(f"ALLOWED_SEXP_OPERATORS = {fmt_set(sexps)}\n\n")
        
        # Voices
        f.write("# --- 5. Voices ---\n")
        f.write(f"ALLOWED_VOICES_GOOGLE = {fmt_set(voices_google)}\n")
        f.write(f"ALLOWED_VOICES_ELEVENLABS = {fmt_set(voices_elevenlabs)}\n")
        f.write(f"ALLOWED_VOICES_INWORLD = {fmt_set(voices_inworld)}\n\n")
        
        # Hardpoints
        f.write("# --- 6. Hardpoints ---\n")
        f.write("# Mapping Class -> {'primary': N, 'secondary': M}\n")
        f.write("NUM_OF_HARDPOINTS = {\n")
        for ship, hp in sorted(hardpoints.items()):
            f.write(f"    {ship!r}: {hp},\n")
        f.write("}\n\n")

        # Secondary Bank Capacities
        f.write("# --- 7. Secondary Bank Capacities ---\n")
        f.write("# Mapping Class -> [cap1, cap2, ...]\n")
        f.write("SHIP_SBANK_CAPACITIES = {\n")
        for ship, caps in sorted(sbank_capacities.items()):
            f.write(f"    {ship!r}: {caps},\n")
        f.write("}\n\n")

        # Secondary Weapon Sizes
        f.write("# --- 8. Secondary Weapon Sizes ---\n")
        f.write("# Mapping Weapon -> float\n")
        f.write("WEAPON_CARGO_SIZES = {\n")
        for weapon, size in sorted(weapon_sizes.items()):
            f.write(f"    {weapon!r}: {size},\n")
        f.write("}\n\n")

        # Ship Bounding Boxes
        f.write("# --- 9. Ship Bounding Boxes ---\n")
        f.write("# Mapping Class -> {'min': [x, y, z], 'max': [x, y, z]}\n")
        f.write("SHIP_BOUNDING_BOXES = {\n")
        for ship, box in sorted(bounding_boxes.items()):
            f.write(f"    {ship!r}: {box},\n")
        f.write("}\n\n")

        # Player Wing Names
        f.write("# --- 10. Player Wing Names ---\n")
        f.write("PLAYER_WING_NAMES = {\"Alpha\", \"Beta\", \"Gamma\", \"Delta\", \"Epsilon\"}\n\n")
    
    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_file()
