"""
Tests for the validator error raised when the ``no-shields`` ship flag is set
on a ship class that is not a fighter or bomber.

Background
----------
In FSO, only fighters and bombers have a shield mesh.  Larger ships (cruisers,
destroyers, transports, freighters, etc.) never carry shields, so the
``no-shields`` flag has no effect on them and almost always indicates an
authoring mistake — for example, a flag copied from a fighter template to a
cruiser template by accident.

The check is a hard **error** (not an advisory warning): ``validate()`` must
return False when it fires.

Cases tested
------------
- Fighter with ``no-shields``                   -> no error (valid use)
- Bomber with ``no-shields``                    -> no error (valid use)
- Standalone cruiser with ``no-shields``        -> error; message names ship and class
- Standalone transport with ``no-shields``      -> error
- Standalone large ship WITHOUT ``no-shields``  -> no error (control case)
- Wing of cruisers with ``no-shields`` in the
  ship template                                 -> exactly one error per wing
                                                   (de-duplication check)
- Two separate wings of large ships, each with
  ``no-shields``                                -> one error per wing (two total)
- Unknown / typo'd class with ``no-shields``    -> no duplicate error (the
  invalid-class error from validate_ships already fires; this check skips it)
"""

import unittest
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap (mirrors every other test file in this directory)
# ---------------------------------------------------------------------------
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

# Unique fragment present in every no-shields applicability error message.
_ERROR_FRAGMENT = "only fighters and bombers can have shields"


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


# ---------------------------------------------------------------------------
# Minimal ship / wing helpers
# ---------------------------------------------------------------------------

