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

    # --- Tests for OPF_POSITIVE semantics (non-negative, not strictly positive) ---

    def test_opf_positive_zero_is_valid(self):
        """
        FSO OPF_POSITIVE means 'positive or zero' (non-negative).
        Literal 0 must be accepted wherever OPF_POSITIVE is expected.
        has-time-elapsed takes one OPF_POSITIVE argument.
        """
        errors = self.validate_string('(has-time-elapsed 0)', SexpReturnType.BOOL)
        positive_errors = [e for e in errors if "non-negative" in e or "must be positive" in e]
        self.assertFalse(positive_errors, f"0 should be valid for OPF_POSITIVE, got: {positive_errors}")

    def test_opf_positive_positive_integer_is_valid(self):
        """A normal positive integer must be accepted for OPF_POSITIVE."""
        errors = self.validate_string('(has-time-elapsed 30)', SexpReturnType.BOOL)
        positive_errors = [e for e in errors if "non-negative" in e or "must be positive" in e]
        self.assertFalse(positive_errors, f"30 should be valid for OPF_POSITIVE, got: {positive_errors}")

    def test_opf_positive_negative_is_invalid(self):
        """
        A negative number must be rejected for OPF_POSITIVE.
        The error message must mention 'non-negative' (positive or zero), not just 'positive'.
        """
        errors = self.validate_string('(has-time-elapsed -1)', SexpReturnType.BOOL)
        positive_errors = [e for e in errors if "non-negative" in e or "must be positive" in e]
        self.assertTrue(positive_errors,
                        f"Expected a non-negative error for -1 in OPF_POSITIVE slot, got: {errors}")
        # Confirm the new wording is used, not the old 'must be positive'
        self.assertTrue(
            any("non-negative" in e for e in positive_errors),
            f"Error message should contain 'non-negative', got: {positive_errors}",
        )

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


# =============================================================================
# Tests for player-ship terminal-state SEXP check
# =============================================================================

