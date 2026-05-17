"""
Tests for the advisory validator warning emitted when a mission contains
ships larger than fighter/bomber scale but none of them have the 'escort' flag.

In FreeSpace it is customary to add important larger ships (cruisers, destroyers,
transports, freighters, science vessels, etc.) to the HUD escort list so the
player can monitor their hull integrity.  Having zero escort-flagged large ships
is often an oversight.

The warning is advisory: validate() must still return True when only this
warning is present, but no errors.

Cases tested:
- Fighter-only mission             -> no warning
- Bomber-only mission              -> no warning
- Fighter + cruiser, cruiser has 'escort'       -> no warning
- Fighter + cruiser, NO large ship has 'escort' -> warning
- Fighter + cruiser + transport, transport has 'escort' -> no warning
  (only a large ship needs to be escorted, not necessarily all)
- Fighter + cruiser + transport, fighter has 'escort' but no large ship does
  -> warning (fighter escort does not count)
- Mission with only nav buoys / sentry guns / cargo containers (utility objects)
  -> no warning (utility objects are excluded from the check)
- Mission with a GTS Centaur support ship (not in utility exclusion set) but
  no escort -> warning (support ships are real ships, not small utility objects)
"""

import unittest
import sys
from pathlib import Path

_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
_repo_root = _parent_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Weapons, Wing
from validator import Validator

_REPO_ROOT = _repo_root

# Unique fragment present in every large-ship-escort warning message.
_WARNING_FRAGMENT = "none of them have the 'escort' flag"


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


# ---------------------------------------------------------------------------
# Minimal ship helpers
# ---------------------------------------------------------------------------

def _fighter(name: str, flags=None) -> Ship:
    """Minimal GTF Ulysses (fighter)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTF Ulysses",
        "team": "Friendly",
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
        "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
    })


def _bomber(name: str, flags=None) -> Ship:
    """Minimal GTB Medusa (bomber — requires 1 primary, 3 secondary banks)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTB Medusa",
        "team": "Friendly",
        "position": [200.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
        "weapons": Weapons(primary=["Avenger"], secondary=["Tsunami", "Tsunami", "MX-50"]),
    })


def _cruiser(name: str, flags=None, destroyed_before_mission_seconds: int = 0) -> Ship:
    """Minimal GTC Fenris (cruiser — larger than fighter/bomber)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTC Fenris",
        "team": "Friendly",
        "position": [500.0, 0.0, 500.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
        "destroyed_before_mission_seconds": destroyed_before_mission_seconds,
    })


def _transport(name: str, flags=None) -> Ship:
    """Minimal GTT Elysium (transport — larger than fighter/bomber)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTT Elysium",
        "team": "Friendly",
        "position": [800.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
    })


