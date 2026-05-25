"""
Regression tests for mission_loader._read_yaml() hardening and raw-data
mutation prevention.

Covers:
1. YAML parse error → clear ValueError with file context
2. Root YAML list  → clear ValueError (not AttributeError)
3. Root YAML scalar → clear ValueError (not AttributeError)
4. Empty YAML file  → treated as empty mapping; fails on missing required
   sections (not on dict.get AttributeError)
5. Asteroid-field normalization does NOT mutate self.data
   (bounds key must survive, min_vec/max_vec must NOT appear)
6. Wing initial_orders normalization does NOT mutate self.data
   (raw YAML value must be the bare SEXP, not the wrapped form)
7. Valid mission still loads without error (smoke test)
"""

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

from mission_loader import MissionLoader, load_mission_from_fsif


# ---------------------------------------------------------------------------
# Minimal valid FSIF used as the base for several tests.
# ---------------------------------------------------------------------------

_MINIMAL_VALID = """\
fsif_version: "1.0"
mission_info:
  name: "Test Mission"
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

# FSIF with an asteroid field that uses `bounds`.
_MINIMAL_WITH_ASTEROID_FIELD = """\
fsif_version: "1.0"
mission_info:
  name: "Asteroid Test"
environment:
  ambient_light_level: [0, 0, 0]
  asteroid_field:
    object_type: "asteroid"
    behavior: "passive"
    num_objects: 10
    average_speed: 5.0
    bounds:
      min: [-500.0, -500.0, -500.0]
      max: [500.0, 500.0, 500.0]
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

# FSIF with a wing that has initial_orders.
_MINIMAL_WITH_WING_ORDERS = """\
fsif_version: "1.0"
mission_info:
  name: "Orders Test"
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
      initial_orders: |
        ( ai-chase-any 89 )
mission_flow: {}
"""


def _write_and_load(fsif_text: str):
    """Write FSIF text to a temp file, return the loaded MissionLoader."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "mission.fsif"
        path.write_text(fsif_text, encoding="utf-8")
        loader = MissionLoader(str(path))
        loader.load()
        return loader


def _write_temp(fsif_text: str) -> str:
    """Write FSIF text to a persistent temp file and return its path."""
    import atexit, tempfile as _tf
    tmp = _tf.NamedTemporaryFile(
        mode="w", suffix=".fsif", delete=False, encoding="utf-8"
    )
    tmp.write(fsif_text)
    tmp.close()
    atexit.register(lambda p=tmp.name: Path(p).unlink(missing_ok=True))
    return tmp.name


class TestReadYamlHardening(unittest.TestCase):
    """_read_yaml() must reject bad YAML and non-mapping roots cleanly."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Malformed YAML
    # ------------------------------------------------------------------

    def test_malformed_yaml_raises_value_error_with_file_context(self):
        """A YAML syntax error must raise ValueError mentioning the file path."""
        bad_yaml = "fsif_version: '1.0'\n  bad_indent:\n- broken"
        path = _write_temp(bad_yaml)
        with self.assertRaises(ValueError) as ctx:
            MissionLoader(path).load()
        msg = str(ctx.exception)
        self.assertIn("Invalid YAML in FSIF file", msg,
                      f"Expected 'Invalid YAML in FSIF file' in: {msg}")
        # The path name (stem) should appear in the error so the user knows
        # which file caused the problem.
        self.assertIn(Path(path).name, msg,
                      f"Expected file name in error: {msg}")

    # ------------------------------------------------------------------
    # Root is a list
    # ------------------------------------------------------------------

    def test_root_list_raises_value_error_not_attribute_error(self):
        """A YAML file whose root is a list must raise ValueError, not AttributeError."""
        root_list_yaml = "- item1\n- item2\n"
        path = _write_temp(root_list_yaml)
        with self.assertRaises(ValueError) as ctx:
            MissionLoader(path).load()
        msg = str(ctx.exception)
        self.assertIn("FSIF root document must be a YAML mapping", msg,
                      f"Expected mapping error message, got: {msg}")
        self.assertIn("list", msg,
                      f"Expected 'list' in error message, got: {msg}")

    # ------------------------------------------------------------------
    # Root is a scalar
    # ------------------------------------------------------------------

    def test_root_scalar_raises_value_error_not_attribute_error(self):
        """A YAML file whose root is a bare string must raise ValueError."""
        scalar_yaml = "just a plain string\n"
        path = _write_temp(scalar_yaml)
        with self.assertRaises(ValueError) as ctx:
            MissionLoader(path).load()
        msg = str(ctx.exception)
        self.assertIn("FSIF root document must be a YAML mapping", msg,
                      f"Expected mapping error message, got: {msg}")

    # ------------------------------------------------------------------
    # Empty file → treated as empty mapping, fails on required sections
    # ------------------------------------------------------------------

    def test_empty_yaml_fails_on_required_sections_not_attribute_error(self):
        """An empty YAML file must fail with a 'Missing required section' error."""
        path = _write_temp("")
        with self.assertRaises(ValueError) as ctx:
            MissionLoader(path).load()
        msg = str(ctx.exception)
        # Should fail on fsif_version or required sections, not AttributeError
        self.assertFalse(
            isinstance(ctx.exception, AttributeError),
            "Expected ValueError, not AttributeError"
        )
        # Must reference a field or section name in the error
        has_context = any(
            tok in msg
            for tok in ("fsif_version", "mission_info", "environment",
                        "player_setup", "entities", "mission_flow",
                        "required")
        )
        self.assertTrue(has_context,
                        f"Expected a meaningful missing-field error, got: {msg}")

    # ------------------------------------------------------------------
    # Valid mission still loads (smoke)
    # ------------------------------------------------------------------

    def test_valid_mission_loads_without_error(self):
        """A well-formed minimal FSIF must load without error."""
        import logging
        logging.disable(logging.NOTSET)
        try:
            loader = _write_and_load(_MINIMAL_VALID)
            self.assertIsNotNone(loader.data)
        finally:
            logging.disable(logging.CRITICAL)


