"""
Tests that the FSIF 4.0 deep Pydantic input validation rejects all legacy
FSIF 3.0 field names before the loader runs any normalization.

The FSIFDocument model (and all nested input models) use extra='forbid',
so any FSIF 3.0 renamed key that is NOT present in the 4.0 input schema
triggers a Pydantic "Extra inputs are not permitted" error.
"""
import sys
import tempfile
import unittest
from pathlib import Path


_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from mission_loader import load_mission_from_fsif


MINIMAL_FSIF_4 = """fsif_version: "4.0"
mission_info:
  name: "Legacy Key Test"
environment:
  ambient_light_level: [0, 0, 0]
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
mission_flow: {}
"""

MINIMAL_FSIF_4_WITH_DOCKED_SHIP = """fsif_version: "4.0"
mission_info:
  name: "Dock Test"
environment:
  ambient_light_level: [0, 0, 0]
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
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      position: [600, 0, 0]
      arrival_cue: |
        ( true )
    - name: "GTT Elysium 1"
      class: "GTT Elysium"
      team: "Friendly"
      position: [540, 0, 20]
      arrival_cue: |
        ( false )
      dock:
        dockee: "GTC Fenris 1"
        docker_point: "topside docking"
        dockee_point: "Docking bay 1"
mission_flow: {}
"""


