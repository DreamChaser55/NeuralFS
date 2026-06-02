import re
from typing import Set
import fs_flags_constants
from common import fs_data
try:
    from weapons_compatibility_data import WEAPON_COMPATIBILITY
except ImportError:
    WEAPON_COMPATIBILITY = {}

# Minimum arrival_distance (metres) for directional arrival methods.
# Values below this threshold risk spawning arriving ships dangerously close
# to — or clipping inside — their arrival anchor.
MIN_ARRIVAL_DISTANCE = 300

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

# Ship classes that support the `cargo` string field.
# Only transports (prefixes GTT/PVT/ST) and cargo containers carry cargo.
# Any other ship class with a cargo field defined is a validation error.
_TRANSPORT_CLASSES: frozenset = frozenset({
    'GTT Elysium',  # Terran transport (GTT prefix)
    'PVT Isis',     # Vasudan transport (PVT prefix)
    'ST Azrael',    # Shivan transport (ST prefix)
})

_CARGO_CONTAINER_CLASSES: frozenset = frozenset({
    'TC 2', 'TSC 2', 'TAC 1', 'TTC 1',  # Terran cargo containers
    'VC 3', 'VAC 4',                      # Vasudan cargo containers
    'SC 5', 'SAC 2',                      # Shivan cargo containers
})

# Combined: all ship classes that are allowed to have the `cargo` field defined.
_CARGO_CAPABLE_CLASSES: frozenset = _TRANSPORT_CLASSES | _CARGO_CONTAINER_CLASSES

