import unittest
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to allow importing modules
# FSIF_to_FS2_Converter/tests/ -> FSIF_to_FS2_Converter/
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
_repo_root = _parent_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from data_models import (
    Mission,
    Message,
    MissionInfo,
    PlayerSetup,
    Environment,
    Ship,
    Weapons,
    Briefing,
    BriefingStage,
    JumpNode,
    Wing,
    pack_ambient_light_rgb,
)
from fs2_writer import FS2Writer
from fsif_to_fs2 import sanitize_path
from mission_loader import load_mission_from_fsif
from validator import Validator
from voice_manager import VoiceManager


class CombinedTesting(unittest.TestCase):
    def make_valid_mission(self) -> Mission:
        return Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Player Ship", extra_ships=[]),
            environment=Environment(),
            ships=[
                Ship.model_validate(
                    {
                        "name": "Player Ship",
                        "class": "GTF Ulysses",
                        "team": "Friendly",
                        "location": [0.0, 0.0, 0.0],
                        "arrival_cue": "( true )",
                        "weapons": Weapons(
                            primary=["Avenger", "Avenger"],
                            secondary=["MX-50"],
                        ),
                    }
                )
            ],
        )

    def make_validator(self, mission: Mission) -> Validator:
        return Validator(mission, _repo_root)

    def test_ascii_mission_passes_validation(self):
        mission = self.make_valid_mission()

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)

    def test_non_ascii_briefing_text_is_rejected(self):
        mission = self.make_valid_mission()
        mission.briefing = Briefing(
            stages=[
                BriefingStage(text="Hold position — protect the convoy.")
            ]
        )

        validator = self.make_validator(mission)

        self.assertFalse(validator.validate())
        self.assertTrue(
            any(
                "briefing.stages[0].text" in error and "U+2014" in error
                for error in validator.errors
            ),
            validator.errors,
        )

    def test_voice_style_instructions_are_excluded_from_ascii_validation(self):
        mission = self.make_valid_mission()
        mission.briefing = Briefing(
            stages=[
                BriefingStage(
                    text="Hold position and protect the convoy.",
                    voice_style_instructions="Calm — authoritative",
                )
            ]
        )

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)

    def test_distance_over_20km_between_objects_warns(self):
        mission = self.make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="Far Node", position=[25000.0, 0.0, 0.0])
        ]

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: 1 object pair(s) exceed" in warning
                and "Ship 'Player Ship' <-> Jump Node 'Far Node'" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_arrival_distance_over_20km_warns_for_ship_and_wing(self):
        mission = self.make_valid_mission()
        mission.ships.append(
            Ship.model_validate(
                {
                    "name": "Escort 1",
                    "class": "GTC Fenris",
                    "team": "Friendly",
                    "location": [500.0, 0.0, 0.0],
                    "arrival_location": "In front of ship",
                    "arrival_anchor": "Player Ship",
                    "arrival_distance": 25001,
                    "arrival_cue": "( true )",
                }
            )
        )
        mission.wings = [
            Wing(
                name="Beta",
                count=1,
                ships=[
                    Ship.model_validate(
                        {
                            "name": "Beta 1",
                            "class": "GTF Ulysses",
                            "team": "Friendly",
                            "location": [1000.0, 0.0, 0.0],
                            "arrival_cue": "( true )",
                            "weapons": Weapons(
                                primary=["Avenger", "Avenger"],
                                secondary=["MX-50"],
                            ),
                        }
                    )
                ],
                position=[1000.0, 0.0, 0.0],
                arrival_location="In front of ship",
                arrival_anchor="Player Ship",
                arrival_distance=22000,
                arrival_cue="( true )",
            )
        ]

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: Ship 'Escort 1' arrival_distance 25001 m" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )
        self.assertTrue(
            any(
                "Mission scale recommendation: Wing 'Beta' arrival_distance 22000 m" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_distance_and_arrival_distance_at_20km_do_not_warn(self):
        mission = self.make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="Limit Node", position=[20000.0, 0.0, 0.0])
        ]
        mission.ships.append(
            Ship.model_validate(
                {
                    "name": "Escort 1",
                    "class": "GTC Fenris",
                    "team": "Friendly",
                    "location": [500.0, 0.0, 0.0],
                    "arrival_location": "In front of ship",
                    "arrival_anchor": "Player Ship",
                    "arrival_distance": 20000,
                    "arrival_cue": "( true )",
                }
            )
        )

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any("Mission scale recommendation:" in warning for warning in validator.warnings),
            validator.warnings,
        )

    def test_3d_mission_design_warns_when_all_objects_on_xz_plane(self):
        mission = self.make_valid_mission()
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission design recommendation: All objects are placed on the 2D XZ plane (Y=0)" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_3d_mission_design_does_not_warn_when_objects_spread_in_y(self):
        mission = self.make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="High Node", position=[0.0, 500.0, 0.0])
        ]
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "Mission design recommendation: All objects are placed on the 2D XZ plane (Y=0)" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_writer_always_emits_fixed_fog_multipliers(self):
        mission = self.make_valid_mission()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("+Fog Near Mult: 1.000000", content)
        self.assertIn("+Fog Far Mult: 1.000000", content)

    def test_pack_ambient_light_rgb_helper(self):
        self.assertEqual(pack_ambient_light_rgb([0, 0, 0]), 0)
        self.assertEqual(pack_ambient_light_rgb([10, 10, 10]), 657930)
        self.assertEqual(pack_ambient_light_rgb([255, 255, 255]), 16777215)

    def test_writer_packs_rgb_ambient_light_into_fs2_integer(self):
        mission = self.make_valid_mission()
        mission.environment = Environment(ambient_light_level=[10, 10, 10])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("$Ambient light level: 657930", content)

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
      location: [0, 0, 0]
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

        self.assertIn("accepts FSIF version '2.8' only", str(ctx.exception))

    def test_loader_rejects_packed_ambient_light_in_fsif_27(self):
        fsif_text = """fsif_version: \"2.8\"

mission_info:
  name: "Invalid Ambient"

player_setup:
  start_ship: "Player Ship"

entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
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
            fsif_path = Path(tmpdir) / "invalid_ambient_26.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("FSIF requires environment.ambient_light_level to be authored as [red, green, blue]", str(ctx.exception))

    def test_loader_rejects_arrival_delay_in_ship_template(self):
        fsif_text = """fsif_version: "2.8"

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
      location: [0, 0, 0]
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
        self.assertIn("must not be authored in ship_templates", str(ctx.exception))

    def test_environment_rejects_invalid_rgb_channel_range(self):
        with self.assertRaises(ValueError) as ctx:
            Environment(ambient_light_level=[256, 0, 0])

        self.assertIn("out of range 0..255", str(ctx.exception))

    def test_environment_rejects_invalid_rgb_shape(self):
        with self.assertRaises(ValueError) as ctx:
            Environment(ambient_light_level=[10, 10])

        self.assertIn("3-item RGB list", str(ctx.exception))

    def test_environment_rejects_packed_integer_input(self):
        with self.assertRaises(ValueError) as ctx:
            Environment.model_validate({"ambient_light_level": 657930})

        self.assertIn("ambient_light_level must be authored as [red, green, blue]", str(ctx.exception))

    def test_sanitize_path_preserves_spaces(self):
        raw = 'missions\\ambient light testing\\white.fsif'
        self.assertEqual(sanitize_path(raw), raw)

    def test_sanitize_path_strips_only_outer_quotes(self):
        raw = '"missions\\ambient light testing\\white.fsif"'
        self.assertEqual(sanitize_path(raw), 'missions\\ambient light testing\\white.fsif')


