import argparse
import sys
import yaml
from pathlib import Path
from typing import Annotated, List, Optional
from pydantic import AfterValidator, BaseModel, Field, ConfigDict, ValidationError, field_validator, model_validator

# ---------------------------------------------------------------------------
# AsciiStr: a Pydantic Annotated type that enforces ASCII-only strings.
# Applied to every FSO-facing string field so validity is guaranteed at
# construction time ("Parse, don't validate").
# ---------------------------------------------------------------------------

def _ascii_check(v: str) -> str:
    """AfterValidator: raises ValueError if *v* contains any non-ASCII character."""
    if v.isascii():
        return v
    offenders: list[str] = []
    for index, ch in enumerate(v):
        if ord(ch) > 127:
            offenders.append(f"{repr(ch)} (U+{ord(ch):04X}, index {index})")
    details = ", ".join(offenders[:5])
    if len(offenders) > 5:
        details += f", ... (+{len(offenders) - 5} more)"
    raise ValueError(f"contains non-ASCII character(s): {details}")

AsciiStr = Annotated[str, AfterValidator(_ascii_check)]

# --- FCIF Data Models ---

class CampaignInfo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: AsciiStr
    description: AsciiStr

    @field_validator('description')
    @classmethod
    def no_double_quotes_in_description(cls, v: str) -> str:
        if '"' in v:
            raise ValueError(
                'campaign.description must not contain double quotes ("), '
                'because it would cause syntax issues in the generated .fc2 file. '
                'Remove all double quotes from the description string.'
            )
        return v

