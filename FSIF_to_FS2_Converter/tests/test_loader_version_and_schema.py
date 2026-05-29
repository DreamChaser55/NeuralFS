"""Tests for FSIF loader version enforcement and schema rejection.

Covers:
- FSIF 2.6 (unsupported version) is rejected with a clear version error.
- An old-version FSIF with many legacy field names fails on the version check,
  NOT with a wall of Pydantic 'Extra inputs are not permitted' errors.
  (Regression guard: version check must fire before schema validation.)
- FSIF 1.0 with a packed integer ambient_light_level is rejected.
- Invalid AI player orders and invalid cruiser goal fail SEXP validation.
- arrival_delay inside a ship template is rejected by the schema.
"""

import sys
import tempfile
import unittest
from pathlib import Path

from mission_loader import load_mission_from_fsif
from _fsif_test_helpers import SilencedTestCase, REPO_ROOT


class LoaderVersionAndSchemaTesting(SilencedTestCase):

    def test_loader_rejects_fsif_26(self):
        fsif_text = """fsif_version: \"2.6\"

mission_info:
  name: "Legacy Mission"

player_setup:
  start_ship: "Player Ship"

entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

mission_flow: {}

environment:
  ambient_light_level: 657930
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "legacy_version.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("accepts FSIF version '1.0' only", str(ctx.exception))

    def test_old_version_fsif_fails_with_version_error_not_pydantic_wall(self):
        """
        Regression test: a FSIF file with an old version number AND many
        renamed/legacy field names must fail with a clean unsupported-version
        error, NOT with a wall of Pydantic 'Extra inputs are not permitted'
        errors caused by incompatible field names.

        This verifies that _validate_version() runs before _validate_fsif_schema()
        in MissionLoader.load().
        """
        fsif_text = """fsif_version: "0.5"

mission_info:
  name: "Old Legacy Mission"

environment:
  ambient_light_level: [0, 0, 0]
  starbitmaps: []

player_setup:
  start_ship: "Player Ship"
  extra_weapons:
    - "Hornet"
  extra_ships:
    - {class: "GTF Ulysses", count: 4}

entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: |
        ( true )
      ai_goals: |
        ( ai-chase-any 89 )

mission_flow:
  events:
    - formula: |
        ( when ( true ) ( do-nothing ) )
      directive_text: "Old directive text field"
  goals:
    - name: "Old Goal"
      message: "Old goal text field"
      formula: |
        ( true )
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "old_version.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        error_msg = str(ctx.exception)

        self.assertIn("Unsupported fsif_version '0.5'", error_msg)
        self.assertIn("accepts FSIF version '1.0' only", error_msg)

        self.assertNotIn("FSIF document validation error", error_msg,
                         "Schema validation ran before version check — Pydantic error wall was not suppressed.")
        self.assertNotIn("Extra inputs are not permitted", error_msg,
                         "Schema validation ran before version check — legacy field names triggered Pydantic errors.")

    def test_loader_rejects_packed_ambient_light_in_fsif_10(self):
        fsif_text = """fsif_version: \"1.0\"

mission_info:
  name: "Invalid Ambient"

player_setup:
  start_ship: "Player Ship"

entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

mission_flow: {}

environment:
  ambient_light_level: 10
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "invalid_ambient.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("FSIF requires environment.ambient_light_level to be authored as [red, green, blue]", str(ctx.exception))

    def test_validator_rejects_invalid_ai_orders_and_goals(self):
        fsif_text = """
fsif_version: "1.0"
mission_info:
  name: "Invalid Orders Demo"
player_setup:
  start_ship: "Player Ship"
entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
    - name: "Cruiser 1"
      class: "GTC Fenris"
      team: "Hostile"
      position: [0, 0, 0]
      initial_orders: |
        ( ai-guard "Player Ship" 89 )
mission_flow:
  events:
    - formula: '( set-player-orders "Player Ship" ( true ) "Do a barrel roll" )'
environment:
  ambient_light_level: [0, 0, 0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "invalid_orders.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            mission = load_mission_from_fsif(str(fsif_path))

            adv_val_dir = REPO_ROOT / "FSIF_to_FS2_Converter" / "Advanced_SEXP_Validator"
            if str(adv_val_dir) not in sys.path:
                sys.path.insert(0, str(adv_val_dir))
            import advanced_sexp_validator
            is_valid = advanced_sexp_validator.validate_mission(mission)
            self.assertFalse(
                is_valid,
                "Expected advanced SEXP validation to fail due to invalid player order and invalid cruiser goal.",
            )

    def test_loader_rejects_arrival_delay_in_ship_template(self):
        fsif_text = """fsif_version: "1.0"

mission_info:
  name: "Invalid Template Arrival Delay"

player_setup:
  start_ship: "Player Ship"

entities:
  ship_templates:
    fighter_template:
      class: "GTF Ulysses"
      team: "Friendly"
      arrival_delay: 5
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  ships:
    - name: "Player Ship"
      template: "fighter_template"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )

mission_flow: {}

environment:
  ambient_light_level: [0, 0, 0]
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "invalid_template_arrival_delay.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("arrival_delay", str(ctx.exception))
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
