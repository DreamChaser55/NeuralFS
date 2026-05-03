import sys
import tempfile
import unittest
from pathlib import Path


_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from mission_loader import load_mission_from_fsif


MINIMAL_FSIF_4 = """fsif_version: "4.0"
mission_info:
  name: "Legacy Key Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Player Ship"
entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: |
        ( true )
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
mission_flow: {}
"""


class FSIF40LegacyKeyTests(unittest.TestCase):
    def _write_and_load(self, fsif_text: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "mission.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def assert_legacy_key_rejected(self, fsif_text: str, old_key: str, new_key: str):
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        msg = str(ctx.exception)
        self.assertIn("FSIF raw document validation error", msg)
        self.assertIn(f"Extra inputs are not permitted [type=extra_forbidden", msg)

    def test_accepts_minimal_fsif_4_keys(self):
        mission = self._write_and_load(MINIMAL_FSIF_4)
        self.assertEqual(mission.player_setup.start_ship, "Player Ship")

    def test_rejects_legacy_player_setup_extra_weapons(self):
        fsif_text = MINIMAL_FSIF_4.replace(
            'player_setup:\n  start_ship: "Player Ship"',
            'player_setup:\n  start_ship: "Player Ship"\n  extra_weapons: ["Hornet"]',
        )
        self.assert_legacy_key_rejected(fsif_text, "extra_weapons", "additional_weapons")

    def test_rejects_legacy_ship_arrival_cue(self):
        fsif_text = MINIMAL_FSIF_4.replace("arrival_condition", "arrival_cue")
        self.assert_legacy_key_rejected(fsif_text, "arrival_cue", "arrival_condition")


if __name__ == "__main__":
    unittest.main()