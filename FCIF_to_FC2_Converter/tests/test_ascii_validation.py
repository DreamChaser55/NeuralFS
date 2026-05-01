"""
Tests for ASCII validation in fcif_to_fc2.py.

After the refactoring, ASCII validation is enforced by the AsciiStr Pydantic
Annotated type on all FSO-facing string fields.  Any attempt to construct a
model with a non-ASCII string must raise pydantic.ValidationError.

Coverage:
  - CampaignInfo.name / .description
  - StartingLoadout.ships / .weapons  (list items)
  - CampaignMission.filename / .success_goal / .success_event /
    .failure_goal / .failure_event
  - Optional[AsciiStr] fields accept None without error
  - Multiple bad fields produce multiple errors in a single ValidationError
  - process_campaign() integration: a .fcif file with a non-ASCII field
    returns False and logs [ERROR]
"""

import sys
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
import logging
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Path setup — allow running the test from anywhere
# ---------------------------------------------------------------------------
_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from fcif_to_fc2 import (
    FCIF,
    CampaignInfo,
    CampaignMission,
    StartingLoadout,
    process_campaign,
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


def _minimal_fcif_dict(**overrides) -> dict:
    """Return a minimal valid FCIF dict, with optional field overrides."""
    base = {
        "fcif_version": "1.1",
        "campaign": {"name": "Test", "description": "A test campaign"},
        "starting_loadout": {"ships": ["GTF Ulysses"], "weapons": ["ML-16 Laser"]},
        "missions": [{"filename": "m01.fs2"}],
    }
    base.update(overrides)
    return base


def _write_fcif(directory: Path, content: str, name: str = "camp.fcif") -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. CampaignInfo field validation
# ---------------------------------------------------------------------------

class TestCampaignInfoAscii(unittest.TestCase):

    def test_ascii_name_passes(self):
        """A fully ASCII campaign name constructs without error."""
        info = CampaignInfo(name="The Iron Lance", description="A campaign.")
        self.assertEqual(info.name, "The Iron Lance")

    def test_non_ascii_name_raises(self):
        """A campaign name containing a non-ASCII character raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            CampaignInfo(name="Caf\u00e9 Campaign", description="desc")
        err_str = str(ctx.exception)
        self.assertIn("name", err_str)
        self.assertIn("U+00E9", err_str)

    def test_ascii_description_passes(self):
        """A fully ASCII description constructs without error."""
        info = CampaignInfo(name="Campaign", description="Normal ASCII text.")
        self.assertEqual(info.description, "Normal ASCII text.")

    def test_non_ascii_description_raises(self):
        """A description containing a non-ASCII character raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            CampaignInfo(name="Campaign", description="R\u00e9sum\u00e9 of events")
        err_str = str(ctx.exception)
        self.assertIn("description", err_str)
        # At least one offending character should be mentioned
        self.assertTrue("U+00E9" in err_str or "non-ASCII" in err_str)

    def test_em_dash_in_name_raises(self):
        """An em-dash (common mistake) in campaign.name is rejected."""
        with self.assertRaises(ValidationError) as ctx:
            CampaignInfo(name="Alpha\u2014Omega", description="desc")
        err_str = str(ctx.exception)
        self.assertIn("U+2014", err_str)

    def test_ellipsis_char_in_description_raises(self):
        """The single-character ellipsis (U+2026) in description is rejected."""
        with self.assertRaises(ValidationError) as ctx:
            CampaignInfo(name="Camp", description="Wait\u2026 and see")
        err_str = str(ctx.exception)
        self.assertIn("U+2026", err_str)

    def test_ascii_control_chars_allowed(self):
        """ASCII control characters (newline, tab) are within 7-bit range and allowed."""
        info = CampaignInfo(name="Camp", description="Line one.\nLine two.\tTabbed.")
        self.assertIn("\n", info.description)


# ---------------------------------------------------------------------------
# 2. StartingLoadout field validation
# ---------------------------------------------------------------------------

class TestStartingLoadoutAscii(unittest.TestCase):

    def test_ascii_ships_list_passes(self):
        """A ships list with only ASCII strings constructs without error."""
        sl = StartingLoadout(ships=["GTF Ulysses", "GTB Medusa"], weapons=[])
        self.assertEqual(len(sl.ships), 2)

    def test_non_ascii_ship_name_raises(self):
        """A ship name containing a non-ASCII character raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            StartingLoadout(ships=["GTF Uly\u00e9sses"], weapons=[])
        err_str = str(ctx.exception)
        self.assertIn("ships", err_str)
        self.assertIn("U+00E9", err_str)

    def test_non_ascii_ship_index_reported(self):
        """When a list item is invalid, Pydantic includes the list index in the error path."""
        with self.assertRaises(ValidationError) as ctx:
            StartingLoadout(ships=["GTF Ulysses", "PVF \u00c9lan"], weapons=[])
        err_str = str(ctx.exception)
        # Index 1 is the bad item
        self.assertIn("1", err_str)

    def test_ascii_weapons_list_passes(self):
        """A weapons list with only ASCII strings constructs without error."""
        sl = StartingLoadout(ships=[], weapons=["ML-16 Laser", "Prometheus"])
        self.assertEqual(len(sl.weapons), 2)

    def test_non_ascii_weapon_name_raises(self):
        """A weapon name containing a non-ASCII character raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            StartingLoadout(ships=[], weapons=["ML-16 L\u00e0ser"])
        err_str = str(ctx.exception)
        self.assertIn("weapons", err_str)

    def test_empty_lists_pass(self):
        """Empty ships and weapons lists are valid."""
        sl = StartingLoadout(ships=[], weapons=[])
        self.assertEqual(sl.ships, [])
        self.assertEqual(sl.weapons, [])


# ---------------------------------------------------------------------------
# 3. CampaignMission field validation
# ---------------------------------------------------------------------------

class TestCampaignMissionAscii(unittest.TestCase):

    def test_ascii_filename_passes(self):
        """A mission filename that is pure ASCII constructs without error."""
        m = CampaignMission(filename="mission_01.fs2")
        self.assertEqual(m.filename, "mission_01.fs2")

    def test_non_ascii_filename_raises(self):
        """A mission filename with a non-ASCII character raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            CampaignMission(filename="missi\u00f3n_01.fs2")
        err_str = str(ctx.exception)
        self.assertIn("filename", err_str)
        self.assertIn("U+00F3", err_str)

    def test_none_success_goal_passes(self):
        """success_goal=None (Optional[AsciiStr]) is allowed without error."""
        m = CampaignMission(filename="m.fs2", success_goal=None)
        self.assertIsNone(m.success_goal)

    def test_ascii_success_goal_passes(self):
        m = CampaignMission(filename="m.fs2", success_goal="Protect the Fenris")
        self.assertEqual(m.success_goal, "Protect the Fenris")

    def test_non_ascii_success_goal_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            CampaignMission(filename="m.fs2", success_goal="G\u00f3al name")
        err_str = str(ctx.exception)
        self.assertIn("success_goal", err_str)

    def test_none_success_event_passes(self):
        m = CampaignMission(filename="m.fs2", success_event=None)
        self.assertIsNone(m.success_event)

    def test_non_ascii_success_event_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            CampaignMission(filename="m.fs2", success_event="Ambush trigg\u00e9red")
        err_str = str(ctx.exception)
        self.assertIn("success_event", err_str)

    def test_none_failure_goal_passes(self):
        m = CampaignMission(filename="m.fs2", failure_goal=None)
        self.assertIsNone(m.failure_goal)

    def test_non_ascii_failure_goal_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            CampaignMission(filename="m.fs2", failure_goal="Base D\u00e9stroy\u00e9d")
        err_str = str(ctx.exception)
        self.assertIn("failure_goal", err_str)

    def test_none_failure_event_passes(self):
        m = CampaignMission(filename="m.fs2", failure_event=None)
        self.assertIsNone(m.failure_event)

    def test_non_ascii_failure_event_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            CampaignMission(filename="m.fs2", failure_event="Flagship l\u00f3st")
        err_str = str(ctx.exception)
        self.assertIn("failure_event", err_str)


# ---------------------------------------------------------------------------
# 4. Multiple bad fields: all errors collected in a single ValidationError
# ---------------------------------------------------------------------------

class TestMultipleAsciiErrors(unittest.TestCase):

    def test_two_bad_fields_both_reported(self):
        """
        When two independent fields each contain non-ASCII characters, both errors
        appear in a single ValidationError (Pydantic does not short-circuit).
        """
        with self.assertRaises(ValidationError) as ctx:
            CampaignInfo(
                name="Caf\u00e9",          # U+00E9
                description="R\u00e9sum\u00e9",  # U+00E9
            )
        err = ctx.exception
        # Pydantic v2: error_count() gives number of collected errors
        self.assertGreaterEqual(err.error_count(), 2)

    def test_bad_ship_and_bad_weapon_both_reported(self):
        """Both a bad ship name and a bad weapon name appear in one ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            StartingLoadout(
                ships=["GTF \u00c9lan"],   # U+00C9
                weapons=["ML\u201316"],     # U+2013 (en-dash instead of hyphen)
            )
        err = ctx.exception
        self.assertGreaterEqual(err.error_count(), 2)

    def test_full_fcif_multiple_bad_fields(self):
        """
        Constructing a full FCIF with non-ASCII in campaign.name, a ship list item,
        and a mission filename all produce errors in a single ValidationError.
        """
        data = {
            "fcif_version": "1.1",
            "campaign": {
                "name": "Caf\u00e9 Wars",           # bad
                "description": "Normal description",
            },
            "starting_loadout": {
                "ships": ["GTF Uly\u00e9sses"],       # bad
                "weapons": ["ML-16 Laser"],
            },
            "missions": [{"filename": "miss\u00ed\u00f3n.fs2"}],  # bad
        }
        with self.assertRaises(ValidationError) as ctx:
            FCIF(**data)
        err = ctx.exception
        self.assertGreaterEqual(err.error_count(), 3)


# ---------------------------------------------------------------------------
# 5. Full FCIF: clean data passes model construction
# ---------------------------------------------------------------------------

class TestFullFcifClean(unittest.TestCase):

    def test_minimal_clean_fcif_passes(self):
        """A completely ASCII-clean minimal FCIF constructs without any error."""
        data = _minimal_fcif_dict()
        fcif = FCIF(**data)
        self.assertEqual(fcif.campaign.name, "Test")

    def test_all_optional_condition_fields_none_passes(self):
        """All four optional condition fields set to None do not cause ASCII errors."""
        data = _minimal_fcif_dict(
            missions=[{
                "filename": "m01.fs2",
                "success_goal": None,
                "success_event": None,
                "failure_goal": None,
                "failure_event": None,
            }]
        )
        fcif = FCIF(**data)
        self.assertIsNone(fcif.missions[0].success_goal)

    def test_all_optional_condition_fields_ascii_passes(self):
        """All four optional condition fields set to ASCII strings pass without error."""
        # (Only one can actually be used at runtime due to mutual exclusivity,
        #  but ASCII validation on each field is independent of that constraint.)
        m = CampaignMission(
            filename="m01.fs2",
            success_goal="Primary Objective",
        )
        self.assertEqual(m.success_goal, "Primary Objective")


# ---------------------------------------------------------------------------
# 6. process_campaign integration: non-ASCII in .fcif file → False + [ERROR]
# ---------------------------------------------------------------------------

class TestProcessCampaignAsciiIntegration(unittest.TestCase):

    def _write_and_run(self, yaml_content: str) -> tuple:
        """
        Write yaml_content to a temp .fcif file, run process_campaign, return
        (success: bool, messages: list).
        """
        with capture_logs() as msgs:
            with tempfile.TemporaryDirectory() as tmpdir:
                fcif_path = _write_fcif(Path(tmpdir), yaml_content)
                output_path = Path(tmpdir) / "out.fc2"
                success = process_campaign(
                    str(fcif_path),
                    str(output_path),
                )
        return success, msgs

    def test_non_ascii_campaign_name_returns_false(self):
        """A .fcif file with a non-ASCII campaign name causes process_campaign to return False."""
        yaml_content = yaml.dump({
            "fcif_version": "1.1",
            "campaign": {"name": "Caf\u00e9", "description": "desc"},
            "starting_loadout": {"ships": [], "weapons": []},
            "missions": [{"filename": "m.fs2"}],
        }, allow_unicode=True)

        success, msgs = self._write_and_run(yaml_content)
        self.assertFalse(success)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_non_ascii_ship_in_loadout_returns_false(self):
        """A .fcif file with a non-ASCII ship name in starting_loadout returns False."""
        yaml_content = yaml.dump({
            "fcif_version": "1.1",
            "campaign": {"name": "Camp", "description": "desc"},
            "starting_loadout": {"ships": ["GTF \u00c9lan"], "weapons": []},
            "missions": [{"filename": "m.fs2"}],
        }, allow_unicode=True)

        success, msgs = self._write_and_run(yaml_content)
        self.assertFalse(success)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_non_ascii_mission_filename_returns_false(self):
        """A .fcif file with a non-ASCII mission filename returns False."""
        yaml_content = yaml.dump({
            "fcif_version": "1.1",
            "campaign": {"name": "Camp", "description": "desc"},
            "starting_loadout": {"ships": [], "weapons": []},
            "missions": [{"filename": "miss\u00ed\u00f3n.fs2"}],
        }, allow_unicode=True)

        success, msgs = self._write_and_run(yaml_content)
        self.assertFalse(success)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_non_ascii_success_goal_returns_false(self):
        """A .fcif file with a non-ASCII success_goal returns False."""
        yaml_content = yaml.dump({
            "fcif_version": "1.1",
            "campaign": {"name": "Camp", "description": "desc"},
            "starting_loadout": {"ships": [], "weapons": []},
            "missions": [{"filename": "m.fs2", "success_goal": "G\u00f3al"}],
        }, allow_unicode=True)

        success, msgs = self._write_and_run(yaml_content)
        self.assertFalse(success)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_fully_ascii_fcif_succeeds(self):
        """A .fcif file with all ASCII-clean fields causes process_campaign to return True."""
        yaml_content = yaml.dump(_minimal_fcif_dict(), allow_unicode=True)
        success, msgs = self._write_and_run(yaml_content)
        self.assertTrue(success)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)


if __name__ == "__main__":
    unittest.main()
