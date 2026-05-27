import argparse
import sys
import yaml
import logging
import re
from pathlib import Path
from typing import Annotated, List, Optional
from pydantic import AfterValidator, BaseModel, Field, ConfigDict, ValidationError, field_validator, model_validator

_root_dir = Path(__file__).resolve().parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
from common.utils import sanitize_path
from common.validation_utils import AsciiStr
from common.fs_data import ALLOWED_SHIP_CLASSES, ALLOWED_WEAPONS, PLAYER_START_WING_NAMES

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

logger = logging.getLogger(__name__)

# --- FCIF Data Models ---

def _check_no_double_quotes(field_name: str, v: str) -> str:
    """Reject a string that contains double quotes.

    All FCIF string fields that are emitted inside FC2 quoted strings must not
    contain double-quote characters.  A ``"`` inside such a string would break the
    FC2 SEXP parser.

    Raises ValueError when a double quote is found.
    """
    if '"' in v:
        raise ValueError(
            f"'{field_name}' must not contain double quotes (\"), "
            f"because the value is emitted inside a quoted string in the generated "
            f".fc2 file and a '\"' would break its SEXP syntax."
        )
    return v


class CampaignInfo(BaseModel):
    """Pydantic model for the ``campaign:`` section of an FCIF file.

    Represents the top-level campaign metadata that is emitted into the ``.fc2``
    header.

    Fields:
        name:        Display name of the campaign.  Written verbatim after
                     ``$Name:`` in the generated ``.fc2`` file.
        description: Human-readable campaign description.  Wrapped in an
                     ``XSTR(...)`` block for FSO localization support.

    Constraints (enforced by field validators):
        - Both fields must be pure ASCII (non-ASCII characters raise
          ``ValidationError``).
        - ``description`` must not contain double-quote characters (``"``),
          because it is emitted inside a quoted FSO string; a ``"`` would break
          the ``.fc2`` SEXP parser.

    Unrecognized extra fields are rejected (``extra='forbid'``).
    """
    model_config = ConfigDict(extra='forbid')
    name: AsciiStr
    description: AsciiStr

    @field_validator('description')
    @classmethod
    def no_double_quotes_in_description(cls, v: str) -> str:
        return _check_no_double_quotes('campaign.description', v)

class StartingLoadout(BaseModel):
    """Pydantic model for the ``starting_loadout:`` section of an FCIF file.

    Specifies the ship classes and weapons that are available to the player at
    campaign start.  In FSO, all ships and weapons are locked by default; only
    items listed here (or unlocked via ``allow-ship``/``allow-weapon`` SEXPs in
    a prior mission) will appear on the loadout screen.

    Fields:
        ships:   List of FSO ship class tokens available at campaign start
                 (e.g. ``"GTF Ulysses"``).  Defaults to an empty list.
        weapons: List of FSO weapon tokens available at campaign start
                 (e.g. ``"ML-16 Laser"``).  Defaults to an empty list.

    Constraints (enforced by field validators):
        - All entries must be pure ASCII.
        - Every ship token must be a recognized FSO ship class
          (checked against ``ALLOWED_SHIP_CLASSES``).
        - Every weapon token must be a recognized FSO weapon token
          (checked against ``ALLOWED_WEAPONS``).

    These lists are written verbatim as ``+Starting Ships:`` and
    ``+Starting Weapons:`` in the generated ``.fc2`` file.

    Unrecognized extra fields are rejected (``extra='forbid'``).
    """
    model_config = ConfigDict(extra='forbid')
    ships: List[AsciiStr] = Field(default_factory=list)
    weapons: List[AsciiStr] = Field(default_factory=list)

    @field_validator('ships')
    @classmethod
    def validate_ships(cls, v: List[str]) -> List[str]:
        for ship in v:
            if ship not in ALLOWED_SHIP_CLASSES:
                raise ValueError(f"Ship '{ship}' is not a valid FSO ship class token.")
        return v

    @field_validator('weapons')
    @classmethod
    def validate_weapons(cls, v: List[str]) -> List[str]:
        for weapon in v:
            if weapon not in ALLOWED_WEAPONS:
                raise ValueError(f"Weapon '{weapon}' is not a valid FSO weapon token.")
        return v

