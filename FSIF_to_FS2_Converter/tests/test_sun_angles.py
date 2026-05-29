"""Tests for the 2-element [pitch, heading] sun angles schema.

Suns are rotationally symmetric sprites, so bank has no visible effect.
FSIF therefore uses [pitch, heading] for suns and the writer hardcodes
bank = 0.0 in the +Angles line it emits. Background bitmaps still use
the full 3-element [pitch, bank, heading] format.

Covers:
- Sun model accepts a valid [pitch, heading] list.
- Sun model rejects the old [pitch, bank, heading] 3-value format.
- Sun model rejects single-element and None angles.
- BackgroundBitmap model continues to accept [pitch, bank, heading].
- BackgroundBitmap model rejects a 2-element list.
- FS2 writer emits hardcoded bank=0.0 for sun +Angles.
- FS2 writer still emits authored bank for background bitmaps.
- Validator warns when a sun has angles [0, 0] (directly in front).
- Validator does not warn for non-zero sun angles.
- End-to-end: FSIF with 2-value sun angles loads correctly and produces valid FS2.
- FSIF with old 3-value sun angles is rejected by the loader.
"""

import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from data_models import (
    BackgroundBitmap,
    Environment,
    Mission,
    MissionInfo,
    PlayerSetup,
    Ship,
    Sun,
    Weapons,
)
from fs2_writer import FS2Writer
from mission_loader import load_mission_from_fsif
from validator import Validator
from _fsif_test_helpers import SilencedTestCase, REPO_ROOT


class SunAnglesTesting(SilencedTestCase):

    # ------------------------------------------------------------------
    # Sun model: valid / invalid element counts
    # ------------------------------------------------------------------

    def test_sun_accepts_two_element_angles(self):
        """Sun model must accept a valid [pitch, heading] list."""
        s = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        self.assertEqual(s.angles, [0.087266, 2.356194])

    def test_sun_rejects_three_element_angles(self):
        """Sun model must reject the old [pitch, bank, heading] 3-value format."""
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 0.0, 2.356194]})

    def test_sun_rejects_one_element_angles(self):
        """Sun model must reject a single-element angles list."""
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": [0.5]})

    def test_sun_rejects_none_angles(self):
        """Sun model must reject None for angles."""
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": None})

    # ------------------------------------------------------------------
    # BackgroundBitmap must remain 3-element
    # ------------------------------------------------------------------

    def test_background_bitmap_still_accepts_three_element_angles(self):
        """BackgroundBitmap model must continue to accept [pitch, bank, heading]."""
        b = BackgroundBitmap.model_validate(
            {"texture": "neb02", "angles": [0.0, 2.321286, 0.0]}
        )
        self.assertEqual(len(b.angles), 3)

    def test_background_bitmap_rejects_two_element_angles(self):
        """BackgroundBitmap model must reject a 2-element angles list."""
        with self.assertRaises((ValidationError, ValueError)):
            BackgroundBitmap.model_validate(
                {"texture": "neb02", "angles": [0.0, 2.321286]}
            )

    # ------------------------------------------------------------------
    # FS2 writer emission: bank must be hardcoded to 0.0
    # ------------------------------------------------------------------

    def test_writer_emits_hardcoded_bank_zero_for_sun(self):
        """FS2 writer must emit '+Angles: <pitch> 0.000000 <heading>' for suns."""
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        mission = Mission(
            mission_info=MissionInfo(name="Sun Emit Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(ambient_light_level=[0, 0, 0], suns=[sun]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            content = out.read_text(encoding="utf-8")

        self.assertIn("+Angles: 0.087266 0.000000 2.356194", content,
                      "Expected sun +Angles line with hardcoded bank=0.000000")

    def test_writer_background_bitmap_still_emits_authored_bank(self):
        """FS2 writer must still emit the authored bank value for background bitmaps."""
        bm = BackgroundBitmap.model_validate(
            {"texture": "neb02", "angles": [0.4, 1.2, 0.3], "scale": 1.0}
        )
        mission = Mission(
            mission_info=MissionInfo(name="Bitmap Emit Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(ambient_light_level=[0, 0, 0], background_bitmaps=[bm]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            content = out.read_text(encoding="utf-8")

        self.assertIn("+Angles: 0.400000 1.200000 0.300000", content,
                      "Expected background bitmap +Angles to include authored bank value")

    # ------------------------------------------------------------------
    # Validator: direct-front sun warning [0, 0]
    # ------------------------------------------------------------------

    def test_validator_warns_for_sun_at_zero_zero(self):
        """Validator must warn when a sun has angles [0, 0] (directly in front)."""
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.0, 0.0]})
        mission = Mission(
            mission_info=MissionInfo(name="Sun Warning Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(ambient_light_level=[0, 0, 0], suns=[sun]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            any("angles [0, 0]" in w or "[0, 0]" in w for w in validator.warnings),
            f"Expected sun direct-front warning mentioning '[0, 0]', got: {validator.warnings}",
        )

    def test_validator_no_warning_for_sun_at_nonzero_angles(self):
        """Validator must not warn when sun angles are non-zero."""
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        mission = Mission(
            mission_info=MissionInfo(name="Sun OK Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(ambient_light_level=[0, 0, 0], suns=[sun]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertFalse(
            any("[0, 0]" in w for w in validator.warnings),
            f"Expected no sun direct-front warning for non-zero angles, got: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # End-to-end: FSIF round-trip through loader and writer
    # ------------------------------------------------------------------

    def test_fsif_sun_two_angle_roundtrip(self):
        """FSIF with 2-value sun angles must load correctly and produce valid FS2."""
        fsif_text = """\
fsif_version: "1.0"
mission_info:
  name: "Sun Roundtrip"
environment:
  ambient_light_level: [0, 0, 0]
  suns:
    - texture: SunVega
      angles: [0.087266, 2.356194]
      scale: 1.5
  background_bitmaps:
    - texture: neb02
      angles: [0.0, 2.321286, 0.0]
      scale: 1.0
    - texture: neb11
      angles: [0.4, 0.6, 0.1]
      scale: 1.0
    - texture: neb12
      angles: [0.8, 1.2, 0.5]
      scale: 1.0
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
      arrival_cue: |
        ( true )
mission_flow: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "sun_rt.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(fsif_path))

            self.assertEqual(len(mission.environment.suns), 1)
            self.assertEqual(len(mission.environment.suns[0].angles), 2,
                             "Expected Sun.angles to have exactly 2 elements after loading")

            out = Path(tmpdir) / "sun_rt.fs2"
            FS2Writer(mission, str(out)).write_mission()
            content = out.read_text(encoding="utf-8")

        self.assertIn("+Angles: 0.087266 0.000000 2.356194", content,
                      "Expected sun +Angles with bank=0.000000 in FS2 output")

    def test_fsif_three_value_sun_angles_rejected(self):
        """FSIF with old 3-value sun angles must be rejected by the loader."""
        fsif_text = """\
fsif_version: "1.0"
mission_info:
  name: "Bad Sun"
environment:
  ambient_light_level: [0, 0, 0]
  suns:
    - texture: SunVega
      angles: [0.087266, 0.000000, 2.356194]
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
      arrival_cue: |
        ( true )
mission_flow: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "bad_sun.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_mission_from_fsif(str(fsif_path))


if __name__ == "__main__":
    unittest.main()
