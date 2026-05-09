"""
Tests for asteroid and debris field object_variants:
- Default variant selection based on object_type
- Valid subset authoring
- Cross-genre rejection
- Unknown variant rejection
- Empty list rejection
- Duplicate variant warning
- FS2 writer emission
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

from mission_loader import load_mission_from_fsif
from data_models import AsteroidField, Environment, Mission, MissionInfo, PlayerSetup, Ship, Weapons
from validator import Validator
from fs2_writer import FS2Writer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_FSIF_TEMPLATE = """fsif_version: "1.0"
mission_info:
  name: "Asteroid Field Test"
environment:
  ambient_light_level: [0, 0, 0]
{asteroid_block}
player_setup:
  start_ship: "Player Ship"
entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
mission_flow: {{}}
"""


def _write_and_load(fsif_text: str):
    """Write FSIF text to a temp file and load it; returns the Mission object."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "mission.fsif"
        path.write_text(fsif_text, encoding="utf-8")
        return load_mission_from_fsif(str(path))


def _make_validator(mission: Mission) -> Validator:
    """Build a validator in silent mode."""
    return Validator(mission, _repo_root)


def _mission_with_asteroid_field(af: AsteroidField) -> Mission:
    """Build a minimal Mission with the given AsteroidField."""
    player_ship = Ship.model_validate({
        "name": "Player Ship",
        "class": "GTF Ulysses",
        "team": "Friendly",
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
    })
    env = Environment(asteroid_field=af)
    return Mission(
        mission_info=MissionInfo(name="Test Mission"),
        player_setup=PlayerSetup(start_ship="Player Ship"),
        environment=env,
        ships=[player_ship],
    )


# ---------------------------------------------------------------------------
# 1. Default variant selection
# ---------------------------------------------------------------------------

class TestAsteroidFieldDefaults(unittest.TestCase):
    """Verify that omitting object_variants triggers the correct genre defaults."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_asteroid_default_variants_loaded(self):
        """Omitting object_variants on asteroid field gives all three asteroid names."""
        fsif_text = MINIMAL_FSIF_TEMPLATE.format(asteroid_block="""\
  asteroid_field:
    object_type: "asteroid"
    behavior: "passive"
    num_objects: 10
""")
        mission = _write_and_load(fsif_text)
        af = mission.environment.asteroid_field
        self.assertIsNotNone(af)
        self.assertEqual(af.object_type, "asteroid")
        self.assertCountEqual(af.object_variants, ["Brown", "Blue", "Orange"])

    def test_debris_default_variants_loaded(self):
        """Omitting object_variants on debris field gives all nine debris names."""
        fsif_text = MINIMAL_FSIF_TEMPLATE.format(asteroid_block="""\
  asteroid_field:
    object_type: "debris"
    behavior: "passive"
    num_objects: 10
