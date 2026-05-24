"""
Regression test for the path constants in fetch_inworld_voices.py.

Verifies that ROOT_DIR, API_KEY_PATH, and OUTPUT_PATH all resolve under the
NeuralFS repository root, not under the common/ subdirectory where the script
resides.  No network calls are made.
"""
import sys
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — add repo root and the parsers_and_generators directory so the
# module can be imported regardless of where the test runner is invoked from.
# ---------------------------------------------------------------------------
_tests_dir = Path(__file__).resolve().parent          # common/parsers_and_generators/tests/
_pg_dir = _tests_dir.parent                           # common/parsers_and_generators/
_common_dir = _pg_dir.parent                          # common/
_repo_root = _common_dir.parent                       # NeuralFS/ (repository root)

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_pg_dir) not in sys.path:
    sys.path.insert(0, str(_pg_dir))

# fetch_inworld_voices imports the optional 'requests' library at module level.
# Guard the import so that the path tests are still skipped gracefully rather
# than crashing the entire test run when 'requests' is not installed.
_requests_available = True
try:
    import requests as _requests_check  # noqa: F401
except ImportError:
    _requests_available = False

_m = None
if _requests_available:
    import fetch_inworld_voices as _m

_skip_no_requests = unittest.skipUnless(
    _requests_available,
    "The 'requests' package is not installed; skipping path tests for "
    "fetch_inworld_voices.py (install it with: pip install requests).",
)


@_skip_no_requests
class TestFetchInworldVoicesPaths(unittest.TestCase):
    """Verify that all path constants in fetch_inworld_voices point to the
    repository root, not to the common/ subdirectory."""

    def test_root_dir_is_repository_root(self):
        """ROOT_DIR must resolve to the NeuralFS repository root."""
        self.assertEqual(
            _m.ROOT_DIR.resolve(),
            _repo_root.resolve(),
            f"ROOT_DIR should be the repo root ({_repo_root!r}), "
            f"got {_m.ROOT_DIR!r} instead. "
            f"The script is two levels below the repo root "
            f"(common/parsers_and_generators/), so parent.parent.parent is required.",
        )

    def test_root_dir_is_not_common_dir(self):
        """ROOT_DIR must not point to the common/ subdirectory."""
        self.assertNotEqual(
            _m.ROOT_DIR.resolve(),
            _common_dir.resolve(),
            "ROOT_DIR incorrectly resolves to common/ instead of the repo root. "
            "This was the original bug: parent.parent was used instead of "
            "parent.parent.parent.",
        )

    def test_api_key_path_under_repo_root(self):
        """API_KEY_PATH must be API_keys/Inworld_API_key.txt under the repo root."""
        expected = _repo_root / "API_keys" / "Inworld_API_key.txt"
        self.assertEqual(
            _m.API_KEY_PATH.resolve(),
            expected.resolve(),
            f"Expected API_KEY_PATH to be {expected!r}, got {_m.API_KEY_PATH!r}.",
        )

    def test_output_path_under_repo_root(self):
        """OUTPUT_PATH must be Documentation/Inworld TTS/voices.txt under the repo root."""
        expected = _repo_root / "Documentation" / "Inworld TTS" / "voices.txt"
        self.assertEqual(
            _m.OUTPUT_PATH.resolve(),
            expected.resolve(),
            f"Expected OUTPUT_PATH to be {expected!r}, got {_m.OUTPUT_PATH!r}.",
        )

    def test_api_key_path_not_under_common(self):
        """API_KEY_PATH must not resolve inside the common/ directory."""
        self.assertFalse(
            str(_m.API_KEY_PATH.resolve()).startswith(str(_common_dir.resolve())),
            f"API_KEY_PATH ({_m.API_KEY_PATH!r}) incorrectly resolves inside common/. "
            f"It should be under the repo root.",
        )

    def test_output_path_not_under_common(self):
        """OUTPUT_PATH must not resolve inside the common/ directory."""
        self.assertFalse(
            str(_m.OUTPUT_PATH.resolve()).startswith(str(_common_dir.resolve())),
            f"OUTPUT_PATH ({_m.OUTPUT_PATH!r}) incorrectly resolves inside common/. "
            f"It should be under the repo root.",
        )


if __name__ == "__main__":
    unittest.main()