def _fighter(name: str, flags=None) -> Ship:
    """GTF Ulysses — valid subject for the ``no-shields`` flag."""
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
    """GTB Medusa — valid subject for the ``no-shields`` flag."""
    return Ship.model_validate({
        "name": name,
        "class": "GTB Medusa",
        "team": "Friendly",
        "position": [200.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
        "weapons": Weapons(primary=["Avenger"], secondary=["Tsunami", "Tsunami", "MX-50"]),
    })


def _cruiser(name: str, flags=None) -> Ship:
    """GTC Fenris — larger than fighter/bomber, ``no-shields`` is superfluous."""
    return Ship.model_validate({
        "name": name,
        "class": "GTC Fenris",
        "team": "Friendly",
        "position": [500.0, 0.0, 500.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
    })


def _transport(name: str, flags=None) -> Ship:
    """GTT Elysium — larger than fighter/bomber, ``no-shields`` is superfluous."""
    return Ship.model_validate({
        "name": name,
        "class": "GTT Elysium",
        "team": "Friendly",
        "position": [800.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags or ["cargo-known"],
    })


def _alpha_wing(ships, initial_orders="( ai-chase-any 89 )") -> Wing:
    return Wing(
        name="Alpha",
        count=len(ships),
        ships=ships,
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders=initial_orders,
    )


def _make_mission(*ships, extra_wings=None) -> Mission:
    """Build a minimal Mission with the given ships.

    The first fighter (GTF Ulysses / GTB Medusa) in the list is placed in a
    Friendly Alpha wing so that player-start validation passes.  All other
    ships remain as standalone ships.  ``extra_wings`` may supply additional
    Wing objects (already attached to the mission).
    """
    all_ships = list(ships)
    start_name = None
    for s in all_ships:
        if s.ship_class in ("GTF Ulysses", "GTB Medusa"):
            start_name = s.name
            break
    if start_name is None:
        start_name = all_ships[0].name

    start_ship = next(s for s in all_ships if s.name == start_name)
    player_wing = _alpha_wing([start_ship])
    wings = [player_wing] + (extra_wings or [])
    return Mission(
        mission_info=MissionInfo(name="Test"),
        player_setup=PlayerSetup(start_ship=start_name),
        environment=Environment(),
        ships=all_ships,
        wings=wings,
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestNoShieldsFlagApplicability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Valid usages — must NOT raise the error
    # ------------------------------------------------------------------

    def test_fighter_with_no_shields_no_error(self):
        """Fighter with ``no-shields`` is valid — shields can be disabled on fighters."""
        ship = _fighter("Alpha 1", flags=["no-shields"])
        mission = _make_mission(ship)
        v = _make_validator(mission)
        # validate() may still return False for other reasons (e.g. hardpoint
        # count mismatch), so only check that our specific error is absent.
        v.validate()
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no no-shields error for a fighter, got: {v.errors}",
        )

    def test_bomber_with_no_shields_no_error(self):
        """Bomber with ``no-shields`` is valid — shields can be disabled on bombers."""
        fighter = _fighter("Alpha 1")
        bomber = _bomber("Alpha 2", flags=["no-shields"])
        mission = _make_mission(fighter, bomber)
        v = _make_validator(mission)
        v.validate()
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no no-shields error for a bomber, got: {v.errors}",
        )

    def test_cruiser_without_no_shields_no_error(self):
        """Cruiser without ``no-shields`` → no error (control case)."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1")
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        v.validate()
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no no-shields error when flag is absent, got: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Invalid usages — must raise the error
    # ------------------------------------------------------------------

    def test_standalone_cruiser_with_no_shields_errors(self):
        """Standalone cruiser with ``no-shields`` must produce a hard error."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1", flags=["cargo-known", "no-shields"])
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        result = v.validate()
        self.assertFalse(result, "Expected validate() to return False")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no-shields error for cruiser, got: {v.errors}",
        )

    def test_error_message_names_ship_and_class(self):
        """The error message must mention both the ship name and its class."""
        fighter = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1", flags=["cargo-known", "no-shields"])
        mission = _make_mission(fighter, cruiser)
        v = _make_validator(mission)
        v.validate()
        matching = [e for e in v.errors if _ERROR_FRAGMENT in e]
        self.assertTrue(matching, "Expected at least one no-shields error")
        msg = matching[0]
        self.assertIn("GTC Fenris 1", msg, f"Error should name the ship: {msg}")
        self.assertIn("GTC Fenris", msg, f"Error should name the class: {msg}")

    def test_standalone_transport_with_no_shields_errors(self):
        """Transport with ``no-shields`` must also produce a hard error."""
        fighter = _fighter("Alpha 1")
        transport = _transport("GTT Elysium 1", flags=["cargo-known", "no-shields"])
        mission = _make_mission(fighter, transport)
        v = _make_validator(mission)
        result = v.validate()
        self.assertFalse(result, "Expected validate() to return False")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no-shields error for transport, got: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Wing de-duplication — one error per wing, not one per member
    # ------------------------------------------------------------------

    def test_wing_of_cruisers_reports_once(self):
        """A wing of 3 cruisers with ``no-shields`` in the template must produce
        exactly ONE error (not three separate per-member errors)."""
        # Build three cruiser ships that belong to a single wing.
        cruiser_ships = [
            _cruiser(f"Bragi {i}", flags=["cargo-known", "no-shields"])
            for i in range(1, 4)
        ]
        cruiser_wing = Wing(
            name="Bragi",
            count=3,
            ships=cruiser_ships,
            position=[1000.0, 0.0, 1000.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        # Player wing
        fighter = _fighter("Alpha 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[fighter] + cruiser_ships,
            wings=[_alpha_wing([fighter]), cruiser_wing],
        )
        v = _make_validator(mission)
        v.validate()
        no_shields_errors = [e for e in v.errors if _ERROR_FRAGMENT in e]
        self.assertEqual(
            len(no_shields_errors), 1,
            f"Expected exactly 1 no-shields error for a 3-ship wing, got {len(no_shields_errors)}: {no_shields_errors}",
        )
        self.assertIn("Bragi", no_shields_errors[0],
                      f"Error should name the wing 'Bragi': {no_shields_errors[0]}")

    def test_two_separate_large_ship_wings_report_one_error_each(self):
        """Two separate wings of larger ships, each with ``no-shields``, must
        each produce exactly one error — two errors in total."""
        cruiser_ships_a = [
            _cruiser(f"Bragi {i}", flags=["cargo-known", "no-shields"])
            for i in range(1, 3)
        ]
        cruiser_ships_b = [
            _cruiser(f"Buri {i}", flags=["cargo-known", "no-shields"])
            for i in range(1, 3)
        ]
        wing_a = Wing(
            name="Bragi",
            count=2,
            ships=cruiser_ships_a,
            position=[1000.0, 0.0, 1000.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        wing_b = Wing(
            name="Buri",
            count=2,
            ships=cruiser_ships_b,
            position=[2000.0, 0.0, 2000.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        fighter = _fighter("Alpha 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[fighter] + cruiser_ships_a + cruiser_ships_b,
            wings=[_alpha_wing([fighter]), wing_a, wing_b],
        )
        v = _make_validator(mission)
        v.validate()
        no_shields_errors = [e for e in v.errors if _ERROR_FRAGMENT in e]
        self.assertEqual(
            len(no_shields_errors), 2,
            f"Expected 2 no-shields errors (one per wing), got {len(no_shields_errors)}: {no_shields_errors}",
        )

    # ------------------------------------------------------------------
    # Unknown class guard — must not stack errors
    # ------------------------------------------------------------------

    def test_unknown_class_with_no_shields_skipped(self):
        """A ship with an unknown/typo'd class that also carries ``no-shields``
        should NOT produce an additional no-shields error on top of the
        already-raised invalid-class error."""
        fighter = _fighter("Alpha 1")
        bad_ship = Ship.model_validate({
            "name": "Mystery Ship",
            "class": "GTX Unknown Typo",   # invalid class
            "team": "Hostile",
            "position": [300.0, 0.0, 0.0],
            "arrival_cue": "( true )",
            "flags": ["no-shields"],
        })
        mission = _make_mission(fighter, bad_ship)
        v = _make_validator(mission)
        v.validate()
        # There must be an invalid-class error for the unknown class.
        self.assertTrue(
            any("invalid class" in e for e in v.errors),
            f"Expected an invalid-class error, got: {v.errors}",
        )
        # There must NOT be an additional no-shields error for this ship.
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no no-shields error for unknown class, got: {v.errors}",
        )


if __name__ == "__main__":
    unittest.main()