""")
        mission = _write_and_load(fsif_text)
        af = mission.environment.asteroid_field
        self.assertIsNotNone(af)
        self.assertEqual(af.object_type, "debris")
        expected = [
            "Terran Debris 1", "Terran Debris 2", "Terran Debris 3",
            "Vasudan Debris 1", "Vasudan Debris 2", "Vasudan Debris 3",
            "Shivan Debris 1", "Shivan Debris 2", "Shivan Debris 3",
        ]
        self.assertCountEqual(af.object_variants, expected)

    def test_no_asteroid_field_section(self):
        """Missions with no asteroid_field should load cleanly (field is None)."""
        fsif_text = MINIMAL_FSIF_TEMPLATE.format(asteroid_block="")
        mission = _write_and_load(fsif_text)
        self.assertIsNone(mission.environment.asteroid_field)


# ---------------------------------------------------------------------------
# 2. Valid subset authoring — should pass validation
# ---------------------------------------------------------------------------

class TestAsteroidFieldValidSubsets(unittest.TestCase):
    """Authoring a valid subset of variants for the selected genre should pass."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_asteroid_single_variant_passes(self):
        af = AsteroidField(object_type="asteroid", object_variants=["Brown"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)
        self.assertFalse(any("object_variants" in e for e in v.errors), v.errors)

    def test_asteroid_two_variants_passes(self):
        af = AsteroidField(object_type="asteroid", object_variants=["Blue", "Orange"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)

    def test_asteroid_all_three_variants_passes(self):
        af = AsteroidField(object_type="asteroid", object_variants=["Brown", "Blue", "Orange"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)

    def test_debris_single_variant_passes(self):
        af = AsteroidField(object_type="debris", object_variants=["Terran Debris 1"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)

    def test_debris_cross_faction_subset_passes(self):
        af = AsteroidField(object_type="debris", object_variants=[
            "Terran Debris 2", "Vasudan Debris 1", "Shivan Debris 3"
        ])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)


# ---------------------------------------------------------------------------
# 3. Cross-genre mixing — should fail validation
# ---------------------------------------------------------------------------

class TestAsteroidFieldCrossGenreRejection(unittest.TestCase):
    """Mixing asteroid and debris variant names must fail validation."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_debris_name_in_asteroid_field_rejected(self):
        af = AsteroidField(object_type="asteroid", object_variants=["Terran Debris 1"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("mutually incompatible" in e for e in v.errors),
            v.errors,
        )

    def test_asteroid_name_in_debris_field_rejected(self):
        af = AsteroidField(object_type="debris", object_variants=["Brown"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("mutually incompatible" in e for e in v.errors),
            v.errors,
        )

    def test_mixed_genres_in_asteroid_field_rejected(self):
        """Some correct + some cross-genre entries should still be rejected."""
        af = AsteroidField(object_type="asteroid", object_variants=["Brown", "Terran Debris 1"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("mutually incompatible" in e for e in v.errors),
            v.errors,
        )


# ---------------------------------------------------------------------------
# 4. Unknown variant names — should fail validation
# ---------------------------------------------------------------------------

class TestAsteroidFieldUnknownVariants(unittest.TestCase):
    """Unknown variant names (not in either genre) must fail validation."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_unknown_asteroid_variant_rejected(self):
        """Typo / old invalid value 'Asteroid Small' must be rejected."""
        af = AsteroidField(object_type="asteroid", object_variants=["Asteroid Small"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("unrecognised" in e for e in v.errors),
            v.errors,
        )

    def test_unknown_debris_variant_rejected(self):
        af = AsteroidField(object_type="debris", object_variants=["Terran Debris One"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("unrecognised" in e for e in v.errors),
            v.errors,
        )

    def test_mixed_valid_and_unknown_rejected(self):
        af = AsteroidField(object_type="asteroid", object_variants=["Brown", "Purple"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())


# ---------------------------------------------------------------------------
# 5. Empty list — should fail validation
# ---------------------------------------------------------------------------

class TestAsteroidFieldEmptyVariants(unittest.TestCase):
    """An explicitly authored empty object_variants list must fail validation."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_empty_list_rejected_for_asteroid(self):
        af = AsteroidField(object_type="asteroid", object_variants=[])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("object_variants is empty" in e for e in v.errors),
            v.errors,
        )

    def test_empty_list_rejected_for_debris(self):
        af = AsteroidField(object_type="debris", object_variants=[])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any("object_variants is empty" in e for e in v.errors),
            v.errors,
        )


# ---------------------------------------------------------------------------
# 6. Duplicate entries — should produce a warning (not error)
# ---------------------------------------------------------------------------

class TestAsteroidFieldDuplicates(unittest.TestCase):
    """Duplicate entries in object_variants should produce a warning, not abort."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_duplicate_asteroid_variant_warns(self):
        af = AsteroidField(object_type="asteroid", object_variants=["Brown", "Brown", "Blue"])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)  # Must NOT abort
        self.assertTrue(
            any("duplicate" in w.lower() for w in v.warnings),
            v.warnings,
        )

    def test_duplicate_debris_variant_warns(self):
        af = AsteroidField(object_type="debris", object_variants=[
            "Terran Debris 1", "Terran Debris 1"
        ])
        mission = _mission_with_asteroid_field(af)
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)
        self.assertTrue(
            any("duplicate" in w.lower() for w in v.warnings),
            v.warnings,
        )


# ---------------------------------------------------------------------------
# 7. FS2 writer emission
# ---------------------------------------------------------------------------

class TestAsteroidFieldWriterEmission(unittest.TestCase):
    """Verify the FS2 writer produces correct +Field Debris Type Name lines."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _write_and_read(self, mission: Mission) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output))
            writer.write_mission()
            return output.read_text(encoding="utf-8")

    def test_asteroid_field_emits_debris_genre_0(self):
        af = AsteroidField(object_type="asteroid", behavior="passive",
                           object_variants=["Brown", "Blue", "Orange"])
        mission = _mission_with_asteroid_field(af)
        content = self._write_and_read(mission)
        self.assertIn("+Debris Genre: 0", content)
        self.assertIn("+Field Debris Type Name: Brown", content)
        self.assertIn("+Field Debris Type Name: Blue", content)
        self.assertIn("+Field Debris Type Name: Orange", content)

    def test_debris_field_emits_debris_genre_1(self):
        af = AsteroidField(object_type="debris", behavior="passive",
                           object_variants=[
                               "Terran Debris 1", "Terran Debris 2", "Terran Debris 3",
                               "Vasudan Debris 1", "Vasudan Debris 2", "Vasudan Debris 3",
                               "Shivan Debris 1", "Shivan Debris 2", "Shivan Debris 3",
                           ])
        mission = _mission_with_asteroid_field(af)
        content = self._write_and_read(mission)
        self.assertIn("+Debris Genre: 1", content)
        for faction in ("Terran Debris 1", "Vasudan Debris 2", "Shivan Debris 3"):
            self.assertIn(f"+Field Debris Type Name: {faction}", content)

    def test_asteroid_field_active_emits_field_type_0(self):
        af = AsteroidField(object_type="asteroid", behavior="active",
                           object_variants=["Brown"])
        mission = _mission_with_asteroid_field(af)
        content = self._write_and_read(mission)
        self.assertIn("+Field Type: 0", content)

    def test_debris_field_passive_emits_field_type_1(self):
        af = AsteroidField(object_type="debris", behavior="passive",
                           object_variants=["Terran Debris 1"])
        mission = _mission_with_asteroid_field(af)
        content = self._write_and_read(mission)
        self.assertIn("+Field Type: 1", content)

    def test_subset_only_emits_specified_variants(self):
        """Only the authored subset should appear; other genre variants must be absent."""
        af = AsteroidField(object_type="asteroid", behavior="passive",
                           object_variants=["Brown"])
        mission = _mission_with_asteroid_field(af)
        content = self._write_and_read(mission)
        self.assertIn("+Field Debris Type Name: Brown", content)
        # Blue and Orange were NOT authored, must not appear
        self.assertNotIn("+Field Debris Type Name: Blue", content)
        self.assertNotIn("+Field Debris Type Name: Orange", content)

    def test_default_asteroid_variants_from_loader(self):
        """Loading a FSIF with omitted object_variants must emit all asteroid defaults."""
        fsif_text = MINIMAL_FSIF_TEMPLATE.format(asteroid_block="""\
  asteroid_field:
    object_type: "asteroid"
    behavior: "passive"
""")
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "mission.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(fsif_path))
            output = Path(tmpdir) / "mission.fs2"
            FS2Writer(mission, str(output)).write_mission()
            content = output.read_text(encoding="utf-8")
        self.assertIn("+Field Debris Type Name: Brown", content)
        self.assertIn("+Field Debris Type Name: Blue", content)
        self.assertIn("+Field Debris Type Name: Orange", content)

    def test_default_debris_variants_from_loader(self):
        """Loading a FSIF with omitted object_variants (debris) must emit all nine defaults."""
        fsif_text = MINIMAL_FSIF_TEMPLATE.format(asteroid_block="""\
  asteroid_field:
    object_type: "debris"
    behavior: "passive"
""")
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "mission.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(fsif_path))
            output = Path(tmpdir) / "mission.fs2"
            FS2Writer(mission, str(output)).write_mission()
            content = output.read_text(encoding="utf-8")
        for name in [
            "Terran Debris 1", "Terran Debris 2", "Terran Debris 3",
            "Vasudan Debris 1", "Vasudan Debris 2", "Vasudan Debris 3",
            "Shivan Debris 1", "Shivan Debris 2", "Shivan Debris 3",
        ]:
            self.assertIn(f"+Field Debris Type Name: {name}", content, content)


# ---------------------------------------------------------------------------
# 8. Demo mission conversion smoke test
# ---------------------------------------------------------------------------

class TestDemoMissionsConvert(unittest.TestCase):
    """Existing demo missions must still load and validate successfully."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _try_load(self, relative_path: str):
        path = _repo_root / relative_path
        if not path.exists():
            self.skipTest(f"Demo file not found: {path}")
        return load_mission_from_fsif(str(path))

    def test_general_demo_loads(self):
        mission = self._try_load("missions/Demo_missions/general_demo.fsif")
        v = _make_validator(mission)
        # Validate passes (warnings allowed; errors must be zero)
        result = v.validate()
        self.assertTrue(result, v.errors)

    def test_evacuation_demo_loads(self):
        mission = self._try_load("missions/Demo_missions/evacuation_demo.fsif")
        v = _make_validator(mission)
        result = v.validate()
        self.assertTrue(result, v.errors)


if __name__ == "__main__":
    unittest.main()
