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
    MissionInfo,
    PlayerSetup,
    Environment,
    Ship,
    Weapons,
    Briefing,
    BriefingStage,
    JumpNode,
    Wing,
)
from fs2_writer import FS2Writer
from mission_loader import load_mission_from_fsif
from validator import Validator


class TestValidatorAscii(unittest.TestCase):
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
                "Mission scale recommendation: distance between Ship 'Player Ship' and Jump Node 'Far Node'" in warning
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

    def test_loader_rejects_removed_environment_fog(self):
        fsif_text = """fsif_version: \"2.5\"

mission_info:
  name: "Fog Legacy"

environment:
  fog:
    near_mult: 0.5
    far_mult: 0.8

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
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "legacy_env_fog.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("environment.fog has been removed from FSIF", str(ctx.exception))

    def test_loader_rejects_removed_nebula_fog(self):
        fsif_text = """fsif_version: \"2.5\"

mission_info:
  name: "Nebula Fog Legacy"

environment:
  nebula:
    enabled: true
    pattern: "nbackblue1"
    fog:
      near_mult: 0.5
      far_mult: 0.8

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
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "legacy_nebula_fog.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("environment.nebula.fog has been removed from FSIF", str(ctx.exception))

    def test_writer_always_emits_fixed_fog_multipliers(self):
        mission = self.make_valid_mission()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("+Fog Near Mult: 1.000000", content)
        self.assertIn("+Fog Far Mult: 1.000000", content)


if __name__ == '__main__':
    unittest.main()