"""
Tests for the FSIF 1.0 schema validation (the current public release).

Verifies:
- Valid FSIF 1.0 files load without errors.
- The converter rejects unknown/extra field names generically (extra='forbid').
- The converter rejects files with wrong version strings.
"""
import sys
import tempfile
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
_repo_root = _converter_dir.parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from mission_loader import load_mission_from_fsif


# ---------------------------------------------------------------------------
# Minimal valid FSIF 1.0 fixture
#
# Uses an Alpha wing so that the fixture is both schema-valid (loads without
# errors) AND conversion-valid (passes full validator).
# player_setup.start_ship must always be a member of a Friendly Alpha, Beta,
# or Gamma wing — standalone player starts are a hard validation error.
# ---------------------------------------------------------------------------

MINIMAL_FSIF_1 = """fsif_version: "1.0"
mission_info:
  name: "Schema Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
mission_flow: {}
"""

MINIMAL_FSIF_1_WITH_DOCKED_SHIP = """fsif_version: "1.0"
mission_info:
  name: "Dock Schema Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
  ships:
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      position: [600, 0, 0]
      arrival_cue: |
        ( true )
    - name: "GTT Elysium 1"
      class: "GTT Elysium"
      team: "Friendly"
      position: [540, 0, 20]
      arrival_cue: |
        ( false )
      dock:
        dockee: "GTC Fenris 1"
        docker_point: "topside docking"
        dockee_point: "Docking bay 1"
mission_flow: {}
"""


class FSIF10SchemaTests(unittest.TestCase):
    """Tests for the FSIF 1.0 schema."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _write_and_load(self, fsif_text: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "mission.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    # -------------------------------------------------------------------------
    # Positive: valid FSIF 1.0 files should load without errors
    # -------------------------------------------------------------------------

    def test_accepts_minimal_fsif_1_0(self):
        """A minimal valid FSIF 1.0 file loads without errors."""
        mission = self._write_and_load(MINIMAL_FSIF_1)
        self.assertEqual(mission.player_setup.start_ship, "Alpha 1")

    def test_accepts_valid_dock_block(self):
        """A valid FSIF 1.0 dock block (using 'dockee') loads without errors."""
        mission = self._write_and_load(MINIMAL_FSIF_1_WITH_DOCKED_SHIP)
        docked_ship = next(s for s in mission.ships if s.name == "GTT Elysium 1")
        self.assertEqual(docked_ship.docked_with, "GTC Fenris 1")
        self.assertEqual(docked_ship.docker_point, "topside docking")
        self.assertEqual(docked_ship.dockee_point, "Docking bay 1")

    # -------------------------------------------------------------------------
    # Negative: wrong version strings must be rejected cleanly
    # -------------------------------------------------------------------------

    def test_rejects_wrong_version_string(self):
        """Current version: "1.0". Any non-1.0 version string must be rejected with a version mismatch error."""
        for bad_version in ("2.0", "3.0", "4.0", "1.1", "0.9"):
            with self.subTest(version=bad_version):
                fsif_text = MINIMAL_FSIF_1.replace(
                    'fsif_version: "1.0"',
                    f'fsif_version: "{bad_version}"',
                )
                with self.assertRaises(ValueError) as ctx:
                    self._write_and_load(fsif_text)
                msg = str(ctx.exception)
                self.assertIn("accepts FSIF version '1.0' only", msg)
                self.assertNotIn("Extra inputs are not permitted", msg,
                                 f"Schema ran before version check for version '{bad_version}'")

    def test_rejects_missing_version(self):
        """A file without fsif_version must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace('fsif_version: "1.0"\n', "")
        with self.assertRaises(ValueError):
            self._write_and_load(fsif_text)

    # -------------------------------------------------------------------------
    # Negative: unknown field names must be rejected by extra='forbid'
    # -------------------------------------------------------------------------

    def test_rejects_unknown_top_level_field(self):
        """An unknown top-level field must be rejected by schema validation."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "mission_flow: {}",
            "mission_flow: {}\nunknown_top_level_field: true",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_ship_field(self):
        """An unknown field on a standalone ship must be rejected by schema validation.
        Uses MINIMAL_FSIF_1_WITH_DOCKED_SHIP which contains standalone ships."""
        # Inject an unknown field into the standalone GTC Fenris 1 ship entry
        fsif_text = MINIMAL_FSIF_1_WITH_DOCKED_SHIP.replace(
            '      arrival_cue: |',
            '      unknown_ship_field: 42\n      arrival_cue: |',
            1,  # replace only the first occurrence (GTC Fenris 1)
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_template_field(self):
        """An unknown field in a ship template must be rejected (templates use extra='forbid')."""
        # Add an unknown field directly into the existing alpha_t template
        fsif_text = MINIMAL_FSIF_1.replace(
            '      class: "GTF Ulysses"',
            '      class: "GTF Ulysses"\n      unknown_tmpl_field: 99',
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_arrival_delay_in_template(self):
        """arrival_delay in a ship template must be rejected (never valid in templates)."""
        # Inject arrival_delay directly into the existing alpha_t template
        fsif_text = MINIMAL_FSIF_1.replace(
            '      class: "GTF Ulysses"',
            '      class: "GTF Ulysses"\n      arrival_delay: 5',
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        msg = str(ctx.exception)
        self.assertIn("arrival_delay", msg)
        self.assertIn("Extra inputs are not permitted", msg)

    def test_rejects_dock_with_unknown_subkey(self):
        """A dock block with an unknown sub-key must be rejected."""
        fsif_text = MINIMAL_FSIF_1_WITH_DOCKED_SHIP.replace(
            '        dockee: "GTC Fenris 1"',
            '        unknown_dock_key: "GTC Fenris 1"',
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_nebula_field(self):
        """An unknown nebula field must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  nebula:\n    enabled: false\n    unknown_nebula_param: 123",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_asteroid_field_key(self):
        """An unknown key inside asteroid_field must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  asteroid_field:\n    unknown_af_key: asteroid",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_reinforcement_field(self):
        """An unknown key in a reinforcement entry must be rejected."""
        # Inject a reinforcement_ships entry with an unknown field before the wings section
        fsif_text = MINIMAL_FSIF_1.replace(
            "  wings:",
            "  reinforcement_ships:\n    - name: \"Alpha 1\"\n      unknown_reinf_key: 1\n  wings:",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_event_field(self):
        """An unknown field in an event must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "mission_flow: {}",
            "mission_flow:\n  events:\n    - name: TestEvent\n      formula: |\n        ( when ( true ) ( do-nothing ) )\n      unknown_event_key: \"value\"",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_message_field(self):
        """An unknown field in a message must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "mission_flow: {}",
            "mission_flow:\n  messages:\n    - name: TestMsg\n      text: \"Hello\"\n      unknown_msg_key: \"value\"",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_briefing_icon_field(self):
        """An unknown field in a briefing icon must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "mission_flow: {}",
            'mission_flow:\n  briefing:\n    stages:\n      - text: "Stage text"\n        icons:\n          - {icon_type: "Fighter", team: "Hostile", display_class: "GTF Ulysses", map_position: [0, 0], unknown_icon_key: "bad"}',
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_rejects_unknown_debriefing_field(self):
        """An unknown field in a debriefing stage must be rejected."""
        fsif_text = MINIMAL_FSIF_1.replace(
            "mission_flow: {}",
            "mission_flow:\n  debriefing:\n    stages:\n      - text: \"Debrief text\"\n        unknown_debrief_key: \"bad\"",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
