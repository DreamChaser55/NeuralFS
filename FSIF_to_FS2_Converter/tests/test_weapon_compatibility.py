"""
Tests for scoped ship-weapon compatibility validation.

Weapon-class compatibility (via WEAPON_COMPATIBILITY) is enforced as a
hard error only for ships that belong to Friendly player starting wings
(Alpha, Beta, Gamma, Delta, Epsilon).  Ships outside those wings (NPC/enemy
wings, standalone NPC ships) may carry canonical-but-incompatible weapons
without causing FSO issues, so the validator completely ignores such
incompatibilities — it emits neither an error nor a warning for them.
"""

import unittest
import sys
from pathlib import Path

# Add parent directories to path
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
_repo_root = _parent_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Weapons, Wing
from validator import Validator

try:
    from weapons_compatibility_data import WEAPON_COMPATIBILITY
except ImportError:
    WEAPON_COMPATIBILITY = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = _repo_root


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


def _ulysses_ship(name: str, *, banshee: bool = False) -> Ship:
    """
    GTF Ulysses with 2 primary and 1 secondary hardpoints.
    When *banshee* is True, the second primary bank is armed with Banshee,
    which is NOT compatible with GTF Ulysses per the FSO ship tables
    (Banshee is restricted to GTF Valkyrie, GTF Hercules, and GTF Loki).
    """
    primary = ["Avenger", "Banshee"] if banshee else ["Avenger", "Avenger"]
    return Ship.model_validate({
        "name": name,
        "class": "GTF Ulysses",
        "team": "Friendly",
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "weapons": Weapons(primary=primary, secondary=["MX-50"]),
    })


