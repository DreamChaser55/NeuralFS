# data_models.py
# Defines Pydantic models for the FSIF mission structure.

from __future__ import annotations
from typing import List, Dict, Any, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from common import fs_data

# --- Constants ---

DEFAULT_ORIENTATION = [
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0
]

# --- Helpers ---


def _normalize_vector(v: Any) -> List[float]:
    """Ensure a 3-element float list. Raises ValueError on any malformed or absent input.

    Only ``list`` and ``tuple`` inputs are accepted. Strings, bytes, mappings,
    and other arbitrary iterables are explicitly rejected to avoid silent
    misinterpretation (e.g. a string ``"123"`` being iterated character-by-character).
    """
    if v is None:
        raise ValueError("Expected a 3-element [x, y, z] list, got None.")
    if isinstance(v, (str, bytes, bytearray)):
        raise ValueError(
            f"Expected a 3-element [x, y, z] list, got a string/bytes value: {v!r}. "
            "Author positions and angles as a YAML list, e.g. [0.0, 0.0, 0.0]."
        )
    if isinstance(v, dict):
        raise ValueError(
            f"Expected a 3-element [x, y, z] list, got a mapping: {v!r}. "
            "Author positions and angles as a YAML list, e.g. [0.0, 0.0, 0.0]."
        )
    if not isinstance(v, (list, tuple)):
        raise ValueError(
            f"Expected a 3-element [x, y, z] list, got {type(v).__name__!r}: {v!r}. "
            "Author positions and angles as a YAML list, e.g. [0.0, 0.0, 0.0]."
        )
    items = v
    if len(items) != 3:
        raise ValueError(
            f"Expected a 3-element [x, y, z] list, got {len(items)} element(s): {v!r}"
        )
    try:
        return [float(items[0]), float(items[1]), float(items[2])]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Vector coordinates must be numbers, got: {v!r}") from e


def _normalize_sun_angles(v: Any) -> List[float]:
    """Ensure a 2-element [pitch, heading] float list for sun angles.

    Sun sprites are rotationally symmetric, so bank has no visible effect and
    is intentionally excluded from the FSIF sun schema. The FS2 writer
    hardcodes bank to 0.0 when emitting the +Angles line for suns.

    Only ``list`` and ``tuple`` inputs are accepted. Strings, bytes, mappings,
    and other arbitrary iterables are explicitly rejected to avoid silent
    misinterpretation.

    Raises ValueError on any malformed or absent input.
    """
    if v is None:
        raise ValueError(
            "Sun angles must be a 2-element [pitch, heading] list, got None. "
            "Bank is omitted because suns are rotationally symmetric."
        )
    if isinstance(v, (str, bytes, bytearray)):
        raise ValueError(
            f"Sun angles must be a 2-element [pitch, heading] list, got a string/bytes value: {v!r}. "
            "Author sun angles as a YAML list, e.g. [0.087266, 2.356194]. "
            "Bank is omitted because suns are rotationally symmetric."
        )
    if isinstance(v, dict):
        raise ValueError(
            f"Sun angles must be a 2-element [pitch, heading] list, got a mapping: {v!r}. "
            "Author sun angles as a YAML list, e.g. [0.087266, 2.356194]. "
            "Bank is omitted because suns are rotationally symmetric."
        )
    if not isinstance(v, (list, tuple)):
        raise ValueError(
            f"Sun angles must be a 2-element [pitch, heading] list, got {type(v).__name__!r}: {v!r}. "
            "Author sun angles as a YAML list, e.g. [0.087266, 2.356194]."
        )
    items = v
    if len(items) != 2:
        raise ValueError(
            f"Sun angles must be a 2-element [pitch, heading] list, "
            f"got {len(items)} element(s): {v!r}. "
            "Bank is omitted because suns are rotationally symmetric."
        )
    try:
        return [float(items[0]), float(items[1])]
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Sun angle values must be numbers, got: {v!r}"
        ) from e


def _normalize_orientation(v: Any) -> List[float]:
    """Ensure a 9-element float list (3×3 rotation matrix). Raises ValueError on bad input.

    Accepted forms:
    - A flat ``list`` or ``tuple`` of 9 numbers.
    - A 3×3 nested ``list`` or ``tuple`` of ``list``/``tuple`` rows (each with 3 numbers).

    Strings, bytes, mappings, and other arbitrary iterables are explicitly
    rejected to avoid silent misinterpretation (e.g. a 9-character string
    being iterated character by character).
    """
    if v is None:
        raise ValueError("orientation must be a 9-element flat list or 3×3 nested list, got None.")
    if isinstance(v, (str, bytes, bytearray)):
        raise ValueError(
            f"orientation must be a 9-element flat list or 3×3 nested list, "
            f"got a string/bytes value: {v!r}. "
            "Author orientation as a YAML list of 9 floats, e.g. [1, 0, 0, 0, 1, 0, 0, 0, 1]."
        )
    if isinstance(v, dict):
        raise ValueError(
            f"orientation must be a 9-element flat list or 3×3 nested list, "
            f"got a mapping: {v!r}. "
            "Author orientation as a YAML list of 9 floats, e.g. [1, 0, 0, 0, 1, 0, 0, 0, 1]."
        )
    if not isinstance(v, (list, tuple)):
        raise ValueError(
            f"orientation must be a 9-element flat list or 3×3 nested list, "
            f"got {type(v).__name__!r}: {v!r}. "
            "Author orientation as a YAML list of 9 floats, e.g. [1, 0, 0, 0, 1, 0, 0, 0, 1]."
        )

    # Handle nested 3×3 form: each element must also be a list/tuple (not a string/dict/etc.)
    flat: List[float] = []
    if len(v) > 0 and isinstance(v[0], (list, tuple)):
        for row in v:
            if not isinstance(row, (list, tuple)):
                raise ValueError(
                    f"orientation 3×3 rows must each be a list or tuple of 3 numbers, "
                    f"got row {row!r}."
                )
            flat.extend(row)
    else:
        flat = list(v)

    if len(flat) != 9:
        raise ValueError(
            f"orientation must have exactly 9 elements, got {len(flat)}: {v!r}"
        )
    try:
        return [float(x) for x in flat]
    except (TypeError, ValueError) as e:
        raise ValueError(f"orientation elements must be numbers, got: {v!r}") from e