class CampaignMission(BaseModel):
    """Pydantic model for a single entry in the ``missions:`` list of an FCIF file.

    Each ``CampaignMission`` corresponds to one ``$Mission:`` block written into
    the ``.fc2`` file.  The order of missions in the FCIF list determines
    campaign progression; the first mission is the starting mission and the last
    one targets ``end-of-campaign``.

    Fields:
        filename:      The bare ``.fs2`` filename of the mission
                       (e.g. ``"m01.fs2"``).  Must not include directory
                       components.  Written after ``$Mission:`` in the ``.fc2``
                       file.
        success_goal:  Name of a mission goal that must be *true* (succeeded)
                       to advance to the next mission.  Emits
                       ``is-previous-goal-true`` in the generated SEXP formula.
        success_event: Name of a mission event that must be *true* (fired) to
                       advance.  Emits ``is-previous-event-true``.
        failure_goal:  Name of a mission goal that must be *false* (failed) to
                       advance.  Emits ``is-previous-goal-false``.
        failure_event: Name of a mission event that must be *false* (did not
                       fire) to advance.  Emits ``is-previous-event-false``.

    At most one advance condition field may be set per mission; setting more
    than one is a ``ValidationError``.  If no condition field is set the
    campaign advances unconditionally (the converter will log a warning).

    Constraints (enforced by field validators):
        - ``filename`` must end with ``.fs2``, must not contain path separators
          (``/`` or ``\\``), must be pure ASCII, and must not contain double
          quotes (``"``).
        - All four advance condition fields must not contain double quotes (``"``),
          because they are emitted inside quoted strings in ``.fc2`` SEXP logic.
        - All string fields must be pure ASCII.

    Unrecognized extra fields are rejected (``extra='forbid'``).
    """
    model_config = ConfigDict(extra='forbid')
    filename: AsciiStr
    success_goal: Optional[AsciiStr] = None
    success_event: Optional[AsciiStr] = None
    failure_goal: Optional[AsciiStr] = None
    failure_event: Optional[AsciiStr] = None

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Reject filenames that contain path separators, lack the .fs2 extension, or contain double quotes."""
        if '/' in v or '\\' in v:
            raise ValueError(
                f"Mission filename must be only the bare mission file name, such as 'missionname.fs2'; "
                f"it must not contain path separators ('/' or '\\'). Found: '{v}'. "
            )
        if not v.lower().endswith('.fs2'):
            raise ValueError(
                f"Mission filename must end with the '.fs2' extension. Found: '{v}'. "
                f"Example of a correct value: 'missionname.fs2'."
            )
        _check_no_double_quotes('missions[*].filename', v)
        return v

    @field_validator('success_goal', 'success_event', 'failure_goal', 'failure_event', mode='before')
    @classmethod
    def no_double_quotes_in_condition_fields(cls, v, info):
        """Reject advance condition names that contain double quotes."""
        if v is not None:
            _check_no_double_quotes(f'missions[*].{info.field_name}', str(v))
        return v

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

SUPPORTED_FCIF_VERSIONS = {"1.0"}

class FCIF(BaseModel):
    """Pydantic model for the complete FCIF campaign definition file.

    This is the top-level model that captures the full contents of a ``.fcif``
    YAML file.  It is produced by ``load_fcif()`` and consumed by
    ``process_campaign()`` to generate a ``.fc2`` campaign file for FSO.

    Fields:
        fcif_version:    FCIF format version string.  Must be ``"1.0"``; any
                         other value causes a ``ValidationError``.  Non-string
                         values (e.g. bare YAML numbers such as ``1.0``) are
                         coerced to string before the version check.
        campaign:        Top-level campaign metadata (name, description).
        starting_loadout: Ships and weapons available to the player from the
                         start of the campaign.
        missions:        Ordered list of missions.  The sequence determines
                         campaign progression.

    Unrecognized extra fields are rejected (``extra='forbid'``).
    """
    model_config = ConfigDict(extra='forbid')
    fcif_version: str = "1.0"
    
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

def load_fcif(path: Path) -> Optional[FCIF]:
    """Load and validate an FCIF YAML file, returning the hydrated model.

    Reads the file at *path*, parses it as YAML, and constructs an ``FCIF``
    Pydantic model from the resulting dictionary.  All schema constraints
    (field types, ASCII requirements, version check, mutual exclusivity of
    advance conditions, etc.) are enforced during construction.

    Args:
        path: Filesystem path to the ``.fcif`` file to load.

    Returns:
        A validated ``FCIF`` instance on success, or ``None`` if any of the
        following errors occur:

        - ``yaml.YAMLError``: the file is not valid YAML.
        - ``pydantic.ValidationError``: the YAML data fails schema validation.
        - Any other exception (e.g. ``OSError`` for a missing/unreadable file).

    All errors are logged at ERROR level before returning ``None``.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return FCIF(**data)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML: {e}")
        return None
    except ValidationError as e:
        logger.error(f"Validation Error:\n{e}")
        return None
    except Exception as e:
        logger.error(f"Error loading file: {e}")
        return None

