import logging
from pathlib import Path
from typing import Set, Dict, List, Optional
from common import fs_data
import yaml
from data_models import Mission
import briefing_icon_types
from validate_sexp_scalar_styles import validate_sexp_styles

from .ascii_checks import AsciiChecksMixin
from .sexp_checks import SexpChecksMixin
from .spatial import SpatialChecksMixin
from .ship_wing_checks import ShipWingChecksMixin
from .environment import EnvironmentChecksMixin
from .briefing import BriefingChecksMixin
from .misc import MiscChecksMixin

logger = logging.getLogger(__name__)

class Validator(
    AsciiChecksMixin,
    SexpChecksMixin,
    SpatialChecksMixin,
    ShipWingChecksMixin,
    EnvironmentChecksMixin,
    BriefingChecksMixin,
    MiscChecksMixin
):
    def __init__(
        self,
        mission: Mission,
        root_dir: Path,
        fsif_path: Optional[Path] = None,
        tts_provider: str = 'google',
        fsif_root_node: Optional[yaml.Node] = None,
    ):
        self.mission = mission
        self.root_dir = root_dir
        self.fsif_path = fsif_path
        self.fsif_root_node = fsif_root_node
        self.tts_provider = tts_provider.lower()
        self.documentation_dir = root_dir / 'Documentation'
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Reference Data Containers (Dynamic)
        self.non_ship_icon_types = {
            "Waypoint",
            "Jump Node",
            "Planet",
            "Small Planet",
            "Asteroid Field"
        }
        self.ship_classes: Set[str] = set()
        self.dockpoints: Dict[str, Set[str]] = {} # class -> set of dockpoints
        self.subsystems: Dict[str, Set[str]] = {} # class -> set of subsystems
        self.voices: Set[str] = set()
        self.allowed_sexp_operators: Set[str] = set()
        self.num_hardpoints: Dict[str, Dict[str, int]] = {}
        
        # Static Reference Data (from fs_data)
        self.allowed_teams = fs_data.ALLOWED_TEAMS
        self.allowed_priorities = fs_data.ALLOWED_PRIORITIES
        self.allowed_ai_classes = fs_data.ALLOWED_AI_CLASSES
        
        self.allowed_music_mission = fs_data.ALLOWED_MUSIC_MISSION
        self.allowed_music_briefing = fs_data.ALLOWED_MUSIC_BRIEFING
        
        self.allowed_icons = set(briefing_icon_types.ICON_TYPE_ID_BY_NAME.keys())
        
        self.allowed_nebula_patterns = fs_data.ALLOWED_NEBULA_PATTERNS
        self.allowed_nebula_poofs = fs_data.ALLOWED_NEBULA_POOFS
        
        self.allowed_suns = fs_data.ALLOWED_SUNS
        self.allowed_planets = fs_data.ALLOWED_PLANETS
        self.allowed_nebulae_bitmaps = fs_data.ALLOWED_NEBULAE_BITMAPS
        
        # Merge all background bitmaps
        self.allowed_backgrounds = fs_data.ALLOWED_BACKGROUNDS

        # Asteroid / Debris field object variant token sets
        self.allowed_asteroid_field_variants = fs_data.ALLOWED_ASTEROID_FIELD_VARIANTS
        self.allowed_debris_field_variants = fs_data.ALLOWED_DEBRIS_FIELD_VARIANTS
        
        self.allowed_anchors_tokens = fs_data.ALLOWED_ANCHORS_TOKENS

        self.allowed_primary_weapons = fs_data.ALLOWED_PRIMARY_WEAPONS
        self.allowed_secondary_weapons = fs_data.ALLOWED_SECONDARY_WEAPONS
        self.allowed_weapons = fs_data.ALLOWED_WEAPONS
        
        # Load Dynamic Data
        self.load_reference_data()

    def load_reference_data(self):
        # 1. Spacecraft Classes
        self.ship_classes = fs_data.ALLOWED_SHIP_CLASSES
        
        # 2. Dockpoints
        self.dockpoints = fs_data.ALLOWED_DOCKPOINTS
        
        # 3. Subsystems
        self.subsystems = fs_data.ALLOWED_SUBSYSTEMS
        
        # 4. Voices (Provider Aware)
        if self.tts_provider == 'elevenlabs':
            self.voices = fs_data.ALLOWED_VOICES_ELEVENLABS
        elif self.tts_provider == 'inworld':
            self.voices = fs_data.ALLOWED_VOICES_INWORLD
        else:
            # Default to Google
            self.voices = fs_data.ALLOWED_VOICES_GOOGLE

        # 5. SEXPs
        self.allowed_sexp_operators = fs_data.ALLOWED_SEXP_OPERATORS

        # 6. Hardpoints
        self.num_hardpoints = fs_data.NUM_OF_HARDPOINTS

        # 7. Ship bounding boxes
        self.ship_bounding_boxes = getattr(fs_data, 'SHIP_BOUNDING_BOXES', {})


    def log_error(self, msg: str):
        self.errors.append(msg)
        
    def log_warning(self, msg: str):
        self.warnings.append(msg)

    def validate(self) -> bool:
        logger.info("[INFO] [Validator] Starting validation...")
        
        self.validate_global_names()
        self.validate_ascii_text_fields()
        self.validate_mission_info()
        self.validate_environment()
        self.validate_mission_scale_recommendations()
        self.validate_3d_mission_design()
        self.validate_spawn_collisions()
        self.validate_waypoint_collisions()
        self.validate_ships()
        self.validate_wings()
        self.validate_standalone_wing_name_patterns()
        self.validate_start_ship()
        self.validate_player_setup()
        self.validate_docking()
        self.validate_reinforcements()
        self.validate_anchors()
        self.validate_asteroid_field_object_variants()
        self.validate_asteroid_targets()
        self.validate_messages()
        self.validate_briefing()
        self.validate_debriefing()
        self.validate_command_briefing()
        self.validate_briefing_span_tags()
        self.validate_briefing_text_styling_scope()
        self.validate_sexps()
        self.validate_audio()
        self.validate_goals_and_directives()
        self.validate_directive_text_sexp_compatibility()

        # Validate SEXP scalar styles (YAML block format check)
        if self.fsif_root_node is not None or self.fsif_path:
            style_errors = validate_sexp_styles(fsif_path=self.fsif_path, root_node=self.fsif_root_node)
            if style_errors:
                for e in style_errors:
                    self.log_error(e)
        
        # Report results
        if self.warnings:
            logger.warning(f"\n[WARNING] [Validator] Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                logger.warning(f"  - {w}")
                
        if self.errors:
            logger.error(f"\n[ERROR] [Validator] Errors ({len(self.errors)}):")
            for e in self.errors:
                logger.error(f"  - {e}")
            logger.error("\n[FAILED] [Validator] Validation FAILED.")
            return False
            
        logger.info("[SUCCESS] [Validator] Validation PASSED.")
        return True