def _none_to_empty_list(v: Any) -> list:
    """Pydantic ``mode='before'`` normalizer: coerce ``None`` to ``[]``.

    Optional FSIF list fields may carry an explicit YAML ``null`` value which
    YAML parses as Python ``None``.  Pydantic v2 rejects ``None`` for a
    ``List[X]`` field even when the field has a ``default_factory``, because
    the factory only runs for absent keys, not for explicitly-supplied
    ``None``.  This helper is used as a ``field_validator(mode='before')`` on
    every runtime list field that authors may legitimately leave as ``null``.
    """
    if v is None:
        return []
    return v


def _normalize_ambient_light_rgb(v: Any) -> List[int]:
    """Ensure ambient light is a 3-element RGB list with 0-255 integer channels."""
    if v is None:
        return [0, 0, 0]

    if isinstance(v, (list, tuple)):
        if len(v) != 3:
            raise ValueError("ambient_light_level must be a 3-item RGB list: [red, green, blue].")

        rgb = []
        channel_names = ('red', 'green', 'blue')
        for idx, item in enumerate(v):
            if isinstance(item, bool) or not isinstance(item, int):
                raise ValueError(
                    f"ambient_light_level {channel_names[idx]} channel must be an integer in range 0..255."
                )
            if not 0 <= item <= 255:
                raise ValueError(
                    f"ambient_light_level {channel_names[idx]} channel {item} is out of range 0..255."
                )
            rgb.append(int(item))

        return rgb

    raise ValueError("ambient_light_level must be authored as [red, green, blue].")


def pack_ambient_light_rgb(rgb: Any) -> int:
    """Convert [red, green, blue] into the packed FS2 ambient-light integer."""
    red, green, blue = _normalize_ambient_light_rgb(rgb)
    return red | (green << 8) | (blue << 16)


def _validate_arrival_method_token(v: Any) -> str:
    """Validate that v is a canonical FSIF arrival_method token.

    Returns the validated string value unchanged.
    Raises ValueError if the value is not in ALLOWED_ARRIVAL_METHODS.
    """
    if not isinstance(v, str):
        raise ValueError(f"arrival_method must be a string, got {type(v).__name__!r}.")
    if v not in fs_data.ALLOWED_ARRIVAL_METHODS:
        allowed = ', '.join(f"'{m}'" for m in sorted(fs_data.ALLOWED_ARRIVAL_METHODS))
        raise ValueError(
            f"Invalid arrival_method '{v}'. "
            f"Allowed values: {allowed}."
        )
    return v


def _validate_departure_method_token(v: Any) -> str:
    """Validate that v is a canonical FSIF departure_method token.

    Returns the validated string value unchanged.
    Raises ValueError if the value is not in ALLOWED_DEPARTURE_METHODS.
    """
    if not isinstance(v, str):
        raise ValueError(f"departure_method must be a string, got {type(v).__name__!r}.")
    if v not in fs_data.ALLOWED_DEPARTURE_METHODS:
        allowed = ', '.join(f"'{m}'" for m in sorted(fs_data.ALLOWED_DEPARTURE_METHODS))
        raise ValueError(
            f"Invalid departure_method '{v}'. "
            f"Allowed values: {allowed}."
        )
    return v


# =============================================================================
# --- Authored FSIF Input Schema (strict Pydantic pre-validation) ---
# =============================================================================
#
# These models validate the raw YAML content against the current FSIF authored
# schema BEFORE any loader normalization (template merging, wing expansion,
# bounds -> min_vec/max_vec, dock block -> docked_with/etc.).
#
# All models use extra='forbid' so any unknown keys are rejected before the
# loader processes the document.
#
# Key differences from the runtime models below:
#   - No internal fields (docked_with / docker_point / dockee_point on ships).
#   - dock: DockInput uses 'dockee' key, not the internal 'docked_with'.
#   - AsteroidFieldInput uses authored 'bounds' mapping, not min_vec/max_vec.
#   - BriefingIconInput accepts [x,z] 2-element map_position authored by author.
#   - ShipTemplateInput explicitly excludes forbidden template fields.
# =============================================================================

class MissionInfoInput(BaseModel):
    """Raw FSIF ``mission_info`` mapping; validated before loader normalization applies defaults."""
    model_config = ConfigDict(extra='forbid')
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    game_type: Optional[str] = None
    flags: Optional[List[str]] = None
    disallow_support_ships: Optional[bool] = None