class TestPlayerShipTerminalStateCheck(unittest.TestCase):
    """
    Verify that has-departed-delay and is-destroyed-delay with the player
    start ship as an argument are detected as errors, while the same operators
    used with non-player ships pass cleanly.
    """

    def setUp(self):
        self.ctx = MissionContext()
        # Register a player ship and a non-player ship
        self.ctx.ships.add("Alpha 1")
        self.ctx.ships.add("Alpha 2")
        self.ctx.ships.add("GTC Fenris 1")
        self.ctx.player_start_ship = "Alpha 1"

        self.parser = SexpParser()
        self.validator = SexpValidator(self.ctx)

    def _errors(self, sexp_str, expected_type=SexpReturnType.BOOL):
        roots = self.parser.parse(sexp_str)
        errors = []
        for root in roots:
            errors.extend(self.validator.validate(root, expected_type=expected_type))
        return errors

    def test_is_destroyed_delay_with_player_ship_is_error(self):
        """is-destroyed-delay with the player start ship must produce an error."""
        errors = self._errors('(is-destroyed-delay 0 "Alpha 1")')
        self.assertTrue(
            any("Invalid mission-end logic" in e for e in errors),
            f"Expected 'Invalid mission-end logic' error, got: {errors}",
        )

    def test_has_departed_delay_with_player_ship_is_error(self):
        """has-departed-delay with the player start ship must produce an error."""
        errors = self._errors('(has-departed-delay 0 "Alpha 1")')
        self.assertTrue(
            any("Invalid mission-end logic" in e for e in errors),
            f"Expected 'Invalid mission-end logic' error, got: {errors}",
        )

    def test_is_destroyed_delay_with_non_player_ship_is_ok(self):
        """is-destroyed-delay with a non-player ship must pass the terminal-state check."""
        errors = self._errors('(is-destroyed-delay 0 "GTC Fenris 1")')
        terminal_errors = [e for e in errors if "Invalid mission-end logic" in e]
        self.assertFalse(
            terminal_errors,
            f"Non-player ship should not trigger terminal-state error, got: {terminal_errors}",
        )

    def test_has_departed_delay_with_non_player_ship_is_ok(self):
        """has-departed-delay with a non-player ship must pass the terminal-state check."""
        errors = self._errors('(has-departed-delay 0 "GTC Fenris 1")')
        terminal_errors = [e for e in errors if "Invalid mission-end logic" in e]
        self.assertFalse(
            terminal_errors,
            f"Non-player ship should not trigger terminal-state error, got: {terminal_errors}",
        )

    def test_nested_in_when_with_player_ship_is_error(self):
        """
        is-destroyed-delay with the player ship nested inside a when formula
        must still be detected.
        """
        errors = self._errors(
            '(when (is-destroyed-delay 0 "Alpha 1") (do-nothing))',
            expected_type=SexpReturnType.NULL,
        )
        self.assertTrue(
            any("Invalid mission-end logic" in e for e in errors),
            f"Expected 'Invalid mission-end logic' inside 'when', got: {errors}",
        )

    def test_player_ship_not_first_arg_is_detected(self):
        """
        Player ship name appearing after a non-player name must still be caught
        (the check scans all ship arguments, not only the first).
        """
        errors = self._errors('(is-destroyed-delay 0 "GTC Fenris 1" "Alpha 1")')
        self.assertTrue(
            any("Invalid mission-end logic" in e for e in errors),
            f"Expected 'Invalid mission-end logic' when player ship is not the first arg, got: {errors}",
        )

    def test_no_player_start_ship_in_context_does_not_crash(self):
        """
        When player_start_ship is None (no player setup configured), the check
        must silently pass without errors or exceptions.
        """
        ctx = MissionContext()
        ctx.ships.add("Alpha 1")
        # player_start_ship intentionally left as None
        validator = SexpValidator(ctx)
        roots = self.parser.parse('(is-destroyed-delay 0 "Alpha 1")')
        errors = []
        for root in roots:
            errors.extend(validator.validate(root, expected_type=SexpReturnType.BOOL))
        terminal_errors = [e for e in errors if "Invalid mission-end logic" in e]
        self.assertFalse(
            terminal_errors,
            f"No player_start_ship set — should not produce terminal-state error, got: {terminal_errors}",
        )

    def test_error_message_names_the_operator(self):
        """The error message must include the offending operator name."""
        errors = self._errors('(has-departed-delay 0 "Alpha 1")')
        self.assertTrue(
            any("has-departed-delay" in e for e in errors),
            f"Error message should mention 'has-departed-delay', got: {errors}",
        )

    def test_error_message_names_the_player_ship(self):
        """The error message must include the player start ship name."""
        errors = self._errors('(is-destroyed-delay 0 "Alpha 1")')
        self.assertTrue(
            any("Alpha 1" in e for e in errors),
            f"Error message should mention 'Alpha 1', got: {errors}",
        )


