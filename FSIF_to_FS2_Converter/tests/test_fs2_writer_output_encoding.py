"""
Regression tests for FS2Writer output encoding and newline determinism.

Verifies that write_mission() produces a file with:
- Explicit UTF-8 encoding (decodeable without errors).
- LF-only newlines (no CRLF bytes) so output is byte-for-byte identical on
  Windows and Linux regardless of the platform's default text-mode behavior.

See NeuralFS_analysis_report.md, fs2_writer.py section:
  'open(self.output_path, 'w') uses the platform default encoding and newline
  behavior ... explicit encoding='utf-8', newline='\\n' would make output
  deterministic across Windows and Linux.'
"""

import sys
import tempfile
import unittest
from pathlib import Path

# FSIF_to_FS2_Converter/tests/ -> FSIF_to_FS2_Converter/ -> repo root
_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
_repo_root = _converter_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from data_models import (
    Environment,
    Mission,
    MissionInfo,
    PlayerSetup,
    Ship,
    Weapons,
    Wing,
)
from fs2_writer import FS2Writer


def _make_minimal_mission() -> Mission:
    """Return a minimal valid Mission that FS2Writer can write without errors."""
    player_ship = Ship.model_validate(
        {
            "name": "Alpha 1",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "arrival_cue": "( true )",
            "weapons": Weapons(
                primary=["Avenger", "Avenger"],
                secondary=["MX-50"],
            ),
        }
    )
    alpha_wing = Wing(
        name="Alpha",
        count=1,
        ships=[player_ship],
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )
    return Mission(
        mission_info=MissionInfo(name="Encoding Test Mission"),
        player_setup=PlayerSetup(start_ship="Alpha 1", additional_ship_choices=[]),
        environment=Environment(),
        ships=[player_ship],
        wings=[alpha_wing],
    )


class TestFS2WriterOutputEncoding(unittest.TestCase):
    """FS2Writer must write UTF-8 files with LF-only line endings."""

    def _write_to_temp(self) -> bytes:
        """Write a minimal mission and return the raw bytes of the output file."""
        mission = _make_minimal_mission()
        with tempfile.NamedTemporaryFile(
            suffix=".fs2", delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            writer = FS2Writer(mission, tmp_path)
            writer.write_mission()
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_output_contains_no_crlf_sequences(self):
        """
        The .fs2 file must not contain Windows-style CRLF (\\r\\n) sequences.

        On Windows, Python's default text mode inserts \\r\\n for every \\n
        written. Specifying newline='\\n' suppresses this translation and
        ensures cross-platform byte-identical output.
        """
        raw = self._write_to_temp()
        self.assertNotIn(
            b"\r\n",
            raw,
            "FS2Writer output must not contain CRLF (\\r\\n) sequences. "
            "Use newline='\\n' in the open() call to suppress platform newline translation.",
        )

    def test_output_contains_lf_newlines(self):
        """
        The .fs2 file must use LF (\\n) as the line terminator.

        This is a sanity check that the file actually contains newlines (i.e.,
        the writer is not producing a single-line file) and that they are
        LF-style.
        """
        raw = self._write_to_temp()
        # Bare \n not preceded by \r — filter out any \r\n first to isolate bare \n
        stripped = raw.replace(b"\r\n", b"")
        self.assertIn(
            b"\n",
            stripped,
            "FS2Writer output must contain LF (\\n) newlines.",
        )

    def test_output_is_valid_utf8(self):
        """
        The .fs2 file must be decodeable as valid UTF-8.

        The converter validates that all FSO-facing strings are ASCII, so the
        content will in practice be ASCII-only. Regardless, the file handle
        must be opened with encoding='utf-8' for explicit, deterministic
        behavior rather than relying on the platform locale.
        """
        raw = self._write_to_temp()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.fail(
                f"FS2Writer output is not valid UTF-8: {exc}. "
                "Use encoding='utf-8' in the open() call."
            )


if __name__ == "__main__":
    unittest.main()
