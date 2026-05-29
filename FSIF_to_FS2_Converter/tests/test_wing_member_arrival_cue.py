"""Regression tests for wing-member arrival_cue behaviour.

Guard against the bug introduced in commit 3efae8d that caused expanded
wing-member Ship objects to carry arrival_cue '( true )' instead of
'( false )', causing FSO wing/loadout errors.

The correct behaviour:
  - Expanded wing-member Ship objects always have arrival_cue '( false )'.
  - The Wing object's own arrival_cue controls when the wing actually arrives.
  - Standalone ships that omit arrival_cue still default to '( true )'.

Covers:
- Wing member Ship objects have arrival_cue '( false )' after loading.
- Wing-level arrival_cue defaults to '( true )' when not authored.
- Authored conditional wing arrival_cue is preserved unchanged.
- Members of a wing with a conditional arrival_cue still have '( false )'.
- FS2 #Objects section emits '( false )' for all wing members.
- FS2 #Wings section emits '( true )' cue for the wing itself.
- Standalone ship omitting arrival_cue defaults to '( true )'.
- Any standalone ship omitting arrival_cue defaults to '( true )'.
- Standalone ships emit '$Arrival Cue: ( true )' in #Objects.
"""

import tempfile
import unittest
from pathlib import Path

from data_models import Mission
from fs2_writer import FS2Writer
from mission_loader import load_mission_from_fsif
from _fsif_test_helpers import SilencedTestCase


_MINIMAL_FSIF_WING_ARRIVAL_CUE = """\
fsif_version: "1.0"
mission_info:
  name: "Wing Arrival Cue Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - class: "GTF Ulysses"
      count: 4
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 4
      position: [0, 0, 0]
mission_flow: {}
"""

_MINIMAL_FSIF_WING_CONDITIONAL_CUE = """\
fsif_version: "1.0"
mission_info:
  name: "Wing Conditional Arrival Cue Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - class: "GTF Ulysses"
      count: 4
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 4
      position: [0, 0, 0]
    - name: "Rama"
      template: "alpha_t"
      count: 2
      position: [1000, 0, 1000]
      arrival_cue: |
        ( has-time-elapsed 30 )
mission_flow: {}
"""

_MINIMAL_FSIF_STANDALONE_SHIP = """\
fsif_version: "1.0"
mission_info:
  name: "Standalone Ship Arrival Cue Test"
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
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
    - name: "GTFr Poseidon 1"
      class: "GTFr Poseidon"
      team: "Friendly"
      position: [500, 0, 500]
mission_flow: {}
"""


