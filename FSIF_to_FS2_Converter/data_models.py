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
    """Ensure a 3-element float list. Raises ValueError on any malformed or absent input."""
    if v is None:
        raise ValueError("Expected a 3-element [x, y, z] list, got None.")
    try:
        items = list(v)
    except TypeError:
        raise ValueError(f"Expected a 3-element [x, y, z] list, got: {v!r}")
    if len(items) != 3:
        raise ValueError(
            f"Expected a 3-element [x, y, z] list, got {len(items)} element(s): {v!r}"
        )
    try:
        return [float(items[0]), float(items[1]), float(items[2])]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Vector coordinates must be numbers, got: {v!r}") from e


def _normalize_orientation(v: Any) -> List[float]:
    """Ensure a 9-element float list (3×3 rotation matrix). Raises ValueError on bad input."""
    if v is None:
        raise ValueError("orientation must be a 9-element flat list or 3×3 nested list, got None.")

    # Handle nested lists (3×3) as well as flat 9-element lists
    flat: List[float] = []
    try:
        if isinstance(v[0], (list, tuple)):
            for row in v:
                flat.extend(row)
        else:
            flat = list(v)
    except (TypeError, IndexError) as e:
        raise ValueError(f"orientation must be a 9-element flat list or 3×3 nested list, got: {v!r}") from e

    if len(flat) != 9:
        raise ValueError(
            f"orientation must have exactly 9 elements, got {len(flat)}: {v!r}"
        )
    try:
        return [float(x) for x in flat]
    except (TypeError, ValueError) as e:
        raise ValueError(f"orientation elements must be numbers, got: {v!r}") from e


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
# --- Authored FSIF 4.0 Input Schema (strict Pydantic pre-validation) ---
# =============================================================================
#
# These models validate the raw YAML content against the FSIF 4.0 authored
# schema BEFORE any loader normalization (template merging, wing expansion,
# bounds -> min_vec/max_vec, dock block -> docked_with/etc.).
#
# All models use extra='forbid' so that legacy FSIF 3.0 field names and any
# other unknown keys are rejected before the loader processes the document.
#
# Key differences from the runtime models below:
#   - No internal fields (docked_with / docker_point / dockee_point on ships).
#   - dock: DockInput uses 'dockee' key, not the internal 'docked_with'.
#   - AsteroidFieldInput uses authored 'bounds' mapping, not min_vec/max_vec.
#   - BriefingIconInput accepts [x,z] 2-element map_position authored by author.
#   - ShipTemplateInput explicitly excludes forbidden template fields.
# =============================================================================

class MissionInfoInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    game_type: Optional[str] = None
    flags: Optional[List[str]] = None
    disallow_support_ships: Optional[bool] = None
    ai_profile: Optional[str] = None


class NebulaInput(BaseModel):
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
    model_config = ConfigDict(extra='forbid')
    object_type: Optional[str] = None
    behavior: Optional[str] = None
    density: Optional[int] = None
    average_speed: Optional[float] = None
    bounds: Optional[BoundsInput] = None
    object_variants: Optional[List[str]] = None
    target_ships: Optional[List[str]] = None


class EnvironmentInput(BaseModel):
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
    model_config = ConfigDict(extra='forbid')
    name: str
    health: Optional[int] = None


class SubsystemsInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Optional[str] = None
    list: Optional[List[SubsystemStatusInput]] = None


class WeaponsInput(BaseModel):
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
    arrival_condition: Optional[str] = None
    departure_method: Optional[str] = None
    departure_anchor: Optional[str] = None
    departure_delay: Optional[int] = None
    departure_condition: Optional[str] = None
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
    arrival_condition: Optional[str] = None
    departure_method: Optional[str] = None
    departure_anchor: Optional[str] = None
    departure_delay: Optional[int] = None
    departure_condition: Optional[str] = None
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
    model_config = ConfigDict(extra='forbid')
    name: str
    position: List[float]


class ReinforcementInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    max_uses: Optional[int] = None
    arrival_delay: Optional[int] = None
    unavailable_messages: Optional[List[str]] = None
    available_messages: Optional[List[str]] = None


class EntitiesInput(BaseModel):
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
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    formula: str
    hud_directive_text: Optional[str] = None


class GoalInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    type: Optional[str] = None
    objective_text: str
    formula: str


class MessageInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None


class BriefingIconInput(BaseModel):
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
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    camera_time: Optional[int] = None
    icons: Optional[List[BriefingIconInput]] = None


class BriefingInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: Optional[List[BriefingStageInput]] = None


class DebriefingStageInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    display_condition: Optional[str] = None
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    recommendation: Optional[str] = None


class DebriefingInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: Optional[List[DebriefingStageInput]] = None


class CommandBriefingStageInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None


class CommandBriefingInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: Optional[List[CommandBriefingStageInput]] = None


class MissionFlowInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    fiction_viewer: Optional[str] = None
    events: Optional[List[EventInput]] = None
    goals: Optional[List[GoalInput]] = None
    messages: Optional[List[MessageInput]] = None
    briefing: Optional[BriefingInput] = None
    debriefing: Optional[DebriefingInput] = None
    command_briefing: Optional[CommandBriefingInput] = None


class AudioSettingsInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mission_music: Optional[str] = None
    briefing_music: Optional[str] = None
    tts_provider: Optional[str] = None