def quote_string(s: str) -> str:
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
    filename_quoted = quote_string(mission.filename)

    if mission.success_goal:
        return f'( is-previous-goal-true {filename_quoted} {quote_string(mission.success_goal)} )'
    if mission.success_event:
        return f'( is-previous-event-true {filename_quoted} {quote_string(mission.success_event)} )'
    if mission.failure_goal:
        return f'( is-previous-goal-false {filename_quoted} {quote_string(mission.failure_goal)} )'
    if mission.failure_event:
        return f'( is-previous-event-false {filename_quoted} {quote_string(mission.failure_event)} )'

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

    filename_quoted = quote_string(mission.filename)

    # Determine the "success" action
    if next_mission_filename:
        next_action = f'( next-mission {quote_string(next_mission_filename)} )'
    else:
        next_action = '( end-of-campaign )'

    # Repeat action (fallback)
    repeat_action = f'( next-mission {filename_quoted} )'

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
    """Write the ``.fc2`` campaign file for the given validated FCIF data.

    Generates the full FSO ``.fc2`` text format and writes it to *output_path*.
    The generated file always uses Unix line endings (``\\n``) and UTF-8
    encoding.

    Output structure:
        - ``$Name:`` / ``$Type: single`` header.
        - ``+Description: XSTR(...)`` block (FSO localization wrapper).
        - ``+Starting Ships: (...)`` and ``+Starting Weapons: (...)`` lines.
        - One ``$Mission:`` block per entry in ``fcif.missions``, each
          containing ``+Flags:``, ``+Main Hall:``, ``+Formula:``, ``+Level:``,
          and ``+Position:`` fields.
        - ``#End`` terminator.

    The ``+Formula:`` for each mission is generated by ``generate_formula()``,
    which encodes the campaign progression logic as a ``( cond ... )`` SEXP.
    The level index (``+Level:``) is zero-based and increments with each
    mission; ``+Position:`` is always ``1`` for linear campaigns.

    Args:
        fcif:        Validated ``FCIF`` model to convert.
        output_path: Filesystem path where the ``.fc2`` file will be written.

    Raises:
        OSError: if the output file cannot be opened or written.
    """
    
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

# --- Campaign Loadout Check ---

