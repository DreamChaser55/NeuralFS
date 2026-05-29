"""Miscellaneous FS2 writer output tests.

Covers:
- Weapon pool secondary bank sizes are computed correctly.
- The writer always emits fixed fog-near/far multipliers (1.0).
- pack_ambient_light_rgb() helper converts RGB to the correct integer.
- The writer emits the packed integer for ambient_light_level in FS2 output.
"""

import tempfile
import unittest
from pathlib import Path

from data_models import (
    Environment,
    Mission,
    MissionInfo,
    PlayerSetup,
    Ship,
    Weapons,
    Wing,
    pack_ambient_light_rgb,
)
from fs2_writer import FS2Writer
from _fsif_test_helpers import SilencedTestCase, make_valid_mission


class FS2WriterMiscTesting(SilencedTestCase):

    def test_writer_weapon_pool_secondary_sizes(self):
        mission = make_valid_mission()

        ship1 = Ship.model_validate(
            {
                "name": "Alpha 1",
                "class": "GTF Ulysses",
                "team": "Friendly",
                "position": [0.0, 0.0, 0.0],
                "arrival_cue": "( true )",
                "weapons": Weapons(
                    primary=["Avenger", "Avenger"],
                    secondary=["Harbinger"],
                ),
            }
        )
        ship2 = Ship.model_validate(
            {
                "name": "Alpha 2",
                "class": "GTF Ulysses",
                "team": "Friendly",
                "position": [0.0, 0.0, 0.0],
                "arrival_cue": "( true )",
                "weapons": Weapons(
                    primary=["Avenger", "Avenger"],
                    secondary=["Harbinger"],
                ),
            }
        )

        mission.wings = [
            Wing(
                name="Alpha",
                count=2,
                ships=[ship1, ship2],
                position=[0.0, 0.0, 0.0],
                arrival_cue="( true )",
            )
        ]
        mission.player_setup.additional_weapons = ["Tsunami"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn('"Harbinger"\t3', content)
        self.assertIn('"Tsunami"\t5', content)

    def test_writer_always_emits_fixed_fog_multipliers(self):
        mission = make_valid_mission()

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
        mission = make_valid_mission()
        mission.environment = Environment(ambient_light_level=[10, 10, 10])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("$Ambient light level: 657930", content)


if __name__ == "__main__":
    unittest.main()
