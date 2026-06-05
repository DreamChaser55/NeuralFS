"""
Tests for reinforcement $Num times emission in the FS2Writer.

Verifies:
- Wing reinforcements emit ``$Num times: <max_uses>`` using the authored value.
- Ship reinforcements always emit ``$Num times: 1`` (hardcoded; FSO's
  $Num times field is a no-op for single-ship reinforcements).
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
from fs2_writer import FS2Writer


# ---------------------------------------------------------------------------
# Minimal FSIF fixture with both a wing reinforcement (max_uses: 3)
# and a ship reinforcement (no max_uses).
# ---------------------------------------------------------------------------

_REINF_WRITER_FSIF = """fsif_version: "1.0"
mission_info:
  name: "Reinforcement Writer Test"
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
    delta_t:
      class: "GTF Apollo"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
  ships:
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      position: [0, 0, 1000]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
    - name: "Delta"
      template: "delta_t"
      count: 2
      position: [100, 0, 0]
  reinforcement_wings:
    - name: "Delta"
      max_uses: 3
  reinforcement_ships:
    - name: "GTC Fenris 1"
mission_flow: {}
"""


def _extract_reinforcements_section(fs2_content: str) -> str:
    """Return the text of the #Reinforcements section from a .fs2 string."""
    start = fs2_content.find('#Reinforcements')
    if start == -1:
        return ""
    next_section = fs2_content.find('\n#', start + 1)
    return fs2_content[start:next_section] if next_section != -1 else fs2_content[start:]


def _find_num_times_for_entry(section: str, entry_name: str) -> str | None:
    """Return the ``$Num times: X`` line for a named entry inside a #Reinforcements block.

    Returns the stripped line, or ``None`` if the entry is not found.
    """
    entry_marker = f'$Name: {entry_name}'
    entry_pos = section.find(entry_marker)
    if entry_pos == -1:
        return None
    # Determine the end of this entry (start of the next $Name: or end of section)
    next_name_pos = section.find('$Name:', entry_pos + len(entry_marker))
    entry_block = section[entry_pos:next_name_pos] if next_name_pos != -1 else section[entry_pos:]
    # Find $Num times within the entry block
    num_pos = entry_block.find('$Num times:')
    if num_pos == -1:
        return None
    eol = entry_block.find('\n', num_pos)
    line = entry_block[num_pos:eol] if eol != -1 else entry_block[num_pos:]
    return line.strip()


class ReinforcementWriterTests(unittest.TestCase):
    """Tests for $Num times emission in write_reinforcements()."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _load_and_write(self, fsif_text: str) -> str:
        """Load FSIF, run the FS2Writer, and return the output file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "mission.fsif"
            fs2_path = Path(tmpdir) / "mission.fs2"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(fsif_path))
            writer = FS2Writer(mission, str(fs2_path))
            writer.write_mission()
            return fs2_path.read_text(encoding="utf-8")

    # -------------------------------------------------------------------------

    def test_wing_reinforcement_emits_authored_max_uses(self):
        """Wing reinforcements must emit $Num times equal to the authored max_uses value.

        Delta is a wing reinforcement with max_uses=3, so the writer must emit
        ``$Num times: 3`` for its entry.
        """
        fs2_content = self._load_and_write(_REINF_WRITER_FSIF)
        section = _extract_reinforcements_section(fs2_content)
        self.assertTrue(section, "#Reinforcements section must be present in output")

        num_times_line = _find_num_times_for_entry(section, "Delta")
        self.assertIsNotNone(
            num_times_line,
            "$Num times line not found for 'Delta' in #Reinforcements section",
        )
        self.assertEqual(
            num_times_line, "$Num times: 3",
            "Wing reinforcement should emit the authored max_uses=3",
        )

    def test_ship_reinforcement_emits_hardcoded_1(self):
        """Ship reinforcements must always emit $Num times: 1 (hardcoded).

        GTC Fenris 1 is a standalone ship reinforcement with no max_uses in
        FSIF (field is not supported for ships).  The writer must hardcode the
        value to 1 because FSO's $Num times is a no-op for single ships.
        """
        fs2_content = self._load_and_write(_REINF_WRITER_FSIF)
        section = _extract_reinforcements_section(fs2_content)
        self.assertTrue(section, "#Reinforcements section must be present in output")

        num_times_line = _find_num_times_for_entry(section, "GTC Fenris 1")
        self.assertIsNotNone(
            num_times_line,
            "$Num times line not found for 'GTC Fenris 1' in #Reinforcements section",
        )
        self.assertEqual(
            num_times_line, "$Num times: 1",
            "Ship reinforcement must always emit $Num times: 1 (hardcoded)",
        )

    def test_reinforcements_section_contains_both_entries(self):
        """The #Reinforcements section must contain entries for both the wing and the ship."""
        fs2_content = self._load_and_write(_REINF_WRITER_FSIF)
        section = _extract_reinforcements_section(fs2_content)
        self.assertIn('$Name: Delta', section,
                      "Delta wing reinforcement must appear in #Reinforcements")
        self.assertIn('$Name: GTC Fenris 1', section,
                      "GTC Fenris 1 ship reinforcement must appear in #Reinforcements")


if __name__ == "__main__":
    unittest.main()