def _support_ship(name: str, flags=None) -> Ship:
    """Minimal GTS Centaur (support ship — large, NOT in small-utility set)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTS Centaur",
        "team": "Friendly",
        "position": [600.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
    })


def _nav_buoy(name: str) -> Ship:
    """Terran NavBuoy — small utility object, excluded from escort check."""
    return Ship.model_validate({
        "name": name,
        "class": "Terran NavBuoy",
        "team": "Friendly",
        "position": [100.0, 0.0, 0.0],
        "arrival_cue": "( true )",
    })


def _sentry_gun(name: str) -> Ship:
    """GTSG Watchdog — small utility object, excluded from escort check."""
    return Ship.model_validate({
        "name": name,
        "class": "GTSG Watchdog",
        "team": "Friendly",
        "position": [150.0, 0.0, 0.0],
        "arrival_cue": "( true )",
    })


def _cargo(name: str) -> Ship:
    """TC 2 cargo container — small utility object, excluded from escort check."""
    return Ship.model_validate({
        "name": name,
        "class": "TC 2",
        "team": "Friendly",
        "position": [175.0, 0.0, 0.0],
        "arrival_cue": "( true )",
    })


def _alpha_wing(ships) -> Wing:
    return Wing(
        name="Alpha",
        count=len(ships),
        ships=ships,
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _make_mission(*ships) -> Mission:
    """Build a minimal Mission with the given ships.

    The first fighter/bomber in the list (or the first ship if none) is used
    as the player start and placed in a Friendly Alpha wing so that the
    player-start validation passes.  All other ships remain standalone.
    """
    all_ships = list(ships)
    # Identify a usable player start ship (first fighter/bomber)
    start_name = all_ships[0].name
    for s in all_ships:
        if s.ship_class in ("GTF Ulysses", "GTB Medusa"):
            start_name = s.name
            break
    start_ship = next(s for s in all_ships if s.name == start_name)
    player_wing = _alpha_wing([start_ship])
    return Mission(
        mission_info=MissionInfo(name="Test"),
        player_setup=PlayerSetup(start_ship=start_name),
        environment=Environment(),
        ships=all_ships,
        wings=[player_wing],
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestLargeShipEscortWarning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Cases that should NOT produce the warning
    # ------------------------------------------------------------------

    def test_fighter_only_mission_no_warning(self):
        """Fighter-only mission: no large ships → no warning."""
        ship = _fighter("Alpha 1")
        mission = _make_mission(ship)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning for fighter-only mission, got: {v.warnings}",
        )

    def test_bomber_only_mission_no_warning(self):
        """Bomber-only mission: no large ships → no warning."""
        ship = _bomber("Bravo 1")
        mission = _make_mission(ship)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning for bomber-only mission, got: {v.warnings}",
        )

    def test_cruiser_with_escort_flag_no_warning(self):
        """Fighter + cruiser where the cruiser has the 'escort' flag → no warning."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1", flags=["cargo-known", "escort"])
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning when cruiser has 'escort', got: {v.warnings}",
        )

    def test_one_of_multiple_large_ships_has_escort_no_warning(self):
        """Fighter + cruiser + transport where only the transport has 'escort' → no warning.
        The check only requires at least one large ship to have the flag."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1")  # no escort flag
        transport = _transport("GTT Elysium 1", flags=["cargo-known", "escort"])
        mission = _make_mission(fighter, cruiser, transport)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning when transport has 'escort', got: {v.warnings}",
        )

    def test_utility_objects_only_no_warning(self):
        """Mission containing only small utility objects (nav buoy, sentry gun,
        cargo container) alongside a fighter: none of these count as large ships,
        so no warning is emitted."""
        fighter = _fighter("Alpha 1")
        buoy = _nav_buoy("Nav Buoy 1")
        sentry = _sentry_gun("Watchdog 1")
        crate = _cargo("Crate 1")
        mission = _make_mission(fighter, buoy, sentry, crate)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning for utility-only non-fighter objects, got: {v.warnings}",
        )

    # ------------------------------------------------------------------
    # Cases that SHOULD produce the warning
    # ------------------------------------------------------------------

    def test_cruiser_without_escort_flag_warns(self):
        """Fighter + cruiser with no 'escort' on any large ship → warning emitted,
        validation still passes."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1")  # no escort flag
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        # Validation must still pass (advisory warning only)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected escort warning for cruiser without 'escort' flag, got: {v.warnings}",
        )

    def test_multiple_large_ships_none_escorted_warns(self):
        """Fighter + cruiser + transport, neither large ship has 'escort' → warning."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1")
        transport = _transport("GTT Elysium 1")
        mission = _make_mission(fighter, cruiser, transport)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected escort warning when no large ship is escorted, got: {v.warnings}",
        )

    def test_only_fighter_has_escort_but_no_large_ship_warns(self):
        """Fighter with 'escort' flag + cruiser without 'escort': fighter escort
        does not satisfy the check — a large ship must have the flag."""
        fighter = _fighter("Alpha 1", flags=["cargo-known", "escort"])
        cruiser = _cruiser("GTC Fenris 1")  # no escort flag
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected escort warning when only a fighter (not a large ship) has 'escort', "
            f"got: {v.warnings}",
        )

    def test_support_ship_without_escort_warns(self):
        """GTS Centaur support ship is NOT in the small-utility exclusion set,
        so a mission with only a fighter + Centaur and no 'escort' flag on the
        Centaur should produce the warning."""
        fighter = _fighter("Alpha 1")
        support = _support_ship("GTS Centaur 1")
        mission = _make_mission(fighter, support)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected escort warning for GTS Centaur without 'escort', got: {v.warnings}",
        )

    def test_support_ship_with_escort_no_warning(self):
        """GTS Centaur support ship WITH 'escort' flag: warning is suppressed."""
        fighter = _fighter("Alpha 1")
        support = _support_ship("GTS Centaur 1", flags=["cargo-known", "escort"])
        mission = _make_mission(fighter, support)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning when GTS Centaur has 'escort', got: {v.warnings}",
        )

    def test_warning_message_mentions_large_ship_class(self):
        """The warning message should mention the class of the offending large ship."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1")
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        v.validate()
        self.assertTrue(
            any("GTC Fenris" in w for w in v.warnings),
            f"Expected warning to mention 'GTC Fenris', got: {v.warnings}",
        )

    def test_destroyed_before_mission_no_warning(self):
        """Fighter + cruiser where the cruiser has a non-zero
        destroyed_before_mission_seconds (pre-placed wreckage) → no warning.

        Ships destroyed before mission start are not actually present during
        play; they exist only as debris.  The escort check should not fire
        for such ships because there is nothing for the player to monitor."""
        fighter = _fighter("Alpha 1")
        # Cruiser is turned into wreckage 30 s before the mission starts.
        cruiser = _cruiser("GTC Fenris 1", destroyed_before_mission_seconds=30)
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no escort warning for a cruiser destroyed before mission start, "
            f"got: {v.warnings}",
        )


if __name__ == "__main__":
    unittest.main()
