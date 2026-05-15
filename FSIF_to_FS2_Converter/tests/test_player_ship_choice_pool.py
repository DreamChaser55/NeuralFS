"""
Tests for validate_player_ship_choice_pool() in ShipWingChecksMixin.

The rule: for non-scramble missions that contain Friendly player starting wings
(Alpha, Beta, Gamma, Delta, Epsilon), the total count in
player_setup.additional_ship_choices must be >= the total number of Friendly
player starting wing slots.  The pool is cross-class (mixing classes is fine).

The check is skipped for scramble missions and missions with no Friendly player
starting wings.

Cases covered:
- Empty pool with 4-ship Alpha wing fails   (reproduces Vega_Requiem Mission_1_1 bug)
- Pool count == wing count passes
- Pool count > wing count passes
- Pool count < wing count (but > 0) fails
- Mixed classes satisfying total count passes  (general_demo pattern)
- Scramble flag suppresses the check (empty pool is accepted)
- No Friendly player starting wings: check is skipped
- Hostile Alpha wing: treated as NPC wing, check is skipped for it
- Non-player wing (Zeta): ignored by the check
- Two player wings: total slots from both are summed
- Two entries for the same class are summed
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

from data_models import (
    Mission, MissionInfo, PlayerSetup, ShipChoice,
    Environment, Ship, Weapons, Wing,
)
from validator import Validator

_REPO_ROOT = _repo_root
_ERROR_FRAGMENT = "player_setup.additional_ship_choices"


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


def _sc(ship_class: str, count: int) -> ShipChoice:
    """Construct a ShipChoice using the required 'class' alias."""
    return ShipChoice.model_validate({"class": ship_class, "count": count})


def _apollo(name: str, team: str = "Friendly") -> Ship:
    return Ship.model_validate({
        "name": name,
        "class": "GTF Apollo",
        "team": team,
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "weapons": Weapons(primary=["ML-16 Laser", "ML-16 Laser"], secondary=["MX-50", "Fury"]),
        "flags": ["no-shields"],
    })


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
        position=[500.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _zeta_wing(ships) -> Wing:
    """Non-player wing — should be ignored by the check."""
    return Wing(
        name="Zeta",
        count=len(ships),
        ships=ships,
        position=[1000.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


class TestPlayerShipChoicePool(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Fails: pool too small
    # ------------------------------------------------------------------

    def test_empty_pool_with_alpha_wing_fails(self):
        """
        Reproduces the Vega_Requiem/Mission_1_1 bug:
        Alpha wing has 4 ships but additional_ship_choices is empty.
        The loadout screen will have zero ships available.
        """
        ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[],   # <-- the bug
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected pool-coverage error, got errors: {v.errors}",
        )

    def test_partial_pool_less_than_wing_slots_fails(self):
        """Pool total (2) < wing slots (4) — should fail."""
        ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[_sc("GTF Apollo", 2)],
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected pool-coverage error, got errors: {v.errors}",
        )

    def test_two_wings_pool_only_covers_one_fails(self):
        """Alpha (4) + Beta (4) = 8 slots total; pool only provides 4 — fails."""
        alpha_ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        beta_ships = [_ulysses(f"Beta {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[_sc("GTF Apollo", 4)],
            ),
            environment=Environment(),
            ships=alpha_ships + beta_ships,
            wings=[_alpha_wing(alpha_ships), _beta_wing(beta_ships)],
        )
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Expected pool-coverage error, got errors: {v.errors}",
        )

    # ------------------------------------------------------------------
    # Passes: pool is sufficient
    # ------------------------------------------------------------------

    def test_exact_count_same_class_passes(self):
        """Pool count exactly equals wing slots — should pass."""
        ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[_sc("GTF Apollo", 4)],
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Unexpected pool error: {v.errors}",
        )

    def test_pool_count_greater_than_wing_slots_passes(self):
        """Pool count (6) > wing slots (4) — more choices than needed is fine."""
        ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[_sc("GTF Apollo", 6)],
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)

    def test_mixed_classes_total_satisfies_wing_passes(self):
        """
        Reproduces general_demo pattern: 2 Hercules + 2 Valkyrie covers a 4-slot wing.
        The check is cross-class — total count is what matters.
        """
        ships = [_ulysses(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[
                    _sc("GTF Hercules", 2),
                    _sc("GTF Valkyrie", 2),
                ],
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Unexpected pool error: {v.errors}",
        )

    def test_duplicate_class_entries_are_summed_passes(self):
        """Two entries for the same class are summed: 2 + 2 = 4 for a 4-slot wing."""
        ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[
                    _sc("GTF Apollo", 2),
                    _sc("GTF Apollo", 2),
                ],
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)

    def test_two_wings_pool_covers_both_passes(self):
        """Alpha (4) + Beta (4) = 8 total slots; pool provides 8 — passes."""
        alpha_ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        beta_ships = [_ulysses(f"Beta {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[
                    _sc("GTF Apollo", 4),
                    _sc("GTF Ulysses", 4),
                ],
            ),
            environment=Environment(),
            ships=alpha_ships + beta_ships,
            wings=[_alpha_wing(alpha_ships), _beta_wing(beta_ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)

    # ------------------------------------------------------------------
    # Exemptions
    # ------------------------------------------------------------------

    def test_scramble_mission_skips_pool_check(self):
        """Scramble missions bypass the loadout screen — pool check is suppressed."""
        ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        mission = Mission(
            mission_info=MissionInfo(name="Test", flags=["scramble"]),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[],   # empty — would normally fail
            ),
            environment=Environment(),
            ships=ships,
            wings=[_alpha_wing(ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Pool check should be suppressed for scramble missions: {v.errors}",
        )

    def test_no_player_wing_skips_pool_check(self):
        """Mission with no Friendly player starting wings skips the pool check."""
        # Only a non-player wing (Zeta) — no Alpha/Beta/Gamma/Delta/Epsilon
        ship = _ulysses("Zeta 1")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Zeta 1",
                additional_ship_choices=[],
            ),
            environment=Environment(),
            ships=[ship],
            wings=[_zeta_wing([ship])],
        )
        v = _make_validator(mission)
        # May have other warnings (non-player-wing start) but no pool ERROR
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Pool check should be skipped for non-player wing: {v.errors}",
        )

    def test_hostile_alpha_wing_skips_pool_check(self):
        """Hostile Alpha wing is an NPC wing — not counted as a player starting wing."""
        ship = _ulysses("Alpha 1", team="Hostile")
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[],
            ),
            environment=Environment(),
            ships=[ship],
            wings=[
                Wing(
                    name="Alpha",
                    count=1,
                    ships=[ship],
                    position=[0.0, 0.0, 0.0],
                    arrival_cue="( true )",
                    initial_orders="( ai-chase-any 89 )",
                )
            ],
        )
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Hostile Alpha wing should not trigger pool check: {v.errors}",
        )

    def test_non_player_wing_not_counted(self):
        """
        An Alpha wing (Friendly, 4 ships) plus a Zeta NPC wing (6 ships):
        only the Alpha wing's 4 slots count; 4 pool ships is sufficient.
        """
        alpha_ships = [_apollo(f"Alpha {i}") for i in range(1, 5)]
        zeta_ships = [_ulysses(f"Zeta {i}") for i in range(1, 7)]
        mission = Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(
                start_ship="Alpha 1",
                additional_ship_choices=[_sc("GTF Apollo", 4)],
            ),
            environment=Environment(),
            ships=alpha_ships + zeta_ships,
            wings=[_alpha_wing(alpha_ships), _zeta_wing(zeta_ships)],
        )
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_ERROR_FRAGMENT in e for e in v.errors),
            f"Unexpected pool error: {v.errors}",
        )


if __name__ == "__main__":
    unittest.main()
