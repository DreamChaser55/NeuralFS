"""
Tests for check_campaign_advance_condition_references() in fcif_to_fc2.py.

Covers:
  - success_goal references a goal defined in the FSIF -> passes
  - failure_goal references a goal defined in the FSIF -> passes
  - success_event references an event defined in the FSIF -> passes
  - failure_event references an event defined in the FSIF -> passes
  - A typo / non-existent goal name -> returns False, logs [ERROR]
  - A typo / non-existent event name -> returns False, logs [ERROR]
  - Error message includes available goal/event names when they exist
  - FSIF missing for a mission without an advance condition -> silently skipped (True)
  - FSIF missing for a mission WITH an advance condition -> returns False, logs [ERROR]
  - Invalid YAML with an advance condition -> returns False, logs [ERROR]
  - Mission with no advance condition field -> silently skipped (True)
  - Multiple missions: one passes, one fails -> returns False
  - All missions pass -> logs confirmation INFO message
  - process_campaign() integration: aborts before writing on a bad reference
"""

import contextlib
import logging
import sys
import tempfile
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow running the test from anywhere
# ---------------------------------------------------------------------------
_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from fcif_to_fc2 import (
    FCIF,
    check_campaign_advance_condition_references,
    process_campaign,
    logger as fcif_logger,
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


def _build_fcif_yaml(missions: list[dict]) -> str:
    """
    Build a minimal FCIF YAML string from a list of mission dicts.
    Each dict must have 'filename' and optionally one advance condition key.
    """
    lines = [
        'fcif_version: "1.0"',
        "campaign:",
        '  name: "Test Campaign"',
        '  description: "A test campaign"',
        "starting_loadout:",
        "  ships: []",
        "  weapons: []",
        "missions:",
    ]
    for m in missions:
        lines.append(f'  - filename: "{m["filename"]}"')
        for field in ("success_goal", "failure_goal", "success_event", "failure_event"):
            if field in m and m[field] is not None:
                lines.append(f'    {field}: "{m[field]}"')
    return "\n".join(lines) + "\n"


def _write_file(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _run_check(fsif_files: dict, missions: list[dict]) -> tuple[bool, list]:
    """
    Helper: write FSIF files to a temp directory, build FCIF, run the check.

    fsif_files: mapping of filename relative to <tmpdir>/fsif/ -> content string.
    missions: list of mission dicts for _build_fcif_yaml().
    Returns (result, log_messages).
    """
    with capture_logs() as msgs:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fsif_dir = tmp_path / "fsif"
            fsif_dir.mkdir(parents=True, exist_ok=True)

            for fsif_name, content in fsif_files.items():
                _write_file(fsif_dir, fsif_name, content)

            fcif = _load_fcif(_build_fcif_yaml(missions))
            fcif_path = tmp_path / "campaign.fcif"
            result = check_campaign_advance_condition_references(fcif, fcif_path)

    return result, msgs


# ---------------------------------------------------------------------------
# FSIF fragments used by multiple tests
# ---------------------------------------------------------------------------

_FSIF_WITH_GOAL = """
mission_flow:
  goals:
    - name: "EscortConvoy"
      type: "Primary"
      objective_text: "Escort the convoy."
      formula: "( true )"
    - name: "ScanTransport"
      type: "Bonus"
      objective_text: "Scan the transport."
      formula: "( true )"
"""

_FSIF_WITH_EVENT = """
mission_flow:
  events:
    - name: "ConvoySafe"
      formula: "( when ( true ) ( do-nothing ) )"
    - name: "ConvoyDestroyed"
      formula: "( when ( true ) ( do-nothing ) )"
"""

_FSIF_EMPTY_FLOW = """
mission_flow: {}
"""

_FSIF_NO_FLOW = """
entities: {}
"""


# ===========================================================================
# Class 1: Happy paths — valid references pass
# ===========================================================================

class TestAdvanceConditionReferencesHappyPath(unittest.TestCase):

    def test_success_goal_exists_passes(self):
        """success_goal referencing an existing goal name returns True."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "success_goal": "EscortConvoy"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_failure_goal_exists_passes(self):
        """failure_goal referencing an existing goal name returns True."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "failure_goal": "ScanTransport"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_success_event_exists_passes(self):
        """success_event referencing an existing event name returns True."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_EVENT},
            [{"filename": "mission_01.fs2", "success_event": "ConvoySafe"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_failure_event_exists_passes(self):
        """failure_event referencing an existing event name returns True."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_EVENT},
            [{"filename": "mission_01.fs2", "failure_event": "ConvoyDestroyed"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_no_advance_condition_skipped_silently(self):
        """A mission with no advance condition field is silently skipped and returns True."""
        result, msgs = _run_check(
            {},  # No FSIF file needed; mission has no condition
            [{"filename": "mission_01.fs2"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_all_missions_pass_logs_info(self):
        """When all referenced names exist, an INFO confirmation is logged."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "success_goal": "EscortConvoy"}],
        )
        self.assertTrue(result, msgs)
        self.assertTrue(
            any("[INFO]" in m and "passed" in m for m in msgs), msgs
        )


# ===========================================================================
# Class 2: Error cases — bad references trigger errors
# ===========================================================================

class TestAdvanceConditionReferenceErrors(unittest.TestCase):

    def test_misspelled_goal_name_fails(self):
        """A typo in success_goal causes an [ERROR] and returns False."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "success_goal": "EscortConvoyy"}],  # typo
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_error_mentions_field_name(self):
        """The error message mentions the offending FCIF field name."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "failure_goal": "Nonexistent"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(
            any("failure_goal" in m for m in msgs), msgs
        )

    def test_error_mentions_referenced_name(self):
        """The error message mentions the referenced name that could not be found."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "success_goal": "BadGoalName"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(
            any("BadGoalName" in m for m in msgs), msgs
        )

    def test_error_lists_available_goals(self):
        """When goals exist but the referenced one doesn't, available names are listed in error."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "success_goal": "Nonexistent"}],
        )
        self.assertFalse(result, msgs)
        error_text = " ".join(msgs)
        # Both actual goal names should be mentioned in available names
        self.assertIn("EscortConvoy", error_text)
        self.assertIn("ScanTransport", error_text)

    def test_misspelled_event_name_fails(self):
        """A typo in success_event causes an [ERROR] and returns False."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_EVENT},
            [{"filename": "mission_01.fs2", "success_event": "ConvoySaffe"}],  # typo
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_event_name_absent_when_no_events_defined(self):
        """Referencing an event in a mission that has no events section fails with a clear message."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_EMPTY_FLOW},
            [{"filename": "mission_01.fs2", "success_event": "SomeEvent"}],
        )
        self.assertFalse(result, msgs)
        error_text = " ".join(msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)
        # Should mention that no events are defined
        self.assertIn("No events", error_text)

    def test_goal_name_absent_when_no_goals_defined(self):
        """Referencing a goal in a mission that has no goals section fails with a clear message."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_NO_FLOW},
            [{"filename": "mission_01.fs2", "success_goal": "SomeGoal"}],
        )
        self.assertFalse(result, msgs)
        error_text = " ".join(msgs)
        self.assertIn("No goals", error_text)

    def test_wrong_collection_type_fails(self):
        """Referencing a goal name that exists only in events (wrong collection) fails."""
        result, msgs = _run_check(
            {"mission_01.fsif": _FSIF_WITH_EVENT},
            # ConvoySafe is an event, not a goal
            [{"filename": "mission_01.fs2", "success_goal": "ConvoySafe"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)


# ===========================================================================
# Class 3: FSIF file issues with advance conditions present
# ===========================================================================

class TestAdvanceConditionFsifFileIssues(unittest.TestCase):

    def test_missing_fsif_with_condition_fails(self):
        """A missing FSIF for a mission WITH an advance condition is a fatal error."""
        result, msgs = _run_check(
            {},  # No FSIF files at all
            [{"filename": "mission_01.fs2", "success_goal": "EscortConvoy"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_missing_fsif_without_condition_passes(self):
        """A missing FSIF for a mission WITHOUT an advance condition is silently skipped."""
        result, msgs = _run_check(
            {},  # No FSIF files at all
            [{"filename": "mission_01.fs2"}],  # No condition
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_invalid_yaml_with_condition_fails(self):
        """Invalid YAML in the FSIF for a mission with an advance condition is a fatal error."""
        result, msgs = _run_check(
            {"mission_01.fsif": "{ invalid yaml: [unclosed"},
            [{"filename": "mission_01.fs2", "success_goal": "EscortConvoy"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_non_mapping_yaml_with_condition_fails(self):
        """FSIF that parses as a non-mapping (e.g., plain list) with a condition fails."""
        result, msgs = _run_check(
            {"mission_01.fsif": "- item1\n- item2\n"},
            [{"filename": "mission_01.fs2", "failure_event": "SomeEvent"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)


# ===========================================================================
# Class 4: Multiple missions — partial failures
# ===========================================================================

class TestAdvanceConditionReferencesMultipleMissions(unittest.TestCase):

    def test_all_missions_valid_returns_true(self):
        """Two missions both with valid references return True."""
        result, msgs = _run_check(
            {
                "mission_01.fsif": _FSIF_WITH_GOAL,
                "mission_02.fsif": _FSIF_WITH_EVENT,
            },
            [
                {"filename": "mission_01.fs2", "success_goal": "EscortConvoy"},
                {"filename": "mission_02.fs2", "success_event": "ConvoySafe"},
            ],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_first_mission_fails_second_still_checked(self):
        """Even if the first mission has a bad reference, the second is still checked."""
        result, msgs = _run_check(
            {
                "mission_01.fsif": _FSIF_WITH_GOAL,
                "mission_02.fsif": _FSIF_WITH_EVENT,
            },
            [
                {"filename": "mission_01.fs2", "success_goal": "BadGoal"},
                {"filename": "mission_02.fs2", "success_event": "BadEvent"},
            ],
        )
        self.assertFalse(result, msgs)
        # Both errors should appear
        error_msgs = [m for m in msgs if "[ERROR]" in m]
        self.assertGreaterEqual(len(error_msgs), 2, msgs)

    def test_mixed_valid_and_invalid_returns_false(self):
        """A valid mission followed by an invalid one returns False overall."""
        result, msgs = _run_check(
            {
                "mission_01.fsif": _FSIF_WITH_GOAL,
                "mission_02.fsif": _FSIF_WITH_EVENT,
            },
            [
                {"filename": "mission_01.fs2", "success_goal": "EscortConvoy"},  # valid
                {"filename": "mission_02.fs2", "success_event": "NonExistentEvent"},  # invalid
            ],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m and "NonExistentEvent" in m for m in msgs), msgs)

    def test_mission_without_condition_between_valid_missions_passes(self):
        """A mission with no condition in the middle of valid missions does not affect result."""
        result, msgs = _run_check(
            {
                "mission_01.fsif": _FSIF_WITH_GOAL,
                "mission_03.fsif": _FSIF_WITH_EVENT,
            },
            [
                {"filename": "mission_01.fs2", "success_goal": "EscortConvoy"},
                {"filename": "mission_02.fs2"},  # no condition, no fsif needed
                {"filename": "mission_03.fs2", "failure_event": "ConvoyDestroyed"},
            ],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)


# ===========================================================================
# Class 5: process_campaign integration
# ===========================================================================

_FCIF_TEMPLATE = """\
fcif_version: "1.0"
campaign:
  name: "Integration Test Campaign"
  description: "Testing advance condition references integration"
starting_loadout:
  ships: []
  weapons: []
missions:
{missions}
"""


def _build_integration_fcif(missions: list[dict]) -> str:
    lines = []
    for m in missions:
        lines.append(f'  - filename: "{m["filename"]}"')
        for field in ("success_goal", "failure_goal", "success_event", "failure_event"):
            if field in m and m[field] is not None:
                lines.append(f'    {field}: "{m[field]}"')
    return _FCIF_TEMPLATE.format(missions="\n".join(lines))


class TestProcessCampaignAdvanceConditionIntegration(unittest.TestCase):

    def _run_integration(self, fsif_files: dict, missions: list[dict]) -> tuple[bool, list]:
        """Write FSIF + FCIF files and invoke process_campaign(); return (result, msgs)."""
        with capture_logs() as msgs:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                fsif_dir = tmp_path / "fsif"
                fsif_dir.mkdir(parents=True, exist_ok=True)

                for name, content in fsif_files.items():
                    _write_file(fsif_dir, name, content)

                fcif_content = _build_integration_fcif(missions)
                fcif_path = tmp_path / "campaign.fcif"
                fcif_path.write_text(fcif_content, encoding="utf-8")
                output_path = tmp_path / "campaign.fc2"

                result = process_campaign(str(fcif_path), str(output_path))

        return result, msgs

    def test_process_campaign_succeeds_with_valid_references(self):
        """process_campaign returns True and writes .fc2 when all references are valid."""
        result, msgs = self._run_integration(
            {"mission_01.fsif": _FSIF_WITH_GOAL},
            [{"filename": "mission_01.fs2", "success_goal": "EscortConvoy"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_process_campaign_fails_with_invalid_goal_reference(self):
        """process_campaign returns False and no .fc2 is written when a goal reference is bad."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fsif_dir = tmp_path / "fsif"
            fsif_dir.mkdir(parents=True, exist_ok=True)
            _write_file(fsif_dir, "mission_01.fsif", _FSIF_WITH_GOAL)

            fcif_content = _build_integration_fcif(
                [{"filename": "mission_01.fs2", "success_goal": "Typo_EscortConvoy"}]
            )
            fcif_path = tmp_path / "campaign.fcif"
            fcif_path.write_text(fcif_content, encoding="utf-8")
            output_path = tmp_path / "campaign.fc2"

            with capture_logs() as msgs:
                result = process_campaign(str(fcif_path), str(output_path))

        self.assertFalse(result, msgs)
        self.assertFalse(output_path.exists(), "No .fc2 should be written on failure")
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_process_campaign_fails_with_invalid_event_reference(self):
        """process_campaign returns False when a success_event reference is invalid."""
        result, msgs = self._run_integration(
            {"mission_01.fsif": _FSIF_WITH_EVENT},
            [{"filename": "mission_01.fs2", "success_event": "NonExistentEvent"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_process_campaign_fails_with_missing_fsif_and_condition(self):
        """process_campaign returns False when the FSIF is absent for a mission with a condition."""
        result, msgs = self._run_integration(
            {},  # No FSIF files
            [{"filename": "mission_01.fs2", "failure_goal": "SomeGoal"}],
        )
        self.assertFalse(result, msgs)
        self.assertTrue(any("[ERROR]" in m for m in msgs), msgs)

    def test_process_campaign_succeeds_without_conditions(self):
        """process_campaign returns True when no missions have advance conditions."""
        result, msgs = self._run_integration(
            {},  # No FSIF needed since no conditions
            [{"filename": "mission_01.fs2"}, {"filename": "mission_02.fs2"}],
        )
        self.assertTrue(result, msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)


if __name__ == "__main__":
    unittest.main()
