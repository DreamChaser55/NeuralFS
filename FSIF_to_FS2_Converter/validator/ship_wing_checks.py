import re
from typing import Set
import fs_flags_constants
import fs_data
try:
    from weapons_compatibility_data import WEAPON_COMPATIBILITY
except ImportError:
    WEAPON_COMPATIBILITY = {}

class ShipWingChecksMixin:
    _WING_NAME_PATTERN = re.compile(r'^(' + '|'.join(sorted(fs_data.PLAYER_WING_NAMES)) + r') \d+$')

    def _ship_has_fighterbay(self, ship_class: str) -> bool:
        """Check if a ship class has a fighterbay subsystem."""
        if ship_class not in self.subsystems:
            return False  # Unknown class, can't verify
        
        for subsys_name in self.subsystems[ship_class]:
            if "fighterbay" in subsys_name.lower():
                return True
        return False

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
            if wing.count > 6:
                self.log_error(f"Wing '{wing.name}' has count {wing.count}. FSO enforces a hard maximum of 6 ships per wing.")

            for f in wing.flags:
                norm = fs_flags_constants.normalize_flag(f)
                if norm not in fs_flags_constants.WING_FLAGS_BUCKET:
                     self.log_error(f"Wing '{wing.name}' has unknown/unsupported flag '{f}'")

            if not wing.ai_goals or not wing.ai_goals.strip():
                self.log_warning(
                    f"Wing '{wing.name}' lacks initial orders (ai_goals). "
                    f"AI-controlled ships in this wing will sit idle."
                )

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