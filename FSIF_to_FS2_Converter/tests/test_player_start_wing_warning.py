"""
Tests for the validator warning emitted when the player start ship is not a
member of a Friendly player starting wing (Alpha, Beta, Gamma, Delta, Epsilon).

The warning is advisory: validate() must still return True when only this
warning is present, but no errors.

Cases tested:
- Alpha 1 (wing leader) -> no warning
- Alpha 2 (non-leader) -> no warning
- Beta 3 (different player wing, non-leader) -> no warning
- Standalone 'Player Ship' -> warning
- Ship in non-player wing 'Zeta' -> warning
- Ship in hostile Alpha wing -> warning
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

_WARNING_FRAGMENT = "not a member of a Friendly player starting wing"


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


def _ulysses(name: str, team: str = "Friendly") -> Ship:
    return Ship.model_validate({
        "name": name,
        "class": "GTF Ulysses",
        "team": team,
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
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


def _beta_wing(ships) -> Wing:
    return Wing(
        name="Beta",
        count=len(ships),
        ships=ships,
        position=[200.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _zeta_wing(ships) -> Wing:
    return Wing(
        name="Zeta",
        count=len(ships),
        ships=ships,
        position=[400.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


class TestPlayerStartWingWarning(unittest.TestCase):
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

    def test_alpha_1_leader_no_warning(self):
        """Player is Alpha 1 (wing leader) in a Friendly Alpha wing — no warning."""
        ship = _ulysses("Alpha 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_alpha_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no player-start-wing warning, got: {v.warnings}",
        )

    def test_alpha_2_non_leader_no_warning(self):
        """Player is Alpha 2 (non-leader) in a Friendly Alpha wing — no warning."""
        ship1 = _ulysses("Alpha 1")
        ship2 = _ulysses("Alpha 2")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 2"),
            environment=Environment(),
            ships=[ship1, ship2],
            wings=[_alpha_wing([ship1, ship2])],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no player-start-wing warning for Alpha 2, got: {v.warnings}",
        )

    def test_beta_3_non_leader_no_warning(self):
        """Player is Beta 3 (non-leader) in a Friendly Beta wing — no warning."""
        ships = [_ulysses(f"Beta {i}") for i in range(1, 4)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Beta 3"),
            environment=Environment(),
            ships=ships,
            wings=[_beta_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no player-start-wing warning for Beta 3, got: {v.warnings}",
        )

    # ------------------------------------------------------------------
    # Cases that SHOULD produce the warning
    # ------------------------------------------------------------------

    def test_standalone_start_ship_warns(self):
        """Standalone player start ship produces the warning (validation still passes)."""
        ship = _ulysses("Player Ship")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Player Ship"),
            environment=Environment(),
            ships=[ship],
        )
        v = _make_validator(mission)
        # Validation must still pass (warning is advisory)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected player-start-wing warning for standalone start, got: {v.warnings}",
        )
        # Warning message must mention the ship name
        self.assertTrue(
            any("Player Ship" in w for w in v.warnings),
            f"Expected warning to mention 'Player Ship', got: {v.warnings}",
        )

    def test_non_player_wing_start_warns(self):
        """Player in a non-player wing ('Zeta') produces the warning."""
        ship = _ulysses("Zeta 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Zeta 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_zeta_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected player-start-wing warning for Zeta wing start, got: {v.warnings}",
        )

    def test_hostile_alpha_wing_start_warns(self):
        """Player in a Hostile Alpha wing produces the warning."""
        ship = _ulysses("Alpha 1", team="Hostile")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_alpha_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected player-start-wing warning for Hostile Alpha start, got: {v.warnings}",
        )


if __name__ == "__main__":
    unittest.main()
