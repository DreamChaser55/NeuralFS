"""Regression tests for arrival/departure method token validation.

Covers:
- Invalid method strings are rejected during FSIF loading (FSIFDocument validation)
  as well as at the runtime model level (Ship / Wing).
- Arrival-only methods ('Near Ship', directional variants) are rejected for
  departure_method at both levels.
- Valid canonical tokens pass without error.
- Case-sensitivity is enforced (tokens must match exactly).
- Omitted method fields default to 'Hyperspace'.
- fs_data constants contain the expected token sets.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Ensure project root and FSIF converter directory are on sys.path
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent         # FSIF_to_FS2_Converter/
_repo_root = _parent_dir.parent           # NeuralFS/
for _p in [str(_repo_root), str(_parent_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_models import Ship, Wing, Weapons, _validate_arrival_method_token, _validate_departure_method_token
from mission_loader import load_mission_from_fsif
from common import fs_data
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Minimal FSIF template for loader-based tests.
# Placeholders:
#   {ship_arrival_method}  – arrival_method value for the standalone ship
#   {ship_departure_method} – departure_method value for the standalone ship
# ---------------------------------------------------------------------------

_MINIMAL_FSIF_TEMPLATE = """\
fsif_version: "4.0"

mission_info:
  name: "Method Test Mission"

player_setup:
  start_ship: "Player Ship"

entities:
  ship_templates:
    alpha_tmpl:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_method: {ship_arrival_method}
      departure_method: {ship_departure_method}
      arrival_condition: |
        ( true )

mission_flow: {{}}

environment:
  ambient_light_level: [0, 0, 0]
"""

_MINIMAL_FSIF_WING_TEMPLATE = """\
fsif_version: "4.0"

mission_info:
  name: "Wing Method Test Mission"

player_setup:
  start_ship: "Alpha 1"

entities:
  ship_templates:
    alpha_tmpl:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

  wings:
    - name: "Alpha"
      template: "alpha_tmpl"
      count: 1
      position: [0, 0, 0]
      arrival_method: {wing_arrival_method}
      departure_method: {wing_departure_method}
      arrival_condition: |
        ( true )

mission_flow: {{}}

environment:
  ambient_light_level: [0, 0, 0]
"""


def _load_from_fsif_text(fsif_text: str):
    """Write FSIF text to a temp file and attempt to load it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test_mission.fsif"
        p.write_text(fsif_text, encoding="utf-8")
        return load_mission_from_fsif(str(p))


class TestFsDataArrivalDepartureConstants(unittest.TestCase):
    """Verify that fs_data contains the expected canonical token sets."""

    def test_arrival_methods_contains_hyperspace(self):
        self.assertIn("Hyperspace", fs_data.ALLOWED_ARRIVAL_METHODS)

    def test_arrival_methods_contains_docking_bay(self):
        self.assertIn("Docking Bay", fs_data.ALLOWED_ARRIVAL_METHODS)

    def test_arrival_methods_contains_all_directional_variants(self):
        expected = {
            "Near Ship",
            "In front of ship",
            "In back of ship",
            "Above ship",
            "Below ship",
            "To left of ship",
            "To right of ship",
        }
        for method in expected:
            self.assertIn(method, fs_data.ALLOWED_ARRIVAL_METHODS, f"Missing arrival method: '{method}'")

    def test_departure_methods_contains_hyperspace(self):
        self.assertIn("Hyperspace", fs_data.ALLOWED_DEPARTURE_METHODS)

    def test_departure_methods_contains_docking_bay(self):
        self.assertIn("Docking Bay", fs_data.ALLOWED_DEPARTURE_METHODS)

    def test_departure_methods_excludes_directional_variants(self):
        arrival_only = {
            "Near Ship",
            "In front of ship",
            "In back of ship",
            "Above ship",
            "Below ship",
            "To left of ship",
            "To right of ship",
        }
        for method in arrival_only:
            self.assertNotIn(method, fs_data.ALLOWED_DEPARTURE_METHODS, f"Departure should NOT include '{method}'")

    def test_departure_methods_has_exactly_two_members(self):
        self.assertEqual(len(fs_data.ALLOWED_DEPARTURE_METHODS), 2)