class NebulaInput(BaseModel):
    """Raw FSIF ``environment.nebula`` mapping; all fields optional as authored."""
    model_config = ConfigDict(extra='forbid')
    enabled: Optional[bool] = None
    pattern: Optional[str] = None
    sensor_range: Optional[float] = None
    storm: Optional[str] = None
    cloud_sprites: Optional[List[str]] = None


class BoundsInput(BaseModel):
    """Authored bounding box for asteroid fields. Loader converts to min_vec/max_vec."""
    model_config = ConfigDict(extra='forbid')
    min: Optional[List[float]] = None
    max: Optional[List[float]] = None


class AsteroidFieldInput(BaseModel):
    """Raw FSIF ``environment.asteroid_field`` mapping including authored ``bounds`` key.

    The loader converts ``bounds.min``/``bounds.max`` to ``min_vec``/``max_vec`` before
    constructing the runtime ``AsteroidField`` model.
    """
    model_config = ConfigDict(extra='forbid')
    object_type: Optional[str] = None
    behavior: Optional[str] = None
    num_objects: Optional[int] = None
    average_speed: Optional[float] = None
    bounds: Optional[BoundsInput] = None
    object_variants: Optional[List[str]] = None
    target_ships: Optional[List[str]] = None


class EnvironmentInput(BaseModel):
    """Raw FSIF ``environment`` mapping; validated before nebula-flag injection and asteroid-field normalization."""
    model_config = ConfigDict(extra='forbid')
    ambient_light_level: Any = None
    # Reuse existing Sun/BackgroundBitmap runtime models here because they
    # already have extra='forbid' and correct field-level validators.
    suns: Optional[List[Any]] = None
    background_bitmaps: Optional[List[Any]] = None
    nebula: Optional[NebulaInput] = None
    asteroid_field: Optional[AsteroidFieldInput] = None


class ShipChoiceInput(BaseModel):
    """Alternative ship pool entry for the loadout screen."""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    ship_class: str = Field(..., alias='class')
    count: int = Field(..., ge=1)


class PlayerSetupInput(BaseModel):
    """Raw FSIF ``player_setup`` mapping; validated before loader normalizes optional list fields."""
    model_config = ConfigDict(extra='forbid')
    start_ship: str
    additional_ship_choices: Optional[List[ShipChoiceInput]] = None
    additional_weapons: Optional[List[str]] = None


class DockInput(BaseModel):
    """Authored dock block on the docker ship. Loader normalizes to docked_with/docker_point/dockee_point."""
    model_config = ConfigDict(extra='forbid')
    dockee: str
    docker_point: str
    dockee_point: str


class SubsystemStatusInput(BaseModel):
    """Raw authored subsystem name + optional health override for a single subsystem."""
    model_config = ConfigDict(extra='forbid')
    name: str
    health: Optional[int] = None


class SubsystemsInput(BaseModel):
    """Raw FSIF subsystems block; ``status`` is ``'all_ok'`` or ``'custom'``."""
    model_config = ConfigDict(extra='forbid')
    status: Optional[str] = None
    list: Optional[List[SubsystemStatusInput]] = None


class WeaponsInput(BaseModel):
    """Raw FSIF weapons block; primary/secondary bank lists and optional ammo overrides as authored."""
    model_config = ConfigDict(extra='forbid')
    primary: Optional[List[str]] = None
    secondary: Optional[List[str]] = None
    secondary_ammo_counts: Optional[List[int]] = None


class ShipTemplateInput(BaseModel):
    """Allowed ship template properties.

    Arrival/departure fields, initial_orders, and docking are intentionally
    absent — they are not permitted in ship_templates and are caught here by
    extra='forbid' before the loader runs.
    """
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    ship_class: Optional[str] = Field(None, alias='class')
    team: Optional[str] = None
    ai_class: Optional[str] = None
    cargo: Optional[str] = None
    initial_speed_percent: Optional[int] = None
    initial_hull_percent: Optional[int] = None
    orientation: Optional[List[float]] = None
    flags: Optional[List[str]] = None
    respawn_priority: Optional[int] = None
    subsystems: Optional[SubsystemsInput] = None
    weapons: Optional[WeaponsInput] = None
    escort_list_priority: Optional[int] = None
    destroyed_before_mission_seconds: Optional[int] = None


class ShipInput(BaseModel):
    """Authored ship definition. Does not include internal fields such as
    docked_with/docker_point/dockee_point — those are produced by loader
    normalization from the 'dock' block.
    """
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    name: str
    template: Optional[str] = None
    ship_class: Optional[str] = Field(None, alias='class')
    team: Optional[str] = None
    position: Optional[List[float]] = None
    orientation: Optional[List[float]] = None
    ai_class: Optional[str] = None
    cargo: Optional[str] = None
    initial_speed_percent: Optional[int] = None
    initial_hull_percent: Optional[int] = None
    flags: Optional[List[str]] = None
    respawn_priority: Optional[int] = None
    subsystems: Optional[SubsystemsInput] = None
    weapons: Optional[WeaponsInput] = None
    dock: Optional[DockInput] = None
    initial_orders: Optional[str] = None
    arrival_method: Optional[str] = None
    arrival_anchor: Optional[str] = None
    arrival_distance: Optional[int] = None
    arrival_delay: Optional[int] = None
    arrival_cue: Optional[str] = None
    departure_method: Optional[str] = None
    departure_anchor: Optional[str] = None
    departure_delay: Optional[int] = None
    departure_cue: Optional[str] = None
    escort_list_priority: Optional[int] = None
    destroyed_before_mission_seconds: Optional[int] = None

    @field_validator('arrival_method', mode='before')
    @classmethod
    def validate_arrival_method(cls, v):
        if v is None:
            return v
        return _validate_arrival_method_token(v)

    @field_validator('departure_method', mode='before')
    @classmethod
    def validate_departure_method(cls, v):
        if v is None:
            return v
        return _validate_departure_method_token(v)


