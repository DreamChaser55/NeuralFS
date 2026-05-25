"""
Regression tests for type-guard enforcement in vector/orientation normalizers.

The helpers _normalize_vector, _normalize_sun_angles, and _normalize_orientation
must explicitly reject non-sequence inputs (strings, bytes, dicts, arbitrary
iterables) instead of silently mis-interpreting them.

These tests pin that contract so future refactors cannot accidentally regress
the clear-error behaviour introduced alongside the P2 finding:
"FSIF Vector/Orientation Normalizers Accept Arbitrary Iterables".
"""
import sys
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
_repo_root = _converter_dir.parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from pydantic import ValidationError
from data_models import (
    Ship,
    Wing,
    Sun,
    BackgroundBitmap,
    JumpNode,
    AsteroidField,
    _normalize_vector,
    _normalize_sun_angles,
    _normalize_orientation,
)


# ---------------------------------------------------------------------------
# Direct normalizer unit tests
# ---------------------------------------------------------------------------

class NormalizeVectorTypeGuardTests(unittest.TestCase):
    """_normalize_vector must reject non-list/tuple inputs early."""

    # --- Valid inputs should still work ---

    def test_accepts_list_of_three_floats(self):
        self.assertEqual(_normalize_vector([1.0, 2.5, -3.0]), [1.0, 2.5, -3.0])

    def test_accepts_tuple_of_three_floats(self):
        self.assertEqual(_normalize_vector((0.0, 100.0, -50.0)), [0.0, 100.0, -50.0])

    def test_accepts_list_of_three_ints(self):
        self.assertEqual(_normalize_vector([0, 0, 0]), [0.0, 0.0, 0.0])

    # --- Invalid types must raise ValueError with clear message ---

    def test_rejects_string_even_if_length_3(self):
        """A 3-character string must not be accepted as 3 coordinates."""
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector("abc")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_numeric_string(self):
        """A string of digits must not silently pass as a coordinate list."""
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector("123")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_bytes(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector(b"\x01\x02\x03")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_dict(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector({"x": 1.0, "y": 2.0, "z": 3.0})
        self.assertIn("mapping", str(ctx.exception).lower())

    def test_rejects_generator(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector(x for x in [0.0, 0.0, 0.0])
        self.assertIn("list", str(ctx.exception).lower())

    def test_rejects_none(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector(None)
        self.assertIn("None", str(ctx.exception))

    def test_rejects_scalar_integer(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector(42)
        self.assertIn("list", str(ctx.exception).lower())

    def test_rejects_wrong_length_list(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_vector([1.0, 2.0])
        self.assertIn("element", str(ctx.exception).lower())


class NormalizeSunAnglesTypeGuardTests(unittest.TestCase):
    """_normalize_sun_angles must reject non-list/tuple inputs early."""

    def test_accepts_list_of_two_floats(self):
        self.assertEqual(_normalize_sun_angles([0.087266, 2.356194]), [0.087266, 2.356194])

    def test_accepts_tuple_of_two_floats(self):
        self.assertEqual(_normalize_sun_angles((0.0, 1.0)), [0.0, 1.0])

    def test_rejects_two_char_string(self):
        """A 2-character string must not be accepted as 2 angle values."""
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles("ab")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_numeric_string(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles("12")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_bytes(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles(b"\x01\x02")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_dict(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles({"pitch": 0.0, "heading": 1.0})
        self.assertIn("mapping", str(ctx.exception).lower())

    def test_rejects_generator(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles(x for x in [0.0, 1.0])
        self.assertIn("list", str(ctx.exception).lower())

    def test_rejects_none(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles(None)
        self.assertIn("None", str(ctx.exception))

    def test_rejects_wrong_length_list(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_sun_angles([0.0, 1.0, 2.0])
        self.assertIn("element", str(ctx.exception).lower())


class NormalizeOrientationTypeGuardTests(unittest.TestCase):
    """_normalize_orientation must reject non-list/tuple inputs early."""

    _IDENTITY = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    _IDENTITY_NESTED = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    def test_accepts_flat_9_element_list(self):
        self.assertEqual(_normalize_orientation(self._IDENTITY), self._IDENTITY)

    def test_accepts_flat_9_element_tuple(self):
        self.assertEqual(
            _normalize_orientation(tuple(self._IDENTITY)),
            self._IDENTITY,
        )

    def test_accepts_nested_3x3_list(self):
        self.assertEqual(_normalize_orientation(self._IDENTITY_NESTED), self._IDENTITY)

    def test_rejects_9_char_string(self):
        """A 9-character string must not be accepted as 9 orientation floats."""
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation("123456789")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_short_string(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation("abc")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_bytes(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09")
        self.assertIn("string", str(ctx.exception).lower())

    def test_rejects_dict(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation({"r0": [1, 0, 0], "r1": [0, 1, 0], "r2": [0, 0, 1]})
        self.assertIn("mapping", str(ctx.exception).lower())

    def test_rejects_generator(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation(float(i) for i in range(9))
        self.assertIn("list", str(ctx.exception).lower())

    def test_rejects_none(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation(None)
        self.assertIn("None", str(ctx.exception))

    def test_rejects_scalar_integer(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation(42)
        self.assertIn("list", str(ctx.exception).lower())

    def test_rejects_wrong_length_flat_list(self):
        with self.assertRaises(ValueError) as ctx:
            _normalize_orientation([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        self.assertIn("9 elements", str(ctx.exception))


# ---------------------------------------------------------------------------
# Pydantic model integration: Ship.position
# ---------------------------------------------------------------------------

class ShipPositionTypeGuardTests(unittest.TestCase):
    """Ship.position must reject invalid container types via _normalize_vector."""

    def _base_ship(self, position):
        return Ship.model_validate({
            "name": "Test Ship",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": position,
            "arrival_cue": "( true )",
        })

    def test_accepts_valid_position_list(self):
        ship = self._base_ship([100.0, 0.0, 200.0])
        self.assertEqual(ship.position, [100.0, 0.0, 200.0])

    def test_rejects_string_position(self):
        """Ship position authored as a plain string must raise a validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            self._base_ship("100 0 200")

    def test_rejects_dict_position(self):
        """Ship position authored as a dict must raise a validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            self._base_ship({"x": 100.0, "y": 0.0, "z": 200.0})

    def test_rejects_scalar_position(self):
        """Ship position authored as a bare number must raise a validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            self._base_ship(42)


# ---------------------------------------------------------------------------
# Pydantic model integration: Ship.orientation
# ---------------------------------------------------------------------------

class ShipOrientationTypeGuardTests(unittest.TestCase):
    """Ship.orientation must reject invalid container types via _normalize_orientation."""

    def _base_ship_with_orientation(self, orientation):
        return Ship.model_validate({
            "name": "Test Ship",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "orientation": orientation,
            "arrival_cue": "( true )",
        })

    def test_accepts_valid_flat_orientation(self):
        ori = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        ship = self._base_ship_with_orientation(ori)
        self.assertEqual(ship.orientation, ori)

    def test_accepts_valid_nested_orientation(self):
        ori = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        ship = self._base_ship_with_orientation(ori)
        self.assertEqual(ship.orientation, [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])

    def test_rejects_string_orientation(self):
        """Orientation authored as a string must raise a validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            self._base_ship_with_orientation("123456789")

    def test_rejects_dict_orientation(self):
        """Orientation authored as a dict must raise a validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            self._base_ship_with_orientation({"r0": [1, 0, 0]})

    def test_rejects_scalar_orientation(self):
        """Orientation authored as a bare number must raise a validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            self._base_ship_with_orientation(1)


# ---------------------------------------------------------------------------
# Pydantic model integration: Sun.angles
# ---------------------------------------------------------------------------

class SunAnglesTypeGuardTests(unittest.TestCase):
    """Sun.angles must reject invalid container types via _normalize_sun_angles."""

    def test_accepts_valid_list(self):
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        self.assertEqual(sun.angles, [0.087266, 2.356194])

    def test_rejects_string_angles(self):
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": "12"})

    def test_rejects_dict_angles(self):
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": {"pitch": 0.0, "heading": 1.0}})

    def test_rejects_scalar_angles(self):
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": 0.5})


# ---------------------------------------------------------------------------
# Pydantic model integration: BackgroundBitmap.angles
# ---------------------------------------------------------------------------

class BackgroundBitmapAnglesTypeGuardTests(unittest.TestCase):
    """BackgroundBitmap.angles uses _normalize_vector and must reject invalid types."""

    def test_accepts_valid_list(self):
        bm = BackgroundBitmap.model_validate(
            {"texture": "neb02", "angles": [0.0, 2.321286, 0.0]}
        )
        self.assertEqual(len(bm.angles), 3)

    def test_rejects_string_angles(self):
        with self.assertRaises((ValidationError, ValueError)):
            BackgroundBitmap.model_validate({"texture": "neb02", "angles": "abc"})

    def test_rejects_dict_angles(self):
        with self.assertRaises((ValidationError, ValueError)):
            BackgroundBitmap.model_validate(
                {"texture": "neb02", "angles": {"pitch": 0.0, "bank": 0.0, "heading": 1.0}}
            )


if __name__ == "__main__":
    unittest.main()