class FSIFDocument(BaseModel):
    """Deep strict-validation model for the raw FSIF 4.0 document.
    
    Used in mission_loader._read_yaml() immediately after YAML parsing.
    All nested sections use extra='forbid' so unknown/legacy FSIF 3.0 keys
    are caught before any loader normalization runs.
    
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
    model_config = ConfigDict(extra='forbid')
    name: str
    health: int = Field(100, ge=0, le=100)

class Subsystems(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['all_ok', 'custom'] = 'all_ok'
    list: List[SubsystemStatus] = Field(default_factory=list)

class Weapons(BaseModel):
    model_config = ConfigDict(extra='forbid')
    primary: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    secondary_ammo_counts: List[int] = Field(default_factory=list)

class ShipChoice(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ship_class: str = Field(..., alias='class')
    count: int = Field(..., ge=1)

class Sun(BaseModel):
    model_config = ConfigDict(extra='forbid')
    texture: str
    angles: List[float]
    scale: float = 1.0

    @field_validator('angles', mode='before')
    @classmethod
    def validate_angles(cls, v):
        return _normalize_vector(v)

class XYFloat(BaseModel):
    model_config = ConfigDict(extra='forbid')
    x: float
    y: float

class XYInt(BaseModel):
    model_config = ConfigDict(extra='forbid')
    x: int
    y: int

class BackgroundBitmap(BaseModel):
    model_config = ConfigDict(extra='forbid')
    texture: str
    angles: List[float]
    scale: Union[float, XYFloat] = 1.0
    
    @field_validator('angles', mode='before')
    @classmethod
    def validate_angles(cls, v):
        return _normalize_vector(v)

class Nebula(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    sensor_range: float = Field(default=3000.0)
    storm: str = 's_standard'
    pattern: Optional[str] = None
    cloud_sprites: List[str] = Field(default_factory=list)

class AsteroidField(BaseModel):
    # 'min_vec'/'max_vec' are an internal representation produced by the
    # mission_loader from the authored 'bounds.min'/'bounds.max' mapping.
    model_config = ConfigDict(extra='forbid')
    density: int = Field(50, ge=0)
    behavior: Literal['active', 'passive'] = Field('passive')
    object_type: Literal['asteroid', 'debris'] = Field('asteroid')
    object_variants: List[str] = Field(
        default_factory=lambda: ["Brown", "Blue", "Orange"]
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
    model_config = ConfigDict(extra='forbid')
    name: str
    author: str = 'FSIF Converter'
    description: str = 'No description provided.'
    game_type: Literal['single', 'multiplayer', 'training'] = 'single'
    flags: List[str] = Field(default_factory=list)
    disallow_support_ships: bool = False
    ai_profile: str = 'FS1 RETAIL'

class PlayerSetup(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start_ship: str
    additional_ship_choices: List[ShipChoice] = Field(default_factory=list)
    additional_weapons: List[str] = Field(default_factory=list)

class Event(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    formula: str
    hud_directive_text: Optional[str] = Field(default=None)

class Goal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    formula: str
    objective_text: str = Field(...)
    type: Literal['Primary', 'Secondary', 'Bonus'] = 'Primary'

class Message(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    text: str = Field(...)
    voice_name: Optional[str] = None # For TTS
    voice_style_instructions: Optional[str] = None # For TTS
    voice_filename: Optional[str] = Field(default=None, exclude=True)

class BriefingIcon(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type_id: int
    icon_type: str = Field(...)
    team: Literal['Friendly', 'Hostile', 'Unknown']
    map_position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    label: str = ''
    highlighted: bool = False
    display_class: str = Field("Terran NavBuoy")

    @field_validator('map_position', mode='before')
    @classmethod
    def validate_map_position(cls, v):
        # FSIF 4.0: Icons are on XZ plane. Input [x, z] ONLY.
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

class Briefing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: List[BriefingStage] = Field(default_factory=list)

class DebriefingStage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    display_condition: str = Field('( true )')
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    voice_filename: Optional[str] = Field(default=None, exclude=True)
    recommendation: str = ''

class Debriefing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: List[DebriefingStage] = Field(default_factory=list)

class CommandBriefingStage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    voice_filename: Optional[str] = Field(default=None, exclude=True)

class CommandBriefing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: List[CommandBriefingStage] = Field(default_factory=list)

class Reinforcement(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    max_uses: int = Field(1, ge=1)
    arrival_delay: int = Field(0, ge=0)
    unavailable_messages: List[str] = Field(default_factory=list)
    available_messages: List[str] = Field(default_factory=list)

class JumpNode(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    position: List[float]

    @field_validator('position', mode='before')
    @classmethod
    def validate_pos(cls, v):
        return _normalize_vector(v)

class Ship(BaseModel):
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
    arrival_condition: str = Field('( false )')

    departure_method: str = Field('Hyperspace')
    departure_anchor: Optional[str] = None
    departure_delay: int = Field(0, ge=0)
    departure_condition: str = Field('( false )')

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

    @field_validator('arrival_method', mode='before')
    @classmethod
    def validate_arrival_method(cls, v):
        return _validate_arrival_method_token(v)

    @field_validator('departure_method', mode='before')
    @classmethod
    def validate_departure_method(cls, v):
        return _validate_departure_method_token(v)

class Wing(BaseModel):
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
    arrival_condition: str = Field('( true )')

    departure_method: str = Field('Hyperspace')
    departure_anchor: Optional[str] = None
    departure_delay: int = Field(0, ge=0)
    departure_condition: str = Field('( false )')

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

    @field_validator('arrival_method', mode='before')
    @classmethod
    def validate_arrival_method(cls, v):
        return _validate_arrival_method_token(v)

    @field_validator('departure_method', mode='before')
    @classmethod
    def validate_departure_method(cls, v):
        return _validate_departure_method_token(v)

class AudioSettings(BaseModel):
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
