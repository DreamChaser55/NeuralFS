"""Tests for the sanitize_path() utility function.

Covers:
- Paths with spaces are preserved unchanged.
- Only the outermost pair of double-quote characters is stripped.
"""

import unittest

from common.utils import sanitize_path
from _fsif_test_helpers import SilencedTestCase


class SanitizePathTesting(SilencedTestCase):

    def test_sanitize_path_preserves_spaces(self):
        raw = 'missions\\ambient light testing\\white.fsif'
        self.assertEqual(sanitize_path(raw), raw)

    def test_sanitize_path_strips_only_outer_quotes(self):
        raw = '"missions\\ambient light testing\\white.fsif"'
        self.assertEqual(sanitize_path(raw), 'missions\\ambient light testing\\white.fsif')


if __name__ == "__main__":
    unittest.main()
