"""
Tests for validate_spawn_collisions() in SpatialChecksMixin.

The check warns when two Hyperspace-arriving entities have overlapping OBBs at
mission start.  It is advisory (warning only; validate() still returns True).

After the per-member wing expansion fix, wing members are each represented as
their own OBB object using their exact spawned position and ship-class bounding
box.  Same-wing member pairs are excluded; only cross-entity pairs are flagged.

Cases tested
------------
- Standalone ship too close to another standalone ship              -> warning
- Large-ship wing member too close to standalone ship              -> warning
  (regression: was silently missed when the whole wing was one OBB)
- Large-ship wing member too close to member of a different wing   -> warning
- Same-wing members that are very close to each other              -> no warning
- Warning label includes parent-wing name for wing-member objects  -> checked
- Fighter/bomber wing near a standalone ship (small OBBs, spaced
  far enough apart)                                                -> no warning
- Directional-arrival wing (Near Ship) near standalone ship        -> no warning
- Pre-spawn docked pair                                            -> no warning
"""

import unittest
import sys
from pathlib import Path

_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
_repo_root = _parent_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Wing
from validator import Validator

_REPO_ROOT = _repo_root

# Fragment present in every spawn-collision warning message.
_WARNING_FRAGMENT = "may cause an immediate collision"


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


def _make_mission(ships, wings=None):
    """Build a minimal Mission with the given ships and optional wings."""
    info = MissionInfo(name="Spawn Collision Test")
    setup = PlayerSetup(start_ship="Alpha 1")
    env = Environment()
    # Ensure the player-start ship exists in the ships list.
    all_ships = list(ships)
    all_wings = list(wings) if wings else []
    return Mission(
        mission_info=info,
        player_setup=setup,
        environment=env,
        ships=all_ships,
        wings=all_wings,
    )


def _player_wing(player_ship: Ship) -> Wing:
    """Wrap a single player ship in a minimal Friendly Alpha wing."""
    return Wing(
        name="Alpha",
        count=1,
        ships=[player_ship],
        position=player_ship.position,
    )


def _large_ship(name, position, team="Friendly", arrival_method="Hyperspace",
                arrival_anchor=None, arrival_distance=None,
                ship_class="GTC Fenris", docked_with=None):
    """Build a minimal cruiser-class ship."""
    data = {
        "name": name,
        "class": ship_class,
        "team": team,
        "position": position,
        "arrival_method": arrival_method,
    }
    if arrival_anchor:
        data["arrival_anchor"] = arrival_anchor
    if arrival_distance is not None:
        data["arrival_distance"] = arrival_distance
    if docked_with:
        data["docked_with"] = docked_with
    return Ship.model_validate(data)