class ShipWingChecksMixin:
    # Broad canonical wing-name pattern for the advisory standalone-name warning.
    # Covers all Terran, Vasudan, and Shivan wing names from the FreeSpace Universe Bible.
    _WING_NAME_PATTERN = re.compile(
        r'^(' + '|'.join(re.escape(n) for n in sorted(fs_data.COMMON_WING_NAMES)) + r') \d+$'
    )

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
            if s.team == 'Friendly' and s.ship_class in self.fighter_bomber_classes
        ]

        
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
        Return the set of ship names that belong to Friendly player-loadout wings.

        Player-loadout wings are the wings whose names are in
        ``fs_data.PLAYER_START_WING_NAMES`` (Alpha, Beta, Gamma) and whose
        first ship has team "Friendly".  These are the only wings shown on the
        FSO loadout screen, so weapon-compatibility is only checked for ships
        in these wings.
        """
        names: Set[str] = set()
        for wing in self.mission.wings:
            if wing.name not in fs_data.PLAYER_START_WING_NAMES:
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
        - Weapon compatibility for Friendly player-loadout wing ships only
          (Alpha, Beta, Gamma). FSO only enforces weapon compatibility for
          ships on the loadout screen; incompatible weapons on other ships
          are harmless.
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
            # Only validate class-level compatibility for ships in Friendly
            # player-loadout wings (Alpha, Beta, Gamma).  FSO only enforces
            # weapon compatibility via the loadout screen; incompatible weapons
            # on any other ship (NPC wings, Delta/Epsilon, standalone ships,
            # enemy ships) are harmless.
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

    @staticmethod
    def _is_cargo_field_defined(ship) -> bool:
        """Return True when the ship's cargo field has a meaningful value.

        The runtime default is ``'Nothing'`` (case-insensitive).  An empty
        string or the literal ``'Nothing'`` both count as "not defined."
        """
        c = (ship.cargo or '').strip()
        return bool(c) and c.lower() != 'nothing'

    def validate_cargo_field(self):
        """Validate the ``cargo`` string field on all ships.

        Four invariants are checked:

        1. **Error** — ``cargo`` is defined on a ship whose class is not a
           transport (``GTT*``, ``PVT*``, ``ST*``) or cargo container
           (``TC 2``, ``TSC 2``, etc.).  Only those two categories support the
           cargo string in FSO.

        2. **Warning** — a *Friendly* transport or cargo container does *not*
           have ``cargo`` defined.  Such ships almost always carry cargo in
           playable missions; missing cargo is likely an authoring oversight.

        3. **Warning** — a *Friendly* ship has ``cargo`` defined but is missing
           the ``cargo-known`` flag.  Friendly ships generally have their cargo
           visible immediately; if the author intentionally wants the player to
           scan the ship, this warning can be ignored.

        4. **Error** — a ship has both the ``scannable`` flag and ``cargo``
           defined.  The ``scannable`` flag completely overrides the cargo
           mechanism — the ship will only show "Scanned"/"Not Scanned" and the
           cargo string is never displayed.  Remove one or the other.
        """
        for ship in self.mission.ships:
            cargo_defined = self._is_cargo_field_defined(ship)
            is_cargo_capable = ship.ship_class in _CARGO_CAPABLE_CLASSES
            is_friendly = ship.team == 'Friendly'
            has_scannable = 'scannable' in ship.flags
            has_cargo_known = 'cargo-known' in ship.flags

            # 1. cargo defined on a non-cargo-capable ship → error
            if cargo_defined and not is_cargo_capable:
                self.log_error(
                    f"Ship '{ship.name}' (class '{ship.ship_class}') has a cargo field defined "
                    f"('{ship.cargo}'), but only transports (GTT Elysium, PVT Isis, ST Azrael) "
                    f"and cargo containers (TC 2, TSC 2, TAC 1, TTC 1, VC 3, VAC 4, SC 5, SAC 2) "
                    f"support the cargo string in FSO. "
                    f"Remove the cargo field from this ship."
                )

            # 2. Friendly transport/cargo container without cargo → warning
            if is_friendly and is_cargo_capable and not cargo_defined:
                self.log_warning(
                    f"Friendly ship '{ship.name}' (class '{ship.ship_class}') is a transport or "
                    f"cargo container but has no cargo defined (cargo defaults to 'Nothing'). "
                    f"Such ships usually carry cargo in playable missions. "
                    f"If this is intentional, ignore this warning."
                )

            # 3. Friendly ship with cargo defined but missing cargo-known flag → warning
            if is_friendly and cargo_defined and not has_cargo_known:
                self.log_warning(
                    f"Friendly ship '{ship.name}' has cargo defined ('{ship.cargo}') "
                    f"but is missing the 'cargo-known' flag. "
                    f"Friendly ships generally have their cargo visible immediately. "
                    f"If the intent is to require the player to scan this ship to reveal its cargo, "
                    f"ignore this warning. Otherwise, add 'cargo-known' to the ship's flags."
                )

            # 4. scannable flag + cargo defined → error
            if cargo_defined and has_scannable:
                self.log_error(
                    f"Ship '{ship.name}' has both the 'scannable' flag and a cargo field defined "
                    f"('{ship.cargo}'). The 'scannable' flag completely overrides the cargo "
                    f"mechanism — the ship will only report 'Scanned'/'Not Scanned' and the "
                    f"cargo string is never shown. "
                    f"Remove either the 'scannable' flag (to use the cargo scanning mechanism) "
                    f"or the cargo field (to use the `scannable` flag)."
                )

    def validate_wings(self):
        """
        Validate wing definitions.

        Invariants:
        - Wing ``count`` must not exceed 6 (FSO hard engine limit on ships per
          wing).
        - Every flag in ``wing.flags`` must be a recognised FSO wing flag from
          ``fs_flags_constants.WING_FLAGS_BUCKET``.
        - Wings without ``initial_orders`` are warned (advisory): AI ships with
          no orders will sit idle, which is almost always an authoring oversight.
        """
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
        like a wing member (e.g. 'Alpha 1', 'Rama 4', 'Theta 2').

        Checks the full canonical FreeSpace wing-name vocabulary from the
        Universe Bible: all Terran friendly/enemy, Vasudan friendly/enemy, and
        Shivan enemy wing prefixes (see ``fs_data.COMMON_WING_NAMES``).

        This is most likely a mistake: the intended pattern is to define the
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

    def _validate_arrival_departure_anchors(self, entity, label, name_to_ship,
                                             valid_targets, directional_locations):
        """Validate arrival/departure anchors for a single ship or wing entity.

        Called by ``validate_anchors`` for each ship and each wing.  ``label``
        is ``"Ship"`` or ``"Wing"`` and drives the entity-type string used in
        every error/warning message, preserving the original per-type wording.
        """
        # Per-type clause used inside the arrival_distance advisory warning to
        # preserve the original ship vs. wing wording exactly.
        if label == "Ship":
            spawn_clause = "spawning the ship dangerously close to or clipping inside its arrival_anchor"
        else:
            spawn_clause = "spawning wing members dangerously close to or clipping inside the arrival_anchor"

        name = entity.name

        arr_loc = entity.arrival_method.strip().lower()
        if arr_loc == "docking bay":
            if not entity.arrival_anchor:
                self.log_error(f"{label} '{name}' uses Docking Bay arrival but is missing 'arrival_anchor'.")
        elif arr_loc in directional_locations:
            if not entity.arrival_anchor:
                self.log_error(f"{label} '{name}' uses directional arrival_method '{entity.arrival_method}' but is missing 'arrival_anchor'.")
            if getattr(entity, 'arrival_distance', None) is None:
                self.log_error(f"{label} '{name}' uses directional arrival_method '{entity.arrival_method}' but is missing 'arrival_distance'.")
            elif entity.arrival_distance < MIN_ARRIVAL_DISTANCE:
                self.log_warning(
                    f"{label} '{name}' uses directional arrival_method '{entity.arrival_method}' "
                    f"with arrival_distance {entity.arrival_distance} m, which is below the "
                    f"recommended minimum of {MIN_ARRIVAL_DISTANCE} m. "
                    f"Too small a distance risks {spawn_clause}. "
                    f"Increase arrival_distance to at least {MIN_ARRIVAL_DISTANCE}."
                )

        if entity.arrival_anchor and entity.arrival_anchor not in valid_targets:
            self.log_error(f"{label} '{name}' references unknown arrival_anchor '{entity.arrival_anchor}'")

        # Fighterbay check for Docking Bay arrival
        if arr_loc == "docking bay" and entity.arrival_anchor:
            if entity.arrival_anchor not in name_to_ship:
                self.log_error(f"{label} '{name}' uses Docking Bay arrival but anchor '{entity.arrival_anchor}' is not a valid ship.")
            else:
                anchor_ship = name_to_ship[entity.arrival_anchor]
                if not self._ship_has_fighterbay(anchor_ship.ship_class):
                    self.log_error(f"{label} '{name}' uses Docking Bay arrival from anchor '{entity.arrival_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

        dep_loc = entity.departure_method.strip().lower()
        if dep_loc == "docking bay":
            if not entity.departure_anchor:
                self.log_error(f"{label} '{name}' uses Docking Bay departure but is missing 'departure_anchor'.")

        if entity.departure_anchor and entity.departure_anchor not in valid_targets:
            self.log_error(f"{label} '{name}' references unknown departure_anchor '{entity.departure_anchor}'")

        # Fighterbay check for Docking Bay departure
        if dep_loc == "docking bay" and entity.departure_anchor:
            if entity.departure_anchor not in name_to_ship:
                self.log_error(f"{label} '{name}' uses Docking Bay departure but anchor '{entity.departure_anchor}' is not a valid ship.")
            else:
                anchor_ship = name_to_ship[entity.departure_anchor]
                if not self._ship_has_fighterbay(anchor_ship.ship_class):
                    self.log_error(f"{label} '{name}' uses Docking Bay departure via anchor '{entity.departure_anchor}', but class '{anchor_ship.ship_class}' does not have a fighterbay subsystem.")

    def validate_anchors(self):
        """
        Validate arrival/departure anchors for ships and wings.

        Checks:
        - Anchor exists (Ship, Wing, or Special Token).
        - If using Docking Bay arrival/departure, ensures anchor has a fighterbay.
        """
        name_to_ship = {s.name: s for s in self.mission.ships}
        valid_targets = set(name_to_ship.keys()) | {w.name for w in self.mission.wings} | self.allowed_anchors_tokens

        directional_locations = {
            "near ship", "in front of ship", "in back of ship",
            "above ship", "below ship", "to left of ship", "to right of ship"
        }

        for ship in self.mission.ships:
            self._validate_arrival_departure_anchors(
                ship, "Ship", name_to_ship, valid_targets, directional_locations)

        for wing in self.mission.wings:
            self._validate_arrival_departure_anchors(
                wing, "Wing", name_to_ship, valid_targets, directional_locations)

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
        - Start ship is a member of a Friendly Alpha, Beta, or Gamma wing.
          Standalone player starts and starts in any other wing (including
          Friendly Delta/Epsilon or hostile wings) are a hard validation error
          because FSO's team loadout screen only works correctly when the
          player starts in one of the first three Friendly wings.
        """
        start_name = self.mission.player_setup.start_ship
        if not start_name:
            self.log_error("player_setup.start_ship is undefined.")
            return

        # Early guard: missions with zero wings cannot have a valid player start.
        if not self.mission.wings:
            self.log_error(
                "Invalid player start ship: mission defines zero wings. "
                "FSIF missions must define at least one Friendly Alpha, Beta, or Gamma wing "
                "containing player_setup.start_ship. "
                "FSO's team loadout screen only works when the player starts in a "
                "Friendly Alpha, Beta, or Gamma wing (e.g. 'Alpha 1', 'Beta 3', 'Gamma 2'). "
                "Define an Alpha, Beta, or Gamma wing in entities.wings and set "
                "player_setup.start_ship to one of its members."
            )
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

        # The player start ship must be a member of a Friendly Alpha, Beta, or
        # Gamma wing.  Non-leader positions such as Alpha 2 or Beta 3 are fully
        # valid and do not trigger this error.
        # Rationale: FSO's team loadout screen reads the player's team entry from
        # the first three wings (Team 1: Alpha, Beta, Gamma).  Starting the player
        # in any other configuration (standalone ship, Delta/Epsilon wing, or any
        # Hostile wing) causes the loadout screen to malfunction.
        #
        # Note: we check the actual start ship's team directly rather than using
        # the wing leader as a proxy.  This correctly handles edge cases where
        # different wing members might have different teams (even though FSIF
        # normally prevents this, the validator should express the rule directly).
        is_in_valid_start_wing = (
            start_wing is not None
            and start_wing.name in fs_data.PLAYER_START_WING_NAMES
            and ship.team == 'Friendly'
        )

        if not is_in_valid_start_wing:
            if start_wing is None:
                reason = (
                    f"'{start_name}' is a standalone ship (not a member of any wing). "
                    f"Standalone player starts are not supported."
                )
            elif start_wing.name not in fs_data.PLAYER_START_WING_NAMES:
                reason = (
                    f"'{start_name}' is in wing '{start_wing.name}', which is not one of "
                    f"the valid player-start wings (Alpha, Beta, Gamma)."
                )
            elif ship.team != 'Friendly':
                reason = (
                    f"'{start_name}' is in wing '{start_wing.name}', but the start ship "
                    f"itself has team '{ship.team}' (must be 'Friendly')."
                )
            else:
                reason = f"'{start_name}' does not meet player-start wing requirements."

            self.log_error(
                f"Invalid player start ship: {reason} "
                f"FSO's team loadout screen only works when the player starts in a "
                f"Friendly Alpha, Beta, or Gamma wing (e.g. 'Alpha 1', 'Beta 3', 'Gamma 2'). "
                f"Define an Alpha, Beta, or Gamma wing in entities.wings and set "
                f"player_setup.start_ship to one of its members."
            )

    # ------------------------------------------------------------------
    # Orientation helpers
    # ------------------------------------------------------------------

    _IDENTITY_ORIENTATION = (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
    )

    def _is_identity_orientation(self, orientation, eps: float = 1e-6) -> bool:
        """Return True when *orientation* is (approximately) the identity matrix."""
        if orientation is None:
            return True  # None → identity default
        if len(orientation) != 9:
            return False  # malformed — not our problem here
        return all(
            abs(v - ref) < eps
            for v, ref in zip(orientation, self._IDENTITY_ORIENTATION)
        )

    # ------------------------------------------------------------------
    # Orientation advisory check
    # ------------------------------------------------------------------

    def validate_large_ship_orientation_defaults(self):
        """Advisory check: warn when larger ships or wings of larger ships
        leave the ``orientation`` field at its identity-matrix default.

        Mirrors the Authoring Guide recommendation that authors set a
        deliberate ``orientation`` on important larger ships.

        **Standalone ships**: any ship whose class is NOT in
        ``self.fighter_bomber_classes`` and NOT in ``_SMALL_UTILITY_CLASSES``,
        whose ``orientation`` is (approximately) the identity matrix.

        **Wings of larger ships**: any wing classified as "larger" (first
        member's ship class not in fighter/bomber or small-utility sets) whose
        ``wing.orientation`` is ``None`` (the authoring guide states that
        omitting the field means it is at the default).

        Excludes ships with ``destroyed_before_mission_seconds > 0``
        (pre-placed wreckage is not a moving presence at mission start).

        Both checks are advisory and do not abort conversion.
        """
        MAX_LISTED = 8

        # ── Collect wing-member names so we can skip them in the ship loop ──
        wing_member_names: Set[str] = set()
        for wing in self.mission.wings:
            for ship in wing.ships:
                wing_member_names.add(ship.name)

        # ── 1. Standalone larger ships with identity orientation ──
        flagged_ships = []
        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue  # handled via the wing-level check
            if ship.ship_class in self.fighter_bomber_classes:
                continue
            if ship.ship_class in _SMALL_UTILITY_CLASSES:
                continue
            if ship.destroyed_before_mission_seconds > 0:
                continue
            # Ships with orientation_target have deliberate facing — skip advisory.
            if getattr(ship, 'orientation_target', None) is not None:
                continue
            # FSO ignores orientation for non-Hyperspace arrivals — skip advisory.
            if ship.arrival_method.strip().lower() != "hyperspace":
                continue
            if self._is_identity_orientation(ship.orientation):
                flagged_ships.append(ship)

        if flagged_ships:
            listed = flagged_ships[:MAX_LISTED]
            ships_str = ', '.join(
                f"{s.name} ({s.ship_class})" for s in listed
            )
            if len(flagged_ships) > MAX_LISTED:
                ships_str += ', ...'
            self.log_warning(
                f"Mission has {len(flagged_ships)} larger-than-fighter/bomber standalone ship(s) "
                f"with the default identity orientation ({ships_str}). "
                f"Default orientation makes the opening scene look grid-aligned and artificial. "
                f"Consider authoring a deliberate `orientation` matrix (or a mission-start "
                f"`set-object-facing-object` event) for important larger ships "
                f"See the FSIF Authoring Guide - 'Initial ship orientation and facing direction'."
            )

        # ── 2. Wings of larger ships with missing (default) orientation ──
        flagged_wings = []
        for wing in self.mission.wings:
            if not wing.ships:
                continue
            lead_class = wing.ships[0].ship_class
            if lead_class in self.fighter_bomber_classes:
                continue
            if lead_class in _SMALL_UTILITY_CLASSES:
                continue
            # Wings with orientation_target have deliberate facing — skip advisory.
            if getattr(wing, 'orientation_target', None) is not None:
                continue
            # FSO ignores orientation for non-Hyperspace arrivals — skip advisory.
            if wing.arrival_method.strip().lower() != "hyperspace":
                continue
            if wing.orientation is None:
                flagged_wings.append(wing)

        if flagged_wings:
            listed = flagged_wings[:MAX_LISTED]
            wings_str = ', '.join(
                f"{w.name} ({w.ships[0].ship_class})" for w in listed
            )
            if len(flagged_wings) > MAX_LISTED:
                wings_str += ', ...'
            self.log_warning(
                f"Mission has {len(flagged_wings)} wing(s) of larger-than-fighter/bomber ships "
                f"without an authored `orientation` field ({wings_str}). "
                f"Wing members default to the identity matrix when `orientation` is omitted, "
                f"which makes the opening scene look grid-aligned and artificial. "
                f"Author `orientation` directly on the wing definition to give all members a "
                f"shared initial facing, or use a mission-start `set-object-facing-object` event. "
                f"See the FSIF Authoring Guide - 'Initial ship orientation and facing direction'."
            )

    def validate_orientation_ignored_for_nonhyperspace_arrival(self):
        """Advisory check: warn when a ship or wing has a deliberate non-default
        ``orientation`` but uses a non-Hyperspace arrival method.

        The FSO engine ignores the authored ``orientation`` for any non-Hyperspace
        arrival (Docking Bay, Near Ship, In front of/behind/above/below/left/right
        of ship).  FSO always overrides the orientation to face the arrival_anchor
        for these methods, so an authored orientation is dead data and should be
        removed to avoid confusion.

        The check fires when BOTH conditions hold:
        1. ``arrival_method`` is not ``"Hyperspace"``.
        2. A deliberate orientation was authored — either ``orientation_target`` is
           set (string target name was authored) OR the orientation matrix differs
           from the identity default.

        Both ships and wings are checked.  The warning is advisory and does not
        abort conversion.
        """
        # Compute wing-member names once so we can skip them in the ship loop.
        # Wing members inherit orientation from the wing definition itself;
        # the relevant check for those is the wing-level loop below.
        wing_member_names: set = set()
        for wing in self.mission.wings:
            for ws in wing.ships:
                wing_member_names.add(ws.name)

        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue
            if ship.arrival_method.strip().lower() == "hyperspace":
                continue
            has_deliberate_orientation = (
                getattr(ship, 'orientation_target', None) is not None
                or not self._is_identity_orientation(ship.orientation)
            )
            if has_deliberate_orientation:
                self.log_warning(
                    f"Ship '{ship.name}' has a non-default `orientation` "
                    f"but uses arrival_method '{ship.arrival_method}'. "
                    f"FSO ignores `orientation` for non-Hyperspace arrivals — "
                    f"the ship is always auto-oriented to face its arrival_anchor. "
                    f"Remove the `orientation` field from this ship."
                )

        for wing in self.mission.wings:
            if wing.arrival_method.strip().lower() == "hyperspace":
                continue
            has_deliberate_orientation = (
                getattr(wing, 'orientation_target', None) is not None
                or not self._is_identity_orientation(wing.orientation)
            )
            if has_deliberate_orientation:
                self.log_warning(
                    f"Wing '{wing.name}' has a non-default `orientation` "
                    f"but uses arrival_method '{wing.arrival_method}'. "
                    f"FSO ignores `orientation` for non-Hyperspace arrivals — "
                    f"the wing is always auto-oriented to face its arrival_anchor. "
                    f"Remove the `orientation` field from this wing."
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

        The check uses ``self.fighter_bomber_classes``
        (``fs_data.FIGHTER_BOMBER_CLASSES``) as the fighter/bomber classifier:
        any ship whose class is NOT in that set is considered
        "larger than fighter/bomber", minus a set of small
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
            if ship.ship_class not in self.fighter_bomber_classes
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