def check_campaign_player_loadouts(fcif: 'FCIF', input_path: Path) -> bool:
    """Verify that all player ships and weapons are unlocked before they are used.

    For each mission in the campaign, the function:

    1. Infers the path to the corresponding ``.fsif`` file as
       ``<fcif_dir>/fsif/<mission_stem>.fsif`` (see ``_infer_fsif_path()``).
    2. Parses the FSIF file as raw YAML (no Pydantic validation).
    3. Collects every ship class and weapon reachable by the player in that
       mission, drawn from:
       - Friendly *Alpha*, *Beta*, and *Gamma* wings (the only wings shown on
         the FSO loadout screen) and their templates.
       - ``player_setup.additional_ship_choices[*].class``.
       - ``player_setup.additional_weapons[*]``.
       - The standalone ship named by ``player_setup.start_ship``, if it
         exists in ``entities.ships``.
    4. Checks that each discovered ship class and weapon is present in the
       cumulative *allowed* set (initialized from ``fcif.starting_loadout``
       and grown by any ``allow-ship``/``allow-weapon`` SEXPs found in
       previously processed missions).
    5. After validating the mission, scans every string value in the FSIF for
       ``allow-ship`` and ``allow-weapon`` SEXP patterns and adds any matched
       tokens to the allowed set for subsequent missions.

    File-not-found and parse failures for a mission's FSIF are **non-fatal**:
    a WARNING is logged and that mission is skipped.  An actual loadout
    violation (a ship or weapon used but not yet unlocked) is **fatal**: an
    ERROR is logged and the function returns ``False`` immediately.

    Args:
        fcif:       Validated ``FCIF`` model containing ``starting_loadout``
                    and the ordered ``missions`` list.
        input_path: Path to the ``.fcif`` file being converted; used to
                    resolve the sibling ``fsif/`` directory.

    Returns:
        ``True`` if all reachable player ships and weapons are unlocked by the
        time each mission is reached, or if every mission's FSIF is skipped
        (missing/unreadable).  ``False`` if any loadout violation is found.
    """
    allowed_ships = set(fcif.starting_loadout.ships)
    allowed_weapons = set(fcif.starting_loadout.weapons)

    # Only Alpha, Beta, and Gamma are shown on the FSO loadout screen.
    player_wings = PLAYER_START_WING_NAMES

    for mission in fcif.missions:
        mission_filename = Path(mission.filename).stem
        fsif_path = input_path.parent / "fsif" / f"{mission_filename}.fsif"
        
        if not fsif_path.exists() or not fsif_path.is_file():
            logger.warning(f"Campaign loadout check: file not found at '{fsif_path}'. Skipping check for this mission.")
            continue
            
        try:
            with open(fsif_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
                data = yaml.safe_load(raw_content)
        except Exception as e:
            logger.warning(f"Campaign loadout check: could not load '{fsif_path}': {e}")
            continue

        if not isinstance(data, dict):
            logger.warning(f"Campaign loadout check: '{fsif_path}' did not parse as a YAML mapping.")
            continue
            
        # 1. Extract player loadout for the current mission
        mission_player_ships = set()
        mission_player_weapons = set()

        player_setup = data.get('player_setup', {}) or {}
        if isinstance(player_setup, dict):
            # start_ship
            start_ship = player_setup.get('start_ship')
            
            # player_setup.additional_ship_choices
            additional_ship_choices = player_setup.get('additional_ship_choices', []) or []
            if isinstance(additional_ship_choices, list):
                for es in additional_ship_choices:
                    if isinstance(es, dict) and 'class' in es:
                        mission_player_ships.add(str(es['class']))
            
            # player_setup.additional_weapons
            additional_weapons = player_setup.get('additional_weapons', []) or []
            if isinstance(additional_weapons, list):
                for ew in additional_weapons:
                    mission_player_weapons.add(str(ew))
        else:
            start_ship = None
                    
        entities = data.get('entities', {}) or {}
        templates_raw = entities.get('ship_templates', {}) or {}
        ships_raw = entities.get('ships', []) or []
        wings_raw = entities.get('wings', []) or []

        templates = {}
        if isinstance(templates_raw, dict):
            for tname, tprops in templates_raw.items():
                if isinstance(tprops, dict):
                    templates[tname] = tprops

        def _add_weapons_from_mapping(weapons_mapping):
            if not isinstance(weapons_mapping, dict):
                return
            for w in (weapons_mapping.get('primary') or []):
                if w:
                    mission_player_weapons.add(str(w))
            for w in (weapons_mapping.get('secondary') or []):
                if w:
                    mission_player_weapons.add(str(w))

        # Check wings
        if isinstance(wings_raw, list):
            for wing in wings_raw:
                if not isinstance(wing, dict):
                    continue
                wname = wing.get('name')
                if wname in player_wings:
                    tname = wing.get('template')
                    if tname is not None and not isinstance(tname, str):
                        logger.error(f"Mission '{fsif_path.name}': Wing '{wname}' must use a string reference for 'template'.")
                        return False
                    tprops = templates.get(tname, {}) if tname else {}
                    cls = tprops.get('class')
                    if cls:
                        mission_player_ships.add(str(cls))
                    _add_weapons_from_mapping(tprops.get('weapons'))

        # Check start_ship if it's a standalone ship
        if start_ship and isinstance(ships_raw, list):
            for ship in ships_raw:
                if not isinstance(ship, dict):
                    continue
                if ship.get('name') == start_ship:
                    tname = ship.get('template')
                    if tname is not None and not isinstance(tname, str):
                        logger.error(f"Mission '{fsif_path.name}': Ship '{start_ship}' must use a string reference for 'template'.")
                        return False
                    tprops = templates.get(tname, {}) if tname else {}
                    cls = ship.get('class') or tprops.get('class')
                    if cls:
                        mission_player_ships.add(str(cls))
                    ship_weapons = ship.get('weapons') or tprops.get('weapons')
                    _add_weapons_from_mapping(ship_weapons)
                    break

        # 2. Validate
        missing_ships = sorted(mission_player_ships - allowed_ships)
        missing_weapons = sorted(mission_player_weapons - allowed_weapons)

        if missing_ships or missing_weapons:
            error_msg = f"Campaign loadout check failed in mission '{fsif_path.name}':\n"
            if missing_ships:
                error_msg += "  The following player ship class(es) were used but not granted:\n"
                for s in missing_ships:
                    error_msg += f"    - \"{s}\"\n"
            if missing_weapons:
                error_msg += "  The following player weapon(s) were used but not granted:\n"
                for w in missing_weapons:
                    error_msg += f"    - \"{w}\"\n"
            error_msg += "Actionable advice: Add them to 'starting_loadout' in the FCIF or grant them via 'allow-ship'/'allow-weapon' SEXP in a previous mission."
            logger.error(error_msg)
            return False

        # 3. State Update (Granting items for the next mission)
        def extract_all_strings(obj):
            if isinstance(obj, str):
                yield obj
            elif isinstance(obj, dict):
                for v in obj.values():
                    yield from extract_all_strings(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from extract_all_strings(item)

        for text_val in extract_all_strings(data):
            for s in re.findall(r'\(\s*allow-ship\s+"([^"]+)"', text_val):
                allowed_ships.add(s)
            for w in re.findall(r'\(\s*allow-weapon\s+"([^"]+)"', text_val):
                allowed_weapons.add(w)

    logger.info("Campaign loadout check passed: all player ships and weapons are covered.")
    return True


def _infer_fsif_path(input_path: Path, mission: 'CampaignMission') -> Path:
    """Infer the expected ``.fsif`` file path for a campaign mission.

    Constructs the path ``<fcif_dir>/fsif/<mission_stem>.fsif``, where
    ``<fcif_dir>`` is the parent directory of *input_path* and
    ``<mission_stem>`` is the filename of ``mission.filename`` without its
    ``.fs2`` extension.

    This convention requires all FSIF source files to be co-located in a
    ``fsif/`` subdirectory next to the ``.fcif`` campaign file.

    Args:
        input_path: Path to the ``.fcif`` file being converted.
        mission:    The ``CampaignMission`` entry whose FSIF path is needed.

    Returns:
        The expected ``Path`` to the ``.fsif`` file (which may or may not
        exist on disk).
    """
    mission_stem = Path(mission.filename).stem
    return input_path.parent / "fsif" / f"{mission_stem}.fsif"


def _get_advance_condition_reference(mission: 'CampaignMission'):
    """Return the active advance condition for a mission as a structured tuple.

    Inspects the four mutually exclusive advance condition fields on *mission*
    and returns metadata about the one that is set.  If no condition is set,
    all three tuple elements are ``None``.

    The returned ``collection_key`` indicates which FSIF ``mission_flow``
    sub-list to search when verifying the reference (``"goals"`` for goal-based
    conditions, ``"events"`` for event-based conditions).

    Args:
        mission: The ``CampaignMission`` entry to inspect.

    Returns:
        A 3-tuple ``(field_name, referenced_name, collection_key)`` where:

        - *field_name* is the FCIF field that is set (e.g. ``"success_goal"``).
        - *referenced_name* is the goal or event name string that was authored.
        - *collection_key* is ``"goals"`` or ``"events"``.

        Returns ``(None, None, None)`` when no advance condition is set.
    """
    if mission.success_goal is not None:
        return ("success_goal", mission.success_goal, "goals")
    if mission.failure_goal is not None:
        return ("failure_goal", mission.failure_goal, "goals")
    if mission.success_event is not None:
        return ("success_event", mission.success_event, "events")
    if mission.failure_event is not None:
        return ("failure_event", mission.failure_event, "events")
    return (None, None, None)


def check_campaign_advance_condition_references(fcif: 'FCIF', input_path: Path) -> bool:
    """Verify that every advance condition references an existing goal or event.

    For each mission that has an advance condition field set
    (``success_goal``, ``failure_goal``, ``success_event``, or
    ``failure_event``), this function:

    1. Infers the path to the corresponding ``.fsif`` file via
       ``_infer_fsif_path()``.
    2. Reads and parses the FSIF file as raw YAML.
    3. Extracts every goal/event ``name`` from
       ``mission_flow.goals`` or ``mission_flow.events`` (depending on the
       condition type).
    4. Checks that the referenced name is present in the extracted set.

    Missions without any advance condition field are silently skipped.

    All failures in this function are **fatal** — the function accumulates
    errors across all missions and returns ``False`` if any reference check
    fails.  Unlike the loadout check, a missing or unparseable FSIF for a
    mission *with* an advance condition is also a fatal error (not a warning),
    because the reference cannot be verified.

    When all references are valid, a confirmation INFO message is logged.

    Args:
        fcif:       Validated ``FCIF`` model containing the ordered missions.
        input_path: Path to the ``.fcif`` file being converted; used to
                    resolve the sibling ``fsif/`` directory via
                    ``_infer_fsif_path()``.

    Returns:
        ``True`` if every advance condition reference resolves to a defined
        goal or event in the corresponding FSIF file (or if no missions have
        advance conditions).  ``False`` if any reference cannot be resolved.
    """
    ok = True

    for mission in fcif.missions:
        field_name, referenced_name, collection_key = _get_advance_condition_reference(mission)

        if referenced_name is None:
            # No advance condition set — nothing to verify.
            continue

        fsif_path = _infer_fsif_path(input_path, mission)

        if not fsif_path.exists() or not fsif_path.is_file():
            logger.error(
                f"Campaign advance condition reference check failed in mission '{mission.filename}':\n"
                f"  Field '{field_name}' references {collection_key[:-1]} '{referenced_name}', "
                f"but the FSIF file could not be found at '{fsif_path}'.\n"
                f"  Actionable advice: Ensure the FSIF file exists at the expected path "
                f"(campaign_folder/fsif/{Path(mission.filename).stem}.fsif), or remove the advance condition field."
            )
            ok = False
            continue

        try:
            with open(fsif_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            logger.error(
                f"Campaign advance condition reference check failed in mission '{mission.filename}':\n"
                f"  Field '{field_name}' references {collection_key[:-1]} '{referenced_name}', "
                f"but the FSIF file '{fsif_path}' could not be parsed: {e}\n"
                f"  Actionable advice: Fix the YAML syntax in the FSIF file."
            )
            ok = False
            continue

        if not isinstance(data, dict):
            logger.error(
                f"Campaign advance condition reference check failed in mission '{mission.filename}':\n"
                f"  Field '{field_name}' references {collection_key[:-1]} '{referenced_name}', "
                f"but the FSIF file '{fsif_path}' did not parse as a YAML mapping.\n"
                f"  Actionable advice: Ensure the FSIF file is a valid YAML mapping."
            )
            ok = False
            continue

        mission_flow = data.get('mission_flow') or {}
        collection = mission_flow.get(collection_key) or []

        # Extract defined names from the collection (goals or events)
        defined_names = set()
        if isinstance(collection, list):
            for item in collection:
                if isinstance(item, dict):
                    name = item.get('name')
                    if isinstance(name, str) and name:
                        defined_names.add(name)

        if referenced_name not in defined_names:
            if defined_names:
                available = ", ".join(f"'{n}'" for n in sorted(defined_names))
                available_hint = f"\n  Available {collection_key}: {available}"
            else:
                available_hint = f"\n  No {collection_key} are defined in mission_flow.{collection_key} of '{fsif_path.name}'."

            logger.error(
                f"Campaign advance condition reference check failed in mission '{mission.filename}':\n"
                f"  Field '{field_name}' references {collection_key[:-1]} '{referenced_name}', "
                f"but no {collection_key[:-1]} with that name exists in '{fsif_path}'."
                f"{available_hint}\n"
                f"  Actionable advice: Fix the FCIF condition name to match an existing "
                f"{collection_key[:-1]} in mission_flow.{collection_key}, or define the referenced "
                f"{collection_key[:-1]} in the FSIF mission file."
            )
            ok = False

    if ok:
        logger.info("Campaign advance condition reference check passed: all referenced goals and events exist.")

    return ok


def check_campaign_advance_conditions(fcif: 'FCIF'):
    """Warn about missions that will advance unconditionally.

    Iterates over all missions in the campaign and logs a WARNING for each
    mission that has none of the four advance condition fields set
    (``success_goal``, ``success_event``, ``failure_goal``,
    ``failure_event``).  Such missions always advance to the next mission
    regardless of outcome, which is often unintentional.

    This check is **non-fatal** — it only logs warnings and does not affect
    the conversion result.  It is called by ``process_campaign()`` before the
    heavier reference and loadout checks.

    Args:
        fcif: Validated ``FCIF`` model whose missions are inspected.
    """
    for mission in fcif.missions:
        if not any([mission.success_goal, mission.success_event, mission.failure_goal, mission.failure_event]):
            logger.warning(f"Advance conditions check: Mission '{mission.filename}' has no advance conditions (success or failure goals/events) defined. It will advance unconditionally.")


def process_campaign(
    input_file: str,
    output_file: Optional[str] = None,
) -> bool:
    """Convert an FCIF campaign file to the FSO ``.fc2`` format.

    This is the main entry point for the conversion pipeline.  It orchestrates
    the following steps in order:

    1. **Input validation** — checks that *input_file* exists and has a
       ``.fcif`` extension.
    2. **FCIF loading** — calls ``load_fcif()`` to parse and schema-validate
       the YAML, including all Pydantic field constraints.
    3. **Advance condition warnings** — calls
       ``check_campaign_advance_conditions()`` to warn about missions that
       lack advance conditions and will advance unconditionally.
    4. **Advance condition reference check** (fatal) — calls
       ``check_campaign_advance_condition_references()`` to verify every
       referenced goal/event name exists in the corresponding FSIF file.
    5. **Player loadout check** (fatal) — calls
       ``check_campaign_player_loadouts()`` to verify that all player ships
       and weapons are unlocked before they are first used.
    6. **FC2 generation** — calls ``write_fc2()`` to emit the ``.fc2`` output
       file.

    Steps 3–5 are only executed when the campaign has at least one mission.
    The output file defaults to *input_file* with the extension replaced by
    ``.fc2`` when *output_file* is not supplied.

    Args:
        input_file:  Path to the ``.fcif`` source file.  May contain
                     surrounding quotes (handled by ``sanitize_path()``).
        output_file: Optional path for the generated ``.fc2`` file.  When
                     ``None``, the output is written next to the input file
                     with the ``.fc2`` extension.

    Returns:
        ``True`` on success (the ``.fc2`` file was written).
        ``False`` on any fatal error (file not found, validation failure,
        missing FSIF references, loadout violations, or write errors); the
        specific cause is logged at ERROR level before returning.
    """
    input_path = Path(sanitize_path(input_file))
    
    if output_file is None:
        output_path = input_path.with_suffix('.fc2')
    else:
        output_path = Path(sanitize_path(output_file))

    if not input_path.exists() or not input_path.is_file():
        logger.error(f"Input file not found at '{input_path}'")
        return False

    if input_path.suffix.lower() != '.fcif':
        logger.error("Input file must have a .fcif extension.")
        return False

    logger.info(f"Loading FCIF: {input_path}")
    fcif_data = load_fcif(input_path)
    
    if not fcif_data:
        return False

    if fcif_data.missions:
        check_campaign_advance_conditions(fcif_data)
        if not check_campaign_advance_condition_references(fcif_data, input_path):
            return False
        if not check_campaign_player_loadouts(fcif_data, input_path):
            return False

    logger.info(f"Converting '{fcif_data.campaign.name}' ({len(fcif_data.missions)} missions)...")
    
    try:
        write_fc2(fcif_data, output_path)
        logger.log(SUCCESS_LEVEL, f"Successfully wrote: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing output: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert FCIF (Freespace Campaign Intermediate Format) to FC2 format.")
    parser.add_argument("input", type=str, help="Input .fcif file")
    parser.add_argument("-o", "--output", type=str, help="Output .fc2 file (optional, defaults to input filename with .fc2 extension)")

    args = parser.parse_args()

    # Configure root logger for CLI
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    success = process_campaign(args.input, args.output)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
