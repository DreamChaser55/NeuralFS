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
repo_root = converter_dir.parent
sys.path.insert(0, str(repo_root))

from advanced_sexp_validator import SexpParser, SexpValidator, MissionContext, SexpReturnType
from common import fs_data

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

# =============================================================================
# Tests for validate_mission diagnostic label naming (FSIF field names)
# =============================================================================

import logging
from types import SimpleNamespace
from advanced_sexp_validator import validate_mission, SexpReturnType as _SRT


def _make_ship(name, arrival_cue=None, departure_cue=None,
               initial_orders=None, ship_class="GTF Ulysses", team="Friendly"):
    """Build a minimal ship-like namespace for validate_mission tests."""
    s = SimpleNamespace()
    s.name = name
    s.ship_class = ship_class
    s.team = team
    s.arrival_cue = arrival_cue
    s.departure_cue = departure_cue
    s.initial_orders = initial_orders
    return s


def _make_wing(name, arrival_cue=None, departure_cue=None,
               initial_orders=None, ship_class="GTF Ulysses", team="Friendly"):
    """Build a minimal wing-like namespace for validate_mission tests."""
    ship = _make_ship(f"{name} 1", ship_class=ship_class, team=team)
    w = SimpleNamespace()
    w.name = name
    w.arrival_cue = arrival_cue
    w.departure_cue = departure_cue
    w.initial_orders = initial_orders
    w.ships = [ship]
    return w


def _make_minimal_mission(ships=None, wings=None):
    """Build a minimal Mission-like namespace with the attrs validate_mission needs."""
    m = SimpleNamespace()
    m.ships = ships or []
    m.wings = wings or []
    m.events = []
    m.goals = []
    m.messages = []
    m.waypoints = {}
    m.jump_nodes = []
    m.debriefing = SimpleNamespace(stages=[])
    return m


class TestValidateMissionDiagnosticLabels(unittest.TestCase):
    """
    Verify that validate_mission() emits FSIF field names in its diagnostics,
    not the old FSO/FS2 labels (Arrival Cue, Departure Cue, AI Goals).
    """

    def _capture_logs(self, mission):
        """Run validate_mission and capture all logged messages."""
        log_records = []
        handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL)
        handler.buffer = []

        class ListHandler(logging.Handler):
            def emit(self, record):
                log_records.append(self.format(record))

        list_handler = ListHandler()
        # Attach to the advanced_sexp_validator logger
        import advanced_sexp_validator as _mod
        logger = logging.getLogger(_mod.__name__)
        logger.addHandler(list_handler)
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        try:
            validate_mission(mission)
        finally:
            logger.removeHandler(list_handler)
            logger.setLevel(original_level)
        return log_records

    def test_arrival_cue_label_not_arrival_cue(self):
        """
        When a ship has an invalid arrival_cue SEXP, the diagnostic must
        reference 'arrival_cue', not 'Arrival Cue'.
        """
        ship = _make_ship("Alpha 1", arrival_cue="( has-arrived-delay 0 \"NonExistentShip\" )")
        mission = _make_minimal_mission(ships=[ship])
        logs = self._capture_logs(mission)

        combined = "\n".join(logs)
        self.assertIn("arrival_cue", combined,
                      "Expected 'arrival_cue' in validator output")
        self.assertNotIn("Arrival Cue", combined,
                         "Old FSO label 'Arrival Cue' should NOT appear in validator output")

    def test_departure_cue_label_not_departure_cue(self):
        """
        When a ship has an invalid departure_cue SEXP, the diagnostic must
        reference 'departure_cue', not 'Departure Cue'.
        """
        ship = _make_ship("Alpha 1",
                          arrival_cue="( true )",
                          departure_cue="( has-arrived-delay 0 \"NonExistentShip\" )")
        mission = _make_minimal_mission(ships=[ship])
        logs = self._capture_logs(mission)

        combined = "\n".join(logs)
        self.assertIn("departure_cue", combined,
                      "Expected 'departure_cue' in validator output")
        self.assertNotIn("Departure Cue", combined,
                         "Old FSO label 'Departure Cue' should NOT appear in validator output")

    def test_initial_orders_label_not_ai_goals(self):
        """
        When a ship has initial_orders with a detectable issue, the diagnostic must
        reference 'initial_orders', not 'AI Goals'.
        """
        # Use a fighter-only AI goal on a non-fighter ship (GTC Fenris) — this
        # triggers an applicability error and will appear in the logs.
        ship = _make_ship(
            "GTC Fenris 1",
            arrival_cue="( true )",
            initial_orders="( goals\n( ai-guard \"Alpha 1\" 89 )\n)",
            ship_class="GTC Fenris",
            team="Friendly",
        )
        ship2 = _make_ship("Alpha 1", arrival_cue="( true )", ship_class="GTF Ulysses", team="Friendly")
        mission = _make_minimal_mission(ships=[ship, ship2])
        logs = self._capture_logs(mission)

        combined = "\n".join(logs)
        self.assertIn("initial_orders", combined,
                      "Expected 'initial_orders' in validator output")
        self.assertNotIn("AI Goals", combined,
                         "Old FSO label 'AI Goals' should NOT appear in validator output")

    def test_wing_arrival_cue_label(self):
        """Wing diagnostic labels must use 'arrival_cue', not 'Arrival Cue'."""
        wing = _make_wing("Beta",
                          arrival_cue="( has-arrived-delay 0 \"NonExistentShip\" )")
        mission = _make_minimal_mission(wings=[wing])
        logs = self._capture_logs(mission)

        combined = "\n".join(logs)
        self.assertIn("arrival_cue", combined,
                      "Expected 'arrival_cue' in wing validator output")
        self.assertNotIn("Arrival Cue", combined,
                         "Old FSO label 'Arrival Cue' should NOT appear in wing validator output")

    def test_wing_initial_orders_label(self):
        """Wing initial_orders diagnostic must reference 'initial_orders', not 'AI Goals'."""
        wing = _make_wing(
            "Gamma",
            arrival_cue="( true )",
            initial_orders="( goals\n( ai-guard \"Alpha 1\" 89 )\n)",
            ship_class="GTC Fenris",
            team="Friendly",
        )
        player = _make_ship("Alpha 1", arrival_cue="( true )")
        mission = _make_minimal_mission(ships=[player], wings=[wing])
        logs = self._capture_logs(mission)

        combined = "\n".join(logs)
        self.assertIn("initial_orders", combined,
                      "Expected 'initial_orders' in wing validator output")
        self.assertNotIn("AI Goals", combined,
                         "Old FSO label 'AI Goals' should NOT appear in wing validator output")

    def test_ai_goal_applicability_still_checked_via_initial_orders(self):
        """
        After refactoring subject tracking away from string parsing,
        AI-goal applicability checks must still fire correctly when a
        non-fighter ship has a fighter-only initial_orders goal.
        """
        ship = _make_ship(
            "GTC Fenris 1",
            arrival_cue="( true )",
            initial_orders="( goals\n( ai-guard \"Alpha 1\" 89 )\n)",
            ship_class="GTC Fenris",
            team="Friendly",
        )
        target = _make_ship("Alpha 1", arrival_cue="( true )")
        mission = _make_minimal_mission(ships=[ship, target])
        logs = self._capture_logs(mission)

        combined = "\n".join(logs)
        self.assertIn("invalid for non-fighter/non-bomber ship", combined,
                      "AI-goal applicability check must still fire after subject tracking refactor")