class StartingLoadout(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ships: List[AsciiStr] = Field(default_factory=list)
    weapons: List[AsciiStr] = Field(default_factory=list)

class CampaignMission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: AsciiStr
    success_goal: Optional[AsciiStr] = None
    success_event: Optional[AsciiStr] = None
    failure_goal: Optional[AsciiStr] = None
    failure_event: Optional[AsciiStr] = None

    @model_validator(mode='after')
    def check_mutual_exclusivity(self) -> 'CampaignMission':
        """Ensure at most one advance condition field is set per mission."""
        condition_fields = {
            'success_goal': self.success_goal,
            'success_event': self.success_event,
            'failure_goal': self.failure_goal,
            'failure_event': self.failure_event,
        }
        set_fields = [name for name, value in condition_fields.items() if value is not None]
        if len(set_fields) > 1:
            raise ValueError(
                f"Mission '{self.filename}': only one advance condition field may be set per mission, "
                f"but found: {', '.join(set_fields)}. "
                f"Use exactly one of: success_goal, success_event, failure_goal, failure_event."
            )
        return self

SUPPORTED_FCIF_VERSIONS = {"1.0", "1.1"}

class FCIF(BaseModel):
    model_config = ConfigDict(extra='forbid')
    fcif_version: str = "1.1"
    
    @field_validator('fcif_version', mode='before')
    @classmethod
    def cast_version_to_str(cls, v) -> str:
        return str(v)

    campaign: CampaignInfo
    starting_loadout: StartingLoadout
    missions: List[CampaignMission]

    @model_validator(mode='after')
    def check_version(self) -> 'FCIF':
        """Reject unsupported FCIF versions."""
        if self.fcif_version not in SUPPORTED_FCIF_VERSIONS:
            raise ValueError(
                f"Unsupported fcif_version: {self.fcif_version}. "
                f"Supported versions: {sorted(SUPPORTED_FCIF_VERSIONS)}"
            )
        return self

# --- Logic ---

def load_fcif(path: Path, log_func=print) -> Optional[FCIF]:
    """Loads and validates the FCIF YAML file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return FCIF(**data)
    except yaml.YAMLError as e:
        log_func(f"[ERROR] Error parsing YAML: {e}")
        return None
    except ValidationError as e:
        log_func(f"[ERROR] Validation Error:\n{e}")
        return None
    except Exception as e:
        log_func(f"[ERROR] Error loading file: {e}")
        return None

def format_sexp_string(s: str) -> str:
    """Formats a string for SEXP (quoted)."""
    return f'"{s}"'

def _build_condition_sexp(mission: CampaignMission) -> Optional[str]:
    """
    Determines the advance condition SEXP for a mission based on its condition field.

    Returns the condition SEXP string, or None if the mission advances unconditionally.

    Mapping:
        success_goal  -> ( is-previous-goal-true  "mission" "name" )
        success_event -> ( is-previous-event-true  "mission" "name" )
        failure_goal  -> ( is-previous-goal-false  "mission" "name" )
        failure_event -> ( is-previous-event-false "mission" "name" )
    """
    mission_quoted = format_sexp_string(mission.filename)

    if mission.success_goal:
        return f'( is-previous-goal-true {mission_quoted} {format_sexp_string(mission.success_goal)} )'
    if mission.success_event:
        return f'( is-previous-event-true {mission_quoted} {format_sexp_string(mission.success_event)} )'
    if mission.failure_goal:
        return f'( is-previous-goal-false {mission_quoted} {format_sexp_string(mission.failure_goal)} )'
    if mission.failure_event:
        return f'( is-previous-event-false {mission_quoted} {format_sexp_string(mission.failure_event)} )'

    return None  # Unconditional

def generate_formula(mission: CampaignMission, next_mission_filename: Optional[str]) -> str:
    """
    Generates the mission progression logic (formula).

    Logic:
    - If an advance condition field is present (success_goal, success_event,
      failure_goal, or failure_event):
        ( cond
           ( ( <condition-sexp> ) ( next-mission "next" ) )
           ( ( true ) ( next-mission "current" ) )
        )
    - If no condition field is set (unconditional):
        ( cond
           ( ( true ) ( next-mission "next" ) )
           ( ( true ) ( next-mission "current" ) )
        )
    - If it's the last mission (next_mission_filename is None):
        Target is ( end-of-campaign ) instead of ( next-mission ... )
    """

    current_mission_quoted = format_sexp_string(mission.filename)

    # Determine the "success" action
    if next_mission_filename:
        next_action = f'( next-mission {format_sexp_string(next_mission_filename)} )'
    else:
        next_action = '( end-of-campaign )'

    # Repeat action (fallback)
    repeat_action = f'( next-mission {current_mission_quoted} )'

    # Build branches
    branches = []

    # Branch 1: Advance condition check
    condition = _build_condition_sexp(mission)
    if condition:
        branches.append(f'( {condition} {next_action} )')
    else:
        # Unconditional advancement
        branches.append(f'( ( true ) {next_action} )')

    # Branch 2: Fallback (Repeat)
    # Always added for robustness and to match standard format
    branches.append(f'( ( true ) {repeat_action} )')

    # Wrap in cond
    formula_body = "\n   ".join(branches)
    return f"( cond\n   {formula_body}\n)"

def write_fc2(fcif: FCIF, output_path: Path):
    """Generates the .fc2 file."""
    
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        # Header
        f.write(f"$Name: {fcif.campaign.name}\n")
        f.write("$Type: single\n")
        
        # Description with XSTR
        # Using -1 for ID as per standard for non-localized text, or allow tool to handle IDs later
        f.write("+Description:\n")
        f.write(f' XSTR("{fcif.campaign.description}", -1)\n')
        f.write("$end_multi_text\n\n")
        
        # Starting Loadout
        ships_str = ' '.join([f'"{s}"' for s in fcif.starting_loadout.ships])
        f.write(f'+Starting Ships: ( {ships_str} )\n\n')
        
        weapons_str = ' '.join([f'"{w}"' for w in fcif.starting_loadout.weapons])
        f.write(f'+Starting Weapons: ( {weapons_str} )\n\n')
        
        # Missions
        for i, mission in enumerate(fcif.missions):
            f.write(f"$Mission: {mission.filename}\n")
            
            f.write("+Flags: 0\n")
            f.write("+Main Hall: \n")
            
            # Logic
            next_mission = None
            if i < len(fcif.missions) - 1:
                next_mission = fcif.missions[i+1].filename
            
            formula = generate_formula(mission, next_mission)
            f.write(f"+Formula: {formula}\n")
            
            # Level and Position
            # Level increments, Position is usually 1 in linear campaigns
            f.write(f"\n+Level: {i}\n")
            f.write("+Position: 1\n\n")
            
        f.write("#End\n")

# --- First Mission Loadout Check ---

def _collect_fsif_ships_and_weapons(fsif_path: Path, log_func) -> Optional[tuple]:
    """
    Parse an FSIF YAML file and collect all ship classes and weapons referenced.

    Returns a tuple (ship_classes: set, primary_weapons: set, secondary_weapons: set),
    or None if the file could not be loaded.

    Covers:
    - entities.ships[*].class  (standalone ships)
    - entities.ship_templates[name].class  (templates used by wings)
    - entities.wings[*].template -> resolved class from templates
    - weapons from standalone ships (entities.ships[*].weapons.primary/secondary)
    - weapons from templates (for wings and for standalone ships using a template)
    """
    try:
        with open(fsif_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        log_func(f"[WARNING] First mission check: could not load '{fsif_path}': {e}")
        return None

    if not isinstance(data, dict):
        log_func(f"[WARNING] First mission check: '{fsif_path}' did not parse as a YAML mapping.")
        return None

    entities = data.get('entities', {}) or {}
    templates_raw = entities.get('ship_templates', {}) or {}
    ships_raw = entities.get('ships', []) or []
    wings_raw = entities.get('wings', []) or []

    ship_classes: set = set()
    primary_weapons: set = set()
    secondary_weapons: set = set()

    def _add_weapons_from_mapping(weapons_mapping):
        """Extract primary/secondary weapons from a weapons dict."""
        if not isinstance(weapons_mapping, dict):
            return
        for w in (weapons_mapping.get('primary') or []):
            if w:
                primary_weapons.add(str(w))
        for w in (weapons_mapping.get('secondary') or []):
            if w:
                secondary_weapons.add(str(w))

    # --- Process templates ---
    templates: dict = {}  # name -> properties dict
    if isinstance(templates_raw, dict):
        for tname, tprops in templates_raw.items():
            if isinstance(tprops, dict):
                templates[tname] = tprops

    # --- Process standalone ships ---
    if isinstance(ships_raw, list):
        for ship in ships_raw:
            if not isinstance(ship, dict):
                continue
            # If the ship references a template, merge: template provides class/weapons,
            # ship-level class overrides template class if present.
            tname = ship.get('template')
            tprops = templates.get(tname, {}) if tname else {}

            cls = ship.get('class') or tprops.get('class')
            if cls:
                ship_classes.add(str(cls))

            # Weapons: ship-level overrides template weapons
            ship_weapons = ship.get('weapons') or tprops.get('weapons')
            _add_weapons_from_mapping(ship_weapons)

    # --- Process wings (resolved via templates) ---
    if isinstance(wings_raw, list):
        for wing in wings_raw:
            if not isinstance(wing, dict):
                continue
            tname = wing.get('template')
            tprops = templates.get(tname, {}) if tname else {}

            cls = tprops.get('class')
            if cls:
                ship_classes.add(str(cls))

            _add_weapons_from_mapping(tprops.get('weapons'))

    return ship_classes, primary_weapons, secondary_weapons


def check_first_mission_loadout(fsif_path_str: str, fcif: 'FCIF', log_func) -> None:
    """
    Check that all ship classes and weapons used in the first FSIF mission are
    present in the FCIF starting_loadout.

    Issues [WARNING] messages for any missing items but does NOT abort conversion.

    :param fsif_path_str: Path to the first mission's .fsif file.
    :param fcif: The loaded FCIF object.
    :param log_func: Logging function.
    """
    fsif_path = Path(fsif_path_str)
    if not fsif_path.exists() or not fsif_path.is_file():
        log_func(f"[WARNING] First mission check: file not found at '{fsif_path}'. Skipping check.")
        return

    if fsif_path.suffix.lower() != '.fsif':
        log_func(f"[WARNING] First mission check: '{fsif_path}' does not have a .fsif extension. Skipping check.")
        return

    log_func(f"[INFO] Running first mission loadout check against '{fsif_path.name}'...")

    result = _collect_fsif_ships_and_weapons(fsif_path, log_func)
    if result is None:
        return  # Error already logged inside helper

    mission_ships, mission_primaries, mission_secondaries = result

    loadout_ships = set(fcif.starting_loadout.ships)
    loadout_weapons = set(fcif.starting_loadout.weapons)

    missing_ships = sorted(mission_ships - loadout_ships)
    missing_weapons = sorted((mission_primaries | mission_secondaries) - loadout_weapons)

    warnings_issued = False

    if missing_ships:
        log_func(
            f"[WARNING] First mission check: the following ship class(es) used in "
            f"'{fsif_path.name}' are NOT in starting_loadout.ships:"
        )
        for s in missing_ships:
            log_func(f"[WARNING]   - \"{s}\"")
        log_func(
            "[WARNING] Ships not in starting_loadout will not appear in the first mission. "
            "Add them to starting_loadout.ships in the FCIF."
        )
        warnings_issued = True

    if missing_weapons:
        log_func(
            f"[WARNING] First mission check: the following weapon(s) used in "
            f"'{fsif_path.name}' are NOT in starting_loadout.weapons:"
        )
        for w in missing_weapons:
            log_func(f"[WARNING]   - \"{w}\"")
        log_func(
            "[WARNING] Weapons not in starting_loadout will not be available in the first mission. "
            "Add them to starting_loadout.weapons in the FCIF."
        )
        warnings_issued = True

    if not warnings_issued:
        log_func("[INFO] First mission loadout check passed: all ships and weapons are in starting_loadout.")


def process_campaign(
    input_file: str,
    output_file: Optional[str] = None,
    first_mission: Optional[str] = None,
    log_func=print,
) -> bool:
    """
    Core conversion logic for the campaign.
    
    :param input_file: Path to the .fcif file.
    :param output_file: Optional path for the output .fc2 file.
    :param first_mission: Optional path to the first mission's .fsif file for loadout validation.
    :param log_func: Function to use for logging output (default: print).
    :return: True if successful, False otherwise.
    """
    input_path = Path(input_file)
    
    if output_file is None:
        output_path = input_path.with_suffix('.fc2')
    else:
        output_path = Path(output_file)

    if not input_path.exists() or not input_path.is_file():
        log_func(f"[ERROR] Input file not found at '{input_path}'")
        return False

    if input_path.suffix.lower() != '.fcif':
        log_func("[ERROR] Input file must have a .fcif extension.")
        return False

    log_func(f"[INFO] Loading FCIF: {input_path}")
    fcif_data = load_fcif(input_path, log_func)
    
    if not fcif_data:
        return False

    # Optional: first-mission loadout check
    if first_mission:
        check_first_mission_loadout(first_mission, fcif_data, log_func)

    log_func(f"[INFO] Converting '{fcif_data.campaign.name}' ({len(fcif_data.missions)} missions)...")
    
    try:
        write_fc2(fcif_data, output_path)
        log_func(f"[SUCCESS] Successfully wrote: {output_path}")
        return True
    except Exception as e:
        log_func(f"[ERROR] Error writing output: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert FCIF (Freespace Campaign Intermediate File) to FC2 format.")
    parser.add_argument("input", type=str, help="Input .fcif file")
    parser.add_argument("-o", "--output", type=str, help="Output .fc2 file (optional, defaults to input filename with .fc2 extension)")
    parser.add_argument(
        "--first-mission",
        dest="first_mission",
        type=str,
        default=None,
        help=(
            "Path to the first mission's .fsif file. "
            "When provided, the converter checks that all ship classes and weapons used "
            "in that mission are present in starting_loadout and warns about any that are missing."
        ),
    )

    args = parser.parse_args()

    # Create a custom log_func for CLI that directs ERROR and FAILED to stderr
    def cli_log(msg: str):
        if msg.startswith("[ERROR]") or msg.startswith("[FAILED]"):
            print(msg, file=sys.stderr)
        else:
            print(msg)

    success = process_campaign(args.input, args.output, first_mission=args.first_mission, log_func=cli_log)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
