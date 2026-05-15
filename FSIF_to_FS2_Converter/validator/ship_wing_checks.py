import re
from typing import Set
import fs_flags_constants
from common import fs_data
try:
    from weapons_compatibility_data import WEAPON_COMPATIBILITY
except ImportError:
    WEAPON_COMPATIBILITY = {}

# Ship classes that are small utility objects and should NOT trigger the
# "no large ship has escort" warning.  These are cargo containers, nav buoys,
# sentry guns, and training drones — objects that the player has
# no gameplay reason to track on the HUD escort list.
_SMALL_UTILITY_CLASSES: frozenset = frozenset({
    # Navigation buoys
    'Terran NavBuoy',
    # Sentry guns
    'GTSG Watchdog', 'GTSG Cerberus', 'PVSG Ankh', 'SSG Trident',
    # Cargo containers
    'TC 2', 'TSC 2', 'TAC 1', 'TTC 1', 'VC 3', 'VAC 4', 'SC 5', 'SAC 2',
    # Training drones
    'GTDr Amazon', 'GTDr Amazon Advanced',
})

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

    def validate_fs1_shield_weapon_canon(self):
        """
        Check for FS1 timeline canon inconsistency:
        Friendly shielded fighters/bombers should not exist if the only
        available primary weapons are basic ones (ML-16 Laser, Disruptor).
        Shields were issued after the Avenger.
        """
        friendly_fighter_bombers = [
            s for s in self.mission.ships 
            if s.team == 'Friendly' and s.ship_class in self.num_hardpoints
        ] # num_hardpoints (fs_data.NUM_OF_HARDPOINTS) contains exactly the set of all fighters and bombers

        
        if not friendly_fighter_bombers:
            return
            
        has_shields = False
        for s in friendly_fighter_bombers:
            if 'no-shields' not in s.flags:
                has_shields = True
                break
                
        if not has_shields:
            return
            
        # Gather all primary weapons used by friendly fighters/bombers
        primaries_used = set()
        for s in friendly_fighter_bombers:
            for w in s.weapons.primary:
                if w:
                    primaries_used.add(w)
                    
        # Add extra weapons that are primary weapons
        for w in self.mission.player_setup.additional_weapons:
            if w in self.allowed_primary_weapons:
                primaries_used.add(w)
                
        if not primaries_used:
            return
            
        if primaries_used.issubset({'ML-16 Laser', 'Disruptor'}):
            self.log_warning(
                "Canon inconsistency: Friendly fighters/bombers have shields but are only equipped with basic primary weapons (ML-16 Laser, Disruptor). "
                "In FS1 canon, shields were issued **after** the Avenger cannon. "
                "Depending on the timeline, consider adding the 'Avenger' to the loadout or adding the 'no-shields' flag to all friendly fighters/bombers."
            )

    def _player_starting_wing_ship_names(self) -> Set[str]:
        """
        Return the set of ship names that belong to Friendly player starting wings.

        Player starting wings are the wings whose names are in
        ``fs_data.PLAYER_WING_NAMES`` (Alpha, Beta, Gamma, Delta, Epsilon) and
        whose first ship has team "Friendly".  These are the only ships for
        which weapon-compatibility must be checked.
        """
        names: Set[str] = set()
        for wing in self.mission.wings:
            if wing.name not in fs_data.PLAYER_WING_NAMES:
                continue
            if not wing.ships:
                continue
            if wing.ships[0].team != 'Friendly':
                continue
            for ship in wing.ships:
                names.add(ship.name)
        return names

    def validate_ships(self):
        """
        Validate ship properties.
        
        Checks:
        - Validity of ship class and team.
        - Known flags and AI class.
        - Weapon compatibility for Friendly player starting wing ships only
          (Alpha, Beta, Gamma, Delta, Epsilon).
        - Subsystem validity (if data available).
        - FS1 shield/weapon canon timeline consistency.
        """
        self.validate_fs1_shield_weapon_canon()

        # Collect names of ships that belong to Friendly player starting wings.
        player_starting_ship_names = self._player_starting_wing_ship_names()
        
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
                if f not in fs_flags_constants.SHIP_FLAGS_BUCKET:
                    self.log_error(f"Ship '{ship.name}' has unknown flag '{f}'")

            # escort_list_priority requires the 'escort' flag
            if ship.escort_list_priority > 0:
                has_escort_flag = 'escort' in ship.flags
                if not has_escort_flag:
                    self.log_error(
                        f"Ship '{ship.name}' has escort_list_priority {ship.escort_list_priority} set, "
                        f"but is missing the 'escort' flag. "
                        f"Add 'escort' to the ship's flags list."
                    )

            # AI Class
            if ship.ai_class and ship.ai_class not in self.allowed_ai_classes:
                self.log_error(f"Ship '{ship.name}' has invalid ai_class '{ship.ai_class}'")

            # Hull Range
            if not (0 <= ship.initial_hull_percent <= 100):
                self.log_error(f"Ship '{ship.name}' initial_hull_percent {ship.initial_hull_percent} out of range [0, 100]")

            # 4. Weapon Compatibility
            # Only validate class-level compatibility for ships in Friendly player
            # starting wings (Alpha, Beta, Gamma, Delta, Epsilon).  FSO only
            # enforces compatible weapons in the context of the player loadout
            # screen; incompatible weapons on NPC/non-starting ships are harmless.
            if ship.ship_class in WEAPON_COMPATIBILITY:
                allowed = WEAPON_COMPATIBILITY[ship.ship_class]
                is_player_starting_ship = ship.name in player_starting_ship_names

                if is_player_starting_ship:
                    # Hard error: incompatible weapon in a player-accessible loadout.
                    for w_name in ship.weapons.primary:
                        if w_name and w_name not in allowed['primary']:
                            self.log_error(f"Ship '{ship.name}' (class {ship.ship_class}) has incompatible primary weapon '{w_name}'. Allowed: {sorted(list(allowed['primary']))}")

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
                if f not in fs_flags_constants.WING_FLAGS_BUCKET:
                     self.log_error(f"Wing '{wing.name}' has unknown/unsupported flag '{f}'")

            if not wing.initial_orders or not wing.initial_orders.strip():
                self.log_warning(
                    f"Wing '{wing.name}' lacks initial_orders. "
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
                 if f == 'player-start':
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
                 self.log_error(f"Docking pair '{ship.name}'/'{dw}': Docker has arrival_cue '( true )' but Dockee has '( false )'. The Dockee must be the arrival leader.")

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
            arr_loc = ship.arrival_method.strip().lower()
            if arr_loc == "docking bay":
                if not ship.arrival_anchor:
                    self.log_error(f"Ship '{ship.name}' uses Docking Bay arrival but is missing 'arrival_anchor'.")
            elif arr_loc in directional_locations:
                if not ship.arrival_anchor:
                    self.log_error(f"Ship '{ship.name}' uses directional arrival_method '{ship.arrival_method}' but is missing 'arrival_anchor'.")
                if getattr(ship, 'arrival_distance', None) is None:
                    self.log_error(f"Ship '{ship.name}' uses directional arrival_method '{ship.arrival_method}' but is missing 'arrival_distance'.")

            if ship.arrival_anchor and ship.arrival_anchor not in valid_targets:
                self.log_error(f"Ship '{ship.name}' references unknown arrival_anchor '{ship.arrival_anchor}'")
            
            # Fighterbay check for Docking Bay arrival
            if arr_loc == "docking bay" and ship.arrival_anchor:
                if ship.arrival_anchor not in name_to_ship:
                    self.log_error(f"Ship '{ship.name}' uses Docking Bay arrival but anchor '{ship.arrival_anchor}' is not a valid ship.")
                else:
                    anchor_ship = name_to_ship[ship.arrival_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Ship '{ship.name}' uses Docking Bay arrival from anchor '{ship.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

            dep_loc = ship.departure_method.strip().lower()
            if dep_loc == "docking bay":
                if not ship.departure_anchor:
                    self.log_error(f"Ship '{ship.name}' uses Docking Bay departure but is missing 'departure_anchor'.")

            if ship.departure_anchor and ship.departure_anchor not in valid_targets:
                self.log_error(f"Ship '{ship.name}' references unknown departure_anchor '{ship.departure_anchor}'")

            # Fighterbay check for Docking Bay departure
            if dep_loc == "docking bay" and ship.departure_anchor:
                if ship.departure_anchor not in name_to_ship:
                    self.log_error(f"Ship '{ship.name}' uses Docking Bay departure but anchor '{ship.departure_anchor}' is not a valid ship.")
                else:
                    anchor_ship = name_to_ship[ship.departure_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Ship '{ship.name}' uses Docking Bay departure via anchor '{ship.departure_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

        # Check Wings
        for w in self.mission.wings:
            arr_loc = w.arrival_method.strip().lower()
            if arr_loc == "docking bay":
                if not w.arrival_anchor:
                    self.log_error(f"Wing '{w.name}' uses Docking Bay arrival but is missing 'arrival_anchor'.")
            elif arr_loc in directional_locations:
                if not w.arrival_anchor:
                    self.log_error(f"Wing '{w.name}' uses directional arrival_method '{w.arrival_method}' but is missing 'arrival_anchor'.")
                if getattr(w, 'arrival_distance', None) is None:
                    self.log_error(f"Wing '{w.name}' uses directional arrival_method '{w.arrival_method}' but is missing 'arrival_distance'.")

            if w.arrival_anchor and w.arrival_anchor not in valid_targets:
                self.log_error(f"Wing '{w.name}' references unknown arrival_anchor '{w.arrival_anchor}'")
            
            # Fighterbay check for Docking Bay arrival
            if arr_loc == "docking bay" and w.arrival_anchor:
                if w.arrival_anchor not in name_to_ship:
                    self.log_error(f"Wing '{w.name}' uses Docking Bay arrival but anchor '{w.arrival_anchor}' is not a valid ship.")
                else:
                    anchor_ship = name_to_ship[w.arrival_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Wing '{w.name}' uses Docking Bay arrival from anchor '{w.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

            dep_loc = w.departure_method.strip().lower()
            if dep_loc == "docking bay":
                if not w.departure_anchor:
                    self.log_error(f"Wing '{w.name}' uses Docking Bay departure but is missing 'departure_anchor'.")

            if w.departure_anchor and w.departure_anchor not in valid_targets:
                self.log_error(f"Wing '{w.name}' references unknown departure_anchor '{w.departure_anchor}'")

            # Fighterbay check for Docking Bay departure
            if dep_loc == "docking bay" and w.departure_anchor:
                if w.departure_anchor not in name_to_ship:
                    self.log_error(f"Wing '{w.name}' uses Docking Bay departure but anchor '{w.departure_anchor}' is not a valid ship.")
                else:
                    anchor_ship = name_to_ship[w.departure_anchor]
                    if not self._ship_has_fighterbay(anchor_ship.ship_class):
                        self.log_error(f"Wing '{w.name}' uses Docking Bay departure via anchor '{w.departure_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

    def validate_player_setup(self):
        """
        Validate player setup configuration.
        
        Checks:
        - Validity of additional_weapons provided.
        - Validity of additional_ship_choices provided.
        """
        setup = self.mission.player_setup
        for w_name in setup.additional_weapons:
            if w_name not in self.allowed_weapons:
                self.log_error(f"Player setup 'additional_weapons' references unknown weapon '{w_name}'")
                
        for choice in setup.additional_ship_choices:
            if choice.ship_class not in self.ship_classes:
                self.log_error(f"Player setup 'additional_ship_choices' references unknown ship class '{choice.ship_class}'")

    def validate_start_ship(self):
        """
        Validate the player start ship configuration.

        Ensures:
        - Start ship exists.
        - If standalone, it has arrival_cue '( true )'.
        - Emits a warning if the start ship is not a member of a Friendly player
          starting wing (Alpha, Beta, Gamma, Delta, or Epsilon), since that is the
          most common and most fully supported authoring pattern in FreeSpace.
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

        # Find the wing (if any) that contains the start ship.
        start_wing = None
        for w in self.mission.wings:
            if any(s.name == start_name for s in w.ships):
                start_wing = w
                break

        in_wing = start_wing is not None

        if not in_wing:
            # Standalone must have arrival_cue true
            cue = "".join(ship.arrival_cue.split()).lower()
            if cue != '(true)':
                self.log_error(f"Player start ship '{start_name}' (standalone) must have arrival_cue '( true )'.")

        # Warn when the player is not a member of a Friendly player starting wing
        # (Alpha, Beta, Gamma, Delta, or Epsilon).  Non-leader positions such as
        # Alpha 2 or Beta 3 are fully valid and do not trigger this warning.
        is_in_friendly_player_starting_wing = (
            start_wing is not None
            and start_wing.name in fs_data.PLAYER_WING_NAMES
            and bool(start_wing.ships)
            and start_wing.ships[0].team == 'Friendly'
        )

        if not is_in_friendly_player_starting_wing:
            self.log_warning(
                f"Player start ship '{start_name}' is not a member of a Friendly player starting wing "
                f"(Alpha, Beta, Gamma, Delta, or Epsilon). "
                f"Most FreeSpace missions place the player in one of these standard wings (e.g. Alpha 1 or Alpha 2). "
                f"A non-standard player start limits weapon-pool calculation, loadout-screen behavior, "
                f"and wingman availability. If this is intentional, ignore this warning; "
                f"otherwise define an Alpha/Beta/Gamma/Delta/Epsilon wing and set "
                f"player_setup.start_ship to one of its members."
            )

    def validate_large_ship_escort_recommendation(self):
        """
        Advisory check: warn when the mission contains potentially important ships larger than
        fighter/bomber scale but none of them have the 'escort' flag.

        In FreeSpace, adding important larger ships to the HUD escort list
        (via the 'escort' ship flag) lets the player monitor their hull
        integrity at all times.  Having zero escorted ships in a mission that
        contains cruisers, destroyers, transports, freighters, science vessels, escape pods,
        or similar potentially important vessels is unusual and often an oversight.

        The check uses ``self.num_hardpoints`` (``fs_data.NUM_OF_HARDPOINTS``)
        as the fighter/bomber classifier: any ship whose class is NOT in that
        dict is considered "larger than fighter/bomber", minus a set of small
        utility objects (nav buoys, sentry guns, cargo containers,
        training drones) that have no gameplay relevance for the escort list.

        The warning is advisory and does not abort conversion.
        """
        # Collect ships that count as "meaningful large ships" for this check.
        # Ships with a non-zero destroyed_before_mission_seconds are destroyed
        # before the mission starts (pre-placed wreckage) and are not actually
        # present in the mission, so they are excluded from this check.
        large_ships = [
            ship for ship in self.mission.ships
            if ship.ship_class not in self.num_hardpoints
            and ship.ship_class not in _SMALL_UTILITY_CLASSES
            and ship.destroyed_before_mission_seconds == 0
        ]

        if not large_ships:
            # No large ships in the mission — nothing to warn about.
            return

        if any('escort' in ship.flags for ship in large_ships):
            # At least one large ship is already on the escort list — OK.
            return

        # Build a compact summary for the warning message (ship names with class
        # in parentheses, capped to avoid excessively long output).
        MAX_LISTED = 8
        listed_ships = large_ships[:MAX_LISTED]
        ships_str = ', '.join(
            f"{ship.name} ({ship.ship_class})" for ship in listed_ships
        )
        if len(large_ships) > MAX_LISTED:
            ships_str += ', ...'

        self.log_warning(
            f"Mission has {len(large_ships)} potentially important larger-than-fighter/bomber ship(s) "
            f"({ships_str}) but none of them have the 'escort' flag. "
            f"In FreeSpace it is customary to add important larger ships to the "
            f"HUD escort list so the player can monitor their hull integrity. "
            f"Consider adding the 'escort' flag to the most important ship(s). "
            f"If all larger ships in this mission are minor or irrelevant to the "
            f"player, you may ignore this warning."
        )
