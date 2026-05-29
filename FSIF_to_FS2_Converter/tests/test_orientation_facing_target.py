"""
Tests for orientation: "object_name" automatic facing feature.

Covers:
1. compute_facing_orientation() math (cardinal directions, level facing, pitched,
   vertical degenerate, coincident-position error).
2. FSIFDocument schema accepts string orientation on ships and wings.
3. Loader integration: string orientation resolved to matrix via temp FSIF files.
4. Validator advisory skipped for entities with orientation_target.
5. Regression: runtime Ship.orientation still rejects bare strings (existing contract).
"""

import math
import sys
import tempfile
import os
import unittest
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap (mirrors _fsif_test_helpers.py)
# ---------------------------------------------------------------------------
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent   # FSIF_to_FS2_Converter/
_repo_root = _parent_dir.parent     # NeuralFS/
for _p in (str(_repo_root), str(_parent_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

REPO_ROOT = _repo_root

from _fsif_test_helpers import SilencedTestCase, make_valid_mission, make_validator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dot_product(a, b):
    return sum(ai * bi for ai, bi in zip(a, b))

def _norm(v):
    return math.sqrt(sum(x * x for x in v))

def _normalized(v):
    n = _norm(v)
    return [x / n for x in v] if n > 1e-12 else v

def _cross(a, b):
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    ]

def _is_unit(v, tol=1e-6):
    return abs(_norm(v) - 1.0) < tol

def _is_orthogonal(a, b, tol=1e-6):
    return abs(_dot_product(a, b)) < tol

def _assert_orientation_orthonormal(tc, mat, msg=""):
    """Assert mat (9-float) is an orthonormal rotation matrix."""
    r = mat[0:3]
    u = mat[3:6]
    f = mat[6:9]
    tc.assertTrue(_is_unit(r), f"{msg} row1 (right) not unit: {r}")
    tc.assertTrue(_is_unit(u), f"{msg} row2 (up) not unit: {u}")
    tc.assertTrue(_is_unit(f), f"{msg} row3 (fwd) not unit: {f}")
    tc.assertTrue(_is_orthogonal(r, u), f"{msg} right/up not orthogonal")
    tc.assertTrue(_is_orthogonal(r, f), f"{msg} right/fwd not orthogonal")
    tc.assertTrue(_is_orthogonal(u, f), f"{msg} up/fwd not orthogonal")

def _assert_faces_toward(tc, mat, source, target, tol=1e-5, msg=""):
    """Assert that the forward row (row3) of mat points from source toward target."""
    dx = target[0] - source[0]
    dy = target[1] - source[1]
    dz = target[2] - source[2]
    length = math.sqrt(dx*dx + dy*dy + dz*dz)
    tc.assertGreater(length, 1e-9, f"{msg} source and target coincident")
    expected_fwd = [dx/length, dy/length, dz/length]
    actual_fwd = mat[6:9]
    for i, (e, a) in enumerate(zip(expected_fwd, actual_fwd)):
        tc.assertAlmostEqual(e, a, delta=tol, msg=f"{msg} forward component {i}")


# ---------------------------------------------------------------------------
# 1. compute_facing_orientation unit tests
# ---------------------------------------------------------------------------

class TestComputeFacingOrientation(SilencedTestCase):
    """Unit tests for common.utils.compute_facing_orientation."""

    def setUp(self):
        from common.utils import compute_facing_orientation
        self.cfo = compute_facing_orientation

    def test_facing_plus_x_from_origin(self):
        """Facing world +X: nose=(1,0,0), right=(0,0,-1), up=(0,1,0)."""
        mat = self.cfo([0, 0, 0], [1, 0, 0])
        _assert_orientation_orthonormal(self, mat, "face +X")
        _assert_faces_toward(self, mat, [0, 0, 0], [1, 0, 0])
        # right should be (0, 0, -1) per FSO formula for level +X facing
        self.assertAlmostEqual(mat[0], 0.0, delta=1e-6)
        self.assertAlmostEqual(mat[1], 0.0, delta=1e-6)
        self.assertAlmostEqual(mat[2], -1.0, delta=1e-6)
        # up should be (0, 1, 0)
        self.assertAlmostEqual(mat[3], 0.0, delta=1e-6)
        self.assertAlmostEqual(mat[4], 1.0, delta=1e-6)
        self.assertAlmostEqual(mat[5], 0.0, delta=1e-6)

    def test_facing_minus_x(self):
        """Facing world -X: nose=(-1,0,0)."""
        mat = self.cfo([0, 0, 0], [-1, 0, 0])
        _assert_orientation_orthonormal(self, mat, "face -X")
        _assert_faces_toward(self, mat, [0, 0, 0], [-1, 0, 0])
        # up should be (0, 1, 0)
        self.assertAlmostEqual(mat[4], 1.0, delta=1e-6)

    def test_facing_plus_z(self):
        """Facing world +Z matches identity matrix."""
        mat = self.cfo([0, 0, 0], [0, 0, 1])
        _assert_orientation_orthonormal(self, mat, "face +Z")
        expected = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        for e, a in zip(expected, mat):
            self.assertAlmostEqual(e, a, delta=1e-6, msg=f"face +Z: identity mismatch")

    def test_facing_minus_z(self):
        """Facing world -Z."""
        mat = self.cfo([0, 0, 0], [0, 0, -1])
        _assert_orientation_orthonormal(self, mat, "face -Z")
        _assert_faces_toward(self, mat, [0, 0, 0], [0, 0, -1])
        # up should be (0, 1, 0)
        self.assertAlmostEqual(mat[4], 1.0, delta=1e-6)

    def test_level_facing_matches_yaw_only_formula(self):
        """For a level target, result equals the documented yaw-only formula."""
        sx, sy, sz = 0.0, 0.0, 0.0
        tx, ty, tz = 3000.0, 0.0, 4000.0
        mat = self.cfo([sx, sy, sz], [tx, ty, tz])
        _assert_orientation_orthonormal(self, mat)

        dx, dz = tx - sx, tz - sz
        length = math.sqrt(dx*dx + dz*dz)
        fx, fz = dx/length, dz/length
        # Documented yaw-only formula: [fz, 0, -fx, 0, 1, 0, fx, 0, fz]
        expected = [fz, 0.0, -fx, 0.0, 1.0, 0.0, fx, 0.0, fz]
        for i, (e, a) in enumerate(zip(expected, mat)):
            self.assertAlmostEqual(e, a, delta=1e-6, msg=f"yaw-only mismatch at idx {i}")

    def test_source_not_at_origin(self):
        """Should work correctly when source is not at the origin."""
        source = [1000.0, 500.0, -300.0]
        target = [2500.0, 500.0, 1200.0]  # level (same Y)
        mat = self.cfo(source, target)
        _assert_orientation_orthonormal(self, mat, "non-origin source")
        _assert_faces_toward(self, mat, source, target)
        # Level facing → up should be world +Y
        self.assertAlmostEqual(mat[4], 1.0, delta=1e-6, msg="up.y should be 1.0 for level facing")

    def test_pitched_facing_upward(self):
        """Target above source: nose points upward, matrix is still orthonormal."""
        source = [0.0, 0.0, 0.0]
        target = [0.0, 1000.0, 1000.0]  # 45 degrees up
        mat = self.cfo(source, target)
        _assert_orientation_orthonormal(self, mat, "pitched up")
        _assert_faces_toward(self, mat, source, target)

    def test_pitched_facing_downward(self):
        """Target below source: nose points downward, matrix is still orthonormal."""
        source = [0.0, 500.0, 0.0]
        target = [500.0, 0.0, 500.0]   # diagonally down
        mat = self.cfo(source, target)
        _assert_orientation_orthonormal(self, mat, "pitched down")
        _assert_faces_toward(self, mat, source, target)

    def test_straight_up_degenerate_case(self):
        """Target directly above: vertical degenerate, matrix still orthonormal."""
        mat = self.cfo([0, 0, 0], [0, 1000, 0])
        _assert_orientation_orthonormal(self, mat, "straight up")
        _assert_faces_toward(self, mat, [0, 0, 0], [0, 1000, 0])

    def test_straight_down_degenerate_case(self):
        """Target directly below: vertical degenerate, matrix still orthonormal."""
        mat = self.cfo([0, 1000, 0], [0, 0, 0])
        _assert_orientation_orthonormal(self, mat, "straight down")
        _assert_faces_toward(self, mat, [0, 1000, 0], [0, 0, 0])

    def test_coincident_positions_raise_value_error(self):
        """Coincident source and target must raise ValueError."""
        with self.assertRaises(ValueError):
            self.cfo([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])

    def test_effectively_coincident_raises(self):
        """Positions within 1e-9 must also raise ValueError."""
        with self.assertRaises(ValueError):
            self.cfo([0.0, 0.0, 0.0], [0.0, 0.0, 1e-10])

    def test_returns_9_floats(self):
        """Result is always a list of exactly 9 floats."""
        mat = self.cfo([0, 0, 0], [100, 0, 0])
        self.assertEqual(len(mat), 9)
        for v in mat:
            self.assertIsInstance(v, float)


# ---------------------------------------------------------------------------
# 2. FSIFDocument schema accepts string orientation
# ---------------------------------------------------------------------------

class TestFSIFDocumentSchemaAcceptsStringOrientation(SilencedTestCase):
    """The strict input schema must accept a string orientation value."""

    def _make_minimal_doc(self, **extra_ship_kwargs):
        """Return a base FSIF doc dict with optional extra keys on the ship."""
        ship = {
            "name": "Alpha 1",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
        }
        ship.update(extra_ship_kwargs)
        return {
            "fsif_version": "1.0",
            "mission_info": {"name": "Test"},
            "environment": {"ambient_light_level": [0, 0, 0]},
            "player_setup": {"start_ship": "Alpha 1"},
            "entities": {
                "ship_templates": {
                    "alpha_t": {
                        "class": "GTF Ulysses",
                        "team": "Friendly",
                        "weapons": {"primary": ["Avenger", "Avenger"], "secondary": ["MX-50"]},
                    }
                },
                "wings": [
                    {"name": "Alpha", "template": "alpha_t", "count": 1, "position": [0.0, 0.0, 0.0]}
                ],
            },
            "mission_flow": {},
        }

    def test_ship_string_orientation_accepted_by_schema(self):
        from data_models import FSIFDocument
        from pydantic import ValidationError
        doc = self._make_minimal_doc(orientation="GTC Dauntless")
        try:
            FSIFDocument(**doc)
        except ValidationError as e:
            self.fail(f"FSIFDocument rejected string orientation: {e}")

    def test_wing_string_orientation_accepted_by_schema(self):
        from data_models import FSIFDocument
        from pydantic import ValidationError
        doc = {
            "fsif_version": "1.0",
            "mission_info": {"name": "Test"},
            "environment": {"ambient_light_level": [0, 0, 0]},
            "player_setup": {"start_ship": "Alpha 1"},
            "entities": {
                "ship_templates": {
                    "alpha_t": {
                        "class": "GTF Ulysses",
                        "team": "Friendly",
                        "weapons": {"primary": ["Avenger", "Avenger"], "secondary": ["MX-50"]},
                    }
                },
                "wings": [
                    {
                        "name": "Alpha",
                        "template": "alpha_t",
                        "count": 1,
                        "position": [0.0, 0.0, 0.0],
                        "orientation": "SC Cain 1",
                    }
                ],
            },
            "mission_flow": {},
        }
        try:
            FSIFDocument(**doc)
        except ValidationError as e:
            self.fail(f"FSIFDocument rejected string wing orientation: {e}")

    def test_ship_matrix_orientation_still_accepted(self):
        """Existing 9-float matrix form must still be accepted."""
        from data_models import FSIFDocument
        from pydantic import ValidationError
        doc = self._make_minimal_doc(orientation=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])
        try:
            FSIFDocument(**doc)
        except ValidationError as e:
            self.fail(f"FSIFDocument rejected matrix orientation: {e}")


