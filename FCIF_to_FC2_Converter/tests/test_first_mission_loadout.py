"""
Tests for the first-mission loadout check in fcif_to_fc2.py.

Covers:
  - _collect_fsif_ships_and_weapons(): FSIF parser helper
  - check_first_mission_loadout(): comparison + warning logic
  - process_campaign() integration with --first-mission
"""

import unittest
import sys
import tempfile
from pathlib import Path

# Add the FCIF_to_FC2_Converter directory to path
_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
if str(_converter_dir) not in sys.path:
    sys.path.insert(0, str(_converter_dir))

from fcif_to_fc2 import (
    _collect_fsif_ships_and_weapons,
    check_first_mission_loadout,
    process_campaign,
    FCIF,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_fsif(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def _write_fcif(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def _make_log() -> tuple:
    """Return (log_func, messages_list). log_func appends to messages_list."""
    messages = []
    return messages.append, messages


def _minimal_fcif_yaml(ships: list[str], weapons: list[str]) -> str:
    if ships:
        ships_section = "  ships:\n" + "\n".join(f'    - "{s}"' for s in ships)
    else:
        ships_section = "  ships: []"
    if weapons:
        weapons_section = "  weapons:\n" + "\n".join(f'    - "{w}"' for w in weapons)
    else:
        weapons_section = "  weapons: []"
    return f"""fcif_version: "1.1"
campaign:
  name: "Test Campaign"
  description: "A test campaign"
starting_loadout:
{ships_section}
{weapons_section}
missions:
  - filename: mission_01.fs2
"""


# ---------------------------------------------------------------------------
# Class 1: _collect_fsif_ships_and_weapons
# ---------------------------------------------------------------------------

class TestCollectFsifShipsAndWeapons(unittest.TestCase):

    def test_standalone_ship_explicit_class(self):
        """A ship with an explicit 'class' field has its class collected."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        ship_classes, _, _ = result
        self.assertIn("GTF Ulysses", ship_classes)

    def test_standalone_ship_via_template(self):
        """A ship that only has 'template' (no explicit class) resolves class from ship_templates."""
        fsif = """
entities:
  ship_templates:
    fighter:
      class: "GTF Hercules"
      team: "Friendly"
  ships:
    - name: "Escort 1"
      template: "fighter"
      location: [0, 0, 0]
      arrival_cue: "( true )"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        ship_classes, _, _ = result
        self.assertIn("GTF Hercules", ship_classes)

    def test_standalone_ship_explicit_class_overrides_template(self):
        """When a ship has both 'class' and 'template', the ship's own class wins."""
        fsif = """
entities:
  ship_templates:
    fighter:
      class: "GTF Ulysses"
      team: "Friendly"
  ships:
    - name: "Custom 1"
      class: "GTF Hercules"
      template: "fighter"
      location: [0, 0, 0]
      arrival_cue: "( true )"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        ship_classes, _, _ = result
        self.assertIn("GTF Hercules", ship_classes)
        self.assertNotIn("GTF Ulysses", ship_classes)

    def test_wing_class_from_template(self):
        """A wing's class is resolved through its template in ship_templates."""
        fsif = """
entities:
  ship_templates:
    enemy_fighter:
      class: "SF Basilisk"
      team: "Hostile"
  wings:
    - name: "Rama"
      template: "enemy_fighter"
      count: 4
      position: [0, 0, 1000]
      arrival_cue: "( true )"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        ship_classes, _, _ = result
        self.assertIn("SF Basilisk", ship_classes)

    def test_primary_weapons_from_standalone_ship(self):
        """Primary weapons on a standalone ship are collected."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: ["ML-16 Laser", "Avenger"]
        secondary: []
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        _, primaries, secondaries = result
        self.assertIn("ML-16 Laser", primaries)
        self.assertIn("Avenger", primaries)
        self.assertEqual(secondaries, set())

    def test_secondary_weapons_from_standalone_ship(self):
        """Secondary weapons on a standalone ship are collected."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: []
        secondary: ["MX-50", "Hornet"]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        _, primaries, secondaries = result
        self.assertIn("MX-50", secondaries)
        self.assertIn("Hornet", secondaries)
        self.assertEqual(primaries, set())

    def test_weapons_from_template_via_wing(self):
        """Primary and secondary weapons defined in a template used by a wing are collected."""
        fsif = """
entities:
  ship_templates:
    friendly_fighter:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Prometheus", "Avenger"]
        secondary: ["Hornet"]
  wings:
    - name: "Alpha"
      template: "friendly_fighter"
      count: 4
      position: [300, 0, -250]
      arrival_cue: "( true )"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        _, primaries, secondaries = result
        self.assertIn("Prometheus", primaries)
        self.assertIn("Avenger", primaries)
        self.assertIn("Hornet", secondaries)

    def test_weapons_from_template_via_standalone_ship(self):
        """A standalone ship that uses a template inherits the template's weapons."""
        fsif = """
entities:
  ship_templates:
    escort:
      class: "GTC Fenris"
      team: "Friendly"
      weapons:
        primary: ["Flail"]
        secondary: ["Stiletto"]
  ships:
    - name: "Fenris 1"
      template: "escort"
      location: [600, 0, -100]
      arrival_cue: "( true )"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        _, primaries, secondaries = result
        self.assertIn("Flail", primaries)
        self.assertIn("Stiletto", secondaries)

    def test_empty_entities(self):
        """An FSIF with an empty entities block returns empty sets without crashing."""
        fsif = """
entities: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        ship_classes, primaries, secondaries = result
        self.assertEqual(ship_classes, set())
        self.assertEqual(primaries, set())
        self.assertEqual(secondaries, set())

    def test_missing_entities_section(self):
        """An FSIF with no 'entities' key at all returns empty sets without crashing."""
        fsif = """
mission_info:
  name: "No Entities"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", fsif)
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNotNone(result)
        assert result is not None
        ship_classes, primaries, secondaries = result
        self.assertEqual(ship_classes, set())
        self.assertEqual(primaries, set())
        self.assertEqual(secondaries, set())

    def test_file_not_found_returns_none(self):
        """A non-existent file path returns None and emits a [WARNING] log message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "does_not_exist.fsif"
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(nonexistent, log_fn)

        self.assertIsNone(result)
        self.assertTrue(any("[WARNING]" in str(m) for m in msgs), msgs)

    def test_invalid_yaml_returns_none(self):
        """A file with invalid YAML content returns None and emits a [WARNING]."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_fsif(Path(tmpdir), "m.fsif", "{ invalid yaml: [unclosed")
            log_fn, msgs = _make_log()
            result = _collect_fsif_ships_and_weapons(path, log_fn)

        self.assertIsNone(result)
        self.assertTrue(any("[WARNING]" in str(m) for m in msgs), msgs)


# ---------------------------------------------------------------------------
# Class 2: check_first_mission_loadout
# ---------------------------------------------------------------------------

def _load_fcif(yaml_str: str) -> FCIF:
    """Parse a YAML string directly into an FCIF model (no file I/O)."""
    import yaml
    data = yaml.safe_load(yaml_str)
    return FCIF(**data)


class TestCheckFirstMissionLoadout(unittest.TestCase):

    def _run_check(self, fsif_content: str, fcif_ships: list, fcif_weapons: list,
                   fsif_filename: str = "m01.fsif") -> list:
        """
        Write an FSIF file, build a minimal FCIF, run the check, return log messages.
        """
        log_fn, msgs = _make_log()
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = _write_fsif(Path(tmpdir), fsif_filename, fsif_content)
            fcif = _load_fcif(_minimal_fcif_yaml(fcif_ships, fcif_weapons))
            check_first_mission_loadout(str(fsif_path), fcif, log_fn)
        return msgs

    # -- Happy path ----------------------------------------------------------

    def test_all_ships_and_weapons_present_passes(self):
        """When all ships and weapons are in starting_loadout, an INFO pass is logged."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: ["ML-16 Laser"]
        secondary: ["MX-50"]
"""
        msgs = self._run_check(fsif, fcif_ships=["GTF Ulysses"],
                               fcif_weapons=["ML-16 Laser", "MX-50"])

        self.assertTrue(any("[INFO]" in m and "passed" in m for m in msgs), msgs)
        self.assertFalse(any("[WARNING]" in m for m in msgs), msgs)

    def test_empty_mission_always_passes(self):
        """An FSIF with no ships/wings/weapons in loadout check yields a clean INFO pass."""
        fsif = """
entities: {}
"""
        msgs = self._run_check(fsif, fcif_ships=[], fcif_weapons=[])

        self.assertTrue(any("[INFO]" in m and "passed" in m for m in msgs), msgs)
        self.assertFalse(any("[WARNING]" in m for m in msgs), msgs)

    # -- Warning cases -------------------------------------------------------

    def test_missing_ship_emits_warning(self):
        """A ship class used in the FSIF but absent from starting_loadout triggers a [WARNING]."""
        fsif = """
entities:
  ships:
    - name: "Escort 1"
      class: "GTF Hercules"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
"""
        msgs = self._run_check(fsif, fcif_ships=[], fcif_weapons=[])

        self.assertTrue(
            any("[WARNING]" in m and "GTF Hercules" in m for m in msgs), msgs
        )

    def test_missing_primary_weapon_emits_warning(self):
        """A primary weapon absent from starting_loadout triggers a [WARNING]."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: ["Prometheus"]
        secondary: []
"""
        msgs = self._run_check(fsif, fcif_ships=["GTF Ulysses"], fcif_weapons=[])

        self.assertTrue(
            any("[WARNING]" in m and "Prometheus" in m for m in msgs), msgs
        )

    def test_missing_secondary_weapon_emits_warning(self):
        """A secondary weapon absent from starting_loadout triggers a [WARNING]."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: []
        secondary: ["Hornet"]
"""
        msgs = self._run_check(fsif, fcif_ships=["GTF Ulysses"], fcif_weapons=[])

        self.assertTrue(
            any("[WARNING]" in m and "Hornet" in m for m in msgs), msgs
        )

    def test_missing_ship_and_weapon_emits_both_warnings(self):
        """Both a missing ship AND a missing weapon each produce their own [WARNING] group."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Hercules"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: ["Banshee"]
        secondary: []
"""
        msgs = self._run_check(fsif, fcif_ships=[], fcif_weapons=[])

        self.assertTrue(any("[WARNING]" in m and "GTF Hercules" in m for m in msgs), msgs)
        self.assertTrue(any("[WARNING]" in m and "Banshee" in m for m in msgs), msgs)

    # -- Edge / error cases --------------------------------------------------

    def test_file_not_found_warns_and_returns_gracefully(self):
        """A non-existent .fsif path triggers a [WARNING] and does not raise an exception."""
        log_fn, msgs = _make_log()
        fcif = _load_fcif(_minimal_fcif_yaml([], []))

        check_first_mission_loadout("/nonexistent/path/m.fsif", fcif, log_fn)

        self.assertTrue(any("[WARNING]" in m for m in msgs), msgs)
        self.assertFalse(any("[ERROR]" in m for m in msgs), msgs)

    def test_wrong_extension_warns_and_returns_gracefully(self):
        """A path with a non-.fsif extension triggers a [WARNING] and is skipped."""
        log_fn, msgs = _make_log()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a valid-content file but with .yaml extension
            wrong_ext = Path(tmpdir) / "mission.yaml"
            wrong_ext.write_text("entities: {}", encoding="utf-8")
            fcif = _load_fcif(_minimal_fcif_yaml([], []))
            check_first_mission_loadout(str(wrong_ext), fcif, log_fn)

        self.assertTrue(any("[WARNING]" in m for m in msgs), msgs)
        # No ships/weapons INFO pass should have been logged (check was skipped)
        self.assertFalse(any("passed" in m for m in msgs), msgs)


# ---------------------------------------------------------------------------
# Class 3: process_campaign integration
# ---------------------------------------------------------------------------

_MINIMAL_FCIF_TEMPLATE = """fcif_version: "1.1"
campaign:
  name: "Integration Test Campaign"
  description: "Testing first mission loadout check integration"
starting_loadout:
  ships:
{ships}
  weapons:
{weapons}
missions:
  - filename: mission_01.fs2
"""


class TestProcessCampaignIntegration(unittest.TestCase):

    def _make_fcif(self, ships: list, weapons: list) -> str:
        ships_yaml = "\n".join(f'    - "{s}"' for s in ships) if ships else "    []"
        weapons_yaml = "\n".join(f'    - "{w}"' for w in weapons) if weapons else "    []"
        return _MINIMAL_FCIF_TEMPLATE.format(ships=ships_yaml, weapons=weapons_yaml)

    def test_conversion_succeeds_with_clean_loadout(self):
        """process_campaign returns True and logs INFO pass when loadout is complete."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: ["ML-16 Laser"]
        secondary: ["MX-50"]
"""
        log_fn, msgs = _make_log()
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = _write_fsif(Path(tmpdir), "m01.fsif", fsif)
            fcif_path = _write_fcif(
                Path(tmpdir), "campaign.fcif",
                self._make_fcif(ships=["GTF Ulysses"], weapons=["ML-16 Laser", "MX-50"])
            )
            output_path = Path(tmpdir) / "campaign.fc2"

            result = process_campaign(
                str(fcif_path),
                str(output_path),
                first_mission=str(fsif_path),
                log_func=log_fn,
            )

        self.assertTrue(result)
        self.assertTrue(any("[INFO]" in m and "passed" in m for m in msgs), msgs)
        self.assertFalse(any("[WARNING]" in m for m in msgs), msgs)

    def test_conversion_still_succeeds_despite_loadout_warnings(self):
        """process_campaign returns True even when loadout warnings are present (non-fatal)."""
        fsif = """
entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Hercules"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: "( true )"
      weapons:
        primary: ["Banshee"]
        secondary: []
"""
        log_fn, msgs = _make_log()
        output_written = False
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = _write_fsif(Path(tmpdir), "m01.fsif", fsif)
            # FCIF starting_loadout intentionally missing the ship and weapon
            fcif_path = _write_fcif(
                Path(tmpdir), "campaign.fcif",
                self._make_fcif(ships=[], weapons=[])
            )
            output_path = Path(tmpdir) / "campaign.fc2"

            result = process_campaign(
                str(fcif_path),
                str(output_path),
                first_mission=str(fsif_path),
                log_func=log_fn,
            )
            # Check while tmpdir still exists
            output_written = output_path.exists()

        # Conversion must still succeed
        self.assertTrue(result)
        # Warnings must have been emitted
        self.assertTrue(any("[WARNING]" in m and "GTF Hercules" in m for m in msgs), msgs)
        self.assertTrue(any("[WARNING]" in m and "Banshee" in m for m in msgs), msgs)
        # Output file must have been written
        self.assertTrue(output_written)

    def test_conversion_without_first_mission_skips_check(self):
        """When first_mission=None, no loadout check log lines are emitted."""
        log_fn, msgs = _make_log()
        with tempfile.TemporaryDirectory() as tmpdir:
            fcif_path = _write_fcif(
                Path(tmpdir), "campaign.fcif",
                self._make_fcif(ships=["GTF Ulysses"], weapons=["ML-16 Laser"])
            )
            output_path = Path(tmpdir) / "campaign.fc2"

            result = process_campaign(
                str(fcif_path),
                str(output_path),
                first_mission=None,
                log_func=log_fn,
            )

        self.assertTrue(result)
        # No "first mission" related INFO or WARNING should appear
        self.assertFalse(
            any("first mission" in m.lower() or "loadout" in m.lower() for m in msgs),
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
