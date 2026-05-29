"""Tests for validate_mission_filename_length() in MiscChecksMixin.

Covers:
- A .fs2 filename longer than 30 characters is rejected with a clear error.
- A .fs2 filename exactly 30 characters long passes validation.
- A .fs2 filename of 31 characters (one over the limit) is rejected.
- A short .fs2 filename passes validation.
- When no fsif_path is provided the check is a no-op (passes).
"""

import unittest
import yaml
from pathlib import Path

from _fsif_test_helpers import REPO_ROOT, SilencedTestCase, make_valid_mission
from validator import Validator


def _make_empty_yaml_root() -> yaml.MappingNode:
    """Return an empty YAML MappingNode so validate_sexp_styles skips file I/O."""
    return yaml.MappingNode(tag='tag:yaml.org,2002:map', value=[])


def _make_validator_with_stem(stem: str) -> Validator:
    """Return a Validator whose fsif_path resolves to <stem>.fs2 as output name."""
    mission = make_valid_mission()
    fsif_path = Path(stem + ".fsif")
    return Validator(mission, REPO_ROOT, fsif_path=fsif_path, fsif_root_node=_make_empty_yaml_root())


class MissionFilenameLengthTests(SilencedTestCase):

    # ------------------------------------------------------------------
    # Failing cases
    # ------------------------------------------------------------------

    def test_filename_31_chars_is_rejected(self):
        # stem = 27 chars  →  .fs2 output name = 27 + 4 = 31 chars  →  error
        stem = "a" * 27
        fs2_name = stem + ".fs2"
        self.assertEqual(len(fs2_name), 31)

        validator = _make_validator_with_stem(stem)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any(
                f"'{fs2_name}'" in error and "30 characters" in error
                for error in validator.errors
            ),
            validator.errors,
        )

    def test_long_filename_is_rejected(self):
        # A clearly oversized name (50-char stem)
        stem = "my_very_long_mission_filename_that_is_way_too_long"
        fs2_name = stem + ".fs2"
        self.assertGreater(len(fs2_name), 30)

        validator = _make_validator_with_stem(stem)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any(
                f"'{fs2_name}'" in error and "30 characters" in error
                for error in validator.errors
            ),
            validator.errors,
        )

    # ------------------------------------------------------------------
    # Passing cases
    # ------------------------------------------------------------------

    def test_filename_exactly_30_chars_passes(self):
        # stem = 26 chars  →  .fs2 output name = 26 + 4 = 30 chars  →  OK
        stem = "a" * 26
        fs2_name = stem + ".fs2"
        self.assertEqual(len(fs2_name), 30)

        validator = _make_validator_with_stem(stem)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any("30 characters" in error for error in validator.errors),
            validator.errors,
        )

    def test_short_filename_passes(self):
        # Typical short mission filename
        validator = _make_validator_with_stem("my_mission")
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any("30 characters" in error for error in validator.errors),
            validator.errors,
        )

    def test_no_fsif_path_skips_check(self):
        # When fsif_path is omitted the check must be a no-op
        mission = make_valid_mission()
        validator = Validator(mission, REPO_ROOT)  # no fsif_path
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any("30 characters" in error for error in validator.errors),
            validator.errors,
        )


if __name__ == "__main__":
    unittest.main()