class WingInput(BaseModel):
    """Raw FSIF wing definition; compact form with template reference and centroid position.

    The loader expands this into a runtime ``Wing`` with individual ``Ship`` members.
    """
    model_config = ConfigDict(extra='forbid')
    name: str
    template: str
    count: int
    position: Optional[List[float]] = None
    wave_count: Optional[int] = None
    next_wave_threshold: Optional[int] = None
    next_wave_delay_min: Optional[int] = None
    next_wave_delay_max: Optional[int] = None
    member_spacing: Optional[float] = None
    arrival_method: Optional[str] = None
    arrival_anchor: Optional[str] = None
    arrival_distance: Optional[int] = None
    arrival_delay: Optional[int] = None
    arrival_cue: Optional[str] = None
    departure_method: Optional[str] = None
    departure_anchor: Optional[str] = None
    departure_delay: Optional[int] = None
    departure_cue: Optional[str] = None
    initial_orders: Optional[str] = None
    flags: Optional[List[str]] = None

    @field_validator('arrival_method', mode='before')
    @classmethod
    def validate_arrival_method(cls, v):
        if v is None:
            return v
        return _validate_arrival_method_token(v)

    @field_validator('departure_method', mode='before')
    @classmethod
    def validate_departure_method(cls, v):
        if v is None:
            return v
        return _validate_departure_method_token(v)


class JumpNodeInput(BaseModel):
    """Raw FSIF jump node entry; name and world-space position as authored."""
    model_config = ConfigDict(extra='forbid')
    name: str
    position: List[float]


class ReinforcementInput(BaseModel):
    """Raw FSIF reinforcement entry; references a ship or wing by name."""
    model_config = ConfigDict(extra='forbid')
    name: str
    max_uses: Optional[int] = None
    arrival_delay: Optional[int] = None
    unavailable_messages: Optional[List[str]] = None
    available_messages: Optional[List[str]] = None


class EntitiesInput(BaseModel):
    """Raw FSIF ``entities`` mapping; top-level container for all authored ship templates, ships, wings, waypoints, reinforcements, and jump nodes."""
    model_config = ConfigDict(extra='forbid')
    ship_templates: Optional[Dict[str, ShipTemplateInput]] = None
    ships: Optional[List[ShipInput]] = None
    wings: Optional[List[WingInput]] = None
    # Waypoints: mapping of path names to lists of [x,y,z] coordinates.
    # Values are left as Any because the coordinate lists are validated later
    # by the loader and runtime models.
    waypoints: Optional[Dict[str, Any]] = None
    reinforcement_wings: Optional[List[ReinforcementInput]] = None
    reinforcement_ships: Optional[List[ReinforcementInput]] = None
    jump_nodes: Optional[List[JumpNodeInput]] = None


class EventInput(BaseModel):
    """Raw FSIF mission event; name, SEXP formula, and optional HUD directive text as authored."""
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    formula: str
    hud_directive_text: Optional[str] = None


class GoalInput(BaseModel):
    """Raw FSIF mission goal; name, type, player-visible objective text, and SEXP formula as authored."""
    model_config = ConfigDict(extra='forbid')
    name: str
    type: Optional[str] = None
    objective_text: str
    formula: str


class MessageInput(BaseModel):
    """Raw FSIF in-mission message; text and optional TTS voice fields as authored."""
    model_config = ConfigDict(extra='forbid')
    name: str
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None


class BriefingIconInput(BaseModel):
    """Raw FSIF briefing icon; ``map_position`` is a 2-element ``[x, z]`` list as authored.

    The runtime ``BriefingIcon`` model normalizes this to ``[x, 0.0, z]`` and resolves the
    numeric ``type_id`` from the canonical ``icon_type`` string.
    """
    model_config = ConfigDict(extra='forbid')
    icon_type: str
    team: str
    # Authors write [x, z] (2 elements). Normalization to [x, 0.0, z] is done
    # by the runtime BriefingIcon validator, not here.
    map_position: Optional[List[float]] = None
    label: Optional[str] = None
    display_class: Optional[str] = None
    highlighted: Optional[bool] = None


class BriefingStageInput(BaseModel):
    """Raw FSIF briefing stage; text, optional TTS fields, camera time, and icon list as authored."""
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    camera_time: Optional[int] = None
    icons: Optional[List[BriefingIconInput]] = None


class BriefingInput(BaseModel):
    """Raw FSIF ``mission_flow.briefing`` mapping; list of authored briefing stages."""
    model_config = ConfigDict(extra='forbid')
    stages: Optional[List[BriefingStageInput]] = None


