import sys
import unittest
from pathlib import Path

_converter_dir = Path(__file__).resolve().parent
_repo_root = _converter_dir.parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from data_models import Mission, MissionInfo, PlayerSetup, Ship, Wing, Environment
from validator import Validator

class TestWaypointCollisions(unittest.TestCase):
    def test_collision_detected(self):
        # Minimal setup
        info = MissionInfo(name="Test Mission")
        setup = PlayerSetup(start_ship="Alpha 1")
        env = Environment()
        
        # Define a path moving along the X-axis
        waypoints = {"Path1": [[100.0, 0.0, 0.0], [500.0, 0.0, 0.0]]}
        
        # Moving ship at the origin
        ship_moving = Ship.model_validate({
            "name": "Alpha 1", 
            "class": "GTC Fenris",
            "team": "Friendly", 
            "position": [0.0, 0.0, 0.0], 
            "initial_orders": '( ai-waypoints "Path1" )'
        })
        
        # Obstacle ship squarely in the middle of the second path segment
        ship_obstacle = Ship.model_validate({
            "name": "GTCv Deimos", 
            "class": "GTC Leviathan", 
            "team": "Friendly", 
            "position": [250.0, 0.0, 0.0]
        })
        
        mission = Mission(
            mission_info=info,
            player_setup=setup,
            environment=env,
            ships=[ship_moving, ship_obstacle],
            waypoints=waypoints
        )
        
        validator = Validator(mission, Path("."), None)
        validator.validate_waypoint_collisions()
        
        # Expecting a warning for Alpha 1 -> GTCv Deimos collision
        self.assertTrue(len(validator.warnings) > 0, "Expected a warning for waypoint collision")
        
        warning_msg = validator.warnings[0]
        self.assertIn("Alpha 1", warning_msg)
        self.assertIn("GTCv Deimos", warning_msg)
        self.assertIn("collision during waypoint movement", warning_msg)

    def test_no_collision_detected(self):
        info = MissionInfo(name="Test Mission")
        setup = PlayerSetup(start_ship="Alpha 1")
        env = Environment()
        
        # Path along X-axis
        waypoints = {"Path1": [[100.0, 0.0, 0.0], [500.0, 0.0, 0.0]]}
        
        ship_moving = Ship.model_validate({
            "name": "Alpha 1", 
            "class": "GTC Fenris",
            "team": "Friendly", 
            "position": [0.0, 0.0, 0.0], 
            "initial_orders": '( ai-waypoints "Path1" )'
        })
        
        # Obstacle ship far away on the Y-axis
        ship_obstacle_safe = Ship.model_validate({
            "name": "GTCv Safe", 
            "class": "GTC Leviathan", 
            "team": "Friendly", 
            "position": [250.0, 5000.0, 0.0]
        })
        
        mission = Mission(
            mission_info=info,
            player_setup=setup,
            environment=env,
            ships=[ship_moving, ship_obstacle_safe],
            waypoints=waypoints
        )
        
        validator = Validator(mission, Path("."), None)
        validator.validate_waypoint_collisions()
        
        # Expecting NO warnings
        self.assertEqual(len(validator.warnings), 0, f"Expected no warnings, got: {validator.warnings}")

    def test_predestroyed_obstacle_not_flagged(self):
        """
        A ship with destroyed_before_mission_seconds > 0 is pre-placed wreckage at
        mission start and produces only sparse debris — it must NOT appear in the
        obstacle list and must NOT trigger a waypoint collision warning.
        """
        info = MissionInfo(name="Test Mission")
        setup = PlayerSetup(start_ship="Alpha 1")
        env = Environment()

        waypoints = {"Path1": [[100.0, 0.0, 0.0], [500.0, 0.0, 0.0]]}

        # Moving cruiser along the X-axis waypoint path
        ship_moving = Ship.model_validate({
            "name": "Alpha 1",
            "class": "GTC Fenris",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "initial_orders": '( ai-waypoints "Path1" )'
        })

        # Pre-destroyed cruiser squarely in the middle of the path — should NOT warn
        ship_predestroyed = Ship.model_validate({
            "name": "GTCv Wreck",
            "class": "GTC Leviathan",
            "team": "Friendly",
            "position": [250.0, 0.0, 0.0],
            "destroyed_before_mission_seconds": 30
        })

        mission = Mission(
            mission_info=info,
            player_setup=setup,
            environment=env,
            ships=[ship_moving, ship_predestroyed],
            waypoints=waypoints
        )

        validator = Validator(mission, Path("."), None)
        validator.validate_waypoint_collisions()

        self.assertEqual(
            len(validator.warnings), 0,
            f"Expected no warnings for pre-destroyed obstacle, got: {validator.warnings}"
        )


