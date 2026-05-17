"""
Tests for the validation error emitted when the player start ship is not a
member of a Friendly Alpha, Beta, or Gamma wing.

FSO's team loadout screen only works when the player starts in one of the
first three Friendly wings (Alpha, Beta, Gamma). Starting anywhere else
(standalone ship, Delta/Epsilon wing, hostile wing, or any other wing) is
therefore a hard validation error that aborts conversion.

Cases tested:
- Alpha 1 (wing leader) -> no error
- Alpha 2 (non-leader) -> no error
- Beta 3 (different player wing, non-leader) -> no error
- Gamma 1 -> no error
- Standalone 'Player Ship' -> error
- Ship in non-player wing 'Zeta' -> error
- Ship in Hostile Alpha wing -> error
- Ship in Friendly Delta wing -> error
- Ship in Friendly Epsilon wing -> error
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

_ERROR_FRAGMENT = "Invalid player start ship"


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


def _make_wing(name: str, ships, position=None) -> Wing:
    return Wing(
        name=name,
        count=len(ships),
        ships=ships,
        position=position or [0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _alpha_wing(ships) -> Wing:
    return _make_wing("Alpha", ships)


def _beta_wing(ships) -> Wing:
    return _make_wing("Beta", ships, [200.0, 0.0, 0.0])


def _gamma_wing(ships) -> Wing:
    return _make_wing("Gamma", ships, [400.0, 0.0, 0.0])


def _delta_wing(ships) -> Wing:
    return _make_wing("Delta", ships, [600.0, 0.0, 0.0])


def _epsilon_wing(ships) -> Wing:
    return _make_wing("Epsilon", ships, [800.0, 0.0, 0.0])


def _zeta_wing(ships) -> Wing:
    return _make_wing("Zeta", ships, [1000.0, 0.0, 0.0])


class TestPlayerStartWingValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Cases that should NOT produce an error
    # ------------------------------------------------------------------

    def test_alpha_1_leader_no_error(self):
        """Player is Alpha 1 (wing leader) in a Friendly Alpha wing — no error."""
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
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no player-start error, got: {v.errors}",
        )

    def test_alpha_2_non_leader_no_error(self):
        """Player is Alpha 2 (non-leader) in a Friendly Alpha wing — no error."""
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
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no player-start error for Alpha 2, got: {v.errors}",
        )

    def test_beta_3_non_leader_no_error(self):
        """Player is Beta 3 (non-leader) in a Friendly Beta wing — no error."""
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
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no player-start error for Beta 3, got: {v.errors}",
        )

    def test_gamma_1_leader_no_error(self):
        """Player is Gamma 1 (wing leader) in a Friendly Gamma wing — no error."""
        ship = _ulysses("Gamma 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Gamma 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_gamma_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected no player-start error for Gamma 1, got: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Cases that SHOULD produce an error (validate() returns False)
    # ------------------------------------------------------------------

    def test_standalone_start_ship_is_error(self):
        """Standalone player start ship is a hard validation error."""
        ship = _ulysses("Player Ship")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Player Ship"),
            environment=Environment(),
            ships=[ship],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate(), "Expected validate() to return False for standalone start")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected player-start error for standalone start, got: {v.errors}",
        )
        # Error message must mention the ship name
        self.assertTrue(
            any("Player Ship" in e for e in v.errors),
            f"Expected error to mention 'Player Ship', got: {v.errors}",
        )

    def test_non_player_wing_start_is_error(self):
        """Player in a non-player wing ('Zeta') is a hard validation error."""
        ship = _ulysses("Zeta 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Zeta 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_zeta_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate(), "Expected validate() to return False for Zeta wing start")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected player-start error for Zeta wing start, got: {v.errors}",
        )

    def test_hostile_alpha_wing_start_is_error(self):
        """Player in a Hostile Alpha wing is a hard validation error."""
        ship = _ulysses("Alpha 1", team="Hostile")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_alpha_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate(), "Expected validate() to return False for Hostile Alpha start")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected player-start error for Hostile Alpha start, got: {v.errors}",
        )

    def test_delta_wing_start_is_error(self):
        """Player in a Friendly Delta wing is a hard validation error.

        FSO's team loadout screen only works for Alpha, Beta, Gamma.
        Delta and Epsilon wings cannot host the player start ship.
        """
        ship = _ulysses("Delta 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Delta 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_delta_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate(), "Expected validate() to return False for Delta wing start")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected player-start error for Delta wing start, got: {v.errors}",
        )
        self.assertTrue(
            any("Delta" in e for e in v.errors),
            f"Expected error to mention 'Delta', got: {v.errors}",
        )

    def test_epsilon_wing_start_is_error(self):
        """Player in a Friendly Epsilon wing is a hard validation error."""
        ship = _ulysses("Epsilon 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Epsilon 1"),
            environment=Environment(),
            ships=[ship],
            wings=[_epsilon_wing([ship])],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate(), "Expected validate() to return False for Epsilon wing start")
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected player-start error for Epsilon wing start, got: {v.errors}",
        )
        self.assertTrue(
            any("Epsilon" in e for e in v.errors),
            f"Expected error to mention 'Epsilon', got: {v.errors}",
        )

    def test_hostile_alpha_non_leader_start_is_error(self):
        """Player start ship has team Hostile even though it is in an Alpha wing — hard error.

        This tests that the validator checks the actual start ship's team rather
        than the wing leader's team.  If the check were only on ships[0].team,
        placing the player on a non-leader Hostile ship in an otherwise Friendly
        Alpha wing would silently pass.
        """
        friendly_leader = _ulysses("Alpha 1", team="Friendly")
        hostile_member = _ulysses("Alpha 2", team="Hostile")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 2"),
            environment=Environment(),
            ships=[friendly_leader, hostile_member],
            wings=[_alpha_wing([friendly_leader, hostile_member])],
        )
        v = _make_validator(mission)
        self.assertFalse(
            v.validate(),
            "Expected validate() to return False when start ship is Hostile despite being in Alpha wing",
        )
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected player-start error for Hostile non-leader in Alpha wing, got: {v.errors}",
        )
        # The error should mention the team problem, not just a missing wing
        self.assertTrue(
            any("Hostile" in e for e in v.errors),
            f"Expected error to mention 'Hostile', got: {v.errors}",
        )


if __name__ == "__main__":
    unittest.main()