# ---------------------------------------------------------------------------
# 3. Loader integration tests (temporary FSIF files)
# ---------------------------------------------------------------------------

# Minimal FSIF template for loader integration tests.  Provides:
#  - Alpha wing (player) with 1 GTF Ulysses at [0,0,0]
#  - GTC Fenris at [2000, 0, 0]  (target ship)
#  - Jump node "Beta Aquilae JN" at [0, 0, 5000]
#  - Waypoint path "Patrol" with 2 points
#
# The orientation field on ship/wing under test is injected dynamically.

_MINIMAL_FSIF = """\
fsif_version: "1.0"
mission_info:
  name: "Orientation Test"
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
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
    fenris_t:
      class: "GTC Fenris"
      team: "Friendly"
      weapons:
        primary: []
        secondary: []
  ships:
    - name: "GTC Dauntless"
      class: "GTC Fenris"
      team: "Friendly"
      position: [2000.0, 0.0, 0.0]
{ship_orientation_block}
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 2
      position: [0.0, 0.0, 0.0]
{wing_orientation_block}
  waypoints:
    Patrol:
      - [500.0, 0.0, 500.0]
      - [1000.0, 0.0, 1000.0]
  jump_nodes:
    - name: "Beta Aquilae JN"
      position: [0.0, 0.0, 5000.0]
mission_flow: {{}}
"""

