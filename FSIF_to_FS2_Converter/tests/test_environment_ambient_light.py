"""Tests for Environment ambient_light_level RGB validation.

Covers:
- RGB channel value out of range 0..255 is rejected.
- Non-3-element list is rejected.
- Packed integer input is rejected with an actionable message.
"""

import unittest

from data_models import Environment
from _fsif_test_helpers import SilencedTestCase


class EnvironmentAmbientLightTesting(SilencedTestCase):

    def test_environment_rejects_invalid_rgb_channel_range(self):
        with self.assertRaises(ValueError) as ctx:
            Environment(ambient_light_level=[256, 0, 0])

        self.assertIn("out of range 0..255", str(ctx.exception))

    def test_environment_rejects_invalid_rgb_shape(self):
        with self.assertRaises(ValueError) as ctx:
            Environment(ambient_light_level=[10, 10])

        self.assertIn("3-item RGB list", str(ctx.exception))

    def test_environment_rejects_packed_integer_input(self):
        with self.assertRaises(ValueError) as ctx:
            Environment.model_validate({"ambient_light_level": 657930})

        self.assertIn("ambient_light_level must be authored as [red, green, blue]", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
