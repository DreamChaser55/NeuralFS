"""Tests for the optional nebula.pattern field and nebula storm token.

Covers:
- Authoring nebula.enabled: true without a pattern must succeed (loading and validation).
- The FS2 writer emits '+Neb2: ' (empty value) when pattern is None.
- An explicit pattern is preserved and emitted verbatim.
- The fullneb flag is auto-injected even when pattern is omitted.
- cloud_sprites still produce '+Neb2 Poofs List' even when pattern is absent.
- '+Neb2' is absent from the output when nebula.enabled is false.
- storm defaults to 'none' when omitted.
- Writer emits '+Storm: none' by default.
- Explicitly authored storm token is preserved and emitted.
- Invalid storm tokens fail validation with a clear error.
- All canonical storm tokens pass validation.
- Invalid storm token is rejected even when nebula.enabled is false.
"""

import tempfile
import unittest
from pathlib import Path

from data_models import Mission
from fs2_writer import FS2Writer
from mission_loader import load_mission_from_fsif
from validator import Validator
from _fsif_test_helpers import SilencedTestCase, REPO_ROOT


_MINIMAL_NEBULA_FSIF_TEMPLATE = """\
fsif_version: "1.0"
mission_info:
  name: "Nebula Pattern Test"
environment:
  ambient_light_level: [5, 5, 5]
  background_bitmaps: []
  nebula:
    enabled: true
    {extra_fields}
player_setup:
  start_ship: "Alpha 1"
entities:
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
mission_flow: {{}}
"""