class WingMemberArrivalCueRegression(SilencedTestCase):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load(self, fsif_text: str) -> Mission:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def _write_fs2(self, mission: Mission) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            return out.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Wing member ship objects must have arrival_cue '( false )'
    # ------------------------------------------------------------------

    def test_wing_member_ships_have_false_arrival_cue_after_load(self):
        """All expanded wing-member Ship objects must have arrival_cue '( false )'."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        self.assertEqual(len(mission.wings), 1)
        wing = mission.wings[0]
        self.assertEqual(len(wing.ships), 4)
        for ship in wing.ships:
            self.assertEqual(
                ship.arrival_cue, '( false )',
                f"Wing member '{ship.name}' has arrival_cue '{ship.arrival_cue}'; expected '( false )'"
            )

    def test_wing_level_arrival_cue_defaults_to_true(self):
        """Wing object arrival_cue should default to '( true )' when not authored."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        wing = mission.wings[0]
        self.assertEqual(
            wing.arrival_cue, '( true )',
            f"Wing arrival_cue '{wing.arrival_cue}'; expected '( true )'"
        )

    def test_conditional_wing_arrival_cue_is_preserved(self):
        """Authored conditional wing arrival_cue must be preserved unchanged."""
        mission = self._load(_MINIMAL_FSIF_WING_CONDITIONAL_CUE)
        rama_wing = next(w for w in mission.wings if w.name == "Rama")
        self.assertIn(
            "has-time-elapsed",
            rama_wing.arrival_cue,
            f"Conditional wing cue not preserved: '{rama_wing.arrival_cue}'"
        )

    def test_conditional_wing_member_ships_still_have_false_cue(self):
        """Members of a wing with a conditional arrival_cue must still have '( false )'."""
        mission = self._load(_MINIMAL_FSIF_WING_CONDITIONAL_CUE)
        rama_wing = next(w for w in mission.wings if w.name == "Rama")
        for ship in rama_wing.ships:
            self.assertEqual(
                ship.arrival_cue, '( false )',
                f"Wing member '{ship.name}' has arrival_cue '{ship.arrival_cue}'; expected '( false )'"
            )

    # ------------------------------------------------------------------
    # FS2 output: #Objects entries must emit '( false )' for wing members
    # ------------------------------------------------------------------

    def test_fs2_objects_section_emits_false_for_wing_members(self):
        """The emitted FS2 file must contain '$Arrival Cue: ( false )' for every wing member."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        content = self._write_fs2(mission)

        objects_start = content.find("#Objects")
        wings_start = content.find("#Wings")
        self.assertGreater(objects_start, -1, "#Objects section not found")
        self.assertGreater(wings_start, -1, "#Wings section not found")

        objects_section = content[objects_start:wings_start]

        for i in range(1, 5):
            name_marker = f"$Name: Alpha {i}"
            self.assertIn(
                name_marker, objects_section,
                f"'{name_marker}' not found in #Objects section"
            )

        true_count = objects_section.count("$Arrival Cue: ( true )")
        false_count = objects_section.count("$Arrival Cue: ( false )")

        self.assertEqual(
            true_count, 0,
            f"#Objects section contains {true_count} '$Arrival Cue: ( true )' entries; expected 0"
        )
        self.assertEqual(
            false_count, 4,
            f"#Objects section contains {false_count} '$Arrival Cue: ( false )' entries; expected 4"
        )

    def test_fs2_wings_section_emits_true_cue_for_wing(self):
        """The emitted FS2 file must contain '$Arrival Cue: ( true )' in the #Wings entry."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        content = self._write_fs2(mission)

        wings_start = content.find("#Wings")
        self.assertGreater(wings_start, -1, "#Wings section not found")

        wings_section = content[wings_start:]
        self.assertIn(
            "$Arrival Cue: ( true )",
            wings_section,
            "#Wings section does not contain '$Arrival Cue: ( true )' for the wing"
        )

    # ------------------------------------------------------------------
    # Standalone ship defaults must remain unaffected
    # ------------------------------------------------------------------

    def test_standalone_ship_omitting_arrival_cue_defaults_to_true(self):
        """A standalone ship that omits arrival_cue must default to '( true )'."""
        mission = self._load(_MINIMAL_FSIF_STANDALONE_SHIP)
        player_ship = next(s for s in mission.ships if s.name == "Player Ship")
        self.assertEqual(
            player_ship.arrival_cue, '( true )',
            f"Standalone player ship arrival_cue '{player_ship.arrival_cue}'; expected '( true )'"
        )

    def test_standalone_npc_ship_omitting_arrival_cue_defaults_to_true(self):
        """Any standalone ship omitting arrival_cue defaults to '( true )'."""
        mission = self._load(_MINIMAL_FSIF_STANDALONE_SHIP)
        npc = next(s for s in mission.ships if s.name == "GTFr Poseidon 1")
        self.assertEqual(
            npc.arrival_cue, '( true )',
            f"Standalone NPC ship arrival_cue '{npc.arrival_cue}'; expected '( true )'"
        )

    def test_fs2_objects_standalone_ship_emits_true_cue(self):
        """Standalone ships must still emit '$Arrival Cue: ( true )' in #Objects."""
        mission = self._load(_MINIMAL_FSIF_STANDALONE_SHIP)
        content = self._write_fs2(mission)

        objects_start = content.find("#Objects")
        wings_start = content.find("#Wings")
        if wings_start == -1:
            wings_start = len(content)
        objects_section = content[objects_start:wings_start]

        self.assertIn(
            "$Arrival Cue: ( true )",
            objects_section,
            "Standalone ship should emit '$Arrival Cue: ( true )' in #Objects"
        )


if __name__ == "__main__":
    unittest.main()
