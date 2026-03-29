# data_models.py
# Defines Pydantic models for the FSIF mission structure.

from __future__ import annotations
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- Constants ---

DEFAULT_ORIENTATION = [
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0
]

DEFAULT_KAMIKAZE_DAMAGE = 1000

# --- Helpers ---


def _normalize_vector(v: Any) -> List[float]:
    """Ensure a 3-element float list. Raises ValueError if input is present but malformed."""
    if not v:
        return [0.0, 0.0, 0.0]
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
    """Ensure a 9-element float list (matrix)."""
    if not v:
        return [
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0
        ]

    # Handle nested lists if necessary, though typical input is flat or nested
    flat = []
    try:
        if isinstance(v[0], (list, tuple)):
             for row in v:
                 flat.extend(row)
        else:
             flat = list(v)

        if len(flat) < 9:
             return [
                1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, 1.0
            ]
        return [float(x) for x in flat[:9]]
    except Exception:
        return [
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0
        ]


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

# --- Sub-Component Models ---

class SubsystemStatus(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    health: int = Field(100, ge=0, le=100)

class Subsystems(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: str = 'all_ok'
    list: List[SubsystemStatus] = Field(default_factory=list)

class Weapons(BaseModel):
    model_config = ConfigDict(extra='forbid')
    primary: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    secondary_ammo: List[int] = Field(default_factory=list)

class ShipChoice(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ship_class: str = Field(..., alias='class')
    count: int

class Sun(BaseModel):
    model_config = ConfigDict(extra='forbid')
    texture: str
    angles: List[float]
    scale: float = 1.0

    @field_validator('angles', mode='before')
    @classmethod
    def validate_angles(cls, v):
        return _normalize_vector(v)

class StarBitmap(BaseModel):
    model_config = ConfigDict(extra='forbid')
    texture: str
    angles: List[float]
    scale: Union[float, Dict[str, float]] = 1.0
    div: Union[Dict[str, int], int] = 1 # simplified for now, usually dict x/y
    
    @field_validator('angles', mode='before')
    @classmethod
    def validate_angles(cls, v):
        return _normalize_vector(v)

class Nebula(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    awacs: float = 3000.0
    storm: str = 's_standard'
    pattern: Optional[str] = None
    poofs: List[str] = Field(default_factory=list)

class AsteroidField(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = "Field_1"
    density: int = 50
    field_type: int = 1 # 0=active, 1=passive
    debris_genre: int = 0 # 0=asteroid, 1=debris
    debris_types: List[str] = Field(default_factory=lambda: ["Brown", "Blue", "Orange"])
    average_speed: float = 20.0
    min_vec: List[float] = Field(default_factory=lambda: [-1000.0, -1000.0, -1000.0])
    max_vec: List[float] = Field(default_factory=lambda: [1000.0, 1000.0, 1000.0])
    targets: List[str] = Field(default_factory=list)

    @field_validator('min_vec', 'max_vec', mode='before')
    @classmethod
    def validate_vec(cls, v):
        return _normalize_vector(v)

class Environment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ambient_light_level: List[int] = Field(default_factory=lambda: [0, 0, 0])
    suns: List[Sun] = Field(default_factory=list)
    starbitmaps: List[StarBitmap] = Field(default_factory=list)
    nebula: Nebula = Field(default_factory=Nebula)
    asteroid_field: Optional[AsteroidField] = None

    @field_validator('ambient_light_level', mode='before')
    @classmethod
    def validate_ambient_light_level(cls, v):
        return _normalize_ambient_light_rgb(v)

class MissionInfo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    author: str = 'FSIF Converter'
    notes: str = 'Generated by FSIF Converter.'
    description: str = 'No description provided.'
    game_type: str = 'single'
    flags: List[str] = Field(default_factory=list)
    disallow_support: bool = False
    ai_profile: str = 'FS1 RETAIL'
    created: Optional[str] = None
    modified: Optional[str] = None

class PlayerSetup(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start_ship: Optional[str] = None
    extra_ships: List[ShipChoice] = Field(default_factory=list)
    extra_weapons: List[str] = Field(default_factory=list)

class Event(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    formula: str
    directive_text: Optional[str] = None

class Goal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    formula: str
    message: str
    type: str = 'Primary'

class Message(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    message: str
    voice_filename: Optional[str] = None
    voice_name: Optional[str] = None # For TTS
    voice_style_instructions: Optional[str] = None # For TTS

class BriefingIcon(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type_id: int
    type: str # canonical string
    team: str
    pos: List[float]
    label: str = ''
    highlighted: bool = False
    class_: str = Field("Terran NavBuoy", alias='class')

    @field_validator('pos', mode='before')
    @classmethod
    def validate_pos(cls, v):
        # FSIF 2.1: Icons are on XZ plane. Input [x, z] ONLY.
        # Normalized to [x, 0.0, z] for internal use.
        if not v:
            return [0.0, 0.0, 0.0]

        # Enforce list/tuple type
        if not isinstance(v, (list, tuple)):
             raise ValueError(f"Briefing icon pos must be a list [x, z], got {type(v)}")

        if len(v) != 2:
             raise ValueError(f"Briefing icon pos must be [x, z] (2 coordinates), got {len(v)}. 3D coordinates are no longer supported.")

        try:
            return [float(v[0]), 0.0, float(v[1])]
        except (ValueError, TypeError):
             raise ValueError(f"Briefing icon coordinates must be numbers, got {v}")

class BriefingStage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    voice_filename: str = 'none.wav'
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    
    # Internal fields (calculated by loader, not authored in FSIF 2.1)
    camera_pos: Optional[List[float]] = None
    camera_orient: Optional[List[float]] = None
    
    camera_time: int = 500
    icons: List[BriefingIcon] = Field(default_factory=list)

    @field_validator('camera_pos', mode='before')
    @classmethod
    def validate_pos(cls, v):
        if v is None: return None
        return _normalize_vector(v)
    
    @field_validator('camera_orient', mode='before')
    @classmethod
    def validate_orient(cls, v):
        if v is None: return None
        return _normalize_orientation(v)

class Briefing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: List[BriefingStage] = Field(default_factory=list)

class DebriefingStage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    condition: str = '( true )'
    voice_filename: str = 'none.wav'
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None
    recommendation: str = ''

class Debriefing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: List[DebriefingStage] = Field(default_factory=list)

class CommandBriefingStage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    ani: str = '<default>'
    voice_filename: str = 'none' # Note: default value should have no extension here, contrary to the BriefingStage counterpart
    voice_name: Optional[str] = None
    voice_style_instructions: Optional[str] = None

class CommandBriefing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: List[CommandBriefingStage] = Field(default_factory=list)

class Reinforcement(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    num_times: int = 1
    arrival_delay: int = 0
    no_messages: List[str] = Field(default_factory=list)
    yes_messages: List[str] = Field(default_factory=list)

class JumpNode(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    position: List[float]

    @field_validator('position', mode='before')
    @classmethod
    def validate_pos(cls, v):
        return _normalize_vector(v)

class Ship(BaseModel):
    # Enforce strict validation (forbid extra fields)
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    name: str
    ship_class: str = Field(..., alias='class') # Required field
    team: str
    location: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: List[float] = Field(default_factory=lambda: [
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    ])
    
    # Optional props with defaults
    iff: str = 'IFF 1'
    ai_behavior: str = 'None'
    ai_class: Optional[str] = None
    cargo_1: str = 'Nothing'
    initial_velocity: int = 33
    initial_hull: int = 100
    
    arrival_location: str = 'Hyperspace'
    arrival_distance: Optional[int] = None
    arrival_anchor: Optional[str] = None
    arrival_delay: int = 0
    arrival_cue: str = '( false )'
    
    departure_location: str = 'Hyperspace'
    departure_anchor: Optional[str] = None
    departure_cue: str = '( false )'
    
    determination: int = 10
    flags: List[str] = Field(default_factory=lambda: ['cargo-known'])
    flags2: List[str] = Field(default_factory=list)
    
    respawn_priority: int = 0
    score: int = 12
    
    subsystems: Subsystems = Field(default_factory=Subsystems)
    weapons: Weapons = Field(default_factory=Weapons)
    
    # Optional logic fields
    ai_goals: Optional[str] = None
    orders_accepted: Optional[List[str]] = None
    orders_accepted_mask: Optional[int] = None
    
    escort_priority: int = 0
    kamikaze_damage: int = 1000
    destroy_at: int = 0
    
    # Docking
    docked_with: Optional[str] = None
    docker_point: Optional[str] = None
    dockee_point: Optional[str] = None
    
    @field_validator('location', mode='before')
    @classmethod
    def validate_loc(cls, v):
        return _normalize_vector(v)

    @field_validator('orientation', mode='before')
    @classmethod
    def validate_orient(cls, v):
        return _normalize_orientation(v)

class Wing(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    name: str
    count: int
    ships: List[Ship] = Field(default_factory=list)
    
    waves: int = 1
    wave_threshold: int = 0
    wave_delay_min: Optional[int] = None
    wave_delay_max: Optional[int] = None
    # wave_delay can be object in FSIF, but normalized before/during loading? 
    # For now assume simplified or handle in loader.
    
    arrival_location: str = 'Hyperspace'
    arrival_distance: Optional[int] = None
    arrival_anchor: Optional[str] = None
    arrival_delay: int = 0
    arrival_cue: str = '( true )'
    
    departure_location: str = 'Hyperspace'
    departure_anchor: Optional[str] = None
    departure_cue: str = '( false )'
    
    flags: List[str] = Field(default_factory=list)
    ai_goals: Optional[str] = None
    
    # FSIF 1.6+ centroid
    position: Optional[List[float]] = None
    spacing: float = 50.0
    
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
