"""Tests for the validator warning emitted when arrival_distance is below the
recommended minimum of 300 m for directional arrival methods.

The warning is advisory: validate() must still return True when only this
warning is present (no other errors).

Directional arrival methods (the ones where arrival_distance is applicable):
  Near Ship, In front of ship, In back of ship,
  Above ship, Below ship, To left of ship, To right of ship

The warning must NOT fire for:
  - Hyperspace arrivals (arrival_distance is ignored)
  - Docking Bay arrivals (arrival_distance is forced to 0; not a directional method)
  - arrival_distance >= 300

Cases tested:
Ships:
  - directional arrival, distance < 300   -> warning
  - directional arrival, distance == 0    -> warning (zero is below minimum)
  - directional arrival, distance == 300  -> no warning (at minimum boundary)
  - directional arrival, distance > 300   -> no warning
  - Hyperspace arrival, no distance set   -> no warning
  - Docking Bay arrival (not directional) -> no warning

Wings:
  - directional arrival, distance < 300   -> warning
  - directional arrival, distance == 300  -> no warning (at minimum boundary)
  - directional arrival, distance > 300   -> no warning
  - Hyperspace arrival, no distance set   -> no warning

Additional:
  - Warning message mentions the ship/wing name and the threshold value.
  - All directional arrival_method variants trigger the warning (spot-check).
"""

import unittest
import sys
from pathlib import Path