class TestArrivalMethodTokenValidatorHelper(unittest.TestCase):
    """Unit tests for the _validate_arrival_method_token helper function."""

    def test_valid_hyperspace(self):
        self.assertEqual(_validate_arrival_method_token("Hyperspace"), "Hyperspace")

    def test_valid_docking_bay(self):
        self.assertEqual(_validate_arrival_method_token("Docking Bay"), "Docking Bay")

    def test_valid_near_ship(self):
        self.assertEqual(_validate_arrival_method_token("Near Ship"), "Near Ship")

    def test_valid_in_front_of_ship(self):
        self.assertEqual(_validate_arrival_method_token("In front of ship"), "In front of ship")

    def test_invalid_unknown_string(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_arrival_method_token("Near Warp")
        self.assertIn("Invalid arrival_method", str(ctx.exception))
        self.assertIn("Near Warp", str(ctx.exception))
        self.assertIn("Allowed values", str(ctx.exception))

    def test_invalid_wrong_case(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_arrival_method_token("hyperspace")
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_invalid_synonym(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_arrival_method_token("In Front Of Ship")
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_invalid_non_string(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_arrival_method_token(42)
        self.assertIn("must be a string", str(ctx.exception))


class TestDepartureMethodTokenValidatorHelper(unittest.TestCase):
    """Unit tests for the _validate_departure_method_token helper function."""

    def test_valid_hyperspace(self):
        self.assertEqual(_validate_departure_method_token("Hyperspace"), "Hyperspace")

    def test_valid_docking_bay(self):
        self.assertEqual(_validate_departure_method_token("Docking Bay"), "Docking Bay")

    def test_invalid_near_ship(self):
        """Near Ship is arrival-only and must be rejected for departure."""
        with self.assertRaises(ValueError) as ctx:
            _validate_departure_method_token("Near Ship")
        self.assertIn("Invalid departure_method", str(ctx.exception))
        self.assertIn("Near Ship", str(ctx.exception))

    def test_invalid_above_ship(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_departure_method_token("Above ship")
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_invalid_unknown_string(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_departure_method_token("Warp Gate")
        self.assertIn("Invalid departure_method", str(ctx.exception))
        self.assertIn("Allowed values", str(ctx.exception))

    def test_invalid_wrong_case(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_departure_method_token("HYPERSPACE")
        self.assertIn("Invalid departure_method", str(ctx.exception))


class TestShipRuntimeModelMethodValidation(unittest.TestCase):
    """Verify that the runtime Ship model rejects invalid method tokens."""

    def _base_ship_data(self, **overrides):
        data = {
            "name": "Test Ship",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "arrival_condition": "( true )",
            "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
        }
        data.update(overrides)
        return data

    def test_default_arrival_method_is_hyperspace(self):
        ship = Ship.model_validate(self._base_ship_data())
        self.assertEqual(ship.arrival_method, "Hyperspace")

    def test_default_departure_method_is_hyperspace(self):
        ship = Ship.model_validate(self._base_ship_data())
        self.assertEqual(ship.departure_method, "Hyperspace")

    def test_valid_arrival_methods_accepted(self):
        for method in fs_data.ALLOWED_ARRIVAL_METHODS:
            with self.subTest(method=method):
                ship = Ship.model_validate(self._base_ship_data(arrival_method=method))
                self.assertEqual(ship.arrival_method, method)

    def test_valid_departure_methods_accepted(self):
        for method in fs_data.ALLOWED_DEPARTURE_METHODS:
            with self.subTest(method=method):
                ship = Ship.model_validate(self._base_ship_data(departure_method=method))
                self.assertEqual(ship.departure_method, method)

    def test_invalid_arrival_method_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            Ship.model_validate(self._base_ship_data(arrival_method="Warp In"))
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_arrival_only_method_rejected_for_departure(self):
        with self.assertRaises(ValidationError) as ctx:
            Ship.model_validate(self._base_ship_data(departure_method="Near Ship"))
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_invalid_departure_method_case_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            Ship.model_validate(self._base_ship_data(departure_method="docking bay"))
        self.assertIn("Invalid departure_method", str(ctx.exception))


class TestWingRuntimeModelMethodValidation(unittest.TestCase):
    """Verify that the runtime Wing model rejects invalid method tokens."""

    def _base_wing_data(self, **overrides):
        ship = Ship.model_validate({
            "name": "Alpha 1",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "arrival_condition": "( true )",
            "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
        })
        data = {
            "name": "Alpha",
            "count": 1,
            "ships": [ship],
            "position": [0.0, 0.0, 0.0],
            "arrival_condition": "( true )",
        }
        data.update(overrides)
        return data

    def test_default_arrival_method_is_hyperspace(self):
        wing = Wing(**self._base_wing_data())
        self.assertEqual(wing.arrival_method, "Hyperspace")

    def test_default_departure_method_is_hyperspace(self):
        wing = Wing(**self._base_wing_data())
        self.assertEqual(wing.departure_method, "Hyperspace")

    def test_valid_arrival_methods_accepted(self):
        for method in fs_data.ALLOWED_ARRIVAL_METHODS:
            with self.subTest(method=method):
                wing = Wing(**self._base_wing_data(arrival_method=method))
                self.assertEqual(wing.arrival_method, method)

    def test_valid_departure_methods_accepted(self):
        for method in fs_data.ALLOWED_DEPARTURE_METHODS:
            with self.subTest(method=method):
                wing = Wing(**self._base_wing_data(departure_method=method))
                self.assertEqual(wing.departure_method, method)

    def test_invalid_arrival_method_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            Wing(**self._base_wing_data(arrival_method="Teleport In"))
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_arrival_only_method_rejected_for_wing_departure(self):
        with self.assertRaises(ValidationError) as ctx:
            Wing(**self._base_wing_data(departure_method="In front of ship"))
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_invalid_departure_method_case_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            Wing(**self._base_wing_data(departure_method="Hyperspace "))  # trailing space
        self.assertIn("Invalid departure_method", str(ctx.exception))


class TestFsifLoaderShipMethodValidation(unittest.TestCase):
    """Verify that the FSIF loader rejects invalid method tokens at parse time."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _load(self, arrival_method: str, departure_method: str):
        fsif_text = _MINIMAL_FSIF_TEMPLATE.format(
            ship_arrival_method=f'"{arrival_method}"',
            ship_departure_method=f'"{departure_method}"',
        )
        return _load_from_fsif_text(fsif_text)

    def test_valid_hyperspace_ship_loads(self):
        mission = self._load("Hyperspace", "Hyperspace")
        player_ship = next(s for s in mission.ships if s.name == "Player Ship")
        self.assertEqual(player_ship.arrival_method, "Hyperspace")
        self.assertEqual(player_ship.departure_method, "Hyperspace")

    def test_valid_in_front_of_ship_arrival_loads(self):
        mission = self._load("In front of ship", "Hyperspace")
        player_ship = next(s for s in mission.ships if s.name == "Player Ship")
        self.assertEqual(player_ship.arrival_method, "In front of ship")

    def test_invalid_arrival_method_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Warp Jump", "Hyperspace")
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_invalid_arrival_method_wrong_case_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("hyperspace", "Hyperspace")
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_arrival_only_method_rejected_for_ship_departure(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Hyperspace", "Near Ship")
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_arrival_only_method_above_ship_rejected_for_ship_departure(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Hyperspace", "Above ship")
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_invalid_departure_method_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Hyperspace", "Jump Gate")
        self.assertIn("Invalid departure_method", str(ctx.exception))


class TestFsifLoaderWingMethodValidation(unittest.TestCase):
    """Verify that the FSIF loader rejects invalid method tokens on wings."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _load(self, arrival_method: str, departure_method: str):
        fsif_text = _MINIMAL_FSIF_WING_TEMPLATE.format(
            wing_arrival_method=f'"{arrival_method}"',
            wing_departure_method=f'"{departure_method}"',
        )
        return _load_from_fsif_text(fsif_text)

    def test_valid_hyperspace_wing_loads(self):
        mission = self._load("Hyperspace", "Hyperspace")
        self.assertEqual(len(mission.wings), 1)
        self.assertEqual(mission.wings[0].arrival_method, "Hyperspace")

    def test_valid_above_ship_wing_arrival_loads(self):
        mission = self._load("Above ship", "Hyperspace")
        self.assertEqual(mission.wings[0].arrival_method, "Above ship")

    def test_invalid_arrival_method_rejected_for_wing(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Subspace Jump", "Hyperspace")
        self.assertIn("Invalid arrival_method", str(ctx.exception))

    def test_arrival_only_method_rejected_for_wing_departure(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Hyperspace", "In front of ship")
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_invalid_departure_method_wrong_case_rejected_for_wing(self):
        with self.assertRaises(ValueError) as ctx:
            self._load("Hyperspace", "DOCKING BAY")
        self.assertIn("Invalid departure_method", str(ctx.exception))

    def test_docking_bay_departure_valid_for_wing(self):
        """Docking Bay is a valid departure method for wings (anchor validation is a separate check)."""
        # The loader will accept the token; anchor/fighterbay checks come later.
        # This test verifies only that the token itself is not rejected.
        try:
            self._load("Hyperspace", "Docking Bay")
        except ValueError as e:
            # Only fail if the error is about an invalid departure_method token;
            # anchor/fighterbay errors are expected and acceptable here.
            if "Invalid departure_method" in str(e):
                self.fail(f"'Docking Bay' should be a valid departure_method token, but got: {e}")


if __name__ == "__main__":
    unittest.main()