class DebriefingStageInput(BaseModel):
    """Raw FSIF debriefing stage; text, optional SEXP display condition, and TTS fields as authored."""
    model_config = ConfigDict(extra='forbid')
    text: str
    display_condition: Optional[str] = None
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    recommendation: Optional[str] = None


class DebriefingInput(BaseModel):
    """Raw FSIF ``mission_flow.debriefing`` mapping; list of authored debriefing stages."""
    model_config = ConfigDict(extra='forbid')
    stages: Optional[List[DebriefingStageInput]] = None


class CommandBriefingStageInput(BaseModel):
    """Raw FSIF command briefing stage; text and optional TTS fields as authored."""
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None


class CommandBriefingInput(BaseModel):
    """Raw FSIF ``mission_flow.command_briefing`` mapping; list of authored command briefing stages."""
    model_config = ConfigDict(extra='forbid')
    stages: Optional[List[CommandBriefingStageInput]] = None


class MissionFlowInput(BaseModel):
    """Raw FSIF ``mission_flow`` mapping; top-level container for all authored flow elements."""
    model_config = ConfigDict(extra='forbid')
    fiction_viewer: Optional[str] = None
    events: Optional[List[EventInput]] = None
    goals: Optional[List[GoalInput]] = None
    messages: Optional[List[MessageInput]] = None
    briefing: Optional[BriefingInput] = None
    debriefing: Optional[DebriefingInput] = None
    command_briefing: Optional[CommandBriefingInput] = None


class AudioSettingsInput(BaseModel):
    """Raw FSIF ``audio`` mapping; music tokens and TTS provider preference as authored."""
    model_config = ConfigDict(extra='forbid')
    mission_music: Optional[str] = None
    briefing_music: Optional[str] = None
    tts_provider: Optional[str] = None


class FSIFDocument(BaseModel):
    """Deep strict-validation model for the raw FSIF document.
    
    Used in mission_loader._read_yaml() immediately after YAML parsing.
    All nested sections use extra='forbid' so any unknown keys are caught
    before any loader normalization runs.
    
    This model is used solely for validation — the loader continues to work
    with the raw dict. Do not add loader-specific internal fields here.
    """
    model_config = ConfigDict(extra='forbid')
    fsif_version: str
    mission_info: MissionInfoInput
    environment: EnvironmentInput
    player_setup: PlayerSetupInput
    entities: EntitiesInput
    mission_flow: MissionFlowInput
    audio: Optional[AudioSettingsInput] = None


# =============================================================================
# --- Runtime Sub-Component Models ---
# =============================================================================
# These models represent the normalized, hydrated mission structure produced
# by the loader after template merging, wing expansion, and normalization.
# They are used by the writer, validator, and TTS provider.

class SubsystemStatus(BaseModel):
    """Runtime subsystem health record; name validated against per-ship canonical lists."""
    model_config = ConfigDict(extra='forbid')
    name: str
    health: int = Field(100, ge=0, le=100)

class Subsystems(BaseModel):
    """Runtime normalized subsystems block; ``status`` defaults to ``'all_ok'`` when not explicitly customized."""
    model_config = ConfigDict(extra='forbid')
    status: Literal['all_ok', 'custom'] = 'all_ok'
    list: List[SubsystemStatus] = Field(default_factory=list)

class Weapons(BaseModel):
    """Runtime normalized weapons block with resolved primary/secondary bank lists for a ship."""
    model_config = ConfigDict(extra='forbid')
    primary: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    secondary_ammo_counts: List[int] = Field(default_factory=list)

class ShipChoice(BaseModel):
    """Runtime alternative player ship pool entry for the loadout screen."""
    model_config = ConfigDict(extra='forbid')
    ship_class: str = Field(..., alias='class')
    count: int = Field(..., ge=1)

class Sun(BaseModel):
    """Runtime background sun; angles normalized to ``[pitch, heading]`` (bank omitted; suns are rotationally symmetric)."""
    model_config = ConfigDict(extra='forbid')
    texture: str
    angles: List[float]
    scale: float = 1.0

    @field_validator('angles', mode='before')
    @classmethod
    def validate_angles(cls, v):
        return _normalize_sun_angles(v)

class XYFloat(BaseModel):
    """Helper model for a 2D float scale value (used by ``BackgroundBitmap.scale`` when x/y differ)."""
    model_config = ConfigDict(extra='forbid')
    x: float
    y: float

class XYInt(BaseModel):
    """Helper model for a 2D integer dimension pair."""
    model_config = ConfigDict(extra='forbid')
    x: int
    y: int

class BackgroundBitmap(BaseModel):
    """Runtime background bitmap; angles normalized to ``[pitch, bank, heading]`` in radians."""
    model_config = ConfigDict(extra='forbid')
    texture: str
    angles: List[float]
    scale: Union[float, XYFloat] = 1.0
    
    @field_validator('angles', mode='before')
    @classmethod
    def validate_angles(cls, v):
        return _normalize_vector(v)

class Nebula(BaseModel):
    """Runtime normalized nebula settings; defaults applied by loader when fields are absent."""
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    sensor_range: float = Field(default=3000.0)
    storm: str = 'none'
    pattern: Optional[str] = None
    cloud_sprites: List[str] = Field(default_factory=list)

    @field_validator('cloud_sprites', mode='before')
    @classmethod
    def coerce_cloud_sprites_null(cls, v):
        return _none_to_empty_list(v)