def _write_temp_fsif(content: str) -> str:
    """Write content to a temp .fsif file and return the path."""
    fd, path = tempfile.mkstemp(suffix=".fsif")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestLoaderOrientationTargetResolution(SilencedTestCase):
    """Integration tests for the loader's _resolve_orientation_targets pass."""

    def _load(self, ship_orientation_block="", wing_orientation_block=""):
        from mission_loader import load_mission_from_fsif
        content = _MINIMAL_FSIF.format(
            ship_orientation_block=ship_orientation_block,
            wing_orientation_block=wing_orientation_block,
        )
        path = _write_temp_fsif(content)
        try:
            return load_mission_from_fsif(path)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _get_ship(self, mission, name):
        return next((s for s in mission.ships if s.name == name), None)

    # ------------------------------------------------------------------
    # Standalone ship with string orientation
    # ------------------------------------------------------------------

    def test_ship_faces_named_ship(self):
        """GTC Dauntless with orientation: 'GTC Dauntless' should raise (self-reference)."""
        # Note: we test a ship pointing at a *different* ship
        # GTC Dauntless is at [2000, 0, 0]; Alpha 1 is at [-25, 0, 0]
        # Let's have GTC Dauntless face Alpha wing centroid
        block = "      orientation: \"Alpha\"\n"
        mission = self._load(ship_orientation_block=block)
        dauntless = self._get_ship(mission, "GTC Dauntless")
        self.assertIsNotNone(dauntless)
        # Alpha wing centroid is [0,0,0]; Dauntless at [2000,0,0] → should face -X direction
        mat = dauntless.orientation
        self.assertEqual(len(mat), 9, "Orientation matrix must have 9 elements")
        # nose (row 3) should point roughly toward -X
        self.assertLess(mat[6], -0.9, "Dauntless nose should point toward -X (facing Alpha)")
        # orientation_target should be preserved
        self.assertEqual(dauntless.orientation_target, "Alpha")
        # result should be orthonormal
        _assert_orientation_orthonormal(self, mat, "Dauntless faces Alpha")

    def test_ship_faces_jump_node(self):
        """Ship with orientation: 'Beta Aquilae JN' faces the jump node."""
        block = "      orientation: \"Beta Aquilae JN\"\n"
        mission = self._load(ship_orientation_block=block)
        dauntless = self._get_ship(mission, "GTC Dauntless")
        # Dauntless at [2000,0,0], jump node at [0,0,5000]
        mat = dauntless.orientation
        _assert_orientation_orthonormal(self, mat, "Dauntless faces JN")
        _assert_faces_toward(self, mat, [2000.0, 0.0, 0.0], [0.0, 0.0, 5000.0])

    def test_ship_faces_waypoint_point(self):
        """Ship with orientation: 'Patrol:1' faces the first waypoint point."""
        block = "      orientation: \"Patrol:1\"\n"
        mission = self._load(ship_orientation_block=block)
        dauntless = self._get_ship(mission, "GTC Dauntless")
        # Dauntless at [2000,0,0], Patrol:1 at [500,0,500]
        mat = dauntless.orientation
        _assert_orientation_orthonormal(self, mat, "Dauntless faces Patrol:1")
        _assert_faces_toward(self, mat, [2000.0, 0.0, 0.0], [500.0, 0.0, 500.0])

    def test_ship_with_no_orientation_target_unaffected(self):
        """Ships without orientation_target keep identity orientation."""
        mission = self._load()
        dauntless = self._get_ship(mission, "GTC Dauntless")
        identity = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        for e, a in zip(identity, dauntless.orientation):
            self.assertAlmostEqual(e, a, delta=1e-6, msg="No-target ship should have identity orientation")
        self.assertIsNone(dauntless.orientation_target)

    # ------------------------------------------------------------------
    # Wing with string orientation
    # ------------------------------------------------------------------

    def test_wing_members_face_target_independently(self):
        """Wing with string orientation: each member faces target from own position."""
        block = "      orientation: \"GTC Dauntless\"\n"
        mission = self._load(wing_orientation_block=block)
        # Alpha wing has 2 members: Alpha 1 at [-25,0,0] and Alpha 2 at [25,0,0]
        # GTC Dauntless at [2000,0,0]
        alpha1 = self._get_ship(mission, "Alpha 1")
        alpha2 = self._get_ship(mission, "Alpha 2")
        self.assertIsNotNone(alpha1)
        self.assertIsNotNone(alpha2)

        for member, pos in [(alpha1, [-25.0, 0.0, 0.0]), (alpha2, [25.0, 0.0, 0.0])]:
            mat = member.orientation
            _assert_orientation_orthonormal(self, mat, f"{member.name} faces Dauntless")
            _assert_faces_toward(self, mat, pos, [2000.0, 0.0, 0.0])
            self.assertEqual(member.orientation_target, "GTC Dauntless")

    # ------------------------------------------------------------------
    # Normal matrix orientation still works (regression)
    # ------------------------------------------------------------------

    def test_ship_matrix_orientation_unchanged(self):
        """Existing 9-float matrix orientation is still emitted unchanged."""
        mat_str = "[0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0]"
        block = f"      orientation: {mat_str}\n"
        mission = self._load(ship_orientation_block=block)
        dauntless = self._get_ship(mission, "GTC Dauntless")
        expected = [0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0]
        for e, a in zip(expected, dauntless.orientation):
            self.assertAlmostEqual(e, a, delta=1e-6, msg="Matrix orientation should be unchanged")
        self.assertIsNone(dauntless.orientation_target)

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_unknown_target_raises_value_error(self):
        """Unknown orientation target name must raise ValueError at load time."""
        from mission_loader import load_mission_from_fsif
        block = "      orientation: \"NonExistent Ship\"\n"
        content = _MINIMAL_FSIF.format(
            ship_orientation_block=block,
            wing_orientation_block="",
        )
        path = _write_temp_fsif(content)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(path)
            self.assertIn("NonExistent Ship", str(ctx.exception))
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_coincident_position_raises_value_error(self):
        """Source and target at same position must raise ValueError."""
        from mission_loader import load_mission_from_fsif
        # Alpha 1 is at approximately [-25, 0, 0] (centroid 0,0,0, offset -25)
        # If we make it face a ship at exactly that same position... hard to arrange.
        # Instead we test: a standalone ship at [0,0,0] facing GTC Dauntless which
        # we'll place at [0,0,0] by overriding the FSIF.
        fsif = """\
fsif_version: "1.0"
mission_info:
  name: "Coincident Test"
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
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  ships:
    - name: "Target Ship"
      class: "GTC Fenris"
      team: "Hostile"
      position: [0.0, 0.0, 0.0]
    - name: "Source Ship"
      class: "GTC Fenris"
      team: "Friendly"
      position: [0.0, 0.0, 0.0]
      orientation: "Target Ship"
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [500.0, 0.0, 0.0]
mission_flow: {}
"""
        path = _write_temp_fsif(fsif)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(path)
            # Should mention the ship name and/or target name
            err_str = str(ctx.exception)
            self.assertTrue(
                "Source Ship" in err_str or "Target Ship" in err_str or "coincident" in err_str.lower() or "same position" in err_str.lower(),
                f"Error message should reference the entity or position issue: {err_str}"
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# 4. Validator advisory skipped for orientation_target entities
# ---------------------------------------------------------------------------

class TestValidatorAdvisorySkipsOrientationTarget(SilencedTestCase):
    """Entities with orientation_target must not trigger the identity-orientation advisory."""

    def _make_mission_with_cruiser(self, orientation_target=None, orientation_matrix=None):
        """Return a Mission containing a standalone GTC Fenris."""
        from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Wing, Weapons
        player_ship = Ship.model_validate({
            "name": "Alpha 1",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "arrival_cue": "( true )",
            "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
        })
        alpha_wing = Wing(
            name="Alpha",
            count=1,
            ships=[player_ship],
            position=[0.0, 0.0, 0.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        cruiser_props = {
            "name": "GTC Fenris 1",
            "class": "GTC Fenris",
            "team": "Friendly",
            "position": [500.0, 0.0, 0.0],
            "arrival_cue": "( true )",
            "weapons": Weapons(),
        }
        if orientation_matrix is not None:
            cruiser_props["orientation"] = orientation_matrix
        cruiser = Ship.model_validate(cruiser_props)
        if orientation_target is not None:
            cruiser.orientation_target = orientation_target
        return Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[player_ship, cruiser],
            wings=[alpha_wing],
        )

    def test_cruiser_with_orientation_target_no_advisory(self):
        """Cruiser with orientation_target set should NOT trigger the identity advisory."""
        mission = self._make_mission_with_cruiser(orientation_target="SC Cain 1")
        v = make_validator(mission)
        v.validate_large_ship_orientation_defaults()
        ship_warnings = [w for w in v.warnings if "GTC Fenris 1" in w and "orientation" in w.lower()]
        self.assertEqual(
            len(ship_warnings), 0,
            f"Expected no advisory for ship with orientation_target, got: {ship_warnings}"
        )

    def test_cruiser_without_orientation_target_warns(self):
        """Cruiser with identity orientation and no target SHOULD trigger the advisory."""
        mission = self._make_mission_with_cruiser()
        v = make_validator(mission)
        v.validate_large_ship_orientation_defaults()
        has_warning = any("GTC Fenris 1" in w for w in v.warnings)
        self.assertTrue(has_warning, "Expected advisory warning for cruiser with identity orientation")

    def _make_mission_with_large_ship_wing(self, orientation_target=None):
        """Return a Mission with a wing of GTC Fenris ships."""
        from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Wing, Weapons
        player_ship = Ship.model_validate({
            "name": "Alpha 1",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "arrival_cue": "( true )",
            "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
        })
        alpha_wing = Wing(
            name="Alpha",
            count=1,
            ships=[player_ship],
            position=[0.0, 0.0, 0.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        fenris_ship = Ship.model_validate({
            "name": "Theta 1",
            "class": "GTC Fenris",
            "team": "Hostile",
            "position": [1000.0, 0.0, 0.0],
            "arrival_cue": "( false )",
            "weapons": Weapons(),
        })
        theta_wing = Wing(
            name="Theta",
            count=1,
            ships=[fenris_ship],
            position=[1000.0, 0.0, 0.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        if orientation_target is not None:
            theta_wing.orientation_target = orientation_target
        return Mission(
            mission_info=MissionInfo(name="Test"),
            player_setup=PlayerSetup(start_ship="Alpha 1"),
            environment=Environment(),
            ships=[player_ship, fenris_ship],
            wings=[alpha_wing, theta_wing],
        )

    def test_large_ship_wing_with_orientation_target_no_advisory(self):
        """Large-ship wing with orientation_target set should NOT trigger the advisory."""
        mission = self._make_mission_with_large_ship_wing(orientation_target="Alpha 1")
        v = make_validator(mission)
        v.validate_large_ship_orientation_defaults()
        wing_warnings = [w for w in v.warnings if "Theta" in w and "orientation" in w.lower()]
        self.assertEqual(
            len(wing_warnings), 0,
            f"Expected no advisory for wing with orientation_target, got: {wing_warnings}"
        )

    def test_large_ship_wing_without_orientation_target_warns(self):
        """Large-ship wing with no orientation and no target SHOULD trigger advisory."""
        mission = self._make_mission_with_large_ship_wing()
        v = make_validator(mission)
        v.validate_large_ship_orientation_defaults()
        has_warning = any("Theta" in w for w in v.warnings)
        self.assertTrue(has_warning, "Expected advisory warning for large-ship wing with no orientation")


# ---------------------------------------------------------------------------
# 5. Regression: runtime Ship.orientation still rejects bare strings
# ---------------------------------------------------------------------------

class TestRuntimeShipModelStillRejectsStringOrientation(SilencedTestCase):
    """The runtime Ship model must still reject string orientation directly.

    This ensures the existing type-guard contract is maintained:
    test_vector_orientation_type_guards.py::ShipOrientationTypeGuardTests
    remains valid.
    """

    def test_runtime_ship_rejects_string_orientation(self):
        from pydantic import ValidationError
        from data_models import Ship
        with self.assertRaises((ValidationError, ValueError)):
            Ship.model_validate({
                "name": "Test",
                "class": "GTF Ulysses",
                "team": "Friendly",
                "position": [0.0, 0.0, 0.0],
                "orientation": "GTC Dauntless",
                "arrival_cue": "( true )",
            })


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    unittest.main()