def _fighter_ship(name, position, arrival_cue="( false )"):
    """Build a minimal fighter-class ship (wing member style)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTF Ulysses",
        "team": "Friendly",
        "position": position,
        "arrival_cue": arrival_cue,
    })


def _make_large_ship_wing(wing_name, ship_class, count, centroid,
                           member_spacing=50.0, arrival_method="Hyperspace",
                           arrival_anchor=None, arrival_distance=None):
    """Expand a large-ship wing with exact member positions (mirrors loader logic)."""
    center_index = (count - 1) / 2.0
    members = []
    for i in range(count):
        offset = (i - center_index) * member_spacing
        members.append(Ship.model_validate({
            "name": f"{wing_name} {i + 1}",
            "class": ship_class,
            "team": "Friendly",
            "position": [centroid[0] + offset, centroid[1], centroid[2]],
            "arrival_cue": "( false )",
        }))
    wing_data = {
        "name": wing_name,
        "count": count,
        "ships": members,
        "position": centroid,
        "member_spacing": member_spacing,
        "arrival_method": arrival_method,
    }
    if arrival_anchor:
        wing_data["arrival_anchor"] = arrival_anchor
    if arrival_distance is not None:
        wing_data["arrival_distance"] = arrival_distance
    return Wing(**wing_data)


# ---------------------------------------------------------------------------
# Helpers to make player-start valid without interfering with collision tests
# ---------------------------------------------------------------------------

def _alpha_player(position=None):
    """Return a player start ship and its Alpha wing."""
    pos = position or [0.0, 5000.0, 0.0]  # Far away by default
    ship = _fighter_ship("Alpha 1", pos, arrival_cue="( true )")
    wing = _player_wing(ship)
    return ship, wing


class TestSpawnCollisionsStandaloneShips(unittest.TestCase):
    """validate_spawn_collisions: standalone ship vs standalone ship."""

    def test_two_overlapping_standalone_ships_warns(self):
        """Two standalone cruisers at the same position must produce a warning."""
        player, player_wing = _alpha_player()
        ship_a = _large_ship("GTC Fenris 1", [0.0, 0.0, 0.0])
        ship_b = _large_ship("GTC Fenris 2", [0.0, 0.0, 0.0])  # identical position
        mission = _make_mission(
            ships=[player, ship_a, ship_b],
            wings=[player_wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected spawn-collision warning, got: {v.warnings}",
        )

    def test_two_widely_separated_standalone_ships_no_warning(self):
        """Two standalone cruisers far apart must not produce a warning."""
        player, player_wing = _alpha_player()
        ship_a = _large_ship("GTC Fenris 1", [0.0, 0.0, 0.0])
        ship_b = _large_ship("GTC Fenris 2", [0.0, 0.0, 2000.0])  # 2 km apart
        mission = _make_mission(
            ships=[player, ship_a, ship_b],
            wings=[player_wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no warning for widely separated ships, got: {v.warnings}",
        )

    def test_docked_pair_not_flagged(self):
        """A pre-spawn docked pair must not produce a spawn-collision warning."""
        player, player_wing = _alpha_player()
        # Dockee arrives normally; docker has arrival_cue false and docked_with set.
        dockee = _large_ship("GTC Fenris 1", [0.0, 0.0, 0.0])
        docker = _large_ship(
            "GTT Elysium 1", [0.0, 0.0, 0.0],
            ship_class="GTT Elysium",
            docked_with="GTC Fenris 1",
        )
        mission = _make_mission(
            ships=[player, dockee, docker],
            wings=[player_wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Docked pair must not produce a spawn-collision warning, got: {v.warnings}",
        )

    def test_directional_arrival_ship_not_checked(self):
        """A ship with a directional arrival method has no fixed initial position
        and must be excluded from the spawn-collision check."""
        player, player_wing = _alpha_player()
        anchor = _large_ship("GTC Anchor", [0.0, 0.0, 0.0])
        directional = _large_ship(
            "GTC Near", [0.0, 0.0, 0.0],
            arrival_method="Near Ship",
            arrival_anchor="GTC Anchor",
            arrival_distance=100,
        )
        mission = _make_mission(
            ships=[player, anchor, directional],
            wings=[player_wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Directional-arrival ship must not trigger spawn-collision warning, got: {v.warnings}",
        )


class TestSpawnCollisionsLargeShipWings(unittest.TestCase):
    """validate_spawn_collisions: large-ship wing member OBB accuracy.

    Regression tests that guard against the old single-centroid-OBB approach
    that would miss collisions between large-ship wing members and nearby ships.
    """

    # Regression geometry: GTC Fenris bounding box (from ship_bounding_boxes.md):
    #   X extents ≈ ±35 m, Y extents ≈ [-100, +80] m, Z extents ≈ [-116, +132] m.
    #
    # Wing centroid at [0,0,0], count=2, member_spacing=1000 m:
    #   Member 1: [-500, 0, 0]
    #   Member 2: [+500, 0, 0]
    #
    # Obstacle at [550, 0, 0] — 50 m from member 2, 550 m from centroid.
    #
    # OLD approach (one centroid OBB + padding=100):
    #   Centroid OBB X extent = 35 + 100 = 135 m.
    #   |550 - 0| = 550 m > 135 m → OLD approach does NOT flag the collision.
    #
    # NEW approach (per-member OBB, no padding):
    #   Member 2 OBB X extent = 35 m; obstacle OBB X extent = 35 m.
    #   |550 - 500| = 50 m < 35 + 35 = 70 m → NEW approach DOES flag it.
    #
    # This is the exact regression the fix was designed to address.
    _WING_CENTROID = [0.0, 0.0, 0.0]
    _WING_SPACING = 1000.0   # large spacing so members are far from centroid
    _OBSTACLE_POS = [550.0, 0.0, 0.0]  # near member 2 (+500), far from centroid (0)

    def test_large_ship_wing_member_near_standalone_warns(self):
        """A large-ship wing member whose OBB overlaps a nearby standalone ship
        must produce a warning (regression: old centroid+padding approach missed
        this when the wing centroid was farther from the obstacle than the
        expanded member that is actually close).

        Geometry:
            member_spacing=1000m → member 2 at [+500,0,0].
            Obstacle at [+550,0,0] — 50m gap from member 2, but 550m from centroid.
            Old centroid OBB X extent = 35+100 = 135m: misses obstacle at 550m.
            New member 2 OBB X extent = 35m: catches obstacle at 50m distance.
        """
        player, player_wing = _alpha_player()
        wing = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=2,
            centroid=self._WING_CENTROID, member_spacing=self._WING_SPACING,
        )
        obstacle = _large_ship("GTC Obstacle", self._OBSTACLE_POS)
        mission = _make_mission(
            ships=player_wing.ships + wing.ships + [obstacle],
            wings=[player_wing, wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected spawn-collision warning for large-ship wing near obstacle, "
            f"got: {v.warnings}",
        )

    def test_same_wing_members_no_warning(self):
        """Members of the same wing must not trigger a spawn-collision warning
        against each other, even when their OBBs overlap due to tight spacing."""
        player, player_wing = _alpha_player()
        # Default member_spacing=50 is much less than the 150m radius → OBBs
        # of adjacent members will overlap, but same-wing pairs are excluded.
        wing = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=3,
            centroid=[0.0, 0.0, 0.0], member_spacing=50.0,
        )
        mission = _make_mission(
            ships=player_wing.ships + wing.ships,
            wings=[player_wing, wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Same-wing members must not produce a spawn-collision warning, "
            f"got: {v.warnings}",
        )

    def test_inter_wing_large_ship_collision_warns(self):
        """Two large-ship wings spawning at the same position should warn for
        cross-wing member pairs."""
        player, player_wing = _alpha_player()
        wing_a = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=1, centroid=[0.0, 0.0, 0.0],
        )
        wing_b = _make_large_ship_wing(
            "Zeta", "GTC Fenris", count=1, centroid=[0.0, 0.0, 0.0],  # same position
        )
        mission = _make_mission(
            ships=player_wing.ships + wing_a.ships + wing_b.ships,
            wings=[player_wing, wing_a, wing_b],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected spawn-collision warning for two wings at same position, "
            f"got: {v.warnings}",
        )

    def test_directional_arrival_large_ship_wing_not_checked(self):
        """A large-ship wing with a directional arrival method has no fixed
        initial position and must not trigger a spawn-collision warning.

        The wing's authored centroid is at [0,0,0] — the same position as the
        obstacle — but because the wing uses 'Near Ship' arrival the members
        are excluded from the static spawn-collision check entirely.
        The anchor is placed far away so it does not itself collide with the
        obstacle and produce a spurious standalone-ship warning.
        """
        player, player_wing = _alpha_player()
        # Anchor is far away so it does not overlap with the obstacle.
        anchor = _large_ship("GTC Anchor", [5000.0, 0.0, 0.0])
        wing = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=2,
            centroid=[0.0, 0.0, 0.0],
            arrival_method="Near Ship",
            arrival_anchor="GTC Anchor",
            arrival_distance=100,
        )
        # Obstacle at wing centroid; would warn if wing members were checked.
        obstacle = _large_ship("GTC Obstacle", [0.0, 0.0, 0.0])
        mission = _make_mission(
            ships=player_wing.ships + wing.ships + [obstacle, anchor],
            wings=[player_wing, wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Directional-arrival large-ship wing must not trigger spawn-collision "
            f"warning, got: {v.warnings}",
        )

    def test_warning_label_shows_parent_wing(self):
        """Warning message must identify the wing membership of the colliding
        member (e.g., 'Wing member X (Wing Y)')."""
        player, player_wing = _alpha_player()
        wing = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=1,
            centroid=[0.0, 0.0, 0.0],
        )
        obstacle = _large_ship("GTC Obstacle", [0.0, 0.0, 0.0])
        mission = _make_mission(
            ships=player_wing.ships + wing.ships + [obstacle],
            wings=[player_wing, wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        combined = "\n".join(v.warnings)
        self.assertIn(
            "Epsilon",
            combined,
            "Warning must mention the parent wing name 'Epsilon'.",
        )
        self.assertIn(
            "Wing member",
            combined,
            "Warning must use the 'Wing member' label for expanded wing ships.",
        )

    def test_large_ship_wing_far_from_obstacle_no_warning(self):
        """A large-ship wing spawning far from any obstacle must not warn."""
        player, player_wing = _alpha_player()
        wing = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=2,
            centroid=[0.0, 0.0, 0.0],
        )
        obstacle = _large_ship("GTC Obstacle", [0.0, 0.0, 3000.0])  # 3 km away
        mission = _make_mission(
            ships=player_wing.ships + wing.ships + [obstacle],
            wings=[player_wing, wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertFalse(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected no warning when large-ship wing is far from obstacle, "
            f"got: {v.warnings}",
        )

    def test_spawn_collision_check_is_advisory_only(self):
        """validate_spawn_collisions must never add errors; only warnings."""
        player, player_wing = _alpha_player()
        wing = _make_large_ship_wing(
            "Epsilon", "GTC Fenris", count=1,
            centroid=[0.0, 0.0, 0.0],
        )
        obstacle = _large_ship("GTC Obstacle", [0.0, 0.0, 0.0])
        mission = _make_mission(
            ships=player_wing.ships + wing.ships + [obstacle],
            wings=[player_wing, wing],
        )
        v = _make_validator(mission)
        v.validate_spawn_collisions()

        self.assertEqual(
            [], v.errors,
            f"validate_spawn_collisions must not add errors, got: {v.errors}",
        )
        # And a warning must have been generated for the collision
        self.assertTrue(
            any(_WARNING_FRAGMENT in w for w in v.warnings),
            f"Expected at least one spawn-collision warning, got: {v.warnings}",
        )


if __name__ == '__main__':
    unittest.main()
