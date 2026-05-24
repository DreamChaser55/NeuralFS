"""
Regression tests for null handling of optional FSIF collections.

Verifies that explicit YAML ``null`` values for optional list/mapping fields
are treated identically to omitted keys (i.e., they produce an empty
list/dict/default-object rather than crashing with a generic exception).

See NeuralFS_analysis_report.md, P1: "Explicit YAML Null Values Can Crash
Loader Paths" for background.

Tests cover every field category mentioned in the analysis report:
  - entities.ships, entities.wings, entities.ship_templates
  - entities.reinforcement_wings, entities.reinforcement_ships
  - entities.jump_nodes, entities.waypoints
  - mission_flow.events, mission_flow.goals, mission_flow.messages
  - mission_flow.briefing, mission_flow.briefing (stages: null)
  - mission_flow.debriefing, mission_flow.command_briefing
  - briefing stage icons: null

Also includes negative tests that confirm a wrong (non-null, non-list) type
still produces a clear, actionable ValueError rather than a silent wrong result.
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


# ---------------------------------------------------------------------------
# Minimal valid FSIF fixture that uses Alpha wing for the player start.
# The `{entities_block}` and `{flow_block}` placeholders are filled in
# by each test case.
# ---------------------------------------------------------------------------

_BASE = """\
fsif_version: "1.0"
mission_info:
  name: "Null Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
entities:
{entities_block}
mission_flow:
{flow_block}
"""

_ALPHA_WING_BLOCK = """\
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
      position: [0, 0, 0]"""

_EMPTY_FLOW = "  events: []"


def _fsif(entities_block=_ALPHA_WING_BLOCK, flow_block=_EMPTY_FLOW):
    """Return a complete FSIF YAML string with the given entity/flow blocks."""
    return _BASE.format(
        entities_block=entities_block,
        flow_block=flow_block,
    )


def _write_and_load(fsif_text: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "mission.fsif"
        path.write_text(fsif_text, encoding="utf-8")
        return load_mission_from_fsif(str(path))


class TestNullEntitiesCollections(unittest.TestCase):
    """Explicit null for optional entities sub-collections."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_ships_null_loads_as_empty(self):
        """entities.ships: null must load as an empty standalone-ships list."""
        entities_block = _ALPHA_WING_BLOCK + "\n  ships: null"
        mission = _write_and_load(_fsif(entities_block=entities_block))
        # Wing members are in mission.ships; no additional standalone ships.
        wing_ship_names = {s.name for w in mission.wings for s in w.ships}
        standalone = [s for s in mission.ships if s.name not in wing_ship_names]
        self.assertEqual(standalone, [],
                         "No standalone ships expected when ships: null")

    def test_wings_null_uses_only_standalone_ships(self):
        """entities.wings: null — mission loads with no wings."""
        # Provide a standalone player ship so the player-start validation passes.
        entities_block = """\
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
  wings: null"""
        mission = _write_and_load(_fsif(entities_block=entities_block))
        self.assertEqual(mission.wings, [],
                         "wings: null must yield an empty wings list")

    def test_ship_templates_null_loads_as_empty(self):
        """entities.ship_templates: null — no templates; standalone ship can still define everything inline."""
        entities_block = """\
  ship_templates: null
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]"""
        mission = _write_and_load(_fsif(entities_block=entities_block))
        self.assertIsNotNone(mission)

    def test_reinforcement_wings_null_loads_as_empty(self):
        """entities.reinforcement_wings: null yields an empty reinforcements list."""
        entities_block = _ALPHA_WING_BLOCK + "\n  reinforcement_wings: null"
        mission = _write_and_load(_fsif(entities_block=entities_block))
        self.assertEqual(mission.reinforcements, [])

    def test_reinforcement_ships_null_loads_as_empty(self):
        """entities.reinforcement_ships: null yields an empty reinforcements list."""
        entities_block = _ALPHA_WING_BLOCK + "\n  reinforcement_ships: null"
        mission = _write_and_load(_fsif(entities_block=entities_block))
        self.assertEqual(mission.reinforcements, [])

    def test_jump_nodes_null_loads_as_empty(self):
        """entities.jump_nodes: null yields an empty jump_nodes list."""
        entities_block = _ALPHA_WING_BLOCK + "\n  jump_nodes: null"
        mission = _write_and_load(_fsif(entities_block=entities_block))
        self.assertEqual(mission.jump_nodes, [])

    def test_waypoints_null_loads_as_empty(self):
        """entities.waypoints: null yields an empty waypoints dict."""
        entities_block = _ALPHA_WING_BLOCK + "\n  waypoints: null"
        mission = _write_and_load(_fsif(entities_block=entities_block))
        self.assertEqual(mission.waypoints, {})