class AsteroidField(BaseModel):
    """Runtime asteroid/debris field; ``min_vec``/``max_vec`` are loader-produced from the authored ``bounds`` mapping.

    ``object_variants`` defaults are injected by the loader based on ``object_type``.
    """
    # 'min_vec'/'max_vec' are an internal representation produced by the
    # mission_loader from the authored 'bounds.min'/'bounds.max' mapping.
    model_config = ConfigDict(extra='forbid')
    num_objects: int = Field(50, ge=0)
    behavior: Literal['active', 'passive'] = Field('passive')
    object_type: Literal['asteroid', 'debris'] = Field('asteroid')
    object_variants: List[str] = Field(
        # Default is asteroid variants; mission_loader overrides per object_type.
        default_factory=lambda: list(fs_data.ASTEROID_FIELD_VARIANTS)
    )
    average_speed: float = 20.0
    min_vec: List[float] = Field(default_factory=lambda: [-1000.0, -1000.0, -1000.0])
    max_vec: List[float] = Field(default_factory=lambda: [1000.0, 1000.0, 1000.0])
    target_ships: List[str] = Field(default_factory=list)

    @field_validator('min_vec', 'max_vec', mode='before')
    @classmethod
    def validate_vec(cls, v):
        return _normalize_vector(v)

class Environment(BaseModel):
    """Runtime normalized environment; all sub-models fully hydrated with defaults by the loader."""
    model_config = ConfigDict(extra='forbid')
    ambient_light_level: List[int] = Field(default_factory=lambda: [0, 0, 0])
    suns: List[Sun] = Field(default_factory=list)
    background_bitmaps: List[BackgroundBitmap] = Field(default_factory=list)
    nebula: Nebula = Field(default_factory=lambda: Nebula())
    asteroid_field: Optional[AsteroidField] = None

    @field_validator('ambient_light_level', mode='before')
    @classmethod
    def validate_ambient_light_level(cls, v):
        return _normalize_ambient_light_rgb(v)

class MissionInfo(BaseModel):
    """Runtime normalized mission metadata with all optional fields resolved to defaults."""
    model_config = ConfigDict(extra='forbid')
    name: str
    author: str = 'FSIF Converter'
    description: str = 'No description provided.'
    game_type: Literal['single', 'multiplayer', 'training'] = 'single'
    flags: List[str] = Field(default_factory=list)
    disallow_support_ships: bool = False

    @field_validator('flags', mode='before')
    @classmethod
    def coerce_flags_null(cls, v):
        return _none_to_empty_list(v)

class PlayerSetup(BaseModel):
    """Runtime normalized player setup; optional loadout lists resolved to empty by default."""
    model_config = ConfigDict(extra='forbid')
    start_ship: str
    additional_ship_choices: List[ShipChoice] = Field(default_factory=list)
    additional_weapons: List[str] = Field(default_factory=list)

    @field_validator('additional_ship_choices', 'additional_weapons', mode='before')
    @classmethod
    def coerce_optional_lists_null(cls, v):
        return _none_to_empty_list(v)

class Event(BaseModel):
    """Runtime mission event; SEXP formula and optional HUD directive text, passed verbatim to the FS2 writer."""
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    formula: str
    hud_directive_text: Optional[str] = Field(default=None)

class Goal(BaseModel):
    """Runtime mission goal with normalized ``type`` defaulting to ``'Primary'``."""
    model_config = ConfigDict(extra='forbid')
    name: str
    formula: str
    objective_text: str = Field(...)
    type: Literal['Primary', 'Secondary', 'Bonus'] = 'Primary'

class Message(BaseModel):
    """Runtime in-mission message; ``voice_filename`` is an internal TTS-assigned path, excluded from serialization."""
    model_config = ConfigDict(extra='forbid')
    name: str
    text: str = Field(...)
    voice_name: Optional[str] = None # For TTS
    voice_style_instructions: Optional[str] = None # For TTS
    voice_filename: Optional[str] = Field(default=None, exclude=True)

class BriefingIcon(BaseModel):
    """Runtime briefing icon; ``type_id`` resolved from ``icon_type`` string, ``map_position`` normalized to ``[x, 0.0, z]``.

    ``display_class_authored`` is an internal loader flag that records whether the author
    explicitly provided ``display_class`` in FSIF; it is never serialized.
    """
    model_config = ConfigDict(extra='forbid')
    type_id: int
    icon_type: str = Field(...)
    team: Literal['Friendly', 'Hostile', 'Unknown']
    map_position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    label: str = ''
    highlighted: bool = False
    display_class: str = Field("Terran NavBuoy")
    # Internal flag: True when the author explicitly wrote display_class in FSIF.
    # Preserved by the loader; never authored directly and never emitted to .fs2.
    display_class_authored: bool = Field(default=False, exclude=True, repr=False)

    @field_validator('map_position', mode='before')
    @classmethod
    def validate_map_position(cls, v):
        # Icons are on XZ plane. Input [x, z] ONLY.
        # Normalized to [x, 0.0, z] for internal use.
        if not v:
            return [0.0, 0.0, 0.0]

        # Enforce list/tuple type
        if not isinstance(v, (list, tuple)):
             raise ValueError(f"Briefing icon map_position must be a list [x, z], got {type(v)}")

        if len(v) != 2:
             raise ValueError(f"Briefing icon map_position must be [x, z] (2 coordinates), got {len(v)}. 3D coordinates are not supported.")

        try:
            return [float(v[0]), 0.0, float(v[1])]
        except (ValueError, TypeError):
             raise ValueError(f"Briefing icon coordinates must be numbers, got {v}")