class TestPlayerShipTerminalStateViaValidateMission(unittest.TestCase):
    """
    Integration-level tests: verify that validate_mission() rejects FSIF missions
    that use has-departed-delay / is-destroyed-delay on the player start ship,
    and accepts them on non-player ships.
    """

    def _make_mission_with_event(self, formula: str, player_start: str = "Alpha 1"):
        """Build a minimal mission namespace whose single event uses the given formula."""
        from types import SimpleNamespace

        event = SimpleNamespace()
        event.name = "TestEvent"
        event.formula = formula

        ship = SimpleNamespace()
        ship.name = player_start
        ship.ship_class = "GTF Ulysses"
        ship.team = "Friendly"
        ship.arrival_cue = None
        ship.departure_cue = None
        ship.initial_orders = None

        ps = SimpleNamespace()
        ps.start_ship = player_start

        m = SimpleNamespace()
        m.ships = [ship]
        m.wings = []
        m.events = [event]
        m.goals = []
        m.messages = []
        m.waypoints = {}
        m.jump_nodes = []
        m.debriefing = SimpleNamespace(stages=[])
        m.player_setup = ps
        return m

    def test_validate_mission_rejects_is_destroyed_delay_on_player(self):
        """validate_mission returns False when an event checks is-destroyed-delay on the player ship."""
        import logging
        logging.disable(logging.CRITICAL)
        try:
            from advanced_sexp_validator import validate_mission
            mission = self._make_mission_with_event(
                '( when ( is-destroyed-delay 0 "Alpha 1" ) ( do-nothing ) )'
            )
            result = validate_mission(mission)
        finally:
            logging.disable(logging.NOTSET)
        self.assertFalse(result, "Expected validate_mission to fail for is-destroyed-delay on player ship")

    def test_validate_mission_rejects_has_departed_delay_on_player(self):
        """validate_mission returns False when an event checks has-departed-delay on the player ship."""
        import logging
        logging.disable(logging.CRITICAL)
        try:
            from advanced_sexp_validator import validate_mission
            mission = self._make_mission_with_event(
                '( when ( has-departed-delay 0 "Alpha 1" ) ( do-nothing ) )'
            )
            result = validate_mission(mission)
        finally:
            logging.disable(logging.NOTSET)
        self.assertFalse(result, "Expected validate_mission to fail for has-departed-delay on player ship")

    def test_validate_mission_accepts_is_destroyed_delay_on_non_player(self):
        """validate_mission does not fail when is-destroyed-delay checks a non-player ship."""
        import logging
        from types import SimpleNamespace
        logging.disable(logging.CRITICAL)
        try:
            from advanced_sexp_validator import validate_mission

            event = SimpleNamespace()
            event.name = "TestEvent"
            event.formula = '( when ( is-destroyed-delay 0 "GTC Fenris 1" ) ( do-nothing ) )'

            player_ship = SimpleNamespace()
            player_ship.name = "Alpha 1"
            player_ship.ship_class = "GTF Ulysses"
            player_ship.team = "Friendly"
            player_ship.arrival_cue = None
            player_ship.departure_cue = None
            player_ship.initial_orders = None

            npc_ship = SimpleNamespace()
            npc_ship.name = "GTC Fenris 1"
            npc_ship.ship_class = "GTC Fenris"
            npc_ship.team = "Friendly"
            npc_ship.arrival_cue = None
            npc_ship.departure_cue = None
            npc_ship.initial_orders = None

            ps = SimpleNamespace()
            ps.start_ship = "Alpha 1"

            m = SimpleNamespace()
            m.ships = [player_ship, npc_ship]
            m.wings = []
            m.events = [event]
            m.goals = []
            m.messages = []
            m.waypoints = {}
            m.jump_nodes = []
            m.debriefing = SimpleNamespace(stages=[])
            m.player_setup = ps

            result = validate_mission(m)
        finally:
            logging.disable(logging.NOTSET)
        self.assertTrue(result, "Expected validate_mission to pass when is-destroyed-delay targets a non-player ship")


# =============================================================================
# Tests for the argument-provider guard (DOMAIN_LITERAL_OPFS check)
# =============================================================================

