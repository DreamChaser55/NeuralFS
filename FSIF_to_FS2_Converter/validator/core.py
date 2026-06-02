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
    """Aggregate FSIF invariant checker.

    Composes all mixin validation passes into a single ``validate()`` call.
    Each mixin enforces a distinct category of FSIF invariants (ASCII content,
    SEXP structure, spatial design guidelines, ship/wing constraints,
    environment tokens, briefing schema, and miscellaneous fields).

    Invariant contract:
    - ``validate()`` returns True when no errors are accumulated, even if
      warnings are present.  A single recorded error causes False.
    - Mixins append to ``self.errors`` (fatal) or ``self.warnings``
      (advisory) via ``log_error`` / ``log_warning`` — they never raise or
      print directly.
    - Reference data loaded in ``load_reference_data()`` is the sole source
      of truth for canonical token sets used during validation.
    """

    def __init__(
        self,
        mission: Mission,
        root_dir: Path,
        fsif_path: Optional[Path] = None,
        tts_provider: Optional[str] = None,
        fsif_root_node: Optional[yaml.Node] = None,
    ):
        self.mission = mission
        self.root_dir = root_dir
        self.fsif_path = fsif_path
        self.fsif_root_node = fsif_root_node
        self.tts_provider = tts_provider.lower() if tts_provider else None
        self.documentation_dir = root_dir / 'Documentation'
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Reference Data Containers (Dynamic)
        self.non_ship_icon_types = briefing_icon_types.NON_SHIP_ICON_TYPES
        self.ship_icon_types = briefing_icon_types.SHIP_ICON_TYPES
        self.ship_classes: Set[str] = set()
        self.dockpoints: Dict[str, Set[str]] = {} # class -> set of dockpoints
        self.subsystems: Dict[str, Set[str]] = {} # class -> set of subsystems
        self.voices: Set[str] = set()
        self.allowed_sexp_operators: Set[str] = set()
        self.fighter_bomber_classes: Set[str] = set()
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
        self.allowed_nebula_storms = fs_data.ALLOWED_NEBULA_STORMS
        
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
        """Populate all token/reference sets used by the mixin validators.

        This is the single place where canonical data from ``fs_data`` and
        ``briefing_icon_types`` is copied into ``self.*`` attributes that the
        mixin checks use.  Any mixin that needs, for example, the set of valid
        ship classes, reads ``self.ship_classes`` rather than importing
        ``fs_data`` directly.

        Invariant: after this method returns, every reference set attribute
        required by a mixin check is populated; a mixin check must never fail
        with an ``AttributeError`` on a reference-set attribute.
        """
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
        elif self.tts_provider == 'google':
            self.voices = fs_data.ALLOWED_VOICES_GOOGLE
        else:
            # No provider was specified.  Voice-name validation is skipped
            # because there is no provider-specific registry to validate against.
            self.voices = set()

        # 5. SEXPs
        self.allowed_sexp_operators = fs_data.ALLOWED_SEXP_OPERATORS

        # 6. Fighter/Bomber classes
        self.fighter_bomber_classes = fs_data.FIGHTER_BOMBER_CLASSES

        # 7. Hardpoints
        self.num_hardpoints = fs_data.NUM_OF_HARDPOINTS

        # 8. Ship bounding boxes
        self.ship_bounding_boxes = getattr(fs_data, 'SHIP_BOUNDING_BOXES', {})


    def should_validate_voice_names(self) -> bool:
        """Return True when a real TTS provider was specified for voice validation."""
        return self.tts_provider in {'google', 'elevenlabs', 'inworld'}


    def log_error(self, msg: str):
        self.errors.append(msg)
        
    def log_warning(self, msg: str):
        self.warnings.append(msg)

    def validate(self) -> bool:
        """Run all FSIF invariant checks and return whether the mission is valid.

        Invariant: the mission is considered valid (returns True) when every
        mixin check completes without appending to ``self.errors``.  Warnings
        do not affect the return value.  The full error and warning lists are
        logged after all checks run so the author receives a consolidated
        report.
        """
        logger.info("[INFO] [Validator] Starting validation...")
        
        self.validate_global_names()
        self.validate_ascii_text_fields()
        self.validate_mission_info()
        self.validate_mission_filename_length()
        self.validate_environment()
        self.validate_mission_scale_recommendations()
        self.validate_3d_mission_design()
        self.validate_spawn_collisions()
        self.validate_waypoint_collisions()
        self.validate_shared_waypoint_orders()
        self.validate_ships()
        self.validate_cargo_field()
        self.validate_wings()
        self.validate_standalone_wing_name_patterns()
        self.validate_large_ship_escort_recommendation()
        self.validate_large_ship_orientation_defaults()
        self.validate_orientation_ignored_for_nonhyperspace_arrival()
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
        self.validate_mission_has_briefing_text_styling()
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