_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent         # FSIF_to_FS2_Converter/
_repo_root = _parent_dir.parent           # NeuralFS/
for _p in [str(_repo_root), str(_parent_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Weapons, Wing
from validator import Validator

_REPO_ROOT = _repo_root

# Fragment that appears in every arrival_distance minimum warning.
_WARNING_FRAGMENT = "below the recommended minimum of 300 m"

# A valid special anchor token recognised by the validator without requiring a
# matching ship/wing name in the mission (see fs_data.ALLOWED_ANCHORS_TOKENS).
_VALID_ANCHOR = "<any friendly player>"


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


# ---------------------------------------------------------------------------
# Ship helpers
# ---------------------------------------------------------------------------

def _player_fighter(name: str = "Alpha 1") -> Ship:
    """Minimal friendly GTF Ulysses for the player start wing."""
    return Ship.model_validate({
        "name": name,
        "class": "GTF Ulysses",
        "team": "Friendly",
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
    })


def _directional_ship(
    name: str,
    arrival_method: str,
    arrival_distance: int,
    anchor: str = _VALID_ANCHOR,
) -> Ship:
    """Hostile ship using a directional arrival_method with the given distance."""
    return Ship.model_validate({
        "name": name,
        "class": "SF Scorpion",
        "team": "Hostile",
        "position": [2000.0, 0.0, 2000.0],
        "arrival_method": arrival_method,
        "arrival_distance": arrival_distance,
        "arrival_anchor": anchor,
        "arrival_cue": "( true )",
        "weapons": Weapons(
            primary=["Shivan Light Laser", "Shivan Light Laser"],
            secondary=["MX-50#Shivan"],
        ),
    })


def _hyperspace_ship(name: str) -> Ship:
    """Hostile ship using the default Hyperspace arrival (no distance)."""
    return Ship.model_validate({
        "name": name,
        "class": "SF Scorpion",
        "team": "Hostile",
        "position": [1500.0, 0.0, 1500.0],
        "arrival_method": "Hyperspace",
        "arrival_cue": "( true )",
        "weapons": Weapons(
            primary=["Shivan Light Laser", "Shivan Light Laser"],
            secondary=["MX-50#Shivan"],
        ),
    })


def _alpha_wing(player_ship: Ship) -> Wing:
    """Minimal Friendly Alpha wing containing a single player fighter."""
    return Wing(
        name="Alpha",
        count=1,
        ships=[player_ship],
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _directional_wing(
    name: str,
    arrival_method: str,
    arrival_distance: int,
    anchor: str = _VALID_ANCHOR,
) -> Wing:
    """Hostile wing using a directional arrival_method with the given distance."""
    member = Ship.model_validate({
        "name": f"{name} 1",
        "class": "SF Scorpion",
        "team": "Hostile",
        "position": [3000.0, 0.0, 3000.0],
        "arrival_cue": "( false )",   # wing members use false
        "weapons": Weapons(
            primary=["Shivan Light Laser", "Shivan Light Laser"],
            secondary=["MX-50#Shivan"],
        ),
    })
    return Wing(
        name=name,
        count=1,
        ships=[member],
        position=[3000.0, 0.0, 3000.0],
        arrival_method=arrival_method,
        arrival_distance=arrival_distance,
        arrival_anchor=anchor,
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _hyperspace_wing(name: str) -> Wing:
    """Hostile wing using the default Hyperspace arrival (no distance)."""
    member = Ship.model_validate({
        "name": f"{name} 1",
        "class": "SF Scorpion",
        "team": "Hostile",
        "position": [3500.0, 0.0, 3500.0],
        "arrival_cue": "( false )",
        "weapons": Weapons(
            primary=["Shivan Light Laser", "Shivan Light Laser"],
            secondary=["MX-50#Shivan"],
        ),
    })
    return Wing(
        name=name,
        count=1,
        ships=[member],
        position=[3500.0, 0.0, 3500.0],
        arrival_method="Hyperspace",
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _make_mission_with_ship(*extra_ships, extra_wings=None) -> Mission:
    """Build a minimal valid Mission with a player Alpha wing + extra ships/wings."""
    player = _player_fighter()
    alpha = _alpha_wing(player)
    all_ships = [player] + list(extra_ships)
    wings = [alpha] + (list(extra_wings) if extra_wings else [])
    # Add wing members from extra_wings to the flat ships list
    for w in wings:
        for ws in w.ships:
            if ws.name not in {s.name for s in all_ships}:
                all_ships.append(ws)
    return Mission(
        mission_info=MissionInfo(name="Test"),
        player_setup=PlayerSetup(start_ship="Alpha 1"),
        environment=Environment(),
        ships=all_ships,
        wings=wings,
    )


# ---------------------------------------------------------------------------
# Tests: standalone ships
# ---------------------------------------------------------------------------

class TestArrivalDistanceMinimumWarningShip(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Cases that SHOULD produce the warning
    # ------------------------------------------------------------------

    def test_ship_directional_distance_below_minimum_warns(self):
        """Directional arrival with distance < 300 → warning emitted."""
        hostile = _directional_ship("Scorpion 1", "In front of ship", 100)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected arrival_distance warning for distance=100, got: {v.warnings}",
        )

    def test_ship_directional_distance_zero_warns(self):
        """Directional arrival with distance == 0 → warning (zero is below minimum)."""
        hostile = _directional_ship("Scorpion 1", "Near Ship", 0)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected arrival_distance warning for distance=0, got: {v.warnings}",
        )

    def test_ship_directional_distance_299_warns(self):
        """Directional arrival with distance 299 (one below minimum) → warning."""
        hostile = _directional_ship("Scorpion 1", "Above ship", 299)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected arrival_distance warning for distance=299, got: {v.warnings}",
        )

    # ------------------------------------------------------------------
    # Cases that should NOT produce the warning
    # ------------------------------------------------------------------

    def test_ship_directional_distance_at_minimum_no_warning(self):
        """Directional arrival with distance == 300 (exactly at minimum) → no warning."""
        hostile = _directional_ship("Scorpion 1", "In front of ship", 300)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for distance=300, got: {v.warnings}",
        )

    def test_ship_directional_distance_above_minimum_no_warning(self):
        """Directional arrival with distance >> 300 → no warning."""
        hostile = _directional_ship("Scorpion 1", "Above ship", 1500)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for distance=1500, got: {v.warnings}",
        )

    def test_ship_hyperspace_arrival_no_warning(self):
        """Hyperspace arrival has no applicable arrival_distance → no warning."""
        hostile = _hyperspace_ship("Scorpion 1")
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for Hyperspace arrival, got: {v.warnings}",
        )

    def test_ship_docking_bay_no_warning(self):
        """Docking Bay is not a directional arrival method → no distance warning."""
        # Note: Docking Bay requires a valid fighterbay anchor; we skip the
        # anchor/fighterbay validation entirely by testing without an anchor,
        # which will produce a different error (not the distance warning).
        # We simply confirm the distance warning does not appear.
        ship = Ship.model_validate({
            "name": "Arriving Ship",
            "class": "SF Scorpion",
            "team": "Hostile",
            "position": [2000.0, 0.0, 2000.0],
            "arrival_method": "Docking Bay",
            "arrival_cue": "( true )",
            "weapons": Weapons(
                primary=["Shivan Light Laser", "Shivan Light Laser"],
                secondary=["MX-50#Shivan"],
            ),
        })
        mission = _make_mission_with_ship(ship)
        v = _make_validator(mission)
        # Ignore other errors (missing anchor etc.); only check distance warning absent.
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for Docking Bay arrival, got: {v.warnings}",
        )

    # ------------------------------------------------------------------
    # Warning message content
    # ------------------------------------------------------------------

    def test_ship_warning_message_mentions_ship_name(self):
        """The warning message should reference the offending ship's name."""
        hostile = _directional_ship("SF Dragon 7", "In back of ship", 50)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        v.validate()
        self.assertTrue(
            any("SF Dragon 7" in w for w in v.warnings),
            f"Expected warning to mention ship name 'SF Dragon 7', got: {v.warnings}",
        )

    def test_ship_warning_is_advisory_validation_passes(self):
        """validate() must return True even when only the distance warning fires."""
        hostile = _directional_ship("Scorpion 1", "Below ship", 1)
        mission = _make_mission_with_ship(hostile)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, f"validate() must return True despite advisory warning, errors: {v.errors}")

    # ------------------------------------------------------------------
    # All directional variants trigger the warning (spot-check)
    # ------------------------------------------------------------------

    def test_all_directional_methods_trigger_warning_when_distance_low(self):
        """Every directional arrival method variant should produce the warning when
        distance < 300.  We test each variant individually."""
        directional_methods = [
            "Near Ship",
            "In front of ship",
            "In back of ship",
            "Above ship",
            "Below ship",
            "To left of ship",
            "To right of ship",
        ]
        for method in directional_methods:
            with self.subTest(method=method):
                hostile = _directional_ship("Scorpion 1", method, 50)
                mission = _make_mission_with_ship(hostile)
                v = _make_validator(mission)
                v.validate()
                self.assertTrue(
                    any(_WARNING_FRAGMENT in w for w in v.warnings),
                    f"Expected arrival_distance warning for method '{method}', got: {v.warnings}",
                )