class BriefingStage(BaseModel):
    """Runtime briefing stage; ``camera_pos``/``camera_orient`` are loader-computed from icon positions, excluded from serialization."""
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    voice_filename: Optional[str] = Field(default=None, exclude=True)
    
    # Internal fields (calculated by loader, not authored in FSIF)
    camera_pos: Optional[List[float]] = Field(default=None, exclude=True, repr=False)
    camera_orient: Optional[List[float]] = Field(default=None, exclude=True, repr=False)
    
    camera_time: int = Field(500, ge=0)
    icons: List[BriefingIcon] = Field(default_factory=list)

    @field_validator('icons', mode='before')
    @classmethod
    def coerce_icons_null(cls, v):
        return _none_to_empty_list(v)

class Briefing(BaseModel):
    """Runtime mission briefing; contains normalized stages with computed camera placement."""
    model_config = ConfigDict(extra='forbid')
    stages: List[BriefingStage] = Field(default_factory=list)

    @field_validator('stages', mode='before')
    @classmethod
    def coerce_stages_null(cls, v):
        return _none_to_empty_list(v)

class DebriefingStage(BaseModel):
    """Runtime debriefing stage; ``display_condition`` defaults to ``( true )`` when not authored."""
    model_config = ConfigDict(extra='forbid')
    text: str
    display_condition: str = Field('( true )')
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    voice_filename: Optional[str] = Field(default=None, exclude=True)
    recommendation: str = ''

class Debriefing(BaseModel):
    """Runtime mission debriefing; contains normalized stages with defaulted display conditions."""
    model_config = ConfigDict(extra='forbid')
    stages: List[DebriefingStage] = Field(default_factory=list)

    @field_validator('stages', mode='before')
    @classmethod
    def coerce_stages_null(cls, v):
        return _none_to_empty_list(v)

class CommandBriefingStage(BaseModel):
    """Runtime command briefing stage; ``voice_filename`` is an internal TTS-assigned path, excluded from serialization."""
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    voice_filename: Optional[str] = Field(default=None, exclude=True)

class CommandBriefing(BaseModel):
    """Runtime command briefing; contains the ordered list of pre-mission command stages."""
    model_config = ConfigDict(extra='forbid')
    stages: List[CommandBriefingStage] = Field(default_factory=list)

    @field_validator('stages', mode='before')
    @classmethod
    def coerce_stages_null(cls, v):
        return _none_to_empty_list(v)

class Reinforcement(BaseModel):
    """Runtime reinforcement entry; loader injects the ``'reinforcement'`` flag onto the referenced ship/wing object."""
    model_config = ConfigDict(extra='forbid')
    name: str
    max_uses: int = Field(1, ge=1)
    arrival_delay: int = Field(0, ge=0)
    unavailable_messages: List[str] = Field(default_factory=list)
    available_messages: List[str] = Field(default_factory=list)

    @field_validator('unavailable_messages', 'available_messages', mode='before')
    @classmethod
    def coerce_messages_null(cls, v):
        return _none_to_empty_list(v)

class JumpNode(BaseModel):
    """Runtime jump node with validated world-space position vector."""
    model_config = ConfigDict(extra='forbid')
    name: str
    position: List[float]

    @field_validator('position', mode='before')
    @classmethod
    def validate_pos(cls, v):
        return _normalize_vector(v)

class Ship(BaseModel):
    """Normalized runtime ship used for FS2 emission; covers both standalone ships and expanded wing members.

    Docking fields (``docked_with``, ``docker_point``, ``dockee_point``) are internal and populated by
    the loader from the authored ``dock`` block on the docker ship; they are never authored directly.
    """
    model_config = ConfigDict(extra='forbid')

    name: str
    ship_class: str = Field(..., alias='class') # Required field
    team: Literal['Friendly', 'Hostile', 'Unknown']
    position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: List[float] = Field(default_factory=lambda: [
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    ])
    
    # Optional props with defaults
    ai_class: Optional[str] = None
    cargo: str = 'Nothing'
    initial_speed_percent: int = Field(33, ge=0, le=100)
    initial_hull_percent: int = Field(100, ge=0, le=100)
    
    arrival_method: str = Field('Hyperspace')
    arrival_distance: Optional[int] = Field(None, ge=0)
    arrival_anchor: Optional[str] = None
    arrival_delay: int = Field(0, ge=0)
    arrival_cue: str = Field('( true )')

    departure_method: str = Field('Hyperspace')
    departure_anchor: Optional[str] = None
    departure_delay: int = Field(0, ge=0)
    departure_cue: str = Field('( false )')

    flags: List[str] = Field(default_factory=lambda: ['cargo-known'])

    respawn_priority: int = Field(0, ge=0)

    subsystems: Subsystems = Field(default_factory=Subsystems)
    weapons: Weapons = Field(default_factory=Weapons)

    initial_orders: Optional[str] = Field(None)

    escort_list_priority: int = Field(0, ge=0)
    destroyed_before_mission_seconds: int = Field(0, ge=0)

    # Docking (internal storage; authored as a 'dock' block on the docker,
    # normalized by the loader from dock.dockee/docker_point/dockee_point)
    docked_with: Optional[str] = None
    docker_point: Optional[str] = None
    dockee_point: Optional[str] = None

    @field_validator('position', mode='before')
    @classmethod
    def validate_position(cls, v):
        return _normalize_vector(v)

    @field_validator('orientation', mode='before')
    @classmethod
    def validate_orient(cls, v):
        return _normalize_orientation(v)

    @field_validator('flags', mode='before')
    @classmethod
    def coerce_flags_null(cls, v):
        return _none_to_empty_list(v)

    @field_validator('arrival_method', mode='before')
    @classmethod
    def validate_arrival_method(cls, v):
        return _validate_arrival_method_token(v)

    @field_validator('departure_method', mode='before')
    @classmethod
    def validate_departure_method(cls, v):
        return _validate_departure_method_token(v)

