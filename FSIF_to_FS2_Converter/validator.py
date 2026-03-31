import re
import math
from pathlib import Path
from typing import Set, Dict, List, Optional
import fs_flags_constants
import fs_data
from data_models import Mission
import briefing_icon_types
from validate_sexp_scalar_styles import validate_sexp_styles

try:
    from weapons_compatibility_data import WEAPON_COMPATIBILITY
except ImportError:
    WEAPON_COMPATIBILITY = {}


class Validator:
    _MISSION_SCALE_RECOMMENDATION_METERS = 20_000.0
    _BRIEFING_SPAN_OPEN_TAG_RE = re.compile(r'^\$([WwKkBbGgYyEeVvRrPpOoFfHhNn])\{$')
    _BRIEFING_STYLE_TAG_RE = re.compile(
        r"""
        \$[WwKkBbGgYyEeVvRrPpOoFfHhNn]\{ |      # span color open, e.g. $y{
        \$[WwKkBbGgYyEeVvRrPpOoFfHhNn](?=(?:\s|$)) | # single-word color, e.g. $R text
        \$\| |                                   # color break
        \$\} |                                   # span color close
        \$(?:quote|semicolon|callsign|rank)\b    # special placeholders
        """,
        re.VERBOSE,
    )

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
        - authored-but-not-emitted helper fields such as asteroid_field.name
        """
        self._validate_ascii_text('mission_flow.fiction_viewer', self.mission.fiction_viewer)

        info = self.mission.mission_info
        self._validate_xstr_text('mission_info.name', info.name)
        self._validate_ascii_text('mission_info.author', info.author)
        self._validate_ascii_text('mission_info.notes', info.notes)
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
            self._validate_xstr_text(f'{prefix}.cargo_1', ship.cargo_1)
            self._validate_ascii_text(f'{prefix}.arrival_location', ship.arrival_location)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', ship.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', ship.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_location', ship.departure_location)
            self._validate_ascii_text(f'{prefix}.departure_anchor', ship.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', ship.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', ship.flags)
            self._validate_ascii_text_list(f'{prefix}.flags2', ship.flags2)
            self._validate_ascii_text(f'{prefix}.ai_goals', ship.ai_goals)
            self._validate_ascii_text(f'{prefix}.docked_with', ship.docked_with)
            self._validate_ascii_text(f'{prefix}.docker_point', ship.docker_point)
            self._validate_ascii_text(f'{prefix}.dockee_point', ship.dockee_point)
            self._validate_ascii_text_list(f'{prefix}.orders_accepted', ship.orders_accepted)
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
            self._validate_ascii_text(f'{prefix}.voice_filename', message.voice_filename)

        for i, stage in enumerate(self.mission.command_briefing.stages):
            prefix = f'command_briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.ani', stage.ani)
            self._validate_ascii_text(f'{prefix}.voice_filename', stage.voice_filename)

        for i, stage in enumerate(self.mission.briefing.stages):
            prefix = f'briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.voice_filename', stage.voice_filename)
            for j, icon in enumerate(stage.icons):
                icon_prefix = f'{prefix}.icons[{j}]'
                self._validate_ascii_text(f'{icon_prefix}.type', icon.type)
                self._validate_ascii_text(f'{icon_prefix}.team', icon.team)
                self._validate_ascii_text(f'{icon_prefix}.class', icon.class_)
                self._validate_xstr_text(f'{icon_prefix}.label', icon.label)

        for i, stage in enumerate(self.mission.debriefing.stages):
            prefix = f'debriefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.condition', stage.condition)
            self._validate_ascii_text(f'{prefix}.voice_filename', stage.voice_filename)
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
        print("[INFO] [Validator] Starting validation...")
        
        self.validate_global_names()
        self.validate_ascii_text_fields()
        self.validate_mission_info()
        self.validate_environment()
        self.validate_mission_scale_recommendations()
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
            print(f"\n[WARNING] [Validator] Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")
                
        if self.errors:
            print(f"\n[ERROR] [Validator] Errors ({len(self.errors)}):")
            for e in self.errors:
                print(f"  - {e}")
            print("\n[FAILED] [Validator] Validation FAILED.")
            return False
            
        print("[SUCCESS] [Validator] Validation PASSED.")
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
            # Targets are only valid for Active (0) Asteroid (0) fields
            if not (af.field_type == 0 and af.debris_genre == 0):
                self.log_warning(f"Asteroid field '{af.name}' defines targets but they will be ignored (type={af.field_type}, genre={af.debris_genre}). Targets are only supported for Active Asteroid fields.")

    def validate_mission_scale_recommendations(self):
        """
        Warn when authored mission geometry exceeds the recommended 20 km scale.

        This is an advisory mission-design check only. It does not fail validation.
        It covers:
        - distances between positioned mission objects (standalone ships, wing centroids, jump nodes, waypoint points)
        - authored arrival_distance values on ships and wings that reference an arrival_anchor
        """
        limit_m = self._MISSION_SCALE_RECOMMENDATION_METERS
        limit_km = limit_m / 1000.0

        positioned_objects = []
        distance_violations = []

        wing_member_names: Set[str] = set()
        for wing in self.mission.wings:
            for ship in wing.ships:
                wing_member_names.add(ship.name)

        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue
            positioned_objects.append(("Ship", ship.name, ship.location))

        for wing in self.mission.wings:
            wing_position = wing.position
            if wing_position is None and wing.ships:
                # Defensive fallback: use the leader position if the authored wing centroid is unexpectedly unavailable.
                wing_position = wing.ships[0].location

            if wing_position is not None:
                positioned_objects.append(("Wing", wing.name, wing_position))

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
            all_flags = ship.flags + ship.flags2
            for f in all_flags:
                norm = fs_flags_constants.normalize_flag(f)
                if norm not in fs_flags_constants.SHIP_FLAGS_BUCKET:
                    self.log_error(f"Ship '{ship.name}' has unknown flag '{f}'")

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

    def _extract_briefing_style_tags(self, text: Optional[str]) -> List[str]:
        if not text:
            return []
        matches = {m.group(0) for m in self._BRIEFING_STYLE_TAG_RE.finditer(text)}
        return sorted(matches)

    def _validate_span_style_tags(self, context: str, text: Optional[str]):
        """
        Validate span-style color tags ($c{ ... $}) in briefing/debriefing text.

        Rule enforced:
        - Every span opening tag must be closed with '$}' before either:
          1) another, different style tag, or
          2) end-of-text.
        """
        if not text:
            return

        tokens = list(self._BRIEFING_STYLE_TAG_RE.finditer(text))

        for idx, tok in enumerate(tokens):
            opening_tag = tok.group(0)
            if not self._BRIEFING_SPAN_OPEN_TAG_RE.match(opening_tag):
                continue

            closed = False
            warned = False

            for next_tok in tokens[idx + 1:]:
                next_tag = next_tok.group(0)

                if next_tag == '$}':
                    closed = True
                    break

                # Placeholders ($callsign, $rank, $quote, $semicolon) are
                # text substitutions, not style tags. They do not open or
                # close a span, so skip them and keep looking for $}.
                if re.match(r'^\$(?:quote|semicolon|callsign|rank)\b', next_tag):
                    continue

                # Any other tag means the current span is unclosed before this tag. FSO does not support
                # nested span tags of any kind.
                self.log_warning(
                    f"{context}: span-style color tag '{opening_tag}' is unclosed before "
                    f"'{next_tag}'. Add '$}}' before '{next_tag}' (or remove '{opening_tag}')."
                )
                warned = True
                break

            if not closed and not warned:
                self.log_warning(
                    f"{context}: span-style color tag '{opening_tag}' is unclosed before end of text. "
                    f"Add '$}}' to close the span."
                )

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
            tags = self._extract_briefing_style_tags(text)
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
        warn_if_has_tags("mission_info.notes", mi.notes)

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

        final_width = max(delta_x, 2.5 * delta_z)
        cam_width = final_width * 1.15
        if cam_width < 1000.0:
            cam_width = 1000.0
        return cam_width

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
                    if icon.class_ and icon.class_ not in self.ship_classes:
                        self.log_error(f"Briefing icon class '{icon.class_}' is not a valid ship class.")

                    # Non-ship icon class check
                    if icon.type in self.non_ship_icon_types:
                        # Default is "Terran NavBuoy". If it's anything else, it's an error.
                        if icon.class_ != "Terran NavBuoy":
                            self.log_error(f"Briefing icon of type '{icon.type}' uses class '{icon.class_}'. Non-ship icons must use the safe default class 'Terran NavBuoy' (or omit the class field).")

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
        
        # Check Ships
        for ship in self.mission.ships:
            if ship.arrival_anchor and ship.arrival_anchor not in valid_targets:
                self.log_error(f"Ship '{ship.name}' references unknown arrival_anchor '{ship.arrival_anchor}'")
            
            # Fighterbay check for Docking Bay arrival
            if ship.arrival_location.strip().lower() == "docking bay" and ship.arrival_anchor:
                if ship.arrival_anchor in name_to_ship:
                    anchor_ship = name_to_ship[ship.arrival_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Ship '{ship.name}' uses Docking Bay arrival from anchor '{ship.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

            if ship.departure_anchor and ship.departure_anchor not in valid_targets:
                self.log_error(f"Ship '{ship.name}' references unknown departure_anchor '{ship.departure_anchor}'")

            # Fighterbay check for Docking Bay departure
            if ship.departure_location.strip().lower() == "docking bay" and ship.departure_anchor:
                if ship.departure_anchor in name_to_ship:
                    anchor_ship = name_to_ship[ship.departure_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Ship '{ship.name}' uses Docking Bay departure via anchor '{ship.departure_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

        # Check Wings
        for w in self.mission.wings:
            if w.arrival_anchor and w.arrival_anchor not in valid_targets:
                self.log_error(f"Wing '{w.name}' references unknown arrival_anchor '{w.arrival_anchor}'")
            
            # Fighterbay check for Docking Bay arrival
            if w.arrival_location.strip().lower() == "docking bay" and w.arrival_anchor:
                if w.arrival_anchor in name_to_ship:
                    anchor_ship = name_to_ship[w.arrival_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Wing '{w.name}' uses Docking Bay arrival from anchor '{w.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

            if w.departure_anchor and w.departure_anchor not in valid_targets:
                self.log_error(f"Wing '{w.name}' references unknown departure_anchor '{w.departure_anchor}'")

            # Fighterbay check for Docking Bay departure
            if w.departure_location.strip().lower() == "docking bay" and w.departure_anchor:
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
            
        # 2. YAML Comments (# space)
        if re.search(r'#\s', sexp):
             self.log_error(f"SEXP error: {context}: Likely YAML comment leakage ('# ' found).")
             
        # 3. Token Length & Operator Validity
        # Regex to strip string literals, respecting escaped quotes/backslashes
        clean = re.sub(r'"(\\.|[^"\\])*"', '""', sexp)
        
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