class TestArgumentProviderGuard(unittest.TestCase):
    """
    Verify that dynamic <argument>-expansion operators (any-of, for-players,
    random-of, for-ship-class, etc.) are rejected when placed in domain-literal
    argument slots (ship names, message names, weapon names, waypoint paths, etc.)
    outside of their legitimate when-argument / every-time-argument contexts.

    Before this fix, the validator silently passed these as false negatives
    because for-players, any-of, etc. carry AMBIGUOUS return types that matched
    the coarse STRING requirement produced by map_opf_to_opr().

    These tests also verify that:
    - Normal literal domain values still pass unchanged.
    - Argument-provider operators are accepted where they legitimately belong.
    """

    def setUp(self):
        self.ctx = MissionContext()
        self.ctx.ships.add("Alpha 1")
        self.ctx.ships.add("Alpha 2")
        self.ctx.wings.add("Alpha")
        self.ctx.messages.add("Message 1")
        self.ctx.waypoints["Path1"] = 3
        self.parser = SexpParser()
        self.validator = SexpValidator(self.ctx)

    def _errors(self, sexp_str, expected_type=SexpReturnType.NULL):
        roots = self.parser.parse(sexp_str)
        errors = []
        for root in roots:
            errors.extend(self.validator.validate(root, expected_type=expected_type))
        return errors

    def _provider_errors(self, sexp_str, expected_type=SexpReturnType.NULL):
        """Return only errors that mention 'argument-provider'."""
        return [e for e in self._errors(sexp_str, expected_type) if "argument-provider" in e]

    # ---- False-negative regression tests: these must now FAIL ----

    def test_for_players_rejected_in_ship_wing_slot(self):
        """
        ( is-destroyed-delay 0 ( for-players ) ) used to pass silently.
        After the fix it must produce an argument-provider error.
        This is the canonical false-negative example documented in the README.
        """
        errs = self._provider_errors(
            "(is-destroyed-delay 0 (for-players))",
            SexpReturnType.BOOL,
        )
        self.assertTrue(errs, "Expected argument-provider error for 'for-players' in ship/wing slot")

    def test_for_ship_class_rejected_in_ship_wing_slot(self):
        """for-ship-class is an argument provider and must be rejected in OPF_SHIP_WING slots."""
        errs = self._provider_errors(
            '(is-destroyed-delay 0 (for-ship-class "GTF Ulysses"))',
            SexpReturnType.BOOL,
        )
        self.assertTrue(errs, "Expected argument-provider error for 'for-ship-class' in ship/wing slot")

    def test_any_of_rejected_in_ship_wing_slot(self):
        """any-of used in place of a ship/wing argument must be rejected."""
        errs = self._provider_errors(
            '(is-destroyed-delay 0 (any-of "Alpha 1" "Alpha 2"))',
            SexpReturnType.BOOL,
        )
        self.assertTrue(errs, "Expected argument-provider error for 'any-of' in ship/wing slot")

    def test_random_of_rejected_in_ship_wing_slot(self):
        """random-of used in place of a ship/wing argument must be rejected."""
        errs = self._provider_errors(
            '(is-destroyed-delay 0 (random-of "Alpha 1" "Alpha 2"))',
            SexpReturnType.BOOL,
        )
        self.assertTrue(errs, "Expected argument-provider error for 'random-of' in ship/wing slot")

    def test_for_ship_team_rejected_in_ship_wing_slot(self):
        """for-ship-team used in place of a ship/wing argument must be rejected."""
        errs = self._provider_errors(
            '(is-destroyed-delay 0 (for-ship-team "Hostile"))',
            SexpReturnType.BOOL,
        )
        self.assertTrue(errs, "Expected argument-provider error for 'for-ship-team' in ship/wing slot")

    def test_for_players_rejected_in_weapon_name_slot(self):
        """
        allow-weapon expects OPF_SHIP_CLASS_NAME/OPF_WEAPON_NAME (domain literal).
        A for-players provider must be rejected there.
        """
        errs = self._provider_errors("(allow-weapon (for-players))")
        self.assertTrue(errs, "Expected argument-provider error for 'for-players' in weapon name slot")

    def test_any_of_rejected_in_message_slot(self):
        """any-of must be rejected in the OPF_MESSAGE (message name) slot of send-message."""
        errs = self._provider_errors(
            '(send-message "Alpha 1" "High" (any-of "Message 1"))'
        )
        self.assertTrue(errs, "Expected argument-provider error for 'any-of' in message slot")

    def test_random_of_rejected_in_who_from_slot(self):
        """random-of must be rejected in the OPF_WHO_FROM (sender) slot of send-message."""
        errs = self._provider_errors(
            '(send-message (random-of "Alpha 1") "High" "Message 1")'
        )
        self.assertTrue(errs, "Expected argument-provider error for 'random-of' in who-from slot")

    def test_in_sequence_rejected_in_ship_wing_slot(self):
        """in-sequence must be rejected in OPF_SHIP_WING slots."""
        errs = self._provider_errors(
            '(protect-ship (in-sequence "Alpha 1" "Alpha 2"))',
        )
        self.assertTrue(errs, "Expected argument-provider error for 'in-sequence' in ship slot")

    def test_for_ship_type_rejected_in_ship_wing_slot(self):
        """for-ship-type must be rejected in OPF_SHIP_WING slots."""
        errs = self._provider_errors(
            '(protect-ship (for-ship-type "Fighter"))',
        )
        self.assertTrue(errs, "Expected argument-provider error for 'for-ship-type' in ship slot")

    # ---- Error message quality ----

    def test_error_message_names_the_provider_operator(self):
        """The error message must include the specific argument-provider operator name."""
        errs = self._provider_errors(
            "(is-destroyed-delay 0 (for-players))",
            SexpReturnType.BOOL,
        )
        self.assertTrue(
            any("for-players" in e for e in errs),
            f"Error should name 'for-players', got: {errs}",
        )

    def test_error_message_names_the_opf_slot(self):
        """The error message must include an OPF identifier for the bad slot."""
        errs = self._provider_errors(
            "(is-destroyed-delay 0 (for-players))",
            SexpReturnType.BOOL,
        )
        self.assertTrue(
            any("OPF_" in e for e in errs),
            f"Error should include OPF identifier, got: {errs}",
        )

    # ---- Non-regression: valid patterns must still pass ----

    def test_literal_ship_wing_still_accepted(self):
        """Normal literal ship/wing names must continue to pass unchanged."""
        errs = self._provider_errors(
            '(is-destroyed-delay 0 "Alpha 1")',
            SexpReturnType.BOOL,
        )
        self.assertFalse(errs, f"Literal ship name should not trigger guard, got: {errs}")

    def test_literal_ship_wing_not_in_context_still_gives_ship_error(self):
        """A bad literal ship name must still produce its existing error (not a guard error)."""
        errs = self._errors('(is-destroyed-delay 0 "NonExistentShip")', SexpReturnType.BOOL)
        # Should have a ship/wing name error, not an argument-provider error
        provider_errs = [e for e in errs if "argument-provider" in e]
        ship_errs = [e for e in errs if "Invalid Ship" in e or "Invalid Ship/Wing" in e]
        self.assertFalse(provider_errs, f"Literal bad ship name should NOT trigger argument-provider guard: {errs}")
        self.assertTrue(ship_errs, f"Bad literal ship name should still produce ship validation error: {errs}")

    def test_literal_message_still_accepted_in_send_message(self):
        """Literal message names in send-message must continue to pass."""
        errs = self._provider_errors(
            '(send-message "Alpha 1" "High" "Message 1")',
        )
        self.assertFalse(errs, f"Literal message name should not trigger guard, got: {errs}")

    def test_literal_weapon_still_accepted_in_allow_weapon(self):
        """Literal weapon names in allow-weapon must continue to pass."""
        errs = self._provider_errors('(allow-weapon "Avenger")')
        self.assertFalse(errs, f"Literal weapon name should not trigger guard, got: {errs}")

    def test_boolean_expression_in_bool_slot_not_affected(self):
        """Boolean nested expressions in boolean slots must not be affected by the guard."""
        errs = self._provider_errors(
            '(when (is-destroyed-delay 0 "Alpha 1") (do-nothing))',
            SexpReturnType.NULL,
        )
        self.assertFalse(errs, f"Boolean nested expression should not trigger guard, got: {errs}")

    def test_number_expression_in_number_slot_not_affected(self):
        """Arithmetic nested expressions in numeric slots must not be affected by the guard."""
        errs = self._provider_errors(
            "(< (distance \"Alpha 1\" \"Alpha 2\") 500)",
            SexpReturnType.BOOL,
        )
        self.assertFalse(errs, f"Numeric nested expression should not trigger guard, got: {errs}")


if __name__ == '__main__':
    unittest.main()