class TestAtomValidatorWording(unittest.TestCase):
    """
    Verify that atom validator error messages use the improved wording
    introduced in Phase 2 of the naming cleanup.
    """

    def setUp(self):
        self.ctx = MissionContext()
        self.parser = SexpParser()
        self.validator = SexpValidator(self.ctx)

    def _errors(self, sexp_str, expected_type=SexpReturnType.NULL):
        roots = self.parser.parse(sexp_str)
        errors = []
        for root in roots:
            errors.extend(self.validator.validate(root, expected_type=expected_type))
        return errors

    def test_invalid_background_bitmap_wording(self):
        """Invalid background bitmap token message must say 'background bitmap token'."""
        errors = self._errors('(add-background-bitmap-new "bad_bitmap" 0 0 0 100 100 4 4)',
                              SexpReturnType.NULL)
        # There may be multiple errors (argument count / type issues); look for the bitmap one.
        bitmap_errors = [e for e in errors if "bitmap" in e.lower() or "background" in e.lower()]
        self.assertTrue(bitmap_errors,
                        f"Expected a background bitmap error, got: {errors}")
        # None of the bitmap errors should contain the old title-case "Background Bitmap"
        # (the new message uses lowercase "background bitmap token")
        self.assertFalse(
            any("Background Bitmap:" in e for e in bitmap_errors),
            f"Old 'Background Bitmap:' wording found in: {bitmap_errors}"
        )

    def test_invalid_nebula_poof_wording(self):
        """Invalid cloud sprite error must mention 'cloud sprite' and 'nebula poof'."""
        errors = self._errors('(nebula-toggle-poof "bad_poof" (true))', SexpReturnType.NULL)
        self.assertTrue(errors, f"Expected errors, got none")
        poof_errors = [e for e in errors if "poof" in e.lower() or "cloud" in e.lower() or "sprite" in e.lower()]
        self.assertTrue(poof_errors, f"Expected a cloud sprite/nebula poof error, got: {errors}")
        # The new wording must include both "cloud sprite" and "nebula poof"
        self.assertTrue(
            any("cloud sprite" in e.lower() for e in poof_errors),
            f"Expected 'cloud sprite' in error, got: {poof_errors}"
        )
        self.assertTrue(
            any("nebula poof" in e.lower() for e in poof_errors),
            f"Expected 'nebula poof' in error, got: {poof_errors}"
        )

    def test_invalid_nebula_storm_token_is_rejected(self):
        """An invalid nebula-change-storm token must produce an error mentioning 'storm'."""
        errors = self._errors('(nebula-change-storm "s_heavy")', SexpReturnType.NULL)
        self.assertTrue(errors, f"Expected errors for invalid storm token, got none")
        storm_errors = [e for e in errors if "storm" in e.lower()]
        self.assertTrue(storm_errors, f"Expected an error mentioning 'storm', got: {errors}")
        # Error must identify the bad token
        self.assertTrue(
            any("s_heavy" in e for e in storm_errors),
            f"Expected 's_heavy' mentioned in storm error, got: {storm_errors}"
        )

    def test_valid_nebula_storm_tokens_are_accepted(self):
        """Every canonical nebula-change-storm token must pass validation."""
        for token in ("none", "s_standard", "s_medium", "s_active", "s_emp"):
            with self.subTest(storm=token):
                errors = self._errors(f'(nebula-change-storm "{token}")', SexpReturnType.NULL)
                storm_errors = [e for e in errors if "storm" in e.lower()]
                self.assertFalse(
                    storm_errors,
                    f"Token '{token}' should be valid, but got storm error(s): {storm_errors}"
                )


import logging.handlers  # needed by _capture_logs above


if __name__ == '__main__':
    unittest.main()
