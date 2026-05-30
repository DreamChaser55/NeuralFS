"""
Tests for validate-only (log-only) mode in process_campaign().

Coverage:
  - process_campaign(validate_only=True) returns True for a valid FCIF and
    does not write a .fc2 file.
  - process_campaign(validate_only=True) returns False for an invalid FCIF and
    does not write a .fc2 file.
  - process_campaign(validate_only=True) does not write a .fc2 file to an
    explicit -o/--output path.
  - process_campaign(validate_only=False) (normal mode) writes a .fc2 file for
    a valid FCIF (sanity check confirming validate_only=True truly suppresses
    the output).
"""

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

from fcif_to_fc2 import process_campaign

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

# Minimal valid FCIF with no missions.  An empty missions list is valid; it
# skips the advance condition reference and loadout checks entirely so no FSIF
# files need to be present on disk.
_VALID_FCIF = """\
fcif_version: "1.0"
campaign:
  name: "Test Campaign"
  description: "A test campaign for validate-only mode."
starting_loadout:
  ships:
    - "GTF Ulysses"
  weapons:
    - "ML-16 Laser"
    - "MX-50"
missions: []
"""

# Invalid FCIF: the required 'campaign' field is missing, which causes a
# Pydantic ValidationError inside load_fcif() and makes process_campaign()
# return False immediately.
_INVALID_FCIF = """\
fcif_version: "1.0"
starting_loadout:
  ships: []
  weapons: []
missions: []
"""


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestValidateOnlyMode(unittest.TestCase):
    """Tests for the validate_only parameter of process_campaign()."""

    def setUp(self):
        # Suppress converter log output so test output is clean.
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_fcif(tmp_dir: Path, content: str, filename: str = "test.fcif") -> Path:
        """Write FCIF *content* to *tmp_dir*/*filename* and return the path."""
        fcif_path = tmp_dir / filename
        fcif_path.write_text(content, encoding="utf-8")
        return fcif_path

    # ------------------------------------------------------------------
    # validate_only=True with a valid FCIF
    # ------------------------------------------------------------------

    def test_validate_only_returns_true_for_valid_fcif(self):
        """validate_only=True returns True when the FCIF is valid."""
        with tempfile.TemporaryDirectory() as tmp:
            fcif_path = self._write_fcif(Path(tmp), _VALID_FCIF)
            result = process_campaign(str(fcif_path), validate_only=True)
            self.assertTrue(result)

    def test_validate_only_does_not_write_fc2_for_valid_fcif(self):
        """validate_only=True must not write a .fc2 file even on success."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fcif_path = self._write_fcif(tmp_path, _VALID_FCIF)
            expected_fc2 = fcif_path.with_suffix(".fc2")

            process_campaign(str(fcif_path), validate_only=True)

            self.assertFalse(
                expected_fc2.exists(),
                f".fc2 file was unexpectedly created at '{expected_fc2}' "
                f"in validate-only mode.",
            )

    def test_validate_only_ignores_explicit_output_path(self):
        """validate_only=True must not write to an explicit output_file path."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fcif_path = self._write_fcif(tmp_path, _VALID_FCIF)
            explicit_output = tmp_path / "should_not_exist.fc2"

            process_campaign(
                str(fcif_path),
                output_file=str(explicit_output),
                validate_only=True,
            )

            self.assertFalse(
                explicit_output.exists(),
                f"FC2 file was written to explicit output path '{explicit_output}' "
                f"even though validate_only=True was set.",
            )

    # ------------------------------------------------------------------
    # validate_only=True with an invalid FCIF
    # ------------------------------------------------------------------

    def test_validate_only_returns_false_for_invalid_fcif(self):
        """validate_only=True returns False when FCIF schema validation fails."""
        with tempfile.TemporaryDirectory() as tmp:
            fcif_path = self._write_fcif(Path(tmp), _INVALID_FCIF)
            result = process_campaign(str(fcif_path), validate_only=True)
            self.assertFalse(result)

    def test_validate_only_does_not_write_fc2_for_invalid_fcif(self):
        """validate_only=True must not write a .fc2 file when validation fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fcif_path = self._write_fcif(tmp_path, _INVALID_FCIF)
            expected_fc2 = fcif_path.with_suffix(".fc2")

            process_campaign(str(fcif_path), validate_only=True)

            self.assertFalse(
                expected_fc2.exists(),
                f".fc2 file was unexpectedly created at '{expected_fc2}' "
                f"despite validation failure in validate-only mode.",
            )

    # ------------------------------------------------------------------
    # Normal mode (validate_only=False) sanity check
    # ------------------------------------------------------------------

    def test_normal_mode_writes_fc2_for_valid_fcif(self):
        """Normal mode (validate_only=False) writes a .fc2 file on success.

        This sanity check confirms that validate_only=True genuinely suppresses
        file output — not that .fc2 files are never written under any condition.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fcif_path = self._write_fcif(tmp_path, _VALID_FCIF)
            expected_fc2 = fcif_path.with_suffix(".fc2")

            result = process_campaign(str(fcif_path), validate_only=False)

            self.assertTrue(result)
            self.assertTrue(
                expected_fc2.exists(),
                f".fc2 file was not written at '{expected_fc2}' in normal mode.",
            )


if __name__ == "__main__":
    unittest.main()