# ---------------------------------------------------------------------------
# Tests: wings
# ---------------------------------------------------------------------------

class TestArrivalDistanceMinimumWarningWing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Cases that SHOULD produce the warning
    # ------------------------------------------------------------------

    def test_wing_directional_distance_below_minimum_warns(self):
        """Directional wing arrival with distance < 300 → warning emitted."""
        enemy_wing = _directional_wing("Rama", "In front of ship", 100)
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected arrival_distance warning for wing distance=100, got: {v.warnings}",
        )

    def test_wing_directional_distance_zero_warns(self):
        """Directional wing arrival with distance == 0 → warning."""
        enemy_wing = _directional_wing("Rama", "Above ship", 0)
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected arrival_distance warning for wing distance=0, got: {v.warnings}",
        )

    # ------------------------------------------------------------------
    # Cases that should NOT produce the warning
    # ------------------------------------------------------------------

    def test_wing_directional_distance_at_minimum_no_warning(self):
        """Directional wing arrival with distance == 300 → no warning."""
        enemy_wing = _directional_wing("Rama", "In front of ship", 300)
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for wing distance=300, got: {v.warnings}",
        )

    def test_wing_directional_distance_above_minimum_no_warning(self):
        """Directional wing arrival with distance 1500 → no warning."""
        enemy_wing = _directional_wing("Rama", "Above ship", 1500)
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for wing distance=1500, got: {v.warnings}",
        )

    def test_wing_hyperspace_arrival_no_warning(self):
        """Wing using Hyperspace arrival → no distance warning."""
        enemy_wing = _hyperspace_wing("Rama")
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no arrival_distance warning for wing Hyperspace arrival, got: {v.warnings}",
        )

    # ------------------------------------------------------------------
    # Warning message content
    # ------------------------------------------------------------------

    def test_wing_warning_message_mentions_wing_name(self):
        """The warning message should reference the offending wing's name."""
        enemy_wing = _directional_wing("Krishna", "Above ship", 10)
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        v.validate()
        self.assertTrue(
            any("Krishna" in w for w in v.warnings),
            f"Expected warning to mention wing name 'Krishna', got: {v.warnings}",
        )

    def test_wing_warning_is_advisory_validation_passes(self):
        """validate() must return True even when only the wing distance warning fires."""
        enemy_wing = _directional_wing("Rama", "Below ship", 5)
        mission = _make_mission_with_ship(extra_wings=[enemy_wing])
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, f"validate() must return True despite advisory warning, errors: {v.errors}")


if __name__ == "__main__":
    unittest.main()