class NebulaPatternTesting(SilencedTestCase):

    def _write_and_load(self, extra_fields: str) -> Mission:
        fsif_text = _MINIMAL_NEBULA_FSIF_TEMPLATE.format(extra_fields=extra_fields)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nebula_test.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def _write_and_load_disabled(self, extra_fields: str) -> Mission:
        """Variant that loads a mission where nebula.enabled is false."""
        fsif_text = _MINIMAL_NEBULA_FSIF_TEMPLATE.format(extra_fields=extra_fields).replace(
            "enabled: true", "enabled: false"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nebula_disabled_test.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def _write_fs2(self, mission: Mission) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            return out.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Loading tests
    # ------------------------------------------------------------------

    def test_load_succeeds_without_pattern(self):
        """enabled: true with no pattern must load without error."""
        mission = self._write_and_load("sensor_range: 2000.0")
        self.assertIsNone(mission.environment.nebula.pattern)
        self.assertTrue(mission.environment.nebula.enabled)

    def test_load_succeeds_with_explicit_pattern(self):
        """enabled: true with an explicit pattern must load and preserve it."""
        mission = self._write_and_load('pattern: "nbackblue1"')
        self.assertEqual(mission.environment.nebula.pattern, "nbackblue1")

    def test_fullneb_flag_injected_without_pattern(self):
        """The fullneb flag must be auto-injected even when pattern is omitted."""
        mission = self._write_and_load("sensor_range: 2000.0")
        flags_lower = [f.strip().lower() for f in mission.mission_info.flags]
        self.assertIn("fullneb", flags_lower)

    # ------------------------------------------------------------------
    # Writer emission tests
    # ------------------------------------------------------------------

    def test_writer_emits_empty_neb2_without_pattern(self):
        """Writer must emit '+Neb2: ' (with empty value) when pattern is None."""
        mission = self._write_and_load("sensor_range: 2000.0")
        content = self._write_fs2(mission)
        self.assertIn("+Neb2: ", content,
                      "Expected '+Neb2: ' (empty value) in fs2 output when no pattern authored")

    def test_writer_emits_pattern_token_when_provided(self):
        """Writer must emit '+Neb2: nbackblue1' when pattern is explicitly set."""
        mission = self._write_and_load('pattern: "nbackblue1"')
        content = self._write_fs2(mission)
        self.assertIn("+Neb2: nbackblue1", content)

    def test_writer_emits_poofs_list_without_pattern(self):
        """cloud_sprites should still produce +Neb2 Poofs List even if pattern is absent."""
        mission = self._write_and_load('cloud_sprites: ["PoofPurp01", "PoofPurp02"]')
        content = self._write_fs2(mission)
        self.assertIn("+Neb2 Poofs List:", content)
        self.assertIn('"PoofPurp01"', content)

    def test_writer_neb2_absent_when_nebula_disabled(self):
        """When nebula.enabled is false, +Neb2 must not appear in the output."""
        fsif_text = """\
fsif_version: "1.0"
mission_info:
  name: "No Nebula"
environment:
  ambient_light_level: [0, 0, 0]
  nebula:
    enabled: false
player_setup:
  start_ship: "Alpha 1"
entities:
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
mission_flow: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "no_nebula.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(path))
        content = self._write_fs2(mission)
        self.assertNotIn("+Neb2", content)

    # ------------------------------------------------------------------
    # Validator tests
    # ------------------------------------------------------------------

    def test_validator_passes_enabled_nebula_without_pattern(self):
        """Validator must accept enabled nebula with no pattern authored."""
        mission = self._write_and_load("sensor_range: 2000.0")
        validator = Validator(mission, REPO_ROOT)
        self.assertTrue(validator.validate(), validator.errors)

    def test_validator_rejects_invalid_explicit_pattern(self):
        """An unrecognised pattern token must still fail validation."""
        mission = self._write_and_load('pattern: "NOT_A_REAL_PATTERN"')
        validator = Validator(mission, REPO_ROOT)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("nebula pattern" in e.lower() for e in validator.errors),
            f"Expected pattern validation error, got: {validator.errors}",
        )

    # ------------------------------------------------------------------
    # Storm default tests
    # ------------------------------------------------------------------

    def test_storm_default_is_none_when_omitted(self):
        """Omitting storm in a full-nebula mission must default to 'none'."""
        mission = self._write_and_load("sensor_range: 2000.0")
        self.assertEqual(
            mission.environment.nebula.storm,
            "none",
            "Expected default storm to be 'none' when not authored",
        )

    def test_writer_emits_storm_none_by_default(self):
        """Writer must emit '+Storm: none' when storm is not explicitly set."""
        mission = self._write_and_load("sensor_range: 2000.0")
        content = self._write_fs2(mission)
        self.assertIn("+Storm: none", content,
                      "Expected '+Storm: none' in fs2 output when storm not authored")

    def test_explicit_storm_value_is_preserved(self):
        """An explicitly authored storm token must be preserved and emitted verbatim."""
        mission = self._write_and_load('storm: "s_medium"')
        self.assertEqual(mission.environment.nebula.storm, "s_medium")
        content = self._write_fs2(mission)
        self.assertIn("+Storm: s_medium", content,
                      "Expected '+Storm: s_medium' in fs2 output when storm: s_medium is authored")

    def test_validator_rejects_invalid_storm_token(self):
        """An unrecognised storm token must fail validation with a clear error message."""
        mission = self._write_and_load('storm: "s_heavy"')
        validator = Validator(mission, REPO_ROOT)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("storm" in e.lower() and "s_heavy" in e for e in validator.errors),
            f"Expected invalid storm token error mentioning 's_heavy', got: {validator.errors}",
        )

    def test_validator_accepts_all_valid_storm_tokens(self):
        """Every canonical storm token must pass validation."""
        for token in ("none", "s_standard", "s_medium", "s_active", "s_emp"):
            with self.subTest(storm=token):
                mission = self._write_and_load(f'storm: "{token}"')
                validator = Validator(mission, REPO_ROOT)
                self.assertTrue(
                    validator.validate(),
                    f"Expected storm token '{token}' to pass validation, got errors: {validator.errors}",
                )

    def test_validator_rejects_invalid_storm_token_when_nebula_disabled(self):
        """An invalid storm token must be rejected even when nebula.enabled is false."""
        mission = self._write_and_load_disabled('storm: "bogus_storm"')
        validator = Validator(mission, REPO_ROOT)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("storm" in e.lower() for e in validator.errors),
            f"Expected storm validation error for disabled nebula, got: {validator.errors}",
        )


if __name__ == "__main__":
    unittest.main()