class Wing(BaseModel):
    """Runtime wing with loader-expanded ``Ship`` member objects and normalized arrival/departure settings.

    ``template`` is retained for reference but all template properties have already been merged
    into the individual ``ships`` entries by the loader.
    """
    model_config = ConfigDict(extra='forbid')
    
    name: str
    count: int = Field(..., ge=1)
    ships: List[Ship] = Field(default_factory=list)
    
    wave_count: int = Field(1, ge=1)
    next_wave_threshold: int = Field(0, ge=0)
    next_wave_delay_min: Optional[int] = Field(None, ge=0)
    next_wave_delay_max: Optional[int] = Field(None, ge=0)
    
    arrival_method: str = Field('Hyperspace')
    arrival_distance: Optional[int] = Field(None, ge=0)
    arrival_anchor: Optional[str] = None
    arrival_delay: int = Field(0, ge=0)
    arrival_cue: str = Field('( true )')

    departure_method: str = Field('Hyperspace')
    departure_anchor: Optional[str] = None
    departure_delay: int = Field(0, ge=0)
    departure_cue: str = Field('( false )')

    flags: List[str] = Field(default_factory=list)
    initial_orders: Optional[str] = Field(None)

    # Wing centroid position
    position: Optional[List[float]] = None
    member_spacing: float = Field(50.0, gt=0)

    # Template reference (used during expansion, kept for record)
    template: Optional[str] = None

    @field_validator('position', mode='before')
    @classmethod
    def validate_pos(cls, v):
        if v is None: return None
        return _normalize_vector(v)

    @field_validator('flags', mode='before')
    @classmethod
    def coerce_flags_null(cls, v):
        return _none_to_empty_list(v)

    @field_validator('arrival_method', mode='before')
    @classmethod
    def validate_arrival_method(cls, v):
        return _validate_arrival_method_token(v)

    @field_validator('departure_method', mode='before')
    @classmethod
    def validate_departure_method(cls, v):
        return _validate_departure_method_token(v)

class AudioSettings(BaseModel):
    """Runtime audio settings; ``tts_provider`` is normalized to lowercase by the validator."""
    model_config = ConfigDict(extra='forbid')
    mission_music: Optional[str] = None
    briefing_music: Optional[str] = None
    tts_provider: Optional[Literal['google', 'elevenlabs', 'inworld', 'none']] = None

    @field_validator('tts_provider', mode='before')
    @classmethod
    def validate_tts_provider(cls, v):
        if v is not None and isinstance(v, str):
            return v.lower()
        return v

class Mission(BaseModel):
    """Top-level runtime mission object; fully normalized and hydrated, consumed by the validator, FS2 writer, and TTS provider.

    ``ships`` is a flat list of ALL ships (standalone + wing members) for linear iteration.
    Wing members are also referenced from their parent ``Wing.ships`` list.
    ``created``/``modified`` are internal timestamps generated at conversion time, never authored in FSIF.
    """
    model_config = ConfigDict(extra='forbid')
    mission_info: MissionInfo
    environment: Environment = Field(default_factory=Environment)
    player_setup: PlayerSetup
    
    # Flat list of ALL ships in the mission (standalone + wing members).
    # Used for linear iteration (e.g., #Objects section, global validation).
    # Wing members are also referenced in their respective Wing objects.
    ships: List[Ship] = Field(default_factory=list)
    wings: List[Wing] = Field(default_factory=list)
    
    waypoints: Dict[str, List[List[float]]] = Field(default_factory=dict)
    events: List[Event] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    messages: List[Message] = Field(default_factory=list)
    
    briefing: Briefing = Field(default_factory=Briefing)
    debriefing: Debriefing = Field(default_factory=Debriefing)
    command_briefing: CommandBriefing = Field(default_factory=CommandBriefing)
    
    fiction_viewer: Optional[str] = None
    reinforcements: List[Reinforcement] = Field(default_factory=list)
    jump_nodes: List[JumpNode] = Field(default_factory=list)
    
    audio: AudioSettings = Field(default_factory=AudioSettings)

    # Internal metadata — generated at conversion time, never authored in FSIF.
    created: str = ''
    modified: str = ''
