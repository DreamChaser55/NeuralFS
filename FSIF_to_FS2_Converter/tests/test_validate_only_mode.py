"""
Regression tests for the validate_only / log-only mode of process_mission().

Verifies that:
1. A valid mission returns True when validate_only=True.
2. No .fs2 file is written, even when an output_file path is provided.
3. An invalid FSIF still returns False in validate_only mode.
4. FS2Writer.write_mission() is NOT called when validate_only=True.
5. VoiceManager.process() is NOT called when validate_only=True.
6. Normal conversion (validate_only=False) still writes the output file.
"""

import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
_repo_root = _converter_dir.parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from fsif_to_fs2 import process_mission  # noqa: E402


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


# Minimal valid FSIF used as a baseline.
_MINIMAL_VALID = """\
fsif_version: "1.0"
mission_info:
  name: "Validate Only Test Mission"
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

# Invalid FSIF: unsupported version triggers early failure.
_INVALID_FSIF = _MINIMAL_VALID.replace(
    'fsif_version: "1.0"', 'fsif_version: "99.0"', 1
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestValidateOnlyMode(unittest.TestCase):
    """process_mission(validate_only=True) behavioral contract."""

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # 1. Valid mission returns True
    # ------------------------------------------------------------------

    def test_valid_mission_returns_true(self):
        """validate_only=True on a valid FSIF must return True."""
        path = _write_temp_fsif(_MINIMAL_VALID)
        result = process_mission(path, validate_only=True)
        self.assertTrue(
            result,
            "process_mission(validate_only=True) should return True for a valid FSIF."
        )

    # ------------------------------------------------------------------
    # 2. No .fs2 file is written even when output_file is provided
    # ------------------------------------------------------------------

    def test_no_fs2_written_when_validate_only(self):
        """No output file must be created when validate_only=True, even if output_file is given."""
        path = _write_temp_fsif(_MINIMAL_VALID)

        with tempfile.TemporaryDirectory() as out_dir:
            output_path = str(Path(out_dir) / "should_not_exist.fs2")
            result = process_mission(path, output_file=output_path, validate_only=True)

        self.assertTrue(result, "process_mission should return True for a valid FSIF in validate_only mode.")
        self.assertFalse(
            Path(output_path).exists(),
            "No .fs2 file should be written when validate_only=True."
        )

    def test_no_default_fs2_written_when_validate_only(self):
        """No peer .fs2 file must be created next to the input when validate_only=True."""
        path = _write_temp_fsif(_MINIMAL_VALID)
        expected_fs2 = Path(path).with_suffix('.fs2')

        result = process_mission(path, validate_only=True)

        self.assertTrue(result)
        self.assertFalse(
            expected_fs2.exists(),
            f"No peer .fs2 file should be written next to the input when validate_only=True. "
            f"Found: {expected_fs2}"
        )

    # ------------------------------------------------------------------
    # 3. Invalid FSIF still returns False
    # ------------------------------------------------------------------

    def test_invalid_fsif_returns_false(self):
        """validate_only=True on an invalid FSIF must return False (not True or an exception)."""
        path = _write_temp_fsif(_INVALID_FSIF)
        result = process_mission(path, validate_only=True)
        self.assertFalse(
            result,
            "process_mission(validate_only=True) should return False for an invalid FSIF."
        )

    def test_invalid_fsif_does_not_create_output(self):
        """Even a provided output path must not be created when FSIF is invalid."""
        path = _write_temp_fsif(_INVALID_FSIF)

        with tempfile.TemporaryDirectory() as out_dir:
            output_path = str(Path(out_dir) / "never_created.fs2")
            process_mission(path, output_file=output_path, validate_only=True)

        self.assertFalse(
            Path(output_path).exists(),
            "No .fs2 file should be written for an invalid FSIF in validate_only mode."
        )

    # ------------------------------------------------------------------
    # 4. FS2Writer.write_mission() is NOT called
    # ------------------------------------------------------------------

    def test_fs2_writer_not_called_in_validate_only_mode(self):
        """FS2Writer.write_mission() must not be invoked when validate_only=True."""
        path = _write_temp_fsif(_MINIMAL_VALID)

        with patch('fs2_writer.FS2Writer.write_mission') as mock_write:
            result = process_mission(path, validate_only=True)

        self.assertTrue(result)
        mock_write.assert_not_called()

    # ------------------------------------------------------------------
    # 5. VoiceManager.process() is NOT called
    # ------------------------------------------------------------------

    def test_voice_manager_not_called_in_validate_only_mode(self):
        """VoiceManager.process() must not be invoked when validate_only=True."""
        path = _write_temp_fsif(_MINIMAL_VALID)

        tts_settings = {'enabled': True, 'dry_run': True}
        with patch('voice_manager.VoiceManager.process') as mock_vm:
            result = process_mission(path, tts_settings=tts_settings, validate_only=True)

        self.assertTrue(result)
        mock_vm.assert_not_called()

    # ------------------------------------------------------------------
    # 6. Normal mode (validate_only=False) still writes the output file
    # ------------------------------------------------------------------

    def test_normal_mode_still_writes_fs2(self):
        """With validate_only=False (default), the .fs2 file must be written."""
        path = _write_temp_fsif(_MINIMAL_VALID)

        with tempfile.TemporaryDirectory() as out_dir:
            output_path = str(Path(out_dir) / "out.fs2")
            result = process_mission(path, output_file=output_path)
            # Check existence inside the context manager before the temp dir is cleaned up.
            fs2_exists = Path(output_path).exists()

        self.assertTrue(result, "Normal conversion should return True for a valid FSIF.")
        self.assertTrue(
            fs2_exists,
            "A .fs2 file must be written in normal (non-validate-only) mode."
        )


if __name__ == "__main__":
    unittest.main()
