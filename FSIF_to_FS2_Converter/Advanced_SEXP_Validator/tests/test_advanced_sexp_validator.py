import unittest
import sys
import os
from pathlib import Path

# Adjust path to find the modules in parent directories
current_dir = Path(__file__).resolve().parent
validator_dir = current_dir.parent
converter_dir = validator_dir.parent

sys.path.insert(0, str(converter_dir))
sys.path.insert(0, str(validator_dir))

from advanced_sexp_validator import SexpParser, SexpValidator, MissionContext, SexpReturnType
import fs_data

class TestAdvancedSexpValidator(unittest.TestCase):
    def setUp(self):
        self.ctx = MissionContext()
        self.ctx.ships.add("Alpha 1")
        self.ctx.wings.add("Alpha")
        self.ctx.variables["hull_strength"] = SexpReturnType.NUMBER
        self.ctx.events.add("Event 1")
        self.ctx.goals.add("Goal 1")
        self.ctx.messages.add("Message 1")
        
        self.parser = SexpParser()
        self.validator = SexpValidator(self.ctx)

    def validate_string(self, sexp_str, expected_type=SexpReturnType.NULL):
        roots = self.parser.parse(sexp_str)
        self.assertTrue(roots, f"Failed to parse: {sexp_str}")
        errors = []
        for root in roots:
            errors.extend(self.validator.validate(root, expected_type=expected_type))
        return errors

    def test_valid_basic(self):
        errors = self.validate_string('(when (true) (do-nothing))', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_valid_weapon_unlock(self):
        errors = self.validate_string('(allow-weapon "Prometheus")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_valid_subsystem(self):
        errors = self.validate_string('(when (is-subsystem-destroyed-delay "Alpha 1" "navigation" 0) (do-nothing))', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_invalid_weapon_name(self):
        errors = self.validate_string('(allow-weapon "SuperMegaLaser")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Weapon" in e for e in errors), f"Expected Invalid Weapon error, got: {errors}")

    def test_invalid_subsystem_name(self):
        errors = self.validate_string('(when (is-subsystem-destroyed-delay "Alpha 1" "flux_capacitor" 0) (do-nothing))', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Subsystem" in e for e in errors), f"Expected Invalid Subsystem error, got: {errors}")

    def test_invalid_ship_class(self):
        errors = self.validate_string('(allow-ship "StarDestroyer")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Ship Class" in e for e in errors))

    def test_invalid_iff(self):
        errors = self.validate_string('(change-iff "Borg" "Alpha 1")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Team" in e for e in errors))

    def test_invalid_ship_name(self):
        errors = self.validate_string('(is-destroyed-delay 0 "NonExistentShip")', SexpReturnType.BOOL)
        # Note: Depending on OPF type (SHIP vs SHIP_WING), error might differ
        self.assertTrue(
            any("Invalid Ship name" in e for e in errors) or 
            any("Invalid Ship/Wing name" in e for e in errors), 
            f"Errors: {errors}"
        )

    def test_valid_ship_flag(self):
        errors = self.validate_string('(alter-ship-flag "cargo-known" (true) (true) "Alpha 1")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_invalid_ship_flag(self):
        errors = self.validate_string('(alter-ship-flag "invalid-flag" (true) (true) "Alpha 1")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Ship Flag" in e for e in errors))

    def test_valid_music(self):
        errors = self.validate_string('(change-soundtrack "1: Genesis")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_invalid_music(self):
        errors = self.validate_string('(change-soundtrack "Invalid Track")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Soundtrack Name" in e for e in errors))

    # --- New Tests for Wildcards and Special Tokens ---

    def test_who_from_valid_ship(self):
        # send-message arg 0 is WHO_FROM
        # (send-message "Alpha 1" "High" "Message 1")
        errors = self.validate_string('(send-message "Alpha 1" "High" "Message 1")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_who_from_valid_wing(self):
        errors = self.validate_string('(send-message "Alpha" "High" "Message 1")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_who_from_valid_special(self):
        errors = self.validate_string('(send-message "#Command" "High" "Message 1")', SexpReturnType.NULL)
        self.assertEqual(errors, [])
        errors = self.validate_string('(send-message "<any wingman>" "High" "Message 1")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_who_from_invalid_special(self):
        errors = self.validate_string('(send-message "#InvalidSource" "High" "Message 1")', SexpReturnType.NULL)
        self.assertTrue(
            any("Invalid Message Sender" in e for e in errors) or
            any("Invalid Special Message Sender" in e for e in errors),
            f"Errors: {errors}"
        )
        
        errors = self.validate_string('(send-message "<any nobody>" "High" "Message 1")', SexpReturnType.NULL)
        self.assertTrue(
            any("Invalid Message Sender" in e for e in errors) or
            any("Invalid Special Message Sender" in e for e in errors),
            f"Errors: {errors}"
        )

    def test_who_from_invalid_generic(self):
        errors = self.validate_string('(send-message "RandomString" "High" "Message 1")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Message Sender" in e for e in errors), f"Errors: {errors}")

    def test_ship_invalid_wildcard(self):
        # ai-chase returns SexpReturnType.AI_GOAL
        errors = self.validate_string('(ai-chase "<any friendly>" 0)', SexpReturnType.AI_GOAL)
        self.assertEqual(errors, [])

        errors = self.validate_string('(ai-chase "<invalid>" 0)', SexpReturnType.AI_GOAL)
        self.assertTrue(any("Invalid Ship" in e for e in errors) or any("Invalid Wing" in e for e in errors) or any("Invalid Ship/Wing" in e for e in errors), f"Got: {errors}")

    # --- Tests for Points and Waypoints (OPF_POINT, OPF_SHIP_POINT) ---

    def test_valid_point_waypoint(self):
        self.ctx.waypoints["Path1"] = 3
        # ai-waypoints uses OPF_WAYPOINT_PATH
        errors = self.validate_string('(ai-waypoints "Path1" 89)', SexpReturnType.AI_GOAL)
        self.assertEqual(errors, [])

    def test_valid_point_specific(self):
        self.ctx.waypoints["Path1"] = 3
        # distance can use OPF_SHIP_WING_POINT
        errors = self.validate_string('(distance "Alpha 1" "Path1:1")', SexpReturnType.NUMBER)
        self.assertEqual(errors, [])

    def test_invalid_point_bounds(self):
        self.ctx.waypoints["Path1"] = 3
        
        # Point out of bounds
        errors = self.validate_string('(distance "Alpha 1" "Path1:4")', SexpReturnType.NUMBER)
        self.assertEqual(len(errors), 1)
        self.assertIn("out of bounds for path 'Path1' (has 3 points)", errors[0])
        
        # Invalid index type
        errors = self.validate_string('(distance "Alpha 1" "Path1:abc")', SexpReturnType.NUMBER)
        self.assertEqual(len(errors), 1)
        self.assertIn("Must be an integer", errors[0])
        
        # Invalid path name
        errors = self.validate_string('(distance "Alpha 1" "Path99:1")', SexpReturnType.NUMBER)
        self.assertEqual(len(errors), 1)
        self.assertIn("Invalid waypoint path: 'Path99'", errors[0])

    def test_invalid_point(self):
        # distance can use OPF_SHIP_WING_POINT
        errors = self.validate_string('(distance "Alpha 1" "NonExistentPath:1")', SexpReturnType.NUMBER)
        self.assertTrue(
            any("Invalid Ship/Wing/Point" in e for e in errors) or
            any("Invalid waypoint path" in e for e in errors),
            f"Errors: {errors}"
        )

    def test_valid_ship_point(self):
        self.ctx.waypoints["Path1"] = 3
        # is-facing arg 1 uses OPF_SHIP_POINT
        # (is-facing "Alpha 1" "Path1:1" 0)
        errors = self.validate_string('(is-facing "Alpha 1" "Path1:1" 0)', SexpReturnType.BOOL)
        self.assertEqual(errors, [])
        errors = self.validate_string('(is-facing "Alpha 1" "Alpha 1" 0)', SexpReturnType.BOOL)
        self.assertEqual(errors, [])

    def test_invalid_ship_point(self):
        # is-facing arg 1 uses OPF_SHIP_POINT
        errors = self.validate_string('(is-facing "Alpha 1" "InvalidTarget" 0)', SexpReturnType.BOOL)
        self.assertTrue(any("Invalid Ship/Point" in e for e in errors))

    # --- Tests for Player Orders and AI Goals Applicability ---

    def test_valid_player_order(self):
        errors = self.validate_string('(set-player-orders "Alpha 1" (true) "Attack Target")', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    def test_invalid_player_order(self):
        errors = self.validate_string('(set-player-orders "Alpha 1" (true) "Do a barrel roll")', SexpReturnType.NULL)
        self.assertTrue(any("Invalid Player AI Order" in e for e in errors), f"Got: {errors}")

    def test_fighter_bomber_only_goals_on_large_ship(self):
        self.ctx.ship_to_class["Orion 1"] = "GTD Orion"
        self.ctx.ships.add("Orion 1")
        self.ctx.ships.add("Beta 1")
        errors = self.validate_string('(add-goal "Orion 1" ( ai-guard "Beta 1" 89 ))', SexpReturnType.NULL)
        self.assertTrue(any("invalid for non-fighter/non-bomber ship" in e for e in errors), f"Got: {errors}")

    def test_fighter_bomber_only_goals_on_fighter(self):
        self.ctx.ship_to_class["Ulysses 1"] = "GTF Ulysses"
        self.ctx.ships.add("Ulysses 1")
        self.ctx.ships.add("Beta 1")
        errors = self.validate_string('(add-goal "Ulysses 1" ( ai-guard "Beta 1" 89 ))', SexpReturnType.NULL)
        self.assertEqual(errors, [])

    # --- Tests for malformed parenthesis detection ---

    def test_extra_closing_paren_top_level(self):
        """An extra ')' after a well-formed expression must raise SyntaxError."""
        with self.assertRaises(SyntaxError):
            self.parser.parse('(when (true) (do-nothing)))')

    def test_leading_closing_paren(self):
        """A bare ')' before any opening expression must raise SyntaxError."""
        with self.assertRaises(SyntaxError):
            self.parser.parse(')(when (true) (do-nothing))')

    def test_extra_closing_paren_between_expressions(self):
        """A stray ')' between two otherwise valid expressions must raise SyntaxError."""
        with self.assertRaises(SyntaxError):
            self.parser.parse('(when (true) (do-nothing))) (do-nothing)')

    def test_balanced_parens_do_not_raise(self):
        """Correctly balanced expressions must not raise."""
        # Should not raise; just verifying symmetry with the error cases above.
        result = self.parser.parse('(when (true) (do-nothing))')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