# ---------------------------------------------------------------------------
# Tests for validate_shared_waypoint_orders
# ---------------------------------------------------------------------------

class TestSharedWaypointOrders(unittest.TestCase):
    """Tests for the shared-waypoint-destination warning."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_mission(ships=None, wings=None, waypoints=None):
        """Build a minimal Mission suitable for shared-waypoint order tests."""
        info = MissionInfo(name="Shared WP Test")
        setup = PlayerSetup(start_ship="Alpha 1")
        env = Environment()
        return Mission(
            mission_info=info,
            player_setup=setup,
            environment=env,
            ships=ships or [],
            wings=wings or [],
            waypoints=waypoints or {},
        )

    @staticmethod
    def _ship(name, initial_orders=None, team="Friendly", ship_class="GTFr Poseidon"):
        """Build a minimal standalone ship with optional initial_orders."""
        data = {
            "name": name,
            "class": ship_class,
            "team": team,
            "position": [0.0, 0.0, 0.0],
        }
        if initial_orders is not None:
            data["initial_orders"] = initial_orders
        return Ship.model_validate(data)

    @staticmethod
    def _wing(name, initial_orders=None, team="Hostile", ship_class="SF Scorpion"):
        """Build a minimal Wing with one member and optional initial_orders."""
        member = Ship.model_validate({
            "name": f"{name} 1",
            "class": ship_class,
            "team": team,
            "position": [500.0, 0.0, 0.0],
            "arrival_cue": "( false )",
        })
        wing_data = dict(
            name=name,
            count=1,
            ships=[member],
            position=[500.0, 0.0, 0.0],
        )
        if initial_orders is not None:
            wing_data["initial_orders"] = initial_orders
        return Wing(**wing_data)

    _WP_FRAGMENT = "share waypoint movement order path"

    # ------------------------------------------------------------------
    # Cases that SHOULD warn
    # ------------------------------------------------------------------

    def test_two_standalone_ships_same_path_warns(self):
        """Two standalone ships sharing a waypoint path should produce a warning."""
        ship1 = self._ship("GTC Dauntless",
                           initial_orders='( goals\n( ai-waypoints-once "ConvoyPath" 89 )\n)')
        ship2 = self._ship("GTFr Trent",
                           initial_orders='( goals\n( ai-waypoints-once "ConvoyPath" 89 )\n)')
        mission = self._make_mission(
            ships=[ship1, ship2],
            waypoints={"ConvoyPath": [[0.0, 0.0, 500.0], [0.0, 0.0, 1000.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertTrue(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected shared-waypoint warning, got: {v.warnings}",
        )
        combined = "\n".join(v.warnings)
        self.assertIn("ConvoyPath", combined)
        self.assertIn("GTC Dauntless", combined)
        self.assertIn("GTFr Trent", combined)

    def test_warning_mentions_both_ai_waypoints_variants(self):
        """ai-waypoints (looping) and ai-waypoints-once on same path both trigger the check."""
        ship1 = self._ship("Freighter A",
                           initial_orders='( goals\n( ai-waypoints "PatrolLoop" 89 )\n)')
        ship2 = self._ship("Freighter B",
                           initial_orders='( goals\n( ai-waypoints-once "PatrolLoop" 89 )\n)')
        mission = self._make_mission(
            ships=[ship1, ship2],
            waypoints={"PatrolLoop": [[100.0, 0.0, 0.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertTrue(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected warning for mixed waypoints variants, got: {v.warnings}",
        )
        combined = "\n".join(v.warnings)
        self.assertIn("PatrolLoop", combined)

    def test_two_wings_same_path_warns(self):
        """Two wings sharing the same waypoint path (each as a unit) should warn."""
        wing1 = self._wing("Alpha",
                           initial_orders='( goals\n( ai-waypoints-once "PatrolPath" 89 )\n)')
        wing2 = self._wing("Beta",
                           initial_orders='( goals\n( ai-waypoints-once "PatrolPath" 89 )\n)')
        mission = self._make_mission(
            ships=[wing1.ships[0], wing2.ships[0]],
            wings=[wing1, wing2],
            waypoints={"PatrolPath": [[200.0, 0.0, 0.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertTrue(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected shared-waypoint warning for two wings, got: {v.warnings}",
        )
        combined = "\n".join(v.warnings)
        self.assertIn("Alpha", combined)
        self.assertIn("Beta", combined)

    def test_ship_and_wing_same_path_warns(self):
        """A standalone ship and a wing sharing a path both appear in the warning."""
        ship = self._ship("GTC Fenris 1",
                          initial_orders='( goals\n( ai-waypoints-once "EscortPath" 89 )\n)')
        wing = self._wing("Delta",
                          initial_orders='( goals\n( ai-waypoints-once "EscortPath" 89 )\n)')
        mission = self._make_mission(
            ships=[ship, wing.ships[0]],
            wings=[wing],
            waypoints={"EscortPath": [[300.0, 0.0, 0.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertTrue(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected warning, got: {v.warnings}",
        )
        combined = "\n".join(v.warnings)
        self.assertIn("EscortPath", combined)
        self.assertIn("GTC Fenris 1", combined)
        self.assertIn("Delta", combined)

    def test_warning_message_contains_actionable_guidance(self):
        """The warning message must mention the offset suggestion."""
        ship1 = self._ship("S1",
                           initial_orders='( goals\n( ai-waypoints-once "DestPath" 89 )\n)')
        ship2 = self._ship("S2",
                           initial_orders='( goals\n( ai-waypoints-once "DestPath" 89 )\n)')
        mission = self._make_mission(
            ships=[ship1, ship2],
            waypoints={"DestPath": [[0.0, 0.0, 500.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        combined = "\n".join(v.warnings)
        # The guidance text must mention offsets so authors know how to fix it
        self.assertIn("offset", combined)

    # ------------------------------------------------------------------
    # Cases that should NOT warn
    # ------------------------------------------------------------------

    def test_no_warning_when_different_paths(self):
        """Ships on different paths should not trigger the warning."""
        ship1 = self._ship("Ship A",
                           initial_orders='( goals\n( ai-waypoints-once "PathA" 89 )\n)')
        ship2 = self._ship("Ship B",
                           initial_orders='( goals\n( ai-waypoints-once "PathB" 89 )\n)')
        mission = self._make_mission(
            ships=[ship1, ship2],
            waypoints={
                "PathA": [[100.0, 0.0, 0.0]],
                "PathB": [[100.0, 0.0, 200.0]],
            },
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertFalse(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected no shared-waypoint warning, got: {v.warnings}",
        )

    def test_no_warning_when_only_one_ship_uses_path(self):
        """A single ship using a waypoint path should not warn."""
        ship = self._ship("Solo Ship",
                          initial_orders='( goals\n( ai-waypoints-once "SoloPath" 89 )\n)')
        mission = self._make_mission(
            ships=[ship],
            waypoints={"SoloPath": [[0.0, 0.0, 500.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertFalse(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected no warning for lone ship, got: {v.warnings}",
        )

    def test_no_warning_for_ships_with_no_waypoint_orders(self):
        """Ships with no initial_orders should produce no warning."""
        ship1 = self._ship("GTC Alpha")   # no initial_orders
        ship2 = self._ship("GTC Beta")    # no initial_orders
        mission = self._make_mission(ships=[ship1, ship2])
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertFalse(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Expected no warning for ships without waypoint orders, got: {v.warnings}",
        )

    def test_wing_members_sharing_wing_level_order_does_not_warn(self):
        """Wing members inheriting the same wing-level order must NOT be counted
        as separate entities that share a path — the wing itself is one entity."""
        wing = self._wing("Alpha",
                          initial_orders='( goals\n( ai-waypoints-once "PatrolPath" 89 )\n)')
        # Only one wing uses the path; no other ship or wing does
        mission = self._make_mission(
            ships=wing.ships,
            wings=[wing],
            waypoints={"PatrolPath": [[200.0, 0.0, 0.0]]},
        )
        v = Validator(mission, Path("."), None)
        v.validate_shared_waypoint_orders()

        self.assertFalse(
            any(self._WP_FRAGMENT in w for w in v.warnings),
            f"Wing members sharing a wing-level order must not warn, got: {v.warnings}",
        )

    def test_validation_is_non_fatal(self):
        """The shared-waypoint check must never abort validation (warning only)."""
        ship1 = self._ship("GTC Dauntless",
                           initial_orders='( goals\n( ai-waypoints-once "ConvoyPath" 89 )\n)')
        ship2 = self._ship("GTFr Trent",
                           initial_orders='( goals\n( ai-waypoints-once "ConvoyPath" 89 )\n)')
        mission = self._make_mission(
            ships=[ship1, ship2],
            waypoints={"ConvoyPath": [[0.0, 0.0, 500.0]]},
        )
        v = Validator(mission, Path("."), None)
        # validate_shared_waypoint_orders should not raise
        v.validate_shared_waypoint_orders()
        # Validation itself (shared-waypoint is a warning, so result can still be True
        # depending on other checks).  The key property is: no errors added.
        self.assertEqual(
            len(v.errors), 0,
            f"validate_shared_waypoint_orders must not add errors, got: {v.errors}",
        )
        # And the warning must be present
        self.assertTrue(len(v.warnings) > 0)


if __name__ == '__main__':
    unittest.main()
