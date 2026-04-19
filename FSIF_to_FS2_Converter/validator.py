import re
import math
import logging
from pathlib import Path
from typing import Set, Dict, List, Optional
import fs_flags_constants
import fs_data
from data_models import Mission
import briefing_icon_types
from validate_sexp_scalar_styles import validate_sexp_styles
from utils import calculate_briefing_camera_height
from text_styling_utils import extract_briefing_style_tags, validate_span_style_tags

try:
    from weapons_compatibility_data import WEAPON_COMPATIBILITY
except ImportError:
    WEAPON_COMPATIBILITY = {}

logger = logging.getLogger(__name__)


class Validator:
    _MISSION_SCALE_RECOMMENDATION_METERS = 20_000.0

    def __init__(self, mission: Mission, root_dir: Path, fsif_path: Optional[Path] = None, tts_provider: str = 'google'):
        self.mission = mission
        self.root_dir = root_dir
        self.fsif_path = fsif_path
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

    def _validate_ascii_text(self, path: str, text: Optional[str]):
        """
        Reject non-ASCII text in FSO-facing FSIF fields.

        ASCII control characters such as '\n', '\r' and '\t' are allowed
        naturally because they are part of the 7-bit ASCII range.
        """
        if text is None:
            return

        value = str(text)
        if value.isascii():
            return

        offenders = []
        for index, ch in enumerate(value):
            if ord(ch) > 127:
                offenders.append(f"{repr(ch)} (U+{ord(ch):04X}, index {index})")

        if not offenders:
            return

        details = ", ".join(offenders[:5])
        if len(offenders) > 5:
            details += f", ... (+{len(offenders) - 5} more)"

        self.log_error(f"{path} contains non-ASCII character(s): {details}")

    def _validate_xstr_text(self, path: str, text: Optional[str]):
        """
        Validates text that will be wrapped in XSTR("...", -1) in the emitted .fs2 file.
        Rejects non-ASCII characters and double quotes (").
        Double quotes break the FSO stuff_string parser when embedded inside an XSTR macro.
        """
        if text is None:
            return
            
        self._validate_ascii_text(path, text)
        
        if '"' in text:
            self.log_error(
                f"{path} contains double quote (\") characters. "
                f"These are not allowed in text fields displayed to the player, as they break "
                f"the FSO engine parser when wrapped in XSTR. Please use single quotes (') instead."
            )

    def _validate_ascii_text_list(self, path: str, values: Optional[List[str]]):
        if not values:
            return
        for i, value in enumerate(values):
            self._validate_ascii_text(f"{path}[{i}]", value)

    def validate_ascii_text_fields(self):
        """
        Validate only FSO-facing string fields.

        Excluded intentionally:
        - voice_name
        - voice_style_instructions
        - internal converter-only helper fields such as wing template names
        """
        self._validate_ascii_text('mission_flow.fiction_viewer', self.mission.fiction_viewer)

        info = self.mission.mission_info
        self._validate_xstr_text('mission_info.name', info.name)
        self._validate_ascii_text('mission_info.author', info.author)
        self._validate_xstr_text('mission_info.description', info.description)
        self._validate_ascii_text('mission_info.game_type', info.game_type)
        self._validate_ascii_text('mission_info.ai_profile', info.ai_profile)
        self._validate_ascii_text_list('mission_info.flags', info.flags)

        env = self.mission.environment
        for i, sun in enumerate(env.suns):
            self._validate_ascii_text(f'environment.suns[{i}].texture', sun.texture)

        for i, bitmap in enumerate(env.starbitmaps):
            self._validate_ascii_text(f'environment.starbitmaps[{i}].texture', bitmap.texture)

        if env.nebula:
            self._validate_ascii_text('environment.nebula.pattern', env.nebula.pattern)
            self._validate_ascii_text('environment.nebula.storm', env.nebula.storm)
            self._validate_ascii_text_list('environment.nebula.poofs', env.nebula.poofs)

        if env.asteroid_field:
            self._validate_ascii_text_list('environment.asteroid_field.debris_types', env.asteroid_field.debris_types)
            self._validate_ascii_text_list('environment.asteroid_field.targets', env.asteroid_field.targets)

        setup = self.mission.player_setup
        self._validate_ascii_text('player_setup.start_ship', setup.start_ship)
        for i, choice in enumerate(setup.extra_ships):
            self._validate_ascii_text(f'player_setup.extra_ships[{i}].class', choice.ship_class)
        self._validate_ascii_text_list('player_setup.extra_weapons', setup.extra_weapons)

        for i, ship in enumerate(self.mission.ships):
            prefix = f'ships[{i}]'
            self._validate_ascii_text(f'{prefix}.name', ship.name)
            self._validate_ascii_text(f'{prefix}.class', ship.ship_class)
            self._validate_ascii_text(f'{prefix}.team', ship.team)
            self._validate_ascii_text(f'{prefix}.ai_class', ship.ai_class)
            self._validate_xstr_text(f'{prefix}.cargo', ship.cargo)
            self._validate_ascii_text(f'{prefix}.arrival_location', ship.arrival_location)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', ship.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', ship.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_location', ship.departure_location)
            self._validate_ascii_text(f'{prefix}.departure_anchor', ship.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', ship.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', ship.flags)
            self._validate_ascii_text(f'{prefix}.ai_goals', ship.ai_goals)
            self._validate_ascii_text(f'{prefix}.docked_with', ship.docked_with)
            self._validate_ascii_text(f'{prefix}.docker_point', ship.docker_point)
            self._validate_ascii_text(f'{prefix}.dockee_point', ship.dockee_point)
            for j, subsystem in enumerate(ship.subsystems.list):
                self._validate_ascii_text(f'{prefix}.subsystems.list[{j}].name', subsystem.name)
            self._validate_ascii_text_list(f'{prefix}.weapons.primary', ship.weapons.primary)
            self._validate_ascii_text_list(f'{prefix}.weapons.secondary', ship.weapons.secondary)

        for i, wing in enumerate(self.mission.wings):
            prefix = f'wings[{i}]'
            self._validate_ascii_text(f'{prefix}.name', wing.name)
            self._validate_ascii_text(f'{prefix}.arrival_location', wing.arrival_location)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', wing.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', wing.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_location', wing.departure_location)
            self._validate_ascii_text(f'{prefix}.departure_anchor', wing.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', wing.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', wing.flags)
            self._validate_ascii_text(f'{prefix}.ai_goals', wing.ai_goals)

        for waypoint_name in self.mission.waypoints.keys():
            self._validate_ascii_text(f'waypoints key {waypoint_name!r}', waypoint_name)

        for i, event in enumerate(self.mission.events):
            prefix = f'events[{i}]'
            self._validate_ascii_text(f'{prefix}.name', event.name)
            self._validate_ascii_text(f'{prefix}.formula', event.formula)
            self._validate_xstr_text(f'{prefix}.directive_text', event.directive_text)

        for i, goal in enumerate(self.mission.goals):
            prefix = f'goals[{i}]'
            self._validate_ascii_text(f'{prefix}.name', goal.name)
            self._validate_ascii_text(f'{prefix}.type', goal.type)
            self._validate_xstr_text(f'{prefix}.message', goal.message)
            self._validate_ascii_text(f'{prefix}.formula', goal.formula)

        for i, message in enumerate(self.mission.messages):
            prefix = f'messages[{i}]'
            self._validate_ascii_text(f'{prefix}.name', message.name)
            self._validate_xstr_text(f'{prefix}.message', message.message)

        for i, stage in enumerate(self.mission.command_briefing.stages):
            prefix = f'command_briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.ani', stage.ani)

        for i, stage in enumerate(self.mission.briefing.stages):
            prefix = f'briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            for j, icon in enumerate(stage.icons):
                icon_prefix = f'{prefix}.icons[{j}]'
                self._validate_ascii_text(f'{icon_prefix}.type', icon.type)
                self._validate_ascii_text(f'{icon_prefix}.team', icon.team)
                self._validate_ascii_text(f'{icon_prefix}.class', icon.ship_class)
                self._validate_xstr_text(f'{icon_prefix}.label', icon.label)

        for i, stage in enumerate(self.mission.debriefing.stages):
            prefix = f'debriefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.condition', stage.condition)
            self._validate_xstr_text(f'{prefix}.recommendation', stage.recommendation)

        for i, reinforcement in enumerate(self.mission.reinforcements):
            prefix = f'reinforcements[{i}]'
            self._validate_ascii_text(f'{prefix}.name', reinforcement.name)
            self._validate_ascii_text_list(f'{prefix}.no_messages', reinforcement.no_messages)
            self._validate_ascii_text_list(f'{prefix}.yes_messages', reinforcement.yes_messages)

        for i, jump_node in enumerate(self.mission.jump_nodes):
            self._validate_ascii_text(f'jump_nodes[{i}].name', jump_node.name)

        audio = self.mission.audio
        self._validate_ascii_text('audio.mission_music', audio.mission_music)
        self._validate_ascii_text('audio.briefing_music', audio.briefing_music)

    def _ship_has_fighterbay(self, ship_class: str) -> bool:
        """Check if a ship class has a fighterbay subsystem."""
        if ship_class not in self.subsystems:
            return False  # Unknown class, can't verify
        
        for subsys_name in self.subsystems[ship_class]:
            if "fighterbay" in subsys_name.lower():
                return True
        return False

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
        if self.fsif_path:
            style_errors = validate_sexp_styles(self.fsif_path)
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

    def validate_global_names(self):
        """
        Validate uniqueness and length of global entity names.
        
        Enforces:
        - Name length < 30 characters (FSO engine limit).
        - Uniqueness within namespaces (Objects, Events, Goals, Messages).
        """
        # Separate namespaces
        objects: Dict[str, str] = {}
        events: Dict[str, str] = {}
        goals: Dict[str, str] = {}
        messages: Dict[str, str] = {}
        
        def check(name, type_, scope):
            if not name: return
            
            # Length Limit
            if len(name) >= 30:
                self.log_error(f"{type_} '{name}' name length {len(name)} exceeds limit (<30).")
            
            # Duplicates in scope
            if name in scope:
                self.log_error(f"{type_} '{name}' conflicts with existing {scope[name]} '{name}'")
            else:
                scope[name] = type_

        # Objects Scope
        for s in self.mission.ships: check(s.name, "Ship", objects)
        for w in self.mission.wings: check(w.name, "Wing", objects)
        for name in self.mission.waypoints: check(name, "Waypoint", objects)
        for j in self.mission.jump_nodes: check(j.name, "Jump Node", objects)
        
        # Events Scope
        for e in self.mission.events: check(e.name, "Event", events)
        
        # Goals Scope
        for g in self.mission.goals: check(g.name, "Goal", goals)
        
        # Messages Scope
        for m in self.mission.messages: check(m.name, "Message", messages)

    def validate_mission_info(self):
        # Validate flags
        for f in self.mission.mission_info.flags:
            # We check if it maps to a known flag bit
            canon = fs_flags_constants.resolve_mission_flag(f)
            if not canon:
                self.log_warning(f"Unknown mission flag: '{f}'")

    def validate_environment(self):
        """
        Validate environment settings (suns, backgrounds, nebula).
        
        Checks that referenced textures and patterns exist in the
        allowed token lists.
        """
        env = self.mission.environment
        
        # Suns
        for i, s in enumerate(env.suns):
            if s.texture not in self.allowed_suns:
                 self.log_error(f"Invalid sun texture '{s.texture}' in environment.suns[{i}]")
            # Warn if sun is at [0, 0, 0] — directly in front of the player at default spawn
            if s.angles and all(abs(a) < 1e-6 for a in s.angles):
                self.log_warning(
                    f"environment.suns[{i}] (texture '{s.texture}') has angles [0, 0, 0], "
                    f"which places the sun directly in front of the player at default spawn "
                    f"orientation. This causes a whiteout blinding effect. "
                    f"Unless it's intended, set a non-zero angles value (in radians)."
                )

        # Starbitmaps
        for i, s in enumerate(env.starbitmaps):
            if s.texture not in self.allowed_backgrounds:
                 self.log_error(f"Invalid starbitmap texture '{s.texture}' in environment.starbitmaps[{i}]")

        if env.nebula and env.nebula.enabled and env.starbitmaps:
            self.log_error(f"environment.starbitmaps must be empty when full nebula is enabled (environment.nebula.enabled: true)")

        mission_flags_lower = {str(flag).strip().lower() for flag in self.mission.mission_info.flags}
        is_subspace_mission = 'subspace' in mission_flags_lower
        is_full_nebula_mission = bool(env.nebula and env.nebula.enabled)

        if is_subspace_mission and env.starbitmaps:
            self.log_error(f"environment.starbitmaps must be empty in subspace missions (they are not visible in subspace)")

        # Sparse normal-space background advisory
        if not is_subspace_mission and not is_full_nebula_mission:
            background_nebula_count = sum(
                1 for bitmap in env.starbitmaps if bitmap.texture in self.allowed_nebulae_bitmaps
            )
            if background_nebula_count < 3:
                self.log_warning(
                    f"This mission has only {background_nebula_count} background nebula "
                    f"starbitmap(s). Good-looking missions usually include at least 3. "
                    f"Consider adding more background nebulae so the sky does not look too empty."
                )

        # Nebula
        if env.nebula.enabled:
            if env.nebula.pattern and env.nebula.pattern not in self.allowed_nebula_patterns:
                self.log_error(f"Invalid nebula pattern '{env.nebula.pattern}'")
            
            for p in env.nebula.poofs:
                if p not in self.allowed_nebula_poofs:
                    self.log_error(f"Invalid nebula poof '{p}'")

        # Asteroid/Debris Field Logic
        af = env.asteroid_field
        if af and af.targets:
            # Targets are only valid for Active Asteroid fields
            if not (af.field_type == 'active' and af.genre == 'asteroid'):
                self.log_warning(f"The asteroid field defines targets but they will be ignored (type='{af.field_type}', genre='{af.genre}'). Targets are only supported for Active Asteroid fields.")

    def validate_mission_scale_recommendations(self):
        """
        Warn when authored mission geometry exceeds the recommended 20 km scale.

        This is an advisory mission-design check only. It does not fail validation.
        It covers:
        - distances between positioned mission objects (standalone ships, wing centroids, jump nodes, waypoint points)
        - authored arrival_distance values on ships and wings that reference an arrival_anchor

        Arrival location awareness:
        - "Hyperspace" (default): the authored location/position field is used directly.
        - "Docking Bay": the object's effective position is inherited from its arrival_anchor ship
          (resolved recursively, with cycle detection).
        - Any directional arrival (e.g. "Near Ship", "In front of ship"): the object is excluded
          from distance checks because it has no definite initial position.
        """
        limit_m = self._MISSION_SCALE_RECOMMENDATION_METERS
        limit_km = limit_m / 1000.0

        # Build a ship-name → Ship lookup for arrival_anchor resolution.
        ship_map = {s.name: s for s in self.mission.ships}

        def resolve_effective_position(arrival_location, arrival_anchor, own_position, visited=None):
            """
            Return the effective starting position of a ship or wing, taking arrival_location
            into account.  Returns None when the object has no definite initial position and
            should therefore be excluded from distance checks.
            """
            arr_loc = (arrival_location or "Hyperspace").strip().lower()

            if arr_loc == "hyperspace":
                return own_position

            if arr_loc == "docking bay":
                if not arrival_anchor:
                    return None  # Malformed; skip
                if visited is None:
                    visited = set()
                if arrival_anchor in visited:
                    return None  # Cycle guard
                visited.add(arrival_anchor)
                anchor_ship = ship_map.get(arrival_anchor)
                if anchor_ship is None:
                    return None  # Anchor not found; skip
                return resolve_effective_position(
                    anchor_ship.arrival_location,
                    anchor_ship.arrival_anchor,
                    anchor_ship.location,
                    visited,
                )

            # Any other directional arrival_location (e.g. "Near Ship", "In front of ship"):
            # the object spawns relative to a moving anchor — no definite initial position.
            return None

        positioned_objects = []
        distance_violations = []

        wing_member_names: Set[str] = set()
        for wing in self.mission.wings:
            for ship in wing.ships:
                wing_member_names.add(ship.name)

        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue
            eff_pos = resolve_effective_position(ship.arrival_location, ship.arrival_anchor, ship.location)
            if eff_pos is not None:
                positioned_objects.append(("Ship", ship.name, eff_pos))

        for wing in self.mission.wings:
            wing_own_position = wing.position
            if wing_own_position is None and wing.ships:
                # Defensive fallback: use the leader position if the authored wing centroid is unexpectedly unavailable.
                wing_own_position = wing.ships[0].location

            eff_pos = resolve_effective_position(wing.arrival_location, wing.arrival_anchor, wing_own_position)
            if eff_pos is not None:
                positioned_objects.append(("Wing", wing.name, eff_pos))

        for jump_node in self.mission.jump_nodes:
            positioned_objects.append(("Jump Node", jump_node.name, jump_node.position))

        for path_name, points in self.mission.waypoints.items():
            for index, point in enumerate(points, start=1):
                positioned_objects.append(("Waypoint", f"{path_name}:{index}", point))

        for i in range(len(positioned_objects)):
            kind_a, name_a, pos_a = positioned_objects[i]
            for j in range(i + 1, len(positioned_objects)):
                kind_b, name_b, pos_b = positioned_objects[j]

                dx = float(pos_a[0]) - float(pos_b[0])
                dy = float(pos_a[1]) - float(pos_b[1])
                dz = float(pos_a[2]) - float(pos_b[2])
                distance_m = math.sqrt(dx * dx + dy * dy + dz * dz)

                if distance_m > limit_m:
                    distance_violations.append((kind_a, name_a, kind_b, name_b, distance_m))

        if distance_violations:
            distance_violations.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
            violation_lines = [
                f"    - {kind_a} '{name_a}' <-> {kind_b} '{name_b}': "
                f"{distance_m / 1000.0:.1f} km"
                for kind_a, name_a, kind_b, name_b, distance_m in distance_violations
            ]
            self.log_warning(
                f"Mission scale recommendation: {len(distance_violations)} object pair(s) exceed the "
                f"recommended maximum distance of {limit_km:.1f} km. Keep points of interest within 20 km "
                f"to avoid long travel times.\n"
                + "\n".join(violation_lines)
            )

        def check_arrival_distance(context: str, arrival_anchor: Optional[str], arrival_distance: Optional[int]):
            if not arrival_anchor or arrival_distance is None:
                return

            if arrival_distance > limit_m:
                self.log_warning(
                    f"Mission scale recommendation: {context} arrival_distance {arrival_distance} m "
                    f"from arrival_anchor '{arrival_anchor}' exceeds the recommended maximum of "
                    f"{limit_km:.1f} km. Keep anchor-based arrivals within 20 km to avoid long travel times."
                )

        for ship in self.mission.ships:
            check_arrival_distance(f"Ship '{ship.name}'", ship.arrival_anchor, ship.arrival_distance)

        for wing in self.mission.wings:
            check_arrival_distance(f"Wing '{wing.name}'", wing.arrival_anchor, wing.arrival_distance)

    def validate_3d_mission_design(self):
        """
        Warn if all objects in a mission are placed strictly on the XZ plane (Y-coordinate = 0).
        This encourages using the 3D space to make missions more interesting and prevent unintended collisions.
        """
        positioned_objects = []

        for ship in self.mission.ships:
            positioned_objects.append(("Ship", ship.name, ship.location))

        for wing in self.mission.wings:
            wing_position = wing.position
            if wing_position is None and wing.ships:
                wing_position = wing.ships[0].location
            if wing_position is not None:
                positioned_objects.append(("Wing", wing.name, wing_position))

        for jump_node in self.mission.jump_nodes:
            positioned_objects.append(("Jump Node", jump_node.name, jump_node.position))

        for path_name, points in self.mission.waypoints.items():
            for index, point in enumerate(points, start=1):
                positioned_objects.append(("Waypoint", f"{path_name}:{index}", point))

        if not positioned_objects:
            return

        all_y_zero = True
        for kind, name, pos in positioned_objects:
            if abs(float(pos[1])) >= 0.001:
                all_y_zero = False
                break

        if all_y_zero:
            self.log_warning(
                "Mission design recommendation: All objects are currently placed on the 2D XZ plane (Y=0). "
                "Spreading objects in the third dimension (Y-axis) creates more interesting 3D missions "
                "and prevents unintended collisions."
            )

    def validate_spawn_collisions(self):
        """
        Warn if ships or wings that arrive via Hyperspace spawn too close to each other.
        """
        positioned_objects = []
        wing_members = set()

        # Collect wing members
        for w in self.mission.wings:
            for s in w.ships:
                wing_members.add(s.name)

        # 1. Collect all standalone ships arriving via Hyperspace
        for s in self.mission.ships:
            if s.name in wing_members:
                continue
            
            arr_loc = s.arrival_location.strip().lower()
            if arr_loc != "hyperspace":
                continue
                
            obb = self._get_world_obb(s.ship_class, s.orientation, s.location, padding=0.0)
            positioned_objects.append({
                'type': 'Ship',
                'name': s.name,
                'pos': s.location,
                'obb': obb,
                'docked_with': s.docked_with
            })

        # 2. Collect all wings arriving via Hyperspace
        for w in self.mission.wings:
            arr_loc = w.arrival_location.strip().lower()
            if arr_loc != "hyperspace":
                continue
                
            # Use wing position, fallback to leader's position
            pos = w.position
            if pos is None and w.ships:
                pos = w.ships[0].location
                
            if pos is None:
                continue

            # Estimate wing bounding box using the first ship's class
            if w.ships:
                obb = self._get_world_obb(w.ships[0].ship_class, w.ships[0].orientation, pos, padding=100.0)
            else:
                ident_orientation = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
                obb = self._get_world_obb("Unknown", ident_orientation, pos, padding=100.0)

            positioned_objects.append({
                'type': 'Wing',
                'name': w.name,
                'pos': pos,
                'obb': obb,
                'docked_with': None # Wings can't be pre-spawn docked
            })

        collisions = []

        # 3. Pairwise check
        for i in range(len(positioned_objects)):
            obj_a = positioned_objects[i]
            for j in range(i + 1, len(positioned_objects)):
                obj_b = positioned_objects[j]

                # Skip if a is explicitly docked to b or vice versa
                if obj_a['docked_with'] == obj_b['name'] or obj_b['docked_with'] == obj_a['name']:
                    continue

                # OBB overlap test
                if self._obb_intersects(obj_a['obb'], obj_b['obb']):
                    dx = float(obj_a['pos'][0]) - float(obj_b['pos'][0])
                    dy = float(obj_a['pos'][1]) - float(obj_b['pos'][1])
                    dz = float(obj_a['pos'][2]) - float(obj_b['pos'][2])
                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                    collisions.append((obj_a, obj_b, dist))

        if collisions:
            # Sort by distance for cleaner logging
            collisions.sort(key=lambda x: x[2])
            for obj_a, obj_b, dist in collisions:
                self.log_warning(
                    f"Mission design recommendation: {obj_a['type']} '{obj_a['name']}' spawns very close to "
                    f"{obj_b['type']} '{obj_b['name']}'. Their bounding boxes intersect (center distance {dist:.1f}m). "
                    f"Both objects arrive via Hyperspace at static locations. This may cause an immediate collision upon mission start or arrival."
                )

    def _dot(self, v1: List[float], v2: List[float]) -> float:
        return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

    def _cross(self, v1: List[float], v2: List[float]) -> List[float]:
        return [
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        ]

    def _normalize(self, v: List[float]) -> List[float]:
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if mag == 0:
            return [0.0, 0.0, 0.0]
        return [v[0]/mag, v[1]/mag, v[2]/mag]

    def _obb_intersects(self, obb_a: dict, obb_b: dict) -> bool:
        T = [obb_b['center'][i] - obb_a['center'][i] for i in range(3)]
        
        axes_a = obb_a['axes']
        axes_b = obb_b['axes']
        
        axes_to_test = []
        axes_to_test.extend(axes_a)
        axes_to_test.extend(axes_b)
        
        for i in range(3):
            for j in range(3):
                cross_axis = self._cross(axes_a[i], axes_b[j])
                if sum(c*c for c in cross_axis) > 1e-6:
                    axes_to_test.append(self._normalize(cross_axis))
                    
        for L in axes_to_test:
            t_proj = abs(self._dot(T, L))
            r_a = sum(obb_a['extents'][i] * abs(self._dot(axes_a[i], L)) for i in range(3))
            r_b = sum(obb_b['extents'][i] * abs(self._dot(axes_b[i], L)) for i in range(3))
            
            if t_proj > r_a + r_b:
                return False
                
        return True

    def _get_ship_radius(self, ship_class: str) -> float:
        """Estimate the collision radius of a ship.
        First tries to use accurate bounding box data, then falls back to prefix heuristic.
        """
        if ship_class in self.ship_bounding_boxes:
            box = self.ship_bounding_boxes[ship_class]
            min_x, min_y, min_z = box['min']
            max_x, max_y, max_z = box['max']
            # Max distance from center to any corner
            return math.sqrt(max(abs(min_x), abs(max_x))**2 + 
                             max(abs(min_y), abs(max_y))**2 + 
                             max(abs(min_z), abs(max_z))**2)
            
        cls = ship_class.upper()
        if any(p in cls for p in ['GTI', 'PVI', 'BASE', 'INSTALLATION']):
            return 1000.0
        if any(cls.startswith(p) for p in ['GTD', 'PVD', 'SD']):
            return 600.0
        if any(cls.startswith(p) for p in ['GTC', 'PVC', 'SC', 'GTSC', 'PVSC']):
            return 150.0
        if any(cls.startswith(p) for p in ['GTFR', 'PVFR', 'SFR', 'GTT', 'PVT', 'ST']):
            return 150.0
        return 50.0

    def _get_world_obb(self, ship_class: str, orientation: List[float], location: List[float], padding: float = 0.0) -> dict:
        """
        Get the world-space Oriented Bounding Box (OBB) for a ship given its class, orientation, location, and optional padding.
        """
        # 1. Get local bounding box
        if ship_class in self.ship_bounding_boxes:
            box = self.ship_bounding_boxes[ship_class]
            min_x, min_y, min_z = box['min']
            max_x, max_y, max_z = box['max']
        else:
            r = self._get_ship_radius(ship_class)
            min_x, min_y, min_z = -r, -r, -r
            max_x, max_y, max_z = r, r, r

        # 2. Local center and extents
        cx = (max_x + min_x) / 2.0
        cy = (max_y + min_y) / 2.0
        cz = (max_z + min_z) / 2.0

        ex = (max_x - min_x) / 2.0 + padding
        ey = (max_y - min_y) / 2.0 + padding
        ez = (max_z - min_z) / 2.0 + padding

        # 3. Local axes in world space
        axis_x = self._normalize([orientation[0], orientation[3], orientation[6]])
        axis_y = self._normalize([orientation[1], orientation[4], orientation[7]])
        axis_z = self._normalize([orientation[2], orientation[5], orientation[8]])

        # 4. Transform local center to world space
        world_cx = orientation[0] * cx + orientation[1] * cy + orientation[2] * cz + location[0]
        world_cy = orientation[3] * cx + orientation[4] * cy + orientation[5] * cz + location[1]
        world_cz = orientation[6] * cx + orientation[7] * cy + orientation[8] * cz + location[2]

        return {
            'center': [world_cx, world_cy, world_cz],
            'axes': [axis_x, axis_y, axis_z],
            'extents': [ex, ey, ez]
        }

    def validate_waypoint_collisions(self):
        """
        Check if standalone ship waypoint move orders are likely to cause a collision 
        with another ship or station in the mission.
        
        Note: Wing-level waypoint orders are intentionally not checked for path collisions. 
        Wings typically consist of fighters or bombers which have their own AI routines for collision avoidance.
        """
        import re
        import math

        # Regex to find ai-waypoints and ai-waypoints-once
        # Extracts the path name, stripping quotes if present
        wp_regex = re.compile(r'\(\s*ai-waypoints(?:-once)?\s+(?:"([^"]+)"|([^"\s)]+))', re.IGNORECASE)

        ships_with_waypoints = set()
        for w in self.mission.wings:
            if w.ai_goals and wp_regex.search(w.ai_goals):
                for s in w.ships:
                    ships_with_waypoints.add(s.name)
                    
        for s in self.mission.ships:
            if s.ai_goals and wp_regex.search(s.ai_goals):
                ships_with_waypoints.add(s.name)

        ship_map = {s.name: s for s in self.mission.ships}

        def get_effective_initial_location(ship_name, visited=None):
            if visited is None:
                visited = set()
            if ship_name in visited:
                return None
            visited.add(ship_name)
            
            s = ship_map.get(ship_name)
            if not s:
                return None
                
            arr_loc = s.arrival_location.strip().lower()
            if arr_loc == "hyperspace":
                return s.location
            elif arr_loc == "docking bay":
                if s.arrival_anchor:
                    anchor_loc = get_effective_initial_location(s.arrival_anchor, visited)
                    if anchor_loc is not None:
                        return anchor_loc
                return s.location
            else:
                return None

        # 1. Collect all stationary or existing objects to check against
        obstacles = []
        wing_members = set()
        for w in self.mission.wings:
            for s in w.ships:
                wing_members.add(s.name)
                
        for s in self.mission.ships:
            radius = self._get_ship_radius(s.ship_class)
            if radius <= 50.0:
                continue
            if s.name in ships_with_waypoints:
                continue
            eff_loc = get_effective_initial_location(s.name)
            if eff_loc is None:
                continue
            
            obb = self._get_world_obb(s.ship_class, s.orientation, eff_loc, padding=0.0)
            
            obstacles.append({
                'name': s.name,
                'pos': eff_loc,
                'radius': radius,
                'obb': obb,
                'is_wing_member': s.name in wing_members
            })

        def point_segment_distance(p, a, b):
            """Calculate the shortest distance from point p to line segment a-b."""
            ab = [b[0]-a[0], b[1]-a[1], b[2]-a[2]]
            ap = [p[0]-a[0], p[1]-a[1], p[2]-a[2]]
            
            ab_len_sq = ab[0]**2 + ab[1]**2 + ab[2]**2
            if ab_len_sq == 0:
                # a and b are the same point
                return math.sqrt(ap[0]**2 + ap[1]**2 + ap[2]**2)
                
            t = (ap[0]*ab[0] + ap[1]*ab[1] + ap[2]*ab[2]) / ab_len_sq
            t = max(0.0, min(1.0, t))
            
            closest = [a[0] + t*ab[0], a[1] + t*ab[1], a[2] + t*ab[2]]
            dist = math.sqrt((p[0]-closest[0])**2 + (p[1]-closest[1])**2 + (p[2]-closest[2])**2)
            return dist

        def get_segment_obb(p1, p2, ship_class):
            if ship_class in self.ship_bounding_boxes:
                box = self.ship_bounding_boxes[ship_class]
                min_x, min_y, min_z = box['min']
                max_x, max_y, max_z = box['max']
            else:
                r = self._get_ship_radius(ship_class)
                min_x, min_y, min_z = -r, -r, -r
                max_x, max_y, max_z = r, r, r
                
            ex = (max_x - min_x) / 2.0
            ey = (max_y - min_y) / 2.0
            ez = (max_z - min_z) / 2.0
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            axis_z = self._normalize([dx, dy, dz])
            if sum(abs(c) for c in axis_z) < 1e-6:
                axis_z = [0.0, 0.0, 1.0]
                
            up = [0.0, 1.0, 0.0]
            if abs(self._dot(axis_z, up)) > 0.999:
                up = [1.0, 0.0, 0.0]
                
            axis_x = self._normalize(self._cross(up, axis_z))
            axis_y = self._normalize(self._cross(axis_z, axis_x))
            
            cx = (p1[0] + p2[0]) / 2.0
            cy = (p1[1] + p2[1]) / 2.0
            cz = (p1[2] + p2[2]) / 2.0
            
            return {
                'center': [cx, cy, cz],
                'axes': [axis_x, axis_y, axis_z],
                'extents': [ex, ey, ez + (dist / 2.0)]
            }

        def check_path_for_collisions(entity_type, entity_name, start_pos, entity_class, path_name):
            if path_name not in self.mission.waypoints:
                return
                
            points = [start_pos] + self.mission.waypoints[path_name]
            collisions = {}
            
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                
                segment_obb = get_segment_obb(p1, p2, entity_class)
                
                for obs in obstacles:
                    # Don't collide with yourself
                    if obs['name'] == entity_name:
                        continue
                        
                    # Exclude collision checks between a ship and its arrival anchor
                    # if the ship starts in the anchor's docking bay
                    entity_ship = ship_map.get(entity_name)
                    obs_ship = ship_map.get(obs['name'])
                    
                    if entity_ship and entity_ship.arrival_location.strip().lower() == "docking bay" and entity_ship.arrival_anchor == obs['name']:
                        continue
                        
                    if obs_ship and obs_ship.arrival_location.strip().lower() == "docking bay" and obs_ship.arrival_anchor == entity_name:
                        continue

                    if self._obb_intersects(segment_obb, obs['obb']):
                        dist = point_segment_distance(obs['pos'], p1, p2)
                        if obs['name'] not in collisions or dist < collisions[obs['name']]:
                            collisions[obs['name']] = dist

            if collisions:
                details = ", ".join(f"ship '{name}' (distance {d:.1f}m, bounding boxes intersect)" for name, d in collisions.items())
                self.log_warning(
                    f"{entity_type} '{entity_name}' waypoint path '{path_name}' passes very close "
                    f"to the initial location of {details}. "
                    f"This could cause a collision during waypoint movement."
                )

        # 2. Check standalone ships
        for s in self.mission.ships:
            if s.name in wing_members:
                continue
            if s.ai_goals:
                match = wp_regex.search(s.ai_goals)
                if match:
                    path_name = match.group(1) or match.group(2)
                    my_radius = self._get_ship_radius(s.ship_class)
                    if my_radius <= 50.0:
                        continue
                    eff_loc = get_effective_initial_location(s.name)
                    if eff_loc is None:
                        continue
                    check_path_for_collisions("Ship", s.name, eff_loc, s.ship_class, path_name)

    def validate_ships(self):
        """
        Validate ship properties.
        
        Checks:
        - Validity of ship class and team.
        - Known flags and AI class.
        - Weapon compatibility (if data available).
        - Subsystem validity (if data available).
        """
        for i, ship in enumerate(self.mission.ships):
            # 1. Class
            if ship.ship_class not in self.ship_classes:
                self.log_error(f"Ship '{ship.name}' has invalid class '{ship.ship_class}'")
            
            # 2. Team
            if ship.team not in self.allowed_teams:
                self.log_error(f"Ship '{ship.name}' has invalid team '{ship.team}'")
            
            # 3. Flags
            all_flags = ship.flags
            for f in all_flags:
                norm = fs_flags_constants.normalize_flag(f)
                if norm not in fs_flags_constants.SHIP_FLAGS_BUCKET:
                    self.log_error(f"Ship '{ship.name}' has unknown flag '{f}'")

            # escort_priority requires the 'escort' flag
            if ship.escort_priority > 0:
                has_escort_flag = any(
                    fs_flags_constants.normalize_flag(f) == 'escort'
                    for f in ship.flags
                )
                if not has_escort_flag:
                    self.log_error(
                        f"Ship '{ship.name}' has escort_priority {ship.escort_priority} set, "
                        f"but is missing the 'escort' flag. "
                        f"Add 'escort' to the ship's flags list."
                    )

            # AI Class
            if ship.ai_class and ship.ai_class not in self.allowed_ai_classes:
                self.log_error(f"Ship '{ship.name}' has invalid ai_class '{ship.ai_class}'")

            # Hull Range
            if not (0 <= ship.initial_hull <= 100):
                self.log_error(f"Ship '{ship.name}' initial_hull {ship.initial_hull} out of range [0, 100]")

            # 4. Weapon Compatibility
            # Only validate if we have data for this class
            if ship.ship_class in WEAPON_COMPATIBILITY:
                allowed = WEAPON_COMPATIBILITY[ship.ship_class]
                
                # Primary weapons
                for w_name in ship.weapons.primary:
                    if w_name and w_name not in allowed['primary']:
                        self.log_error(f"Ship '{ship.name}' (class {ship.ship_class}) has incompatible primary weapon '{w_name}'. Allowed: {sorted(list(allowed['primary']))}")
                
                # Secondary weapons
                for w_name in ship.weapons.secondary:
                    if w_name and w_name not in allowed['secondary']:
                        self.log_error(f"Ship '{ship.name}' (class {ship.ship_class}) has incompatible secondary weapon '{w_name}'. Allowed: {sorted(list(allowed['secondary']))}")

            # 5. Subsystems
            # Only validate if we have data for this class
            if ship.ship_class in self.subsystems:
                valid_subs = self.subsystems[ship.ship_class]
                if ship.subsystems.status == 'custom':
                    for sub in ship.subsystems.list:
                        if sub.name.lower() == 'pilot': continue # Pilot is special/virtual
                        if sub.name not in valid_subs:
                            self.log_error(f"Ship '{ship.name}' (class {ship.ship_class}) references invalid subsystem '{sub.name}'")

            # 6. Hardpoints (Primary/Secondary Banks)
            if ship.ship_class in self.num_hardpoints:
                req_primary = self.num_hardpoints[ship.ship_class]['primary']
                req_secondary = self.num_hardpoints[ship.ship_class]['secondary']
                
                if len(ship.weapons.primary) != req_primary:
                    self.log_error(f"Ship '{ship.name}' ({ship.ship_class}) has {len(ship.weapons.primary)} primary banks specified, but requires {req_primary}.")
                
                if len(ship.weapons.secondary) != req_secondary:
                    self.log_error(f"Ship '{ship.name}' ({ship.ship_class}) has {len(ship.weapons.secondary)} secondary banks specified, but requires {req_secondary}.")

    def validate_wings(self):
        for wing in self.mission.wings:
            for f in wing.flags:
                norm = fs_flags_constants.normalize_flag(f)
                if norm not in fs_flags_constants.WING_FLAGS_BUCKET:
                     self.log_error(f"Wing '{wing.name}' has unknown/unsupported flag '{f}'")

            if not wing.ai_goals or not wing.ai_goals.strip():
                self.log_warning(
                    f"Wing '{wing.name}' lacks initial orders (ai_goals). "
                    f"AI-controlled ships in this wing will sit idle."
                )

    # Common Terran wing name prefixes used in player starting wings.
    _WING_NAME_PATTERN = re.compile(r'^(Alpha|Beta|Gamma|Delta|Epsilon) \d+$')

    def validate_standalone_wing_name_patterns(self):
        """
        Warn if a standalone ship (not part of any wing) has a name that looks
        like a wing member (e.g. 'Alpha 1', 'Beta 2', 'Gamma 3').

        Common Terran wing prefixes checked: Alpha, Beta, Gamma, Delta, Epsilon.

        This is almost always a mistake: the intended pattern is to define the
        wing via entities.wings, not to create individual standalone ships with
        wing-member-style names.  The warning is advisory only and does not
        abort conversion.
        """
        # Collect names of every ship that belongs to a wing (wing members are
        # expanded into mission.ships, so we must identify them explicitly).
        wing_member_names: Set[str] = set()
        for wing in self.mission.wings:
            for ship in wing.ships:
                wing_member_names.add(ship.name)

        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue  # already a proper wing member – skip
            if self._WING_NAME_PATTERN.match(ship.name):
                prefix = ship.name.rsplit(' ', 1)[0]
                self.log_warning(
                    f"Standalone ship '{ship.name}' has a wing-member-style name "
                    f"(prefix '{prefix}'). If this is meant to be part of a wing, "
                    f"define it using entities.wings instead. "
                    f"If intentional, ignore this warning."
                )

    def validate_docking(self):
        """
        Validate pre-spawn docking configurations.
        
        Checks:
        - Completeness (docker and dockee points).
        - No self-docking.
        - Reference validity (ships exist).
        - Conflict detection (ships involved in multiple pairs).
        - Player constraints (player cannot start docked).
        - Dockpoint validity for specific ship classes.
        - Arrival logic (exactly one leader with arrival_cue true).
        """
        # References, Constraints, and Logic
        
        docked_members = set()
        name_to_ship = {s.name: s for s in self.mission.ships}
        player_ships = set()
        if self.mission.player_setup.start_ship:
             player_ships.add(self.mission.player_setup.start_ship)
        for s in self.mission.ships:
             # Check flags for player-start
             for f in s.flags:
                 if fs_flags_constants.normalize_flag(f) == 'player_start':
                     player_ships.add(s.name)

        for ship in self.mission.ships:
            dw = ship.docked_with
            if not dw: continue
            
            # 1. Completeness
            if not (ship.docker_point and ship.dockee_point):
                self.log_error(f"Ship '{ship.name}' docking incomplete: requires 'docker_point' and 'dockee_point'")
                continue # Cannot validate further
            
            # 2. Self-docking
            if dw == ship.name:
                self.log_error(f"Ship '{ship.name}' cannot dock with itself")
                continue
            
            # 3. Unknown partner
            if dw not in name_to_ship:
                self.log_error(f"Ship '{ship.name}' docked with unknown ship '{dw}'")
                continue
                
            other = name_to_ship[dw]
            
            # 4. Conflicts (Already docked check)
            if ship.name in docked_members:
                self.log_error(f"Ship '{ship.name}' is involved in multiple docking definitions")
            if dw in docked_members:
                self.log_error(f"Ship '{dw}' (partner of '{ship.name}') is involved in multiple docking definitions")
                
            docked_members.add(ship.name)
            docked_members.add(dw)
            
            # 5. Player Constraint
            if ship.name in player_ships:
                self.log_error(f"Player ship '{ship.name}' cannot be pre-spawn docked")
            if dw in player_ships:
                self.log_error(f"Player ship '{dw}' cannot be pre-spawn docked")

            # 6. Valid Dockpoints
            if ship.docker_point:
                if ship.ship_class in self.dockpoints:
                    if ship.docker_point not in self.dockpoints[ship.ship_class]:
                        self.log_error(f"Ship '{ship.name}' references invalid docker_point '{ship.docker_point}' for class '{ship.ship_class}'")
            
            if ship.dockee_point:
                if other.ship_class in self.dockpoints:
                    if ship.dockee_point not in self.dockpoints[other.ship_class]:
                         self.log_error(f"Ship '{ship.name}' references invalid dockee_point '{ship.dockee_point}' for class '{other.ship_class}' (ship '{other.name}')")

            # 7. Arrival Logic (Strict)
            docker_true = ("".join(ship.arrival_cue.split()).lower() == '(true)')
            dockee_true = ("".join(other.arrival_cue.split()).lower() == '(true)')
            
            if docker_true and dockee_true:
                self.log_error(f"Docking pair '{ship.name}'/'{dw}': Both have arrival_cue '( true )'. Only the dockee (leader) should be true.")
            elif not docker_true and not dockee_true:
                self.log_error(f"Docking pair '{ship.name}'/'{dw}': Both have arrival_cue '( false )'. The dockee (leader) must be '( true )'.")
            elif docker_true and not dockee_true:
                 self.log_error(f"Docking pair '{ship.name}'/'{dw}': Docker has cue '( true )' but Dockee has '( false )'. The Dockee must be the arrival leader.")

    def validate_reinforcements(self):
        """
        Validate that reinforcement entries reference existing ships or wings.
        """
        all_ships = {s.name for s in self.mission.ships}
        all_wings = {w.name for w in self.mission.wings}
        
        for r in self.mission.reinforcements:
            if r.name not in all_ships and r.name not in all_wings:
                self.log_error(f"Reinforcement references unknown ship/wing '{r.name}'")

    def validate_messages(self):
        """
        Validate message definitions.
        
        Checks that referenced voice names exist in the TTS registry.
        """
        for msg in self.mission.messages:
            # Voice Name
            if msg.voice_name and msg.voice_name not in self.voices:
                self.log_error(f"Message '{msg.name}' uses unknown voice_name '{msg.voice_name}'")

    def _validate_span_style_tags(self, context: str, text: Optional[str]):
        """
        Validate span-style color tags ($c{ ... $}) in briefing/debriefing text.
        """
        for w in validate_span_style_tags(text):
            self.log_warning(f"{context}: {w}")

    def validate_briefing_span_tags(self):
        """
        Validate span-style color-tag balancing in supported styling contexts:
        command briefing, mission briefing and debriefing text.
        """
        for i, stage in enumerate(self.mission.command_briefing.stages, start=1):
            self._validate_span_style_tags(f"Command briefing stage {i} text", stage.text)

        for i, stage in enumerate(self.mission.briefing.stages, start=1):
            self._validate_span_style_tags(f"Briefing stage {i} text", stage.text)

        for i, stage in enumerate(self.mission.debriefing.stages, start=1):
            self._validate_span_style_tags(f"Debriefing stage {i} text", stage.text)

    def validate_briefing_text_styling_scope(self):
        """
        Warn if briefing/debriefing text styling tags are used outside supported contexts.

        Styling tags are intended only for fiction viewer, command briefing,
        mission briefing and debriefing text blocks.
        """
        guidance = (
            "Briefing text styling tags belong only to fiction viewer, "
            "command briefing, mission briefing and debriefing text."
        )

        def warn_if_has_tags(context: str, text: Optional[str]):
            tags = extract_briefing_style_tags(text)
            if tags:
                tags_joined = ", ".join(tags)
                self.log_warning(f"{context} contains briefing styling tags ({tags_joined}). {guidance}")

        # In-mission text channels where styling tags do not belong.
        for idx, msg in enumerate(self.mission.messages, start=1):
            warn_if_has_tags(
                f"mission_flow.messages[{idx}] ('{msg.name}') message",
                msg.message,
            )

        for idx, goal in enumerate(self.mission.goals, start=1):
            warn_if_has_tags(
                f"mission_flow.goals[{idx}] ('{goal.name}') message",
                goal.message,
            )

        for idx, event in enumerate(self.mission.events, start=1):
            if event.directive_text:
                event_name = event.name if event.name else f"Event {idx}"
                warn_if_has_tags(
                    f"mission_flow.events[{idx}] ('{event_name}') directive_text",
                    event.directive_text,
                )

        # Other authored text fields outside supported briefing/debriefing contexts.
        mi = self.mission.mission_info
        warn_if_has_tags("mission_info.name", mi.name)
        warn_if_has_tags("mission_info.description", mi.description)

    def _calculate_briefing_camera_width(self, icons) -> float:
        """
        Replicate the briefing camera width calculation from MissionLoader.

        Returns the camera Y-height (== camera width) that the converter would
        automatically assign to a stage containing the given icons.  This is the
        same value used as the reference distance for the icon proximity check.

        Formula (mirrors _calculate_briefing_camera in mission_loader.py):
          final_width = max(delta_x, 2.5 * delta_z)
          cam_width   = max(final_width * 1.15, 1000.0)

        Args:
            icons: Iterable of BriefingIcon objects (must have .pos as [x, 0, z]).

        Returns:
            float: The computed camera width (minimum 1000.0).
        """
        x_values = [ic.pos[0] for ic in icons]
        z_values = [ic.pos[2] for ic in icons]

        delta_x = max(x_values) - min(x_values)
        delta_z = max(z_values) - min(z_values)

        return calculate_briefing_camera_height(delta_x, delta_z)

    def validate_briefing(self):
        """
        Validate briefing stages and icons.
        
        Checks:
        - Voice name validity.
        - Icon absence, types, teams, and classes.
        - Icon proximity (warns if any two icons are closer than 5% of the
          automatically calculated camera width, which would cause visual overlap).
        """

        for i, stage in enumerate(self.mission.briefing.stages):
            # Validate voice name
            if stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Briefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

            # Check for the absence of icons
            if not stage.icons:
                self.log_warning(f"Briefing stage {i+1} has no icons defined.")

            # Validate icon properties
            if stage.icons:
                for icon in stage.icons:
                    if icon.type not in self.allowed_icons:
                        self.log_error(f"Briefing icon has invalid type '{icon.type}'")
                    
                    # Team check
                    if icon.team and icon.team not in self.allowed_teams:
                        self.log_error(f"Briefing icon has invalid team '{icon.team}'")
                        
                    # Class check
                    if icon.ship_class and icon.ship_class not in self.ship_classes:
                        self.log_error(f"Briefing icon class '{icon.ship_class}' is not a valid ship class.")

                    # Non-ship icon class check
                    if icon.type in self.non_ship_icon_types:
                        # Default is "Terran NavBuoy". If it's anything else, it's an error.
                        if icon.ship_class != "Terran NavBuoy":
                            self.log_error(f"Briefing icon of type '{icon.type}' uses class '{icon.ship_class}'. Non-ship icons must use the safe default class 'Terran NavBuoy' (or omit the class field).")

            # Icon proximity check: warn if any two icons are closer than 5% of the camera width.
            # Camera width calcutated here mirrors the calculation in MissionLoader._calculate_briefing_camera.
            if stage.icons and len(stage.icons) >= 2:
                cam_width = self._calculate_briefing_camera_width(stage.icons)
                threshold = 0.05 * cam_width

                def _icon_label(ic) -> str:
                    """Return a human-readable identifier for an icon."""
                    if ic.label:
                        return f"'{ic.label}' ({ic.type})"
                    return f"(type '{ic.type}')"

                icons_list = stage.icons
                for a_idx in range(len(icons_list)):
                    for b_idx in range(a_idx + 1, len(icons_list)):
                        ic_a = icons_list[a_idx]
                        ic_b = icons_list[b_idx]
                        dx = ic_a.pos[0] - ic_b.pos[0]
                        dz = ic_a.pos[2] - ic_b.pos[2]
                        dist = math.sqrt(dx * dx + dz * dz)
                        if dist < threshold:
                            self.log_warning(
                                f"Briefing stage {i+1}: icons {_icon_label(ic_a)} and "
                                f"{_icon_label(ic_b)} are too close together "
                                f"(distance {dist:.1f}, minimum {threshold:.1f} = 5% of "
                                f"camera width {cam_width:.1f}). "
                                f"Consider spreading them further apart to prevent visual overlap."
                            )

    def validate_debriefing(self):
        for i, stage in enumerate(self.mission.debriefing.stages):
            # Validate SEXP condition
            if stage.condition:
                self._check_sexp_string(f"Debriefing stage {i+1} condition", stage.condition)

                # Warn if condition is a bare '( true )' — always-true conditions are
                # insufficiently restrictive and may cause incorrect text to be shown
                normalized_cue = "".join(stage.condition.split()).lower()
                if normalized_cue == '(true)':
                    self.log_warning(
                        f"Debriefing stage {i+1} uses '( true )' as its condition. "
                        f"This condition is always true and will cause the stage to display "
                        f"regardless of the mission outcome (e.g., a success message will also "
                        f"appear after a failure). "
                        f"Use a specific SEXP (e.g., '( is-event-true-delay \"...\" 0 )') to "
                        f"precisely target the intended outcome."
                    )

            # Validate Voice
            if stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Debriefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

    def validate_command_briefing(self):
        for i, stage in enumerate(self.mission.command_briefing.stages):
            if stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Command Briefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

    def validate_anchors(self):
        """
        Validate arrival/departure anchors for ships and wings.
        
        Checks:
        - Anchor exists (Ship, Wing, or Special Token).
        - If using Docking Bay arrival/departure, ensures anchor has a fighterbay.
        """
        # Collect all valid anchor targets
        name_to_ship = {s.name: s for s in self.mission.ships}
        valid_targets = set(name_to_ship.keys()) | {w.name for w in self.mission.wings} | self.allowed_anchors_tokens
        
        directional_locations = {
            "near ship", "in front of ship", "in back of ship",
            "above ship", "below ship", "to left of ship", "to right of ship"
        }

        # Check Ships
        for ship in self.mission.ships:
            arr_loc = ship.arrival_location.strip().lower()
            if arr_loc == "docking bay":
                if not ship.arrival_anchor:
                    self.log_error(f"Ship '{ship.name}' uses Docking Bay arrival but is missing 'arrival_anchor'.")
            elif arr_loc in directional_locations:
                if not ship.arrival_anchor:
                    self.log_error(f"Ship '{ship.name}' uses directional arrival '{ship.arrival_location}' but is missing 'arrival_anchor'.")
                if getattr(ship, 'arrival_distance', None) is None:
                    self.log_error(f"Ship '{ship.name}' uses directional arrival '{ship.arrival_location}' but is missing 'arrival_distance'.")

            if ship.arrival_anchor and ship.arrival_anchor not in valid_targets:
                self.log_error(f"Ship '{ship.name}' references unknown arrival_anchor '{ship.arrival_anchor}'")
            
            # Fighterbay check for Docking Bay arrival
            if arr_loc == "docking bay" and ship.arrival_anchor:
                if ship.arrival_anchor in name_to_ship:
                    anchor_ship = name_to_ship[ship.arrival_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Ship '{ship.name}' uses Docking Bay arrival from anchor '{ship.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

            dep_loc = ship.departure_location.strip().lower()
            if dep_loc == "docking bay":
                if not ship.departure_anchor:
                    self.log_error(f"Ship '{ship.name}' uses Docking Bay departure but is missing 'departure_anchor'.")

            if ship.departure_anchor and ship.departure_anchor not in valid_targets:
                self.log_error(f"Ship '{ship.name}' references unknown departure_anchor '{ship.departure_anchor}'")

            # Fighterbay check for Docking Bay departure
            if dep_loc == "docking bay" and ship.departure_anchor:
                if ship.departure_anchor in name_to_ship:
                    anchor_ship = name_to_ship[ship.departure_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Ship '{ship.name}' uses Docking Bay departure via anchor '{ship.departure_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

        # Check Wings
        for w in self.mission.wings:
            arr_loc = w.arrival_location.strip().lower()
            if arr_loc == "docking bay":
                if not w.arrival_anchor:
                    self.log_error(f"Wing '{w.name}' uses Docking Bay arrival but is missing 'arrival_anchor'.")
            elif arr_loc in directional_locations:
                if not w.arrival_anchor:
                    self.log_error(f"Wing '{w.name}' uses directional arrival '{w.arrival_location}' but is missing 'arrival_anchor'.")
                if getattr(w, 'arrival_distance', None) is None:
                    self.log_error(f"Wing '{w.name}' uses directional arrival '{w.arrival_location}' but is missing 'arrival_distance'.")

            if w.arrival_anchor and w.arrival_anchor not in valid_targets:
                self.log_error(f"Wing '{w.name}' references unknown arrival_anchor '{w.arrival_anchor}'")
            
            # Fighterbay check for Docking Bay arrival
            if arr_loc == "docking bay" and w.arrival_anchor:
                if w.arrival_anchor in name_to_ship:
                    anchor_ship = name_to_ship[w.arrival_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Wing '{w.name}' uses Docking Bay arrival from anchor '{w.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

            dep_loc = w.departure_location.strip().lower()
            if dep_loc == "docking bay":
                if not w.departure_anchor:
                    self.log_error(f"Wing '{w.name}' uses Docking Bay departure but is missing 'departure_anchor'.")

            if w.departure_anchor and w.departure_anchor not in valid_targets:
                self.log_error(f"Wing '{w.name}' references unknown departure_anchor '{w.departure_anchor}'")

            # Fighterbay check for Docking Bay departure
            if dep_loc == "docking bay" and w.departure_anchor:
                if w.departure_anchor in name_to_ship:
                    anchor_ship = name_to_ship[w.departure_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Wing '{w.name}' uses Docking Bay departure via anchor '{w.departure_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

    def validate_asteroid_targets(self):
        af = self.mission.environment.asteroid_field
        if not af or not af.targets:
            return
            
        valid_ships = {s.name for s in self.mission.ships}
        for t in af.targets:
            if t not in valid_ships:
                self.log_error(f"Asteroid field target '{t}' does not exist.")

    def validate_player_setup(self):
        """
        Validate player setup configuration.
        
        Checks:
        - Validity of extra weapons provided.
        - Validity of ship choices provided.
        """
        setup = self.mission.player_setup
        for w_name in setup.extra_weapons:
            if w_name not in self.allowed_weapons:
                self.log_error(f"Player setup 'extra_weapons' references unknown weapon '{w_name}'")
                
        for choice in setup.extra_ships:
            if choice.ship_class not in self.ship_classes:
                self.log_error(f"Player setup 'extra_ships' references unknown ship class '{choice.ship_class}'")

    def validate_start_ship(self):
        """
        Validate the player start ship configuration.
        
        Ensures:
        - Start ship exists.
        - If standalone, it has arrival_cue '( true )'.
        """
        start_name = self.mission.player_setup.start_ship
        if not start_name:
            self.log_error("player_setup.start_ship is undefined.")
            return
        
        # Check if ship exists
        ship = next((s for s in self.mission.ships if s.name == start_name), None)
        if not ship:
            self.log_error(f"Player start ship '{start_name}' not found in entities.")
            return
            
        # Check if standalone (not part of a wing)
        in_wing = False
        for w in self.mission.wings:
            if any(s.name == start_name for s in w.ships):
                in_wing = True
                break
        
        if not in_wing:
            # Standalone must have arrival_cue true
            cue = "".join(ship.arrival_cue.split()).lower()
            if cue != '(true)':
                self.log_error(f"Player start ship '{start_name}' (standalone) must have arrival_cue '( true )'.")

    def validate_audio(self):
        """
        Validate mission music selections against allowed tracks.
        """
        audio = self.mission.audio
        if audio.mission_music and audio.mission_music not in self.allowed_music_mission:
            self.log_error(f"Invalid mission_music '{audio.mission_music}'")
        if audio.briefing_music and audio.briefing_music not in self.allowed_music_briefing:
            self.log_error(f"Invalid briefing_music '{audio.briefing_music}'")

    def validate_sexps(self):
        """
        Perform structural validation of all SEXP formulas in the mission.
        
        Checks:
        - Events, Goals, Arrival/Departure cues, AI Goals.
        - Parenthesis balance.
        - YAML comment leakage.
        - Token length limits.
        - Basic operator validity.
        
        Note: The basic validation only checks the validity of the outermost operator.
        Nested operators inside compound SEXPs are not checked here. Deep semantic
        validation of operator validity at depth is delegated to the Advanced SEXP Validator.
        """
        # Gather all SEXP strings with context
        sexps = []
        
        # Events
        for e in self.mission.events:
            if e.formula: sexps.append((f"Event '{e.name}' formula", e.formula))
            
        # Goals
        for g in self.mission.goals:
            if g.formula: sexps.append((f"Goal '{g.name}' formula", g.formula))
            
        # Ships/Wings cues and ai_goals
        for s in self.mission.ships:
            if s.arrival_cue: sexps.append((f"Ship '{s.name}' arrival_cue", s.arrival_cue))
            if s.departure_cue: sexps.append((f"Ship '{s.name}' departure_cue", s.departure_cue))
            if s.ai_goals: sexps.append((f"Ship '{s.name}' ai_goals", s.ai_goals))
            
        for w in self.mission.wings:
            if w.arrival_cue: sexps.append((f"Wing '{w.name}' arrival_cue", w.arrival_cue))
            if w.departure_cue: sexps.append((f"Wing '{w.name}' departure_cue", w.departure_cue))
            if w.ai_goals: sexps.append((f"Wing '{w.name}' ai_goals", w.ai_goals))
            
        for ctx, sexp in sexps:
            self._check_sexp_string(ctx, sexp)

    def _check_sexp_string(self, context, sexp):
        """
        Helper method to perform basic structural checks on a single SEXP string.
        """
        if not sexp: return
        
        # 1. Parens
        open_p = sexp.count('(')
        close_p = sexp.count(')')
        if open_p != close_p:
            self.log_error(f"SEXP error: {context}: Mismatched parentheses (Open: {open_p}, Close: {close_p})")
            
        # Regex to strip string literals, respecting escaped quotes/backslashes
        clean = re.sub(r'"(\\.|[^"\\])*"', '""', sexp)

        # 2. YAML Comments (# space)
        if re.search(r'#\s', clean):
             self.log_error(f"SEXP error: {context}: Likely YAML comment leakage ('# ' found).")
             
        # 3. Token Length & Operator Validity
        # Parse first token (Outermost Operator)
        match = re.search(r'\(\s*([^\s)]+)', clean)
        if match:
             operator = match.group(1)
             if self.allowed_sexp_operators and operator not in self.allowed_sexp_operators:
                  try:
                      float(operator)
                  except ValueError:
                      if operator not in ('true', 'false'):
                           self.log_error(f"SEXP error: {context}: Unknown operator '{operator}'.")

        # Split by delimiters (parens, whitespace) for length check
        tokens = re.split(r'[\s()]+', clean)
        for t in tokens:
            if not t: continue
            if len(t) >= 30:
                self.log_error(f"SEXP error: {context}: Token '{t[:15]}...' length {len(t)} exceeds limit (<30).")

    def validate_goals_and_directives(self):
        """
        Warn if the number of events with directive_text is less than the number of goals.
        """
        num_goals = len(self.mission.goals)
        if num_goals == 0:
            return

        num_directives = sum(1 for event in self.mission.events if event.directive_text)

        if num_directives < num_goals:
            self.log_warning(
                f"Mission has {num_goals} goal(s) but only {num_directives} event(s) with a directive_text. "
                f"It is highly recommended that every important mission goal has a corresponding "
                f"event with a directive_text so that the objective is visible on the player's HUD."
            )

    def validate_directive_text_sexp_compatibility(self):
        """
        Warn if events with directive_text use is-event-true-delay, is-event-false-delay,
        or similar event/goal-referencing SEXPs in their formula.

        The FSO engine cannot initially evaluate the possibility of an event becoming
        true/false when its formula references other events or goals via these operators.
        As a result, the grey 'pending' directive is never displayed on the HUD.

        Events with directive_text should use simple, directly-evaluable conditions
        (e.g., is-destroyed-delay, has-arrived-delay, percent-ships-destroyed).
        """
        DIRECTIVE_INCOMPATIBLE_SEXPS = [
            "is-event-true-delay",
            "is-event-false-delay",
            "is-event-true-msecs-delay",
            "is-event-false-msecs-delay",
            "is-goal-true-delay",
            "is-goal-false-delay",
        ]

        for i, event in enumerate(self.mission.events):
            if not event.directive_text or not event.formula:
                continue

            # Strip quoted string literals to avoid false positives from event/goal
            # name arguments that happen to contain an operator name as a substring.
            formula_clean = re.sub(r'"(\\.|[^"\\])*"', '""', event.formula)

            found_ops = [op for op in DIRECTIVE_INCOMPATIBLE_SEXPS if op in formula_clean]

            if found_ops:
                event_name = event.name if event.name else f"(unnamed, index {i})"
                ops_str = ", ".join(f"'{op}'" for op in found_ops)
                self.log_warning(
                    f"Event '{event_name}' has a directive_text but its formula uses "
                    f"{ops_str}. Directive text does not work correctly when the formula "
                    f"references other events or goals via these SEXPs: the engine cannot "
                    f"initially determine whether the event could become true or false, so "
                    f"the grey directive will never be displayed on the HUD. "
                    f"Use simpler, directly-evaluable conditions (e.g., is-destroyed-delay, "
                    f"has-arrived-delay, percent-ships-destroyed) in events with directive_text."
                )