def _alpha_wing(ship: Ship) -> Wing:
    """Minimal Alpha wing (player starting wing) wrapping a single ship."""
    return Wing(
        name="Alpha",
        count=1,
        ships=[ship],
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


# Condition shared by the banshee-specific tests:
#   – compatibility data exists for GTF Ulysses, AND
#   – Banshee is NOT in its allowed primaries (i.e., it is actually incompatible).
_BANSHEE_INCOMPATIBLE_WITH_ULYSSES = (
    "GTF Ulysses" in WEAPON_COMPATIBILITY
    and "Banshee" not in WEAPON_COMPATIBILITY.get("GTF Ulysses", {}).get("primary", set())
)


class TestWeaponCompatibilityScopedToPlayerWings(unittest.TestCase):
    """
    Verify that incompatible-weapon detection is scoped correctly:
    - ERROR for ships in Friendly player starting wings (Alpha…Epsilon).
    - Completely ignored (no error, no warning) for all other ships.
    """

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Player starting wing → hard error
    # ------------------------------------------------------------------

    @unittest.skipUnless(
        _BANSHEE_INCOMPATIBLE_WITH_ULYSSES,
        "WEAPON_COMPATIBILITY data unavailable or Banshee is compatible with GTF Ulysses",
    )
    def test_incompatible_weapon_in_alpha_wing_is_hard_error(self):
        """
        Banshee in a GTF Ulysses that is part of Alpha wing must produce a
        validation ERROR and cause validate() to return False.
        """
        ship = _ulysses_ship("Alpha 1", banshee=True)
        mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_alpha_wing(ship)],
        )
        v = _make_validator(mission)

        self.assertFalse(
            v.validate(),
            "Expected validation to fail due to incompatible weapon in Alpha wing",
        )
        self.assertTrue(
            any("Alpha 1" in e and "incompatible" in e.lower() for e in v.errors),
            f"Expected incompatible-weapon ERROR mentioning 'Alpha 1', got errors: {v.errors}",
        )

    @unittest.skipUnless(
        _BANSHEE_INCOMPATIBLE_WITH_ULYSSES,
        "WEAPON_COMPATIBILITY data unavailable or Banshee is compatible with GTF Ulysses",
    )
    def test_incompatible_weapon_in_beta_wing_is_hard_error(self):
        """
        Incompatible weapon in Beta wing (another player starting wing) must
        also be a hard error.
        """
        ship = _ulysses_ship("Beta 1", banshee=True)
        beta_wing = Wing(
            name="Beta",
            count=1,
            ships=[ship],
            position=[200.0, 0.0, 0.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        # Also need a valid player start ship
        player_ship = _ulysses_ship("Alpha 1", banshee=False)
        mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[player_ship, ship],
            wings=[_alpha_wing(player_ship), beta_wing],
        )
        v = _make_validator(mission)

        self.assertFalse(v.validate(), f"Expected validation to fail for Beta 1, errors: {v.errors}")
        self.assertTrue(
            any("Beta 1" in e and "incompatible" in e.lower() for e in v.errors),
            f"Expected incompatible-weapon ERROR mentioning 'Beta 1', got errors: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Non-player wing → completely ignored (no error, no warning)
    # ------------------------------------------------------------------

    @unittest.skipUnless(
        _BANSHEE_INCOMPATIBLE_WITH_ULYSSES,
        "WEAPON_COMPATIBILITY data unavailable or Banshee is compatible with GTF Ulysses",
    )
    def test_incompatible_weapon_in_non_player_wing_is_ignored(self):
        """
        Banshee in a GTF Ulysses inside a non-player wing (e.g. 'Rama') must
        be completely ignored by the validator: validate() must return True and
        no incompatible-weapon error or warning should be emitted for that ship.
        """
        player_ship = _ulysses_ship("Alpha 1", banshee=False)
        npc_ship = _ulysses_ship("Rama 1", banshee=True)
        npc_wing = Wing(
            name="Rama",
            count=1,
            ships=[npc_ship],
            position=[500.0, 0.0, 500.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 60 )",
        )
        mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[player_ship, npc_ship],
            wings=[_alpha_wing(player_ship), npc_wing],
        )
        v = _make_validator(mission)

        # Validation must pass
        self.assertTrue(
            v.validate(),
            f"Expected validation to pass for non-player-wing incompatible weapon, errors: {v.errors}",
        )
        # No incompatible-weapon warning for Rama 1
        self.assertFalse(
            any("Rama 1" in w and "incompatible" in w.lower() for w in v.warnings),
            f"Expected no incompatible-weapon WARNING for 'Rama 1', got warnings: {v.warnings}",
        )
        # No incompatible-weapon error for Rama 1
        self.assertFalse(
            any("Rama 1" in e and "incompatible" in e.lower() for e in v.errors),
            f"Expected no incompatible-weapon ERROR for 'Rama 1', got errors: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Standalone NPC ship → completely ignored (no error, no warning)
    # ------------------------------------------------------------------

    @unittest.skipUnless(
        _BANSHEE_INCOMPATIBLE_WITH_ULYSSES,
        "WEAPON_COMPATIBILITY data unavailable or Banshee is compatible with GTF Ulysses",
    )
    def test_incompatible_weapon_on_standalone_npc_ship_is_ignored(self):
        """
        Banshee in a standalone ship that is NOT part of any wing must be
        completely ignored by the validator: validate() must return True and
        no incompatible-weapon error or warning should be emitted for that ship.
        """
        player_ship = _ulysses_ship("Alpha 1", banshee=False)
        npc_ship = _ulysses_ship("NPC Fighter", banshee=True)
        # npc_ship is standalone – not added to any Wing
        mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[player_ship, npc_ship],
            wings=[_alpha_wing(player_ship)],
        )
        v = _make_validator(mission)

        self.assertTrue(
            v.validate(),
            f"Expected validation to pass for standalone NPC incompatible weapon, errors: {v.errors}",
        )
        # No incompatible-weapon warning for NPC Fighter
        self.assertFalse(
            any("NPC Fighter" in w and "incompatible" in w.lower() for w in v.warnings),
            f"Expected no incompatible-weapon WARNING for 'NPC Fighter', got: {v.warnings}",
        )
        # No incompatible-weapon error for NPC Fighter
        self.assertFalse(
            any("NPC Fighter" in e and "incompatible" in e.lower() for e in v.errors),
            f"Expected no incompatible-weapon ERROR for 'NPC Fighter', got: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Sanity: fully compatible Alpha wing → no compatibility messages
    # ------------------------------------------------------------------

    @unittest.skipUnless(
        "GTF Ulysses" in WEAPON_COMPATIBILITY,
        "WEAPON_COMPATIBILITY data unavailable for GTF Ulysses",
    )
    def test_compatible_weapons_in_alpha_wing_produces_no_compatibility_messages(self):
        """
        A fully compatible Alpha wing loadout must not produce any
        incompatible-weapon errors or warnings.
        """
        ship = _ulysses_ship("Alpha 1", banshee=False)
        mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_alpha_wing(ship)],
        )
        v = _make_validator(mission)

        self.assertTrue(v.validate(), f"Expected validation to pass, got errors: {v.errors}")
        self.assertFalse(
            any("incompatible" in e.lower() for e in v.errors),
            f"Expected no compatibility errors, got: {v.errors}",
        )
        self.assertFalse(
            any("incompatible" in w.lower() for w in v.warnings),
            f"Expected no compatibility warnings, got: {v.warnings}",
        )


if __name__ == "__main__":
    unittest.main()
