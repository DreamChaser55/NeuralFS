import unittest
import sys
import tempfile
from pathlib import Path

# Add Fiction_Viewer_Validator/ to sys.path so the validator can be imported
# regardless of where the test runner is invoked from.
_current_dir = Path(__file__).resolve().parent          # Fiction_Viewer_Validator/tests/
_parent_dir = _current_dir.parent                       # Fiction_Viewer_Validator/
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from fiction_viewer_validator import FictionViewerValidator


class TestNonAsciiDetection(unittest.TestCase):
    """
    Tests that verify the core bug fix: non-ASCII bytes are reported with their
    actual hex values and byte offsets, not as the Unicode replacement character
    U+FFFD that would appear when decoding with errors='replace'.
    """

    def _run(self, raw: bytes) -> FictionViewerValidator:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "story.txt"
            p.write_bytes(raw)
            v = FictionViewerValidator(p)
            v.validate()
        return v

    def test_non_utf8_byte_reports_actual_hex_value(self):
        """
        0x97 is a Windows-1252 em dash; it is not valid UTF-8.
        The error must name '0x97', not 'U+FFFD' (the replacement character
        that would appear if the file were decoded with errors='replace').
        """
        v = self._run(b"Hello \x97 world")

        self.assertEqual(len(v.errors), 1, v.errors)
        self.assertIn("0x97", v.errors[0])
        self.assertNotIn("U+FFFD", v.errors[0])
        self.assertNotIn("\\ufffd", v.errors[0])

    def test_non_ascii_error_shows_byte_offset(self):
        """
        The reported byte offset must match the actual position in the file
        so the user can locate the byte with a hex editor.
        """
        # b"prefix" is 6 bytes, so 0x97 is at byte offset 6.
        v = self._run(b"prefix\x97")

        self.assertFalse(v.errors == [], v.errors)
        self.assertIn("byte offset 6", v.errors[0])

    def test_utf8_non_ascii_reports_individual_bytes(self):
        """
        A valid UTF-8 non-ASCII character (curly quote U+2018, encoded as
        0xE2 0x80 0x98) must be reported as three separate byte entries,
        each with its correct hex value.
        """
        v = self._run("It\u2018s a test".encode("utf-8"))   # b"It\xe2\x80\x98s a test"

        self.assertFalse(v.errors == [], v.errors)
        error_text = v.errors[0]
        self.assertIn("0xE2", error_text)
        self.assertIn("0x80", error_text)
        self.assertIn("0x98", error_text)

    def test_multiple_non_ascii_bytes_all_reported(self):
        """
        Multiple non-ASCII bytes in the same file must all be listed.
        """
        # 0x97 at offset 0, 0x96 at offset 4
        v = self._run(b"\x97abc\x96")

        self.assertFalse(v.errors == [], v.errors)
        error_text = v.errors[0]
        self.assertIn("0x97", error_text)
        self.assertIn("0x96", error_text)
        self.assertIn("byte offset 0", error_text)
        self.assertIn("byte offset 4", error_text)


class TestCleanFile(unittest.TestCase):
    """Regression: a pure-ASCII file must pass without errors or warnings."""

    def test_clean_ascii_file_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "story.txt"
            p.write_bytes(b"This is a clean ASCII story.\nNo issues here.\n")
            v = FictionViewerValidator(p)
            result = v.validate()

        self.assertTrue(result)
        self.assertEqual(v.errors, [])
        self.assertEqual(v.warnings, [])


class TestFictionViewerStringCheck(unittest.TestCase):
    """Regression: the 'fiction viewer' phrase check still works."""

    def test_fiction_viewer_string_triggers_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "story.txt"
            p.write_bytes(b"This text mentions fiction viewer in it.")
            v = FictionViewerValidator(p)
            result = v.validate()

        # Warning only — not an error, so validate() returns True.
        self.assertTrue(result)
        self.assertEqual(v.errors, [])
        self.assertTrue(
            any("fiction viewer" in w.lower() for w in v.warnings),
            v.warnings,
        )

    def test_fiction_viewer_string_absent_no_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "story.txt"
            p.write_bytes(b"Normal story text with no internal feature names.")
            v = FictionViewerValidator(p)
            v.validate()

        self.assertFalse(
            any("fiction viewer" in w.lower() for w in v.warnings),
            v.warnings,
        )


class TestSpanTagCheck(unittest.TestCase):
    """Regression: span-style color tag validation still works."""

    def test_unclosed_span_tag_triggers_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "story.txt"
            p.write_bytes(b"Engage $f{ Alpha Wing and destroy the enemy.")
            v = FictionViewerValidator(p)
            result = v.validate()

        # Warning only — not an error.
        self.assertTrue(result)
        self.assertEqual(v.errors, [])
        self.assertTrue(
            any("unclosed" in w.lower() or "$f{" in w for w in v.warnings),
            v.warnings,
        )

    def test_closed_span_tag_no_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "story.txt"
            p.write_bytes(b"Engage $f{ Alpha Wing $} and destroy the enemy.")
            v = FictionViewerValidator(p)
            v.validate()

        self.assertEqual(v.errors, [])
        self.assertFalse(
            any("unclosed" in w.lower() for w in v.warnings),
            v.warnings,
        )


class TestErrorHandling(unittest.TestCase):
    """Regression: attempting to validate a missing file returns False."""

    def test_nonexistent_file_returns_false(self):
        p = Path("/nonexistent/path/that/does/not/exist.txt")
        v = FictionViewerValidator(p)
        result = v.validate()

        self.assertFalse(result)
        self.assertTrue(len(v.errors) > 0, "Expected at least one error for a missing file")


if __name__ == "__main__":
    unittest.main()
