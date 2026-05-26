"""
Regression tests for process_mission() load-failure handling.

Verifies that process_mission() returns False and logs a readable error
(rather than raising an unhandled exception) when the input .fsif file
contains:

1. Malformed YAML (YAML parse error)
2. An unknown / forbidden top-level field (Pydantic schema violation)
3. A missing required section
4. An unsupported fsif_version

See NeuralFS_analysis_report.md, P2:
"FSIF Entry Point Catches Only Some Load Failures" for background.
"""

import logging
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

from fsif_to_fs2 import process_mission  # noqa: E402 (path setup must come first)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp_fsif(content: str) -> str:
    """Write *content* to a temporary .fsif file and return its path string."""
    import atexit
    import tempfile as _tf

    tmp = _tf.NamedTemporaryFile(
        mode="w", suffix=".fsif", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    atexit.register(lambda p=tmp.name: Path(p).unlink(missing_ok=True))
    return tmp.name


# Minimal valid FSIF used as a baseline reference.
_MINIMAL_VALID = """\
fsif_version: "1.0"
mission_info:
  name: "Load Failure Test Mission"
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
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
mission_flow: {}
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestProcessMissionLoadFailures(unittest.TestCase):
    """process_mission() must return False cleanly for all expected load errors."""

    @classmethod
    def setUpClass(cls):
        # Suppress converter log output during tests to keep pytest output clean.
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Malformed YAML
    # ------------------------------------------------------------------

    def test_malformed_yaml_returns_false_not_exception(self):
        """
        A file with invalid YAML syntax must cause process_mission() to return
        False, not raise yaml.YAMLError or any other exception.
        """
        bad_yaml = "fsif_version: '1.0'\n  bad_indent:\n- broken"
        path = _write_temp_fsif(bad_yaml)

        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "out.fs2")
            result = process_mission(path, output_file=output)

        self.assertFalse(
            result,
            "process_mission() should return False for malformed YAML, not True."
        )

    # ------------------------------------------------------------------
    # Unknown field (Pydantic schema violation)
    # ------------------------------------------------------------------

    def test_unknown_top_level_field_returns_false_not_exception(self):
        """
        An FSIF file with an unknown top-level key causes a Pydantic
        ValidationError inside the loader, which is re-raised as ValueError.
        process_mission() must return False, not propagate the exception.
        """
        fsif_with_bad_field = _MINIMAL_VALID + "\nunknown_field: this_should_be_rejected\n"
        path = _write_temp_fsif(fsif_with_bad_field)

        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "out.fs2")
            result = process_mission(path, output_file=output)

        self.assertFalse(
            result,
            "process_mission() should return False for an unknown FSIF field, not True."
        )

    # ------------------------------------------------------------------
    # Missing required section
    # ------------------------------------------------------------------

    def test_missing_required_section_returns_false_not_exception(self):
        """
        An FSIF file that omits the required 'entities' section must cause
        process_mission() to return False, not raise.
        """
        fsif_missing_section = """\
fsif_version: "1.0"
mission_info:
  name: "No Entities Mission"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
mission_flow: {}
"""
        path = _write_temp_fsif(fsif_missing_section)

        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "out.fs2")
            result = process_mission(path, output_file=output)

        self.assertFalse(
            result,
            "process_mission() should return False for a missing required section, not True."
        )

    # ------------------------------------------------------------------
    # Unsupported fsif_version
    # ------------------------------------------------------------------

    def test_unsupported_version_returns_false_not_exception(self):
        """
        An FSIF file with a version string other than '1.0' must cause
        process_mission() to return False, not raise.
        """
        fsif_bad_version = _MINIMAL_VALID.replace(
            'fsif_version: "1.0"', 'fsif_version: "99.0"', 1
        )
        path = _write_temp_fsif(fsif_bad_version)

        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "out.fs2")
            result = process_mission(path, output_file=output)

        self.assertFalse(
            result,
            "process_mission() should return False for an unsupported FSIF version, not True."
        )

    # ------------------------------------------------------------------
    # Sanity: valid mission still succeeds
    # ------------------------------------------------------------------

    def test_valid_minimal_mission_returns_true(self):
        """
        A fully valid minimal FSIF must still convert successfully and return True.
        """
        path = _write_temp_fsif(_MINIMAL_VALID)

        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "out.fs2")
            result = process_mission(path, output_file=output)

        self.assertTrue(
            result,
            "process_mission() should return True for a valid minimal FSIF."
        )


if __name__ == "__main__":
    unittest.main()