class TestRawDataPreservation(unittest.TestCase):
    """Loader normalization must not mutate self.data (the raw parsed YAML)."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Asteroid field: bounds must survive; min_vec/max_vec must not appear
    # ------------------------------------------------------------------

    def test_asteroid_field_bounds_not_removed_from_raw_data(self):
        """
        After loading, self.data['environment']['asteroid_field'] must still
        contain the authored 'bounds' key — the normalization (which translates
        bounds -> min_vec/max_vec) works on a copy and must not strip 'bounds'
        from the original parsed document.
        """
        loader = _write_and_load(_MINIMAL_WITH_ASTEROID_FIELD)
        raw_af = loader.data.get('environment', {}).get('asteroid_field', {})
        self.assertIn(
            'bounds', raw_af,
            "self.data['environment']['asteroid_field'] must keep the authored "
            f"'bounds' key after loading. Got keys: {list(raw_af.keys())}"
        )

    def test_asteroid_field_min_vec_not_injected_into_raw_data(self):
        """
        The loader-internal 'min_vec' key (produced from 'bounds.min') must NOT
        appear in self.data — it belongs only on the hydrated runtime model.
        """
        loader = _write_and_load(_MINIMAL_WITH_ASTEROID_FIELD)
        raw_af = loader.data.get('environment', {}).get('asteroid_field', {})
        self.assertNotIn(
            'min_vec', raw_af,
            "Loader-internal 'min_vec' key must not be injected into self.data. "
            f"Got keys: {list(raw_af.keys())}"
        )

    def test_asteroid_field_max_vec_not_injected_into_raw_data(self):
        """
        Same as above for 'max_vec'.
        """
        loader = _write_and_load(_MINIMAL_WITH_ASTEROID_FIELD)
        raw_af = loader.data.get('environment', {}).get('asteroid_field', {})
        self.assertNotIn(
            'max_vec', raw_af,
            "Loader-internal 'max_vec' key must not be injected into self.data. "
            f"Got keys: {list(raw_af.keys())}"
        )

    # ------------------------------------------------------------------
    # Wing initial_orders: raw value must remain the bare SEXP, not wrapped
    # ------------------------------------------------------------------

    def test_wing_initial_orders_not_wrapped_in_raw_data(self):
        """
        After loading, the raw wing dict in self.data must still carry the
        authored bare SEXP string for initial_orders, not the runtime-wrapped
        '( goals ... )' form.  The loader normalizes initial_orders on a copy
        so the original document is unaffected.
        """
        loader = _write_and_load(_MINIMAL_WITH_WING_ORDERS)
        raw_wings = loader.data.get('entities', {}).get('wings', [])
        self.assertTrue(raw_wings, "Expected at least one raw wing in self.data")
        raw_orders = raw_wings[0].get('initial_orders', '')
        self.assertNotIn(
            '( goals', raw_orders,
            "Raw initial_orders in self.data must not be wrapped in '( goals ... )'. "
            f"Got: {raw_orders!r}"
        )
        # The authored content must still be present
        self.assertIn(
            'ai-chase-any', raw_orders,
            f"Expected authored content in raw initial_orders. Got: {raw_orders!r}"
        )

    def test_wing_initial_orders_wrapped_in_hydrated_mission(self):
        """
        The hydrated Wing object (in loader.all_wings) must carry the wrapped
        '( goals ... )' form — confirming that normalization was applied but
        only to the copy.
        """
        loader = _write_and_load(_MINIMAL_WITH_WING_ORDERS)
        self.assertTrue(loader.all_wings, "Expected at least one hydrated wing")
        wing_orders = loader.all_wings[0].initial_orders or ''
        self.assertIn(
            '( goals', wing_orders,
            "Hydrated Wing.initial_orders must be wrapped in '( goals ... )'. "
            f"Got: {wing_orders!r}"
        )


if __name__ == '__main__':
    unittest.main()
