"""
Tests for the campaign player loadout check in fcif_to_fc2.py.

Covers:
  - check_campaign_player_loadouts(): comprehensive validation + state updates
  - process_campaign() integration
"""

import unittest
import sys
import tempfile
import logging
from pathlib import Path

# Add the FCIF_to_FC2_Converter directory to path
_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from fcif_to_fc2 import (
    check_campaign_player_loadouts,
    process_campaign,
    FCIF,
    logger as fcif_logger
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        level_name = record.levelname
        if record.levelno == 25:
            level_name = "SUCCESS"
        self.messages.append(f"[{level_name}] {record.getMessage()}")

def _write_fsif(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_fcif(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


import contextlib

@contextlib.contextmanager
def capture_logs():
    """Context manager to capture fcif_logger logs."""
    handler = LogCaptureHandler()
    handler.setLevel(logging.DEBUG)
    old_level = fcif_logger.level
    old_propagate = fcif_logger.propagate
    fcif_logger.setLevel(logging.DEBUG)
    fcif_logger.addHandler(handler)
    fcif_logger.propagate = False
    try:
        yield handler.messages
    finally:
        fcif_logger.removeHandler(handler)
        fcif_logger.setLevel(old_level)
        fcif_logger.propagate = old_propagate


def _load_fcif(yaml_str: str) -> FCIF:
    """Parse a YAML string directly into an FCIF model (no file I/O)."""
    import yaml
    data = yaml.safe_load(yaml_str)
    return FCIF(**data)


def _minimal_fcif_yaml(ships: list[str], weapons: list[str], missions: list[str] = ["mission_01.fs2"]) -> str:
    if ships:
        ships_section = "  ships:\n" + "\n".join(f'    - "{s}"' for s in ships)
    else:
        ships_section = "  ships: []"
    if weapons:
        weapons_section = "  weapons:\n" + "\n".join(f'    - "{w}"' for w in weapons)
    else:
        weapons_section = "  weapons: []"
        
    missions_section = "missions:\n" + "\n".join(f'  - filename: "{m}"' for m in missions)
    
    return f"""fcif_version: "1.1"
campaign:
  name: "Test Campaign"
  description: "A test campaign"
starting_loadout:
{ships_section}
{weapons_section}
{missions_section}
"""


# ---------------------------------------------------------------------------
# Class 1: check_campaign_player_loadouts
# ---------------------------------------------------------------------------

class TestCheckCampaignPlayerLoadouts(unittest.TestCase):

    def _run_check(self, fsif_files: dict, fcif_ships: list, fcif_weapons: list, missions: list = ["mission_01.fs2"]) -> tuple[bool, list]:
        """
        Write FSIF files, build a minimal FCIF, run the check, return (success, log messages).
        fsif_files: dict mapping mission filename (e.g. "mission_01.fsif") to content string.
        """
        with capture_logs() as msgs:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                fsif_dir = tmp_path / "fsif"
                fsif_dir.mkdir(parents=True, exist_ok=True)
                
                for fsif_name, fsif_content in fsif_files.items():
                    _write_fsif(fsif_dir, fsif_name, fsif_content)
                
                fcif = _load_fcif(_minimal_fcif_yaml(fcif_ships, fcif_weapons, missions))
                
                fcif_path = tmp_path / "campaign.fcif"
                result = check_campaign_player_loadouts(fcif, fcif_path)
                
        return result, msgs

    # -- Happy path ----------------------------------------------------------

    def test_all_ships_and_weapons_present_passes(self):
        """When all ships and weapons are in starting_loadout, it returns True."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
      weapons:
        primary: ["ML-16 Laser"]
        secondary: ["MX-50"]
player_setup:
  start_ship: "Alpha 1"
"""
        result, msgs = self._run_check(
            {"mission_01.fsif": fsif}, 
            fcif_ships=["GTF Ulysses"],
            fcif_weapons=["ML-16 Laser", "MX-50"]
        )

        self.assertTrue(result)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_empty_mission_always_passes(self):
        """An FSIF with no ships/wings/weapons in loadout check passes."""
        fsif = """
entities: {}
"""
        result, msgs = self._run_check({"mission_01.fsif": fsif}, fcif_ships=[], fcif_weapons=[])

        self.assertTrue(result)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_additional_ship_choices_and_weapons_are_checked(self):
        """FSIF 4.0 additional loadout fields must be included in the campaign check."""
        fsif = """
entities: {}
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - { class: "GTF Hercules", count: 1 }
  additional_weapons:
    - "Hornet"
"""
        result, msgs = self._run_check(
            {"mission_01.fsif": fsif},
            fcif_ships=[],
            fcif_weapons=[],
        )

        self.assertFalse(result)
        self.assertTrue(any("[ERROR]" in m and "GTF Hercules" in m for m in msgs), msgs)
        self.assertTrue(any("[ERROR]" in m and "Hornet" in m for m in msgs), msgs)

    # -- Error cases -------------------------------------------------------

    def test_missing_ship_emits_error(self):
        """A player ship class used in the FSIF but absent from loadout triggers an [ERROR]."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Hercules"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
player_setup:
  start_ship: "Alpha 1"
"""
        result, msgs = self._run_check({"mission_01.fsif": fsif}, fcif_ships=[], fcif_weapons=[])

        self.assertFalse(result)
        self.assertTrue(
            any("[ERROR]" in m and "GTF Hercules" in m for m in msgs), msgs
        )

    def test_missing_primary_weapon_emits_error(self):
        """A primary weapon absent from loadout triggers an [ERROR]."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
      weapons:
        primary: ["Prometheus"]
        secondary: []
player_setup:
  start_ship: "Alpha 1"
"""
        result, msgs = self._run_check(
            {"mission_01.fsif": fsif}, 
            fcif_ships=["GTF Ulysses"], 
            fcif_weapons=[]
        )

        self.assertFalse(result)
        self.assertTrue(
            any("[ERROR]" in m and "Prometheus" in m for m in msgs), msgs
        )

    def test_missing_secondary_weapon_emits_error(self):
        """A secondary weapon absent from loadout triggers an [ERROR]."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
      weapons:
        primary: []
        secondary: ["Hornet"]
player_setup:
  start_ship: "Alpha 1"
"""
        result, msgs = self._run_check(
            {"mission_01.fsif": fsif}, 
            fcif_ships=["GTF Ulysses"], 
            fcif_weapons=[]
        )

        self.assertFalse(result)
        self.assertTrue(
            any("[ERROR]" in m and "Hornet" in m for m in msgs), msgs
        )

    def test_missing_ship_and_weapon_emits_both_errors(self):
        """Both a missing ship AND a missing weapon produce errors in the same check."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Hercules"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
      weapons:
        primary: ["Banshee"]
        secondary: []
player_setup:
  start_ship: "Alpha 1"
"""
        result, msgs = self._run_check({"mission_01.fsif": fsif}, fcif_ships=[], fcif_weapons=[])

        self.assertFalse(result)
        self.assertTrue(any("[ERROR]" in m and "GTF Hercules" in m for m in msgs), msgs)
        self.assertTrue(any("[ERROR]" in m and "Banshee" in m for m in msgs), msgs)

    # -- SEXP loadout granting ------------------------------------------------

    def test_allow_ship_and_weapon_grants_for_next_mission(self):
        """Items granted via allow-ship and allow-weapon in mission 1 should be valid in mission 2."""
        fsif_1 = """
entities: {}
mission_flow:
  events:
    - formula: ( allow-ship "GTF Hercules" )
    - formula: ( allow-weapon "Prometheus" )
"""
        fsif_2 = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Hercules"
      team: "Friendly"
      position: [0, 0, 0]
      weapons:
        primary: ["Prometheus"]
player_setup:
  start_ship: "Alpha 1"
"""
        result, msgs = self._run_check(
            {"mission_01.fsif": fsif_1, "mission_02.fsif": fsif_2},
            fcif_ships=[], fcif_weapons=[],
            missions=["mission_01.fs2", "mission_02.fs2"]
        )
        
        self.assertTrue(result)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    # -- Edge cases --------------------------------------------------

    def test_file_not_found_warns_and_continues(self):
        """A non-existent .fsif path triggers a [WARNING] and skips."""
        result, msgs = self._run_check({}, fcif_ships=[], fcif_weapons=[])

        self.assertTrue(result)
        self.assertTrue(any("[WARNING]" in m and "file not found" in m.lower() for m in msgs), msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_invalid_yaml_warns_and_continues(self):
        """A file with invalid YAML content returns True and emits a [WARNING]."""
        result, msgs = self._run_check({"mission_01.fsif": "{ invalid yaml: [unclosed"}, fcif_ships=[], fcif_weapons=[])

        self.assertTrue(result)
        self.assertTrue(any("[WARNING]" in m for m in msgs), msgs)


# ---------------------------------------------------------------------------
# Class 2: process_campaign integration
# ---------------------------------------------------------------------------

_MINIMAL_FCIF_TEMPLATE = """fcif_version: "1.1"
campaign:
  name: "Integration Test Campaign"
  description: "Testing campaign loadout check integration"
starting_loadout:
  ships:
{ships}
  weapons:
{weapons}
missions:
  - filename: mission_01.fs2
"""


class TestProcessCampaignIntegration(unittest.TestCase):

    def _make_fcif(self, ships: list, weapons: list) -> str:
        ships_yaml = "\n".join(f'    - "{s}"' for s in ships) if ships else "    []"
        weapons_yaml = "\n".join(f'    - "{w}"' for w in weapons) if weapons else "    []"
        return _MINIMAL_FCIF_TEMPLATE.format(ships=ships_yaml, weapons=weapons_yaml)

    def test_conversion_succeeds_with_clean_loadout(self):
        """process_campaign returns True when loadout is complete."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
      weapons:
        primary: ["ML-16 Laser"]
        secondary: ["MX-50"]
player_setup:
  start_ship: "Alpha 1"
"""
        with capture_logs() as msgs:
            with tempfile.TemporaryDirectory() as tmpdir:
                fsif_dir = Path(tmpdir) / "fsif"
                fsif_dir.mkdir(parents=True, exist_ok=True)
                _write_fsif(fsif_dir, "mission_01.fsif", fsif)
                fcif_path = _write_fcif(
                    Path(tmpdir), "campaign.fcif",
                    self._make_fcif(ships=["GTF Ulysses"], weapons=["ML-16 Laser", "MX-50"])
                )
                output_path = Path(tmpdir) / "campaign.fc2"

                result = process_campaign(
                    str(fcif_path),
                    str(output_path),
                )

        self.assertTrue(result)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_conversion_fails_with_loadout_errors(self):
        """process_campaign returns False when loadout errors are present."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Hercules"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_condition: "( true )"
      weapons:
        primary: ["Banshee"]
        secondary: []
player_setup:
  start_ship: "Alpha 1"
"""
        with capture_logs() as msgs:
            with tempfile.TemporaryDirectory() as tmpdir:
                fsif_dir = Path(tmpdir) / "fsif"
                fsif_dir.mkdir(parents=True, exist_ok=True)
                _write_fsif(fsif_dir, "mission_01.fsif", fsif)
                # FCIF starting_loadout intentionally missing the ship and weapon
                fcif_path = _write_fcif(
                    Path(tmpdir), "campaign.fcif",
                    self._make_fcif(ships=[], weapons=[])
                )
                output_path = Path(tmpdir) / "campaign.fc2"

                result = process_campaign(
                    str(fcif_path),
                    str(output_path),
                )

        # Conversion must fail
        self.assertFalse(result)
        # Errors must have been emitted
        self.assertTrue(any("[ERROR]" in m and "GTF Hercules" in m for m in msgs), msgs)
        self.assertTrue(any("[ERROR]" in m and "Banshee" in m for m in msgs), msgs)

    def test_conversion_without_fsif_file_skips_check(self):
        """When the inferred FSIF file is missing, it logs a warning and conversion succeeds."""
        with capture_logs() as msgs:
            with tempfile.TemporaryDirectory() as tmpdir:
                fcif_path = _write_fcif(
                    Path(tmpdir), "campaign.fcif",
                    self._make_fcif(ships=["GTF Ulysses"], weapons=["ML-16 Laser"])
                )
                output_path = Path(tmpdir) / "campaign.fc2"

                result = process_campaign(
                    str(fcif_path),
                    str(output_path),
                )

        self.assertTrue(result)
        # Warning about the missing file should appear
        self.assertTrue(
            any("[WARNING]" in m and "file not found" in m.lower() for m in msgs),
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