class VoiceManagerTesting(unittest.TestCase):
    def setUp(self):
        self.mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(extra_ships=[]),
            environment=Environment(),
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fsif_path = Path(self.temp_dir.name) / "dummy.fsif"
        self.tts_settings = {"mode": "unique"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_determinism(self):
        """Test that re-running with same input produces same filenames (determinism)."""
        self.mission.messages = [
            Message(name="Alpha", message="Msg 1", voice_name="Voice1"),
            Message(name="Alpha", message="Msg 2", voice_name="Voice1"),
            Message(name="Alpha", message="Msg 3", voice_name="Voice1"),
        ]

        vm1 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm1.process()
        filenames1 = [m.voice_filename for m in self.mission.messages]

        for m in self.mission.messages:
            m.voice_filename = None

        vm2 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm2.process()
        filenames2 = [m.voice_filename for m in self.mission.messages]

        self.assertEqual(filenames1, filenames2, "Filenames should be deterministic across runs")
        self.assertEqual(filenames1, ["alpha.wav", "alpha_1.wav", "alpha_2.wav"])

    def test_length_limit_simple(self):
        """Test strict truncation to 25 chars for stem."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit"
        self.mission.messages = [
            Message(name=long_name, message="Msg", voice_name="Voice1")
        ]

        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        fname = self.mission.messages[0].voice_filename
        self.assertIsNotNone(fname)
        assert fname is not None
        self.assertTrue(len(fname) <= 29, f"Filename '{fname}' exceeds 29 chars")
        self.assertTrue(fname.endswith(".wav"))
        self.assertEqual(fname, "this_is_a_very_long_name_.wav")

    def test_length_limit_collision(self):
        """Test truncation when suffix is added."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit"
        self.mission.messages = [
            Message(name=long_name, message="Msg 1", voice_name="Voice1"),
            Message(name=long_name, message="Msg 2", voice_name="Voice1"),
            Message(name=long_name, message="Msg 3", voice_name="Voice1"),
        ]

        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        fnames = [m.voice_filename for m in self.mission.messages]

        for fn in fnames:
            self.assertIsNotNone(fn)
            assert fn is not None
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")

        self.assertEqual(fnames[0], "this_is_a_very_long_name_.wav")
        self.assertEqual(fnames[1], "this_is_a_very_long_nam_1.wav")
        self.assertEqual(fnames[2], "this_is_a_very_long_nam_2.wav")

    def test_extreme_suffix(self):
        """Test logic with longer suffixes (e.g. _10)."""
        long_name = "test_limit"
        msgs = [
            Message(name=long_name, message=f"Msg {i}", voice_name="Voice1")
            for i in range(12)
        ]

        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        self.assertEqual(msgs[11].voice_filename, "test_limit_11.wav")

        vlong = "aaaaaaaaaaaaaaaaaaaaaaaaa"
        msgs = [
            Message(name=vlong, message=f"Msg {i}", voice_name="Voice1")
            for i in range(12)
        ]

        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        self.assertEqual(msgs[0].voice_filename, "a" * 25 + ".wav")
        self.assertEqual(msgs[1].voice_filename, "a" * 23 + "_1.wav")
        self.assertEqual(msgs[10].voice_filename, "a" * 22 + "_10.wav")

        for fn in [m.voice_filename for m in msgs]:
            self.assertIsNotNone(fn)
            assert fn is not None
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")


if __name__ == '__main__':
    unittest.main()