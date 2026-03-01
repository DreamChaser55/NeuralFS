import re
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
        self.validate_mission_info()
        self.validate_environment()
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
        self.validate_sexps()
        self.validate_audio()

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

    def validate_briefing(self):
        """
        Validate briefing stages and icons.
        
        Checks:
        - Voice name validity.
        - Icon absence, types, teams, and classes.
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

    def validate_debriefing(self):
        for i, stage in enumerate(self.mission.debriefing.stages):
            # Validate SEXP condition
            if stage.condition:
                self._check_sexp_string(f"Debriefing stage {i+1} condition", stage.condition)
            
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
                
        for choice in setup.ship_choices:
            if choice.ship_class not in self.ship_classes:
                self.log_error(f"Player setup 'ship_choices' references unknown ship class '{choice.ship_class}'")

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
