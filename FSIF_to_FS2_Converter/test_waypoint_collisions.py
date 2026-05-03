import unittest
from pathlib import Path
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

if __name__ == '__main__':
    unittest.main()