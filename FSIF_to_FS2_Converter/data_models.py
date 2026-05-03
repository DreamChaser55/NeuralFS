# data_models.py
# Defines Pydantic models for the FSIF mission structure.

from __future__ import annotations
from typing import List, Dict, Any, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

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

# --- Raw Document Models (for initial strict validation) ---

class EntitiesSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ship_templates: Optional[Dict[str, Any]] = None
    ships: Optional[List[Dict[str, Any]]] = None
    wings: Optional[List[Dict[str, Any]]] = None
    waypoints: Optional[Dict[str, Any]] = None
    reinforcement_wings: Optional[List[Dict[str, Any]]] = None
    reinforcement_ships: Optional[List[Dict[str, Any]]] = None
    jump_nodes: Optional[List[Dict[str, Any]]] = None

class MissionFlowSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    fiction_viewer: Optional[str] = None
    events: Optional[List[Dict[str, Any]]] = None
    goals: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    briefing: Optional[Dict[str, Any]] = None
    debriefing: Optional[Dict[str, Any]] = None
    command_briefing: Optional[Dict[str, Any]] = None

class FSIFDocument(BaseModel):
    model_config = ConfigDict(extra='forbid')
    fsif_version: str
    mission_info: Dict[str, Any]
    environment: Dict[str, Any]
    player_setup: Dict[str, Any]
    entities: EntitiesSection
    mission_flow: MissionFlowSection
    audio: Optional[Dict[str, Any]] = None

# --- Sub-Component Models ---

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
    sensor_range: float = Field(3000.0)
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
    
    arrival_method: Literal['Hyperspace', 'Docking Bay', 'Near Ship', 'In front of ship', 'In back of ship', 'Above ship', 'Below ship', 'To left of ship', 'To right of ship'] = Field('Hyperspace')
    arrival_distance: Optional[int] = Field(None, ge=0)
    arrival_anchor: Optional[str] = None
    arrival_delay: int = Field(0, ge=0)
    arrival_condition: str = Field('( false )')
    
    departure_method: Literal['Hyperspace', 'Docking Bay'] = Field('Hyperspace')
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
    
    # Docking (internal storage; authored as a 'dock' block on the docker)
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

class Wing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    name: str
    count: int = Field(..., ge=1)
    ships: List[Ship] = Field(default_factory=list)
    
    wave_count: int = Field(1, ge=1)
    next_wave_threshold: int = Field(0, ge=0)
    next_wave_delay_min: Optional[int] = Field(None, ge=0)
    next_wave_delay_max: Optional[int] = Field(None, ge=0)
    
    arrival_method: Literal['Hyperspace', 'Docking Bay', 'Near Ship', 'In front of ship', 'In back of ship', 'Above ship', 'Below ship', 'To left of ship', 'To right of ship'] = Field('Hyperspace')
    arrival_distance: Optional[int] = Field(None, ge=0)
    arrival_anchor: Optional[str] = None
    arrival_delay: int = Field(0, ge=0)
    arrival_condition: str = Field('( true )')
    
    departure_method: Literal['Hyperspace', 'Docking Bay'] = Field('Hyperspace')
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