class FSIF40LegacyKeyTests(unittest.TestCase):
    def _write_and_load(self, fsif_text: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "mission.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def assert_legacy_key_rejected(self, fsif_text: str, old_key: str, new_key: str):
        """Assert that a file containing a legacy key is rejected by Pydantic input validation."""
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        msg = str(ctx.exception)
        # Pydantic extra='forbid' produces "Extra inputs are not permitted"
        self.assertIn("Extra inputs are not permitted", msg,
                      f"Expected Pydantic extra_forbidden error for key '{old_key}', got: {msg}")
        # The error message must name the problematic field
        self.assertIn(old_key, msg,
                      f"Expected error to mention legacy key '{old_key}', got: {msg}")

    # -------------------------------------------------------------------------
    # Positive: valid FSIF 4.0 files should load without errors
    # -------------------------------------------------------------------------

    def test_accepts_minimal_fsif_4_keys(self):
        """A minimal valid FSIF 4.0 file loads without errors."""
        mission = self._write_and_load(MINIMAL_FSIF_4)
        self.assertEqual(mission.player_setup.start_ship, "Player Ship")

    def test_accepts_valid_dock_block(self):
        """A valid FSIF 4.0 dock block (using 'dockee') loads without errors."""
        mission = self._write_and_load(MINIMAL_FSIF_4_WITH_DOCKED_SHIP)
        # GTT Elysium 1 should be docked with GTC Fenris 1
        docked_ship = next(s for s in mission.ships if s.name == "GTT Elysium 1")
        self.assertEqual(docked_ship.docked_with, "GTC Fenris 1")
        self.assertEqual(docked_ship.docker_point, "topside docking")
        self.assertEqual(docked_ship.dockee_point, "Docking bay 1")

    # -------------------------------------------------------------------------
    # player_setup renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_player_setup_extra_weapons(self):
        """extra_weapons (FSIF 3.0) must be rejected; use additional_weapons (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            'player_setup:\n  start_ship: "Player Ship"',
            'player_setup:\n  start_ship: "Player Ship"\n  extra_weapons: ["Hornet"]',
        )
        self.assert_legacy_key_rejected(fsif_text, "extra_weapons", "additional_weapons")

    def test_rejects_legacy_player_setup_extra_ships(self):
        """extra_ships (FSIF 3.0) must be rejected; use additional_ship_choices (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            'player_setup:\n  start_ship: "Player Ship"',
            'player_setup:\n  start_ship: "Player Ship"\n  extra_ships:\n    - {class: "GTF Ulysses", count: 4}',
        )
        self.assert_legacy_key_rejected(fsif_text, "extra_ships", "additional_ship_choices")

    # -------------------------------------------------------------------------
    # Ship arrival/departure renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_ship_arrival_location(self):
        """arrival_location (FSIF 3.0) must be rejected; use arrival_method (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      arrival_location: Hyperspace\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "arrival_location", "arrival_method")

    def test_rejects_legacy_ship_departure_location(self):
        """departure_location (FSIF 3.0) must be rejected; use departure_method (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      departure_location: Hyperspace\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "departure_location", "departure_method")

    def test_rejects_legacy_ship_location(self):
        """location (FSIF 3.0 ship position) must be rejected; use position (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      position: [0, 0, 0]",
            "      location: [0, 0, 0]",
        )
        self.assert_legacy_key_rejected(fsif_text, "location", "position")

    def test_rejects_legacy_ship_ai_goals(self):
        """ai_goals (FSIF 3.0) must be rejected; use initial_orders (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      ai_goals: |\n        ( ai-chase-any 89 )\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "ai_goals", "initial_orders")

    def test_rejects_legacy_ship_initial_velocity(self):
        """initial_velocity (FSIF 3.0) must be rejected; use initial_speed_percent (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      initial_velocity: 33\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "initial_velocity", "initial_speed_percent")

    def test_rejects_legacy_ship_initial_hull(self):
        """initial_hull (FSIF 3.0) must be rejected; use initial_hull_percent (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      initial_hull: 100\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "initial_hull", "initial_hull_percent")

    def test_rejects_legacy_ship_escort_priority(self):
        """escort_priority (FSIF 3.0) must be rejected; use escort_list_priority (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      escort_priority: 90\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "escort_priority", "escort_list_priority")

    def test_rejects_legacy_ship_destroy_before_mission(self):
        """destroy_before_mission (FSIF 3.0) must be rejected; use destroyed_before_mission_seconds (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "      weapons:",
            "      destroy_before_mission: 0\n      weapons:",
        )
        self.assert_legacy_key_rejected(fsif_text, "destroy_before_mission", "destroyed_before_mission_seconds")

    # -------------------------------------------------------------------------
    # Weapons renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_weapons_secondary_ammo(self):
        """secondary_ammo (FSIF 3.0) must be rejected; use secondary_ammo_counts (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            '        secondary: ["MX-50"]',
            '        secondary: ["MX-50"]\n        secondary_ammo: [40]',
        )
        self.assert_legacy_key_rejected(fsif_text, "secondary_ammo", "secondary_ammo_counts")

    # -------------------------------------------------------------------------
    # Dock block renames (the dock.with silent-drop bug)
    # -------------------------------------------------------------------------

    def test_rejects_legacy_dock_with(self):
        """dock.with (FSIF 3.0) must be rejected; use dock.dockee (4.0).
        
        This is the most critical legacy key test: before deep Pydantic validation,
        dock.with was silently ignored (dock_src.get('dockee') returned None),
        causing the ship to be loaded as not docked instead of failing.
        """
        fsif_text = MINIMAL_FSIF_4_WITH_DOCKED_SHIP.replace(
            "        dockee: \"GTC Fenris 1\"",
            "        with: \"GTC Fenris 1\"",
        )
        self.assert_legacy_key_rejected(fsif_text, "with", "dockee")

    # -------------------------------------------------------------------------
    # Environment renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_environment_starbitmaps(self):
        """starbitmaps (FSIF 3.0) must be rejected; use background_bitmaps (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  starbitmaps: []",
        )
        self.assert_legacy_key_rejected(fsif_text, "starbitmaps", "background_bitmaps")

    def test_rejects_legacy_nebula_awacs(self):
        """awacs (FSIF 3.0 nebula field) must be rejected; use sensor_range (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  nebula:\n    enabled: false\n    awacs: 3000.0",
        )
        self.assert_legacy_key_rejected(fsif_text, "awacs", "sensor_range")

    def test_rejects_legacy_nebula_poofs(self):
        """poofs (FSIF 3.0 nebula field) must be rejected; use cloud_sprites (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  nebula:\n    enabled: false\n    poofs: []",
        )
        self.assert_legacy_key_rejected(fsif_text, "poofs", "cloud_sprites")

    def test_rejects_legacy_asteroid_field_genre(self):
        """genre (FSIF 3.0 asteroid_field field) must be rejected; use object_type (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  asteroid_field:\n    genre: asteroid",
        )
        self.assert_legacy_key_rejected(fsif_text, "genre", "object_type")

    def test_rejects_legacy_asteroid_field_type(self):
        """type (FSIF 3.0 asteroid_field field) must be rejected; use behavior (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  asteroid_field:\n    type: passive",
        )
        self.assert_legacy_key_rejected(fsif_text, "type", "behavior")

    def test_rejects_legacy_asteroid_field_debris_types(self):
        """debris_types (FSIF 3.0) must be rejected; use object_variants (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  asteroid_field:\n    debris_types: []",
        )
        self.assert_legacy_key_rejected(fsif_text, "debris_types", "object_variants")

    def test_rejects_legacy_asteroid_field_targets(self):
        """targets (FSIF 3.0) must be rejected; use target_ships (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "  ambient_light_level: [0, 0, 0]",
            "  ambient_light_level: [0, 0, 0]\n  asteroid_field:\n    targets: []",
        )
        self.assert_legacy_key_rejected(fsif_text, "targets", "target_ships")

    # -------------------------------------------------------------------------
    # Reinforcement renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_reinforcement_num_times(self):
        """num_times (FSIF 3.0) must be rejected; use max_uses (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            "",
        )
        # Build FSIF with a reinforcement using num_times
        fsif_with_reinf = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            "",
        )
        fsif_with_reinf = MINIMAL_FSIF_4.replace(
            "  ships:",
            "  reinforcement_ships:\n    - name: \"Player Ship\"\n      num_times: 1\n  ships:",
        )
        self.assert_legacy_key_rejected(fsif_with_reinf, "num_times", "max_uses")

    def test_rejects_legacy_reinforcement_yes_messages(self):
        """yes_messages (FSIF 3.0) must be rejected; use available_messages (4.0)."""
        fsif_with_reinf = MINIMAL_FSIF_4.replace(
            "  ships:",
            "  reinforcement_ships:\n    - name: \"Player Ship\"\n      yes_messages: []\n  ships:",
        )
        self.assert_legacy_key_rejected(fsif_with_reinf, "yes_messages", "available_messages")

    def test_rejects_legacy_reinforcement_no_messages(self):
        """no_messages (FSIF 3.0) must be rejected; use unavailable_messages (4.0)."""
        fsif_with_reinf = MINIMAL_FSIF_4.replace(
            "  ships:",
            "  reinforcement_ships:\n    - name: \"Player Ship\"\n      no_messages: []\n  ships:",
        )
        self.assert_legacy_key_rejected(fsif_with_reinf, "no_messages", "unavailable_messages")

    # -------------------------------------------------------------------------
    # mission_flow renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_event_directive_text(self):
        """directive_text (FSIF 3.0 event field) must be rejected; use hud_directive_text (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            "mission_flow:\n  events:\n    - name: TestEvent\n      formula: |\n        ( when ( true ) ( do-nothing ) )\n      directive_text: \"Do something\"",
        )
        self.assert_legacy_key_rejected(fsif_text, "directive_text", "hud_directive_text")

    def test_rejects_legacy_goal_message(self):
        """message (FSIF 3.0 goal field) must be rejected; use objective_text (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            "mission_flow:\n  goals:\n    - name: TestGoal\n      formula: |\n        ( true )\n      message: \"Objective text\"",
        )
        self.assert_legacy_key_rejected(fsif_text, "message", "objective_text")

    def test_rejects_legacy_message_message(self):
        """message (FSIF 3.0 message text field) must be rejected; use text (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            "mission_flow:\n  messages:\n    - name: TestMsg\n      message: \"Hello\"",
        )
        self.assert_legacy_key_rejected(fsif_text, "message", "text")

    def test_rejects_legacy_debriefing_condition(self):
        """condition (FSIF 3.0 debriefing stage field) must be rejected; use display_condition (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            "mission_flow:\n  debriefing:\n    stages:\n      - text: \"Debrief text\"\n        condition: |\n          ( true )",
        )
        self.assert_legacy_key_rejected(fsif_text, "condition", "display_condition")

    # -------------------------------------------------------------------------
    # Briefing icon renames
    # -------------------------------------------------------------------------

    def test_rejects_legacy_briefing_icon_type(self):
        """type (FSIF 3.0 briefing icon field) must be rejected; use icon_type (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            'mission_flow:\n  briefing:\n    stages:\n      - text: "Stage text"\n        icons:\n          - {type: "Fighter", team: "Hostile", map_position: [0, 0]}',
        )
        self.assert_legacy_key_rejected(fsif_text, "type", "icon_type")

    def test_rejects_legacy_briefing_icon_class(self):
        """class (FSIF 3.0 briefing icon field) must be rejected; use display_class (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            'mission_flow:\n  briefing:\n    stages:\n      - text: "Stage text"\n        icons:\n          - {icon_type: "Fighter", team: "Hostile", class: "SF Dragon", map_position: [0, 0]}',
        )
        self.assert_legacy_key_rejected(fsif_text, "class", "display_class")

    def test_rejects_legacy_briefing_icon_pos(self):
        """pos (FSIF 3.0 briefing icon field) must be rejected; use map_position (4.0)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "mission_flow: {}",
            'mission_flow:\n  briefing:\n    stages:\n      - text: "Stage text"\n        icons:\n          - {icon_type: "Fighter", team: "Hostile", pos: [100, 200]}',
        )
        self.assert_legacy_key_rejected(fsif_text, "pos", "map_position")

    # -------------------------------------------------------------------------
    # Ship template forbidden fields
    # -------------------------------------------------------------------------

    def test_rejects_legacy_template_arrival_delay(self):
        """arrival_delay in a ship template must be rejected (never valid in templates)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "entities:",
            "entities:\n  ship_templates:\n    tmpl:\n      class: GTF Ulysses\n      team: Friendly\n      arrival_delay: 5",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        msg = str(ctx.exception)
        self.assertIn("arrival_delay", msg)
        self.assertIn("Extra inputs are not permitted", msg)

    def test_rejects_template_initial_orders(self):
        """initial_orders in a ship template must be rejected (not permitted in templates)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "entities:",
            "entities:\n  ship_templates:\n    tmpl:\n      class: GTF Ulysses\n      team: Friendly\n      initial_orders: |\n        ( ai-chase-any 89 )",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        msg = str(ctx.exception)
        self.assertIn("initial_orders", msg)
        self.assertIn("Extra inputs are not permitted", msg)

    def test_rejects_template_dock(self):
        """dock in a ship template must be rejected (not permitted in templates)."""
        fsif_text = MINIMAL_FSIF_4.replace(
            "entities:",
            "entities:\n  ship_templates:\n    tmpl:\n      class: GTF Ulysses\n      team: Friendly\n      dock:\n        dockee: SomeShip\n        docker_point: port\n        dockee_point: bay",
        )
        with self.assertRaises(ValueError) as ctx:
            self._write_and_load(fsif_text)
        msg = str(ctx.exception)
        self.assertIn("dock", msg)
        self.assertIn("Extra inputs are not permitted", msg)


if __name__ == "__main__":
    unittest.main()