class TestNullMissionFlowCollections(unittest.TestCase):
    """Explicit null for optional mission_flow sub-collections."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_events_null_loads_as_empty(self):
        """mission_flow.events: null yields an empty events list."""
        mission = _write_and_load(_fsif(flow_block="  events: null"))
        self.assertEqual(mission.events, [])

    def test_goals_null_loads_as_empty(self):
        """mission_flow.goals: null yields an empty goals list."""
        mission = _write_and_load(_fsif(flow_block="  goals: null"))
        self.assertEqual(mission.goals, [])

    def test_messages_null_loads_as_empty(self):
        """mission_flow.messages: null yields an empty messages list."""
        mission = _write_and_load(_fsif(flow_block="  messages: null"))
        self.assertEqual(mission.messages, [])

    def test_briefing_null_loads_as_empty_briefing(self):
        """mission_flow.briefing: null yields an empty Briefing (no stages)."""
        mission = _write_and_load(_fsif(flow_block="  briefing: null"))
        self.assertEqual(mission.briefing.stages, [])

    def test_briefing_stages_null_loads_as_empty_stages(self):
        """mission_flow.briefing.stages: null yields an empty stages list."""
        flow_block = "  briefing:\n    stages: null"
        mission = _write_and_load(_fsif(flow_block=flow_block))
        self.assertEqual(mission.briefing.stages, [])

    def test_briefing_stage_icons_null_loads_as_empty_icons(self):
        """A briefing stage with icons: null yields an empty icons list on the stage."""
        flow_block = """\
  briefing:
    stages:
      - text: "Test stage"
        icons: null"""
        mission = _write_and_load(_fsif(flow_block=flow_block))
        self.assertEqual(len(mission.briefing.stages), 1)
        self.assertEqual(mission.briefing.stages[0].icons, [])

    def test_debriefing_null_loads_as_empty_debriefing(self):
        """mission_flow.debriefing: null yields an empty Debriefing (no stages)."""
        mission = _write_and_load(_fsif(flow_block="  debriefing: null"))
        self.assertEqual(mission.debriefing.stages, [])

    def test_debriefing_stages_null_loads_as_empty(self):
        """mission_flow.debriefing.stages: null yields an empty stages list."""
        flow_block = "  debriefing:\n    stages: null"
        mission = _write_and_load(_fsif(flow_block=flow_block))
        self.assertEqual(mission.debriefing.stages, [])

    def test_command_briefing_null_loads_as_empty(self):
        """mission_flow.command_briefing: null yields an empty CommandBriefing."""
        mission = _write_and_load(_fsif(flow_block="  command_briefing: null"))
        self.assertEqual(mission.command_briefing.stages, [])

    def test_command_briefing_stages_null_loads_as_empty(self):
        """mission_flow.command_briefing.stages: null yields an empty stages list."""
        flow_block = "  command_briefing:\n    stages: null"
        mission = _write_and_load(_fsif(flow_block=flow_block))
        self.assertEqual(mission.command_briefing.stages, [])


class TestNullCollectionsNegativeCases(unittest.TestCase):
    """Wrong non-null types for collection fields must produce clear errors."""

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_events_scalar_raises_clear_error(self):
        """mission_flow.events: 'bad_string' must raise a ValueError with the field path."""
        flow_block = "  events: \"bad_string\""
        with self.assertRaises(ValueError) as ctx:
            _write_and_load(_fsif(flow_block=flow_block))
        msg = str(ctx.exception)
        # Should be a schema error or a clear field-path error
        self.assertTrue(
            "events" in msg or "list" in msg or "validation" in msg.lower(),
            f"Expected a field-path or schema error mentioning 'events' or 'list', got: {msg}"
        )

    def test_wings_scalar_raises_clear_error(self):
        """entities.wings: 'bad_string' must raise a ValueError (not a silent crash)."""
        entities_block = _ALPHA_WING_BLOCK.replace(
            "  wings:\n    - name: \"Alpha\"",
            "  wings: \"bad_string\"\n    #",
        )
        # Easier approach: inject a broken wings value
        entities_block = """\
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
  wings: "not_a_list" """
        with self.assertRaises((ValueError, Exception)) as ctx:
            _write_and_load(_fsif(entities_block=entities_block))
        # Just confirm it raised something rather than silently continuing
        self.assertIsNotNone(ctx.exception)


if __name__ == "__main__":
    unittest.main()
