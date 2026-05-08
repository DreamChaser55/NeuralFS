import unittest
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to allow importing modules
# FSIF_to_FS2_Converter/tests/ -> FSIF_to_FS2_Converter/
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
_repo_root = _parent_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from data_models import (
    Mission,
    Message,
    MissionInfo,
    PlayerSetup,
    Environment,
    Ship,
    Weapons,
    Briefing,
    BriefingStage,
    JumpNode,
    Wing,
    pack_ambient_light_rgb,
)
from fs2_writer import FS2Writer
from common.utils import sanitize_path
from mission_loader import load_mission_from_fsif
from validator import Validator
from voice_manager import VoiceManager


class CombinedTesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def make_valid_mission(self) -> Mission:
        return Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(),
            ships=[
                Ship.model_validate(
                    {
                        "name": "Player Ship",
                        "class": "GTF Ulysses",
                        "team": "Friendly",
                        "position": [0.0, 0.0, 0.0],
                        "arrival_cue": "( true )",
                        "weapons": Weapons(
                            primary=["Avenger", "Avenger"],
                            secondary=["MX-50"],
                        ),
                    }
                )
            ],
        )

    def make_validator(self, mission: Mission) -> Validator:
        return Validator(mission, _repo_root)

    def test_ascii_mission_passes_validation(self):
        mission = self.make_valid_mission()

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)

    def test_non_ascii_briefing_text_is_rejected(self):
        mission = self.make_valid_mission()
        mission.briefing = Briefing(
            stages=[
                BriefingStage(text="Hold position — protect the convoy.")
            ]
        )

        validator = self.make_validator(mission)

        self.assertFalse(validator.validate())
        self.assertTrue(
            any(
                "briefing.stages[0].text" in error and "U+2014" in error
                for error in validator.errors
            ),
            validator.errors,
        )

    def test_voice_style_instructions_are_excluded_from_ascii_validation(self):
        mission = self.make_valid_mission()
        mission.briefing = Briefing(
            stages=[
                BriefingStage(
                    text="Hold position and protect the convoy.",
                    voice_style_instructions="Calm — authoritative",
                )
            ]
        )

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)

    def test_distance_over_20km_between_objects_warns(self):
        mission = self.make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="Far Node", position=[25000.0, 0.0, 0.0])
        ]

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: 1 object pair(s) exceed" in warning
                and "Ship 'Player Ship' <-> Jump Node 'Far Node'" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_arrival_distance_over_20km_warns_for_ship_and_wing(self):
        mission = self.make_valid_mission()
        mission.ships.append(
            Ship.model_validate(
                {
                    "name": "Escort 1",
                    "class": "GTC Fenris",
                    "team": "Friendly",
                    "position": [500.0, 0.0, 0.0],
                    "arrival_method": "In front of ship",
                    "arrival_anchor": "Player Ship",
                    "arrival_distance": 25001,
                    "arrival_cue": "( true )",
                }
            )
        )
        mission.wings = [
            Wing(
                name="Beta",
                count=1,
                ships=[
                    Ship.model_validate(
                        {
                            "name": "Beta 1",
                            "class": "GTF Ulysses",
                            "team": "Friendly",
                            "position": [1000.0, 0.0, 0.0],
                            "arrival_cue": "( true )",
                            "weapons": Weapons(
                                primary=["Avenger", "Avenger"],
                                secondary=["MX-50"],
                            ),
                        }
                    )
                ],
                position=[1000.0, 0.0, 0.0],
                arrival_method="In front of ship",
                arrival_anchor="Player Ship",
                arrival_distance=22000,
                arrival_cue="( true )",
            )
        ]

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: Ship 'Escort 1' arrival_distance 25001 m" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )
        self.assertTrue(
            any(
                "Mission scale recommendation: Wing 'Beta' arrival_distance 22000 m" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_distance_and_arrival_distance_at_20km_do_not_warn(self):
        mission = self.make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="Limit Node", position=[20000.0, 0.0, 0.0])
        ]
        mission.ships.append(
            Ship.model_validate(
                {
                    "name": "Escort 1",
                    "class": "GTC Fenris",
                    "team": "Friendly",
                    "position": [500.0, 0.0, 0.0],
                    "arrival_method": "In front of ship",
                    "arrival_anchor": "Player Ship",
                    "arrival_distance": 20000,
                    "arrival_cue": "( true )",
                }
            )
        )

        validator = self.make_validator(mission)

        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any("Mission scale recommendation:" in warning for warning in validator.warnings),
            validator.warnings,
        )

    def test_3d_mission_design_warns_when_all_objects_on_xz_plane(self):
        mission = self.make_valid_mission()
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "All objects are currently placed on the 2D XZ plane (Y=0)" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_3d_mission_design_does_not_warn_when_objects_spread_in_y(self):
        mission = self.make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="High Node", position=[0.0, 500.0, 0.0])
        ]
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "Mission design recommendation: All objects are placed on the 2D XZ plane (Y=0)" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_writer_weapon_pool_secondary_sizes(self):
        mission = self.make_valid_mission()
        
        # We must add two ships to the wing's `ships` list, since `fs2_writer` uses `len(wing.ships)`
        ship1 = Ship.model_validate(
            {
                "name": "Alpha 1",
                "class": "GTF Ulysses",
                "team": "Friendly",
                "position": [0.0, 0.0, 0.0],
                "arrival_cue": "( true )",
                "weapons": Weapons(
                    primary=["Avenger", "Avenger"],
                    secondary=["Harbinger"],
                ),
            }
        )
        ship2 = Ship.model_validate(
            {
                "name": "Alpha 2",
                "class": "GTF Ulysses",
                "team": "Friendly",
                "position": [0.0, 0.0, 0.0],
                "arrival_cue": "( true )",
                "weapons": Weapons(
                    primary=["Avenger", "Avenger"],
                    secondary=["Harbinger"],
                ),
            }
        )
        
        mission.wings = [
            Wing(
                name="Alpha",
                count=2,
                ships=[ship1, ship2],
                position=[0.0, 0.0, 0.0],
                arrival_cue="( true )",
            )
        ]
        mission.player_setup.additional_weapons = ["Tsunami"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn('"Harbinger"\t3', content)
        self.assertIn('"Tsunami"\t5', content)

    def test_writer_always_emits_fixed_fog_multipliers(self):
        mission = self.make_valid_mission()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("+Fog Near Mult: 1.000000", content)
        self.assertIn("+Fog Far Mult: 1.000000", content)

    def test_pack_ambient_light_rgb_helper(self):
        self.assertEqual(pack_ambient_light_rgb([0, 0, 0]), 0)
        self.assertEqual(pack_ambient_light_rgb([10, 10, 10]), 657930)
        self.assertEqual(pack_ambient_light_rgb([255, 255, 255]), 16777215)

    def test_writer_packs_rgb_ambient_light_into_fs2_integer(self):
        mission = self.make_valid_mission()
        mission.environment = Environment(ambient_light_level=[10, 10, 10])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mission.fs2"
            writer = FS2Writer(mission, str(output_path))
            writer.write_mission()
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("$Ambient light level: 657930", content)

    def test_loader_rejects_fsif_26(self):
        fsif_text = """fsif_version: \"2.6\"

mission_info:
  name: "Legacy Mission"

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
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

mission_flow: {}

environment:
  ambient_light_level: 657930
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "legacy_version.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("accepts FSIF version '4.0' only", str(ctx.exception))

    def test_old_version_fsif_fails_with_version_error_not_pydantic_wall(self):
        """
        Regression test: a FSIF file with an old version number AND many
        renamed/legacy field names must fail with a clean unsupported-version
        error, NOT with a wall of Pydantic 'Extra inputs are not permitted'
        errors caused by incompatible field names.

        This verifies that _validate_version() runs before _validate_fsif_schema()
        in MissionLoader.load().
        """
        # Combine old fsif_version with several legacy FSIF 3.0 field names
        # that would each generate a Pydantic error if schema validation ran first.
        fsif_text = """fsif_version: "3.0"

mission_info:
  name: "Old Legacy Mission"

environment:
  ambient_light_level: [0, 0, 0]
  starbitmaps: []

player_setup:
  start_ship: "Player Ship"
  extra_weapons:
    - "Hornet"
  extra_ships:
    - {class: "GTF Ulysses", count: 4}

entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: |
        ( true )
      ai_goals: |
        ( ai-chase-any 89 )

mission_flow:
  events:
    - formula: |
        ( when ( true ) ( do-nothing ) )
      directive_text: "Old directive text field"
  goals:
    - name: "Old Goal"
      message: "Old goal text field"
      formula: |
        ( true )
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "old_version.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        error_msg = str(ctx.exception)

        # Must contain the simple version mismatch message
        self.assertIn("Unsupported fsif_version '3.0'", error_msg)
        self.assertIn("accepts FSIF version '4.0' only", error_msg)

        # Must NOT contain Pydantic schema error markers — version check must
        # have fired before the schema validator had a chance to run.
        self.assertNotIn("FSIF document validation error", error_msg,
                         "Schema validation ran before version check — Pydantic error wall was not suppressed.")
        self.assertNotIn("Extra inputs are not permitted", error_msg,
                         "Schema validation ran before version check — legacy field names triggered Pydantic errors.")

    def test_loader_rejects_packed_ambient_light_in_fsif_27(self):
        fsif_text = """fsif_version: \"4.0\"

mission_info:
  name: "Invalid Ambient"

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
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

mission_flow: {}

environment:
  ambient_light_level: 10
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "invalid_ambient_26.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("FSIF requires environment.ambient_light_level to be authored as [red, green, blue]", str(ctx.exception))

    def test_validator_rejects_invalid_ai_orders_and_goals(self):
        fsif_text = """
fsif_version: "4.0"
mission_info:
  name: "Invalid Orders Demo"
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
    - name: "Cruiser 1"
      class: "GTC Fenris"
      team: "Hostile"
      position: [0, 0, 0]
      initial_orders: |
        ( ai-guard "Player Ship" 89 )
mission_flow:
  events:
    - formula: '( set-player-orders "Player Ship" ( true ) "Do a barrel roll" )'
environment:
  ambient_light_level: [0, 0, 0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "invalid_orders.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            # Load should succeed
            mission = load_mission_from_fsif(str(fsif_path))
            
            # But Advanced SEXP Validation should fail it
            adv_val_dir = _repo_root / "FSIF_to_FS2_Converter" / "Advanced_SEXP_Validator"
            if str(adv_val_dir) not in sys.path:
                sys.path.insert(0, str(adv_val_dir))
            import advanced_sexp_validator
            is_valid = advanced_sexp_validator.validate_mission(mission)
            self.assertFalse(is_valid, "Expected advanced SEXP validation to fail due to invalid player order and invalid cruiser goal.")

    def test_loader_rejects_arrival_delay_in_ship_template(self):
        fsif_text = """fsif_version: "4.0"

mission_info:
  name: "Invalid Template Arrival Delay"

player_setup:
  start_ship: "Player Ship"

entities:
  ship_templates:
    fighter_template:
      class: "GTF Ulysses"
      team: "Friendly"
      arrival_delay: 5
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  ships:
    - name: "Player Ship"
      template: "fighter_template"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )

mission_flow: {}

environment:
  ambient_light_level: [0, 0, 0]
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "invalid_template_arrival_delay.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_mission_from_fsif(str(fsif_path))

        self.assertIn("arrival_delay", str(ctx.exception))
        # Deep Pydantic input validation (ShipTemplateInput extra='forbid') catches
        # this before the loader's _validate_ship_template_authoring_rules runs.
        self.assertIn("Extra inputs are not permitted", str(ctx.exception))

    def test_environment_rejects_invalid_rgb_channel_range(self):
        with self.assertRaises(ValueError) as ctx:
            Environment(ambient_light_level=[256, 0, 0])

        self.assertIn("out of range 0..255", str(ctx.exception))

    def test_environment_rejects_invalid_rgb_shape(self):
        with self.assertRaises(ValueError) as ctx:
            Environment(ambient_light_level=[10, 10])

        self.assertIn("3-item RGB list", str(ctx.exception))

    def test_environment_rejects_packed_integer_input(self):
        with self.assertRaises(ValueError) as ctx:
            Environment.model_validate({"ambient_light_level": 657930})

        self.assertIn("ambient_light_level must be authored as [red, green, blue]", str(ctx.exception))

    def test_sanitize_path_preserves_spaces(self):
        raw = 'missions\\ambient light testing\\white.fsif'
        self.assertEqual(sanitize_path(raw), raw)

    def test_sanitize_path_strips_only_outer_quotes(self):
        raw = '"missions\\ambient light testing\\white.fsif"'
        self.assertEqual(sanitize_path(raw), 'missions\\ambient light testing\\white.fsif')


class VoiceManagerTesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(),
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fsif_path = Path(self.temp_dir.name) / "dummy.fsif"
        self.tts_settings = {"mode": "unique"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_determinism(self):
        """Test that re-running with same input produces same filenames (determinism)."""
        self.mission.messages = [
            Message(name="Alpha", text="Msg 1", voice_name="Voice1"),
            Message(name="Alpha", text="Msg 2", voice_name="Voice1"),
            Message(name="Alpha", text="Msg 3", voice_name="Voice1"),
        ]

        vm1 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm1.process()
        filenames1 = [m.voice_filename for m in self.mission.messages]

        vm2 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm2.process()
        filenames2 = [m.voice_filename for m in self.mission.messages]

        self.assertEqual(filenames1, filenames2, "Filenames should be deterministic across runs")
        self.assertEqual(filenames1, ["alpha.wav", "alpha_1.wav", "alpha_2.wav"])

    def test_length_limit_simple(self):
        """Test strict truncation to 25 chars for stem."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit"
        self.mission.messages = [
            Message(name=long_name, text="Msg", voice_name="Voice1")
        ]

        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        fname = self.mission.messages[0].voice_filename
        self.assertIsNotNone(fname)
        assert fname is not None
        self.assertTrue(len(fname) <= 29, f"Filename '{fname}' exceeds 29 chars")
        self.assertTrue(fname.endswith(".wav"))
        self.assertEqual(fname, "this_is_a_very_long_name_.wav")

    def test_length_limit_collision(self):
        """Test truncation when suffix is added."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit"
        self.mission.messages = [
            Message(name=long_name, text="Msg 1", voice_name="Voice1"),
            Message(name=long_name, text="Msg 2", voice_name="Voice1"),
            Message(name=long_name, text="Msg 3", voice_name="Voice1"),
        ]

        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        fnames = [m.voice_filename for m in self.mission.messages]

        for fn in fnames:
            self.assertIsNotNone(fn)
            assert fn is not None
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")

        self.assertEqual(fnames[0], "this_is_a_very_long_name_.wav")
        self.assertEqual(fnames[1], "this_is_a_very_long_nam_1.wav")
        self.assertEqual(fnames[2], "this_is_a_very_long_nam_2.wav")

    def test_extreme_suffix(self):
        """Test logic with longer suffixes (e.g. _10)."""
        long_name = "test_limit"
        msgs = [
            Message(name=long_name, text=f"Msg {i}", voice_name="Voice1")
            for i in range(12)
        ]

        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        self.assertEqual(msgs[11].voice_filename, "test_limit_11.wav")

        vlong = "aaaaaaaaaaaaaaaaaaaaaaaaa"
        msgs = [
            Message(name=vlong, text=f"Msg {i}", voice_name="Voice1")
            for i in range(12)
        ]

        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        self.assertEqual(msgs[0].voice_filename, "a" * 25 + ".wav")
        self.assertEqual(msgs[1].voice_filename, "a" * 23 + "_1.wav")
        self.assertEqual(msgs[10].voice_filename, "a" * 22 + "_10.wav")

        for fn in [m.voice_filename for m in msgs]:
            self.assertIsNotNone(fn)
            assert fn is not None
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")


# ---------------------------------------------------------------------------
# Nebula pattern optionality tests
# ---------------------------------------------------------------------------

_MINIMAL_NEBULA_FSIF_TEMPLATE = """\
fsif_version: "4.0"
mission_info:
  name: "Nebula Pattern Test"
environment:
  ambient_light_level: [5, 5, 5]
  background_bitmaps: []
  nebula:
    enabled: true
    {extra_fields}
player_setup:
  start_ship: "Alpha 1"
entities:
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
mission_flow: {{}}
"""


class NebulaPatternTesting(unittest.TestCase):
    """Tests for the optional nebula.pattern field.

    Authoring `nebula.enabled: true` without a `pattern` must succeed.
    The FS2 writer should emit `+Neb2: ` (empty value) in that case.
    Providing an explicit pattern must still emit the pattern token.
    """

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _write_and_load(self, extra_fields: str):
        fsif_text = _MINIMAL_NEBULA_FSIF_TEMPLATE.format(extra_fields=extra_fields)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nebula_test.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def _write_and_load_disabled(self, extra_fields: str):
        """Variant that loads a mission where nebula.enabled is false."""
        fsif_text = _MINIMAL_NEBULA_FSIF_TEMPLATE.format(extra_fields=extra_fields).replace(
            "enabled: true", "enabled: false"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nebula_disabled_test.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def _write_fs2(self, mission: Mission) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            return out.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Loading tests
    # ------------------------------------------------------------------

    def test_load_succeeds_without_pattern(self):
        """enabled: true with no pattern must load without error."""
        mission = self._write_and_load("sensor_range: 2000.0")
        self.assertIsNone(mission.environment.nebula.pattern)
        self.assertTrue(mission.environment.nebula.enabled)

    def test_load_succeeds_with_explicit_pattern(self):
        """enabled: true with an explicit pattern must load and preserve it."""
        mission = self._write_and_load('pattern: "nbackblue1"')
        self.assertEqual(mission.environment.nebula.pattern, "nbackblue1")

    def test_fullneb_flag_injected_without_pattern(self):
        """The fullneb flag must be auto-injected even when pattern is omitted."""
        mission = self._write_and_load("sensor_range: 2000.0")
        flags_lower = [f.strip().lower() for f in mission.mission_info.flags]
        self.assertIn("fullneb", flags_lower)

    # ------------------------------------------------------------------
    # Writer emission tests
    # ------------------------------------------------------------------

    def test_writer_emits_empty_neb2_without_pattern(self):
        """Writer must emit '+Neb2: ' (with empty value) when pattern is None."""
        mission = self._write_and_load("sensor_range: 2000.0")
        content = self._write_fs2(mission)
        self.assertIn("+Neb2: ", content,
                      "Expected '+Neb2: ' (empty value) in fs2 output when no pattern authored")

    def test_writer_emits_pattern_token_when_provided(self):
        """Writer must emit '+Neb2: nbackblue1' when pattern is explicitly set."""
        mission = self._write_and_load('pattern: "nbackblue1"')
        content = self._write_fs2(mission)
        self.assertIn("+Neb2: nbackblue1", content)

    def test_writer_emits_poofs_list_without_pattern(self):
        """cloud_sprites should still produce +Neb2 Poofs List even if pattern is absent."""
        mission = self._write_and_load('cloud_sprites: ["PoofPurp01", "PoofPurp02"]')
        content = self._write_fs2(mission)
        self.assertIn("+Neb2 Poofs List:", content)
        self.assertIn('"PoofPurp01"', content)

    def test_writer_neb2_absent_when_nebula_disabled(self):
        """When nebula.enabled is false, +Neb2 must not appear in the output."""
        fsif_text = """\
fsif_version: "4.0"
mission_info:
  name: "No Nebula"
environment:
  ambient_light_level: [0, 0, 0]
  nebula:
    enabled: false
player_setup:
  start_ship: "Alpha 1"
entities:
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
mission_flow: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "no_nebula.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(path))
        content = self._write_fs2(mission)
        self.assertNotIn("+Neb2", content)

    # ------------------------------------------------------------------
    # Validator tests
    # ------------------------------------------------------------------

    def test_validator_passes_enabled_nebula_without_pattern(self):
        """Validator must accept enabled nebula with no pattern authored."""
        mission = self._write_and_load("sensor_range: 2000.0")
        validator = Validator(mission, _repo_root)
        self.assertTrue(validator.validate(), validator.errors)

    def test_validator_rejects_invalid_explicit_pattern(self):
        """An unrecognised pattern token must still fail validation."""
        mission = self._write_and_load('pattern: "NOT_A_REAL_PATTERN"')
        validator = Validator(mission, _repo_root)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("nebula pattern" in e.lower() for e in validator.errors),
            f"Expected pattern validation error, got: {validator.errors}",
        )

    # ------------------------------------------------------------------
    # Storm default tests
    # ------------------------------------------------------------------

    def test_storm_default_is_none_when_omitted(self):
        """Omitting storm in a full-nebula mission must default to 'none'."""
        mission = self._write_and_load("sensor_range: 2000.0")
        self.assertEqual(
            mission.environment.nebula.storm,
            "none",
            "Expected default storm to be 'none' when not authored",
        )

    def test_writer_emits_storm_none_by_default(self):
        """Writer must emit '+Storm: none' when storm is not explicitly set."""
        mission = self._write_and_load("sensor_range: 2000.0")
        content = self._write_fs2(mission)
        self.assertIn("+Storm: none", content,
                      "Expected '+Storm: none' in fs2 output when storm not authored")

    def test_explicit_storm_value_is_preserved(self):
        """An explicitly authored storm token must be preserved and emitted verbatim."""
        mission = self._write_and_load('storm: "s_medium"')
        self.assertEqual(mission.environment.nebula.storm, "s_medium")
        content = self._write_fs2(mission)
        self.assertIn("+Storm: s_medium", content,
                      "Expected '+Storm: s_medium' in fs2 output when storm: s_medium is authored")

    def test_validator_rejects_invalid_storm_token(self):
        """An unrecognised storm token must fail validation with a clear error message."""
        mission = self._write_and_load('storm: "s_heavy"')
        validator = Validator(mission, _repo_root)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("storm" in e.lower() and "s_heavy" in e for e in validator.errors),
            f"Expected invalid storm token error mentioning 's_heavy', got: {validator.errors}",
        )

    def test_validator_accepts_all_valid_storm_tokens(self):
        """Every canonical storm token must pass validation."""
        for token in ("none", "s_standard", "s_medium", "s_active", "s_emp"):
            with self.subTest(storm=token):
                mission = self._write_and_load(f'storm: "{token}"')
                validator = Validator(mission, _repo_root)
                self.assertTrue(
                    validator.validate(),
                    f"Expected storm token '{token}' to pass validation, got errors: {validator.errors}",
                )

    def test_validator_rejects_invalid_storm_token_when_nebula_disabled(self):
        """An invalid storm token must be rejected even when nebula.enabled is false."""
        # nebula.enabled defaults to false; storm should still be validated for token fidelity
        mission = self._write_and_load_disabled('storm: "bogus_storm"')
        validator = Validator(mission, _repo_root)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("storm" in e.lower() for e in validator.errors),
            f"Expected storm validation error for disabled nebula, got: {validator.errors}",
        )


class SunAnglesTesting(unittest.TestCase):
    """Tests for the 2-element [pitch, heading] sun angles schema.

    Suns are rotationally symmetric sprites, so bank has no visible effect.
    FSIF therefore uses [pitch, heading] for suns and the writer hardcodes
    bank = 0.0 in the +Angles line it emits.  Background bitmaps still use
    the full 3-element [pitch, bank, heading] format.
    """

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    # ------------------------------------------------------------------
    # Sun model: valid / invalid element counts
    # ------------------------------------------------------------------

    def test_sun_accepts_two_element_angles(self):
        """Sun model must accept a valid [pitch, heading] list."""
        from data_models import Sun
        s = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        self.assertEqual(s.angles, [0.087266, 2.356194])

    def test_sun_rejects_three_element_angles(self):
        """Sun model must reject the old [pitch, bank, heading] 3-value format."""
        from data_models import Sun
        from pydantic import ValidationError
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 0.0, 2.356194]})

    def test_sun_rejects_one_element_angles(self):
        """Sun model must reject a single-element angles list."""
        from data_models import Sun
        from pydantic import ValidationError
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": [0.5]})

    def test_sun_rejects_none_angles(self):
        """Sun model must reject None for angles."""
        from data_models import Sun
        from pydantic import ValidationError
        with self.assertRaises((ValidationError, ValueError)):
            Sun.model_validate({"texture": "SunVega", "angles": None})

    # ------------------------------------------------------------------
    # BackgroundBitmap must remain 3-element
    # ------------------------------------------------------------------

    def test_background_bitmap_still_accepts_three_element_angles(self):
        """BackgroundBitmap model must continue to accept [pitch, bank, heading]."""
        from data_models import BackgroundBitmap
        b = BackgroundBitmap.model_validate(
            {"texture": "neb02", "angles": [0.0, 2.321286, 0.0]}
        )
        self.assertEqual(len(b.angles), 3)

    def test_background_bitmap_rejects_two_element_angles(self):
        """BackgroundBitmap model must reject a 2-element angles list."""
        from data_models import BackgroundBitmap
        from pydantic import ValidationError
        with self.assertRaises((ValidationError, ValueError)):
            BackgroundBitmap.model_validate(
                {"texture": "neb02", "angles": [0.0, 2.321286]}
            )

    # ------------------------------------------------------------------
    # FS2 writer emission: bank must be hardcoded to 0.0
    # ------------------------------------------------------------------

    def test_writer_emits_hardcoded_bank_zero_for_sun(self):
        """FS2 writer must emit '+Angles: <pitch> 0.000000 <heading>' for suns."""
        from data_models import Sun, Environment as Env, MissionInfo, PlayerSetup, Ship, Weapons
        # Build a mission with one sun
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        mission = Mission(
            mission_info=MissionInfo(name="Sun Emit Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Env(ambient_light_level=[0, 0, 0], suns=[sun]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )

        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            content = out.read_text(encoding="utf-8")

        # The expected line contains pitch, hardcoded bank=0, and heading
        self.assertIn("+Angles: 0.087266 0.000000 2.356194", content,
                      "Expected sun +Angles line with hardcoded bank=0.000000")

    def test_writer_background_bitmap_still_emits_authored_bank(self):
        """FS2 writer must still emit the authored bank value for background bitmaps."""
        from data_models import BackgroundBitmap, Environment as Env, MissionInfo, PlayerSetup, Ship, Weapons
        bm = BackgroundBitmap.model_validate(
            {"texture": "neb02", "angles": [0.4, 1.2, 0.3], "scale": 1.0}
        )
        mission = Mission(
            mission_info=MissionInfo(name="Bitmap Emit Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Env(ambient_light_level=[0, 0, 0], background_bitmaps=[bm]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )

        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            content = out.read_text(encoding="utf-8")

        # pitch=0.4, bank=1.2, heading=0.3 — bank must be the authored value
        self.assertIn("+Angles: 0.400000 1.200000 0.300000", content,
                      "Expected background bitmap +Angles to include authored bank value")

    # ------------------------------------------------------------------
    # Validator: direct-front sun warning [0, 0]
    # ------------------------------------------------------------------

    def test_validator_warns_for_sun_at_zero_zero(self):
        """Validator must warn when a sun has angles [0, 0] (directly in front)."""
        from data_models import Sun, Environment as Env
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.0, 0.0]})
        mission = Mission(
            mission_info=MissionInfo(name="Sun Warning Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Env(ambient_light_level=[0, 0, 0], suns=[sun]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )
        validator = Validator(mission, _repo_root)
        # Validation may still pass (warning, not error), but warning must be present
        validator.validate()
        self.assertTrue(
            any("angles [0, 0]" in w or "[0, 0]" in w for w in validator.warnings),
            f"Expected sun direct-front warning mentioning '[0, 0]', got: {validator.warnings}",
        )

    def test_validator_no_warning_for_sun_at_nonzero_angles(self):
        """Validator must not warn when sun angles are non-zero."""
        from data_models import Sun, Environment as Env
        sun = Sun.model_validate({"texture": "SunVega", "angles": [0.087266, 2.356194]})
        mission = Mission(
            mission_info=MissionInfo(name="Sun OK Test"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Env(ambient_light_level=[0, 0, 0], suns=[sun]),
            ships=[
                Ship.model_validate({
                    "name": "Player Ship",
                    "class": "GTF Ulysses",
                    "team": "Friendly",
                    "position": [0, 0, 0],
                    "arrival_cue": "( true )",
                    "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
                })
            ],
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertFalse(
            any("[0, 0]" in w for w in validator.warnings),
            f"Expected no sun direct-front warning for non-zero angles, got: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # End-to-end: FSIF round-trip through loader and writer
    # ------------------------------------------------------------------

    def test_fsif_sun_two_angle_roundtrip(self):
        """FSIF with 2-value sun angles must load correctly and produce valid FS2."""
        fsif_text = """\
fsif_version: "4.0"
mission_info:
  name: "Sun Roundtrip"
environment:
  ambient_light_level: [0, 0, 0]
  suns:
    - texture: SunVega
      angles: [0.087266, 2.356194]
      scale: 1.5
  background_bitmaps:
    - texture: neb02
      angles: [0.0, 2.321286, 0.0]
      scale: 1.0
    - texture: neb11
      angles: [0.4, 0.6, 0.1]
      scale: 1.0
    - texture: neb12
      angles: [0.8, 1.2, 0.5]
      scale: 1.0
player_setup:
  start_ship: "Alpha 1"
entities:
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
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
mission_flow: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "sun_rt.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            mission = load_mission_from_fsif(str(fsif_path))

            self.assertEqual(len(mission.environment.suns), 1)
            self.assertEqual(len(mission.environment.suns[0].angles), 2,
                             "Expected Sun.angles to have exactly 2 elements after loading")

            out = Path(tmpdir) / "sun_rt.fs2"
            FS2Writer(mission, str(out)).write_mission()
            content = out.read_text(encoding="utf-8")

        # Check bank is hardcoded to 0 in FS2 output
        self.assertIn("+Angles: 0.087266 0.000000 2.356194", content,
                      "Expected sun +Angles with bank=0.000000 in FS2 output")

    def test_fsif_three_value_sun_angles_rejected(self):
        """FSIF with old 3-value sun angles must be rejected by the loader."""
        fsif_text = """\
fsif_version: "4.0"
mission_info:
  name: "Bad Sun"
environment:
  ambient_light_level: [0, 0, 0]
  suns:
    - texture: SunVega
      angles: [0.087266, 0.000000, 2.356194]
player_setup:
  start_ship: "Alpha 1"
entities:
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
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
mission_flow: {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fsif_path = Path(tmpdir) / "bad_sun.fsif"
            fsif_path.write_text(fsif_text, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_mission_from_fsif(str(fsif_path))


class DemoConversionTesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def test_demo_missions_conversion(self):
        demo_missions_dir = _repo_root / "missions" / "Demo_missions"
        self.assertTrue(demo_missions_dir.exists(), f"Demo missions directory not found: {demo_missions_dir}")
        
        fsif_files = list(demo_missions_dir.glob("*.fsif"))
        self.assertTrue(len(fsif_files) > 0, "No demo missions found to test.")
        
        from fsif_to_fs2 import process_mission
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for fsif_path in fsif_files:
                output_path = Path(tmpdir) / (fsif_path.stem + ".fs2")
                success = process_mission(
                    str(fsif_path), 
                    str(output_path), 
                    tts_settings={'enabled': True, 'dry_run': True}
                )
                self.assertTrue(success, f"Failed to convert demo mission: {fsif_path.name}")
                self.assertTrue(output_path.exists(), f"Output file not generated for: {fsif_path.name}")

    def test_demo_campaigns_conversion(self):
        demo_campaigns_dir = _repo_root / "campaigns" / "Demo_campaigns"
        self.assertTrue(demo_campaigns_dir.exists(), f"Demo campaigns directory not found: {demo_campaigns_dir}")
        
        fcif_files = list(demo_campaigns_dir.glob("*.fcif"))
        self.assertTrue(len(fcif_files) > 0, "No demo campaigns found to test.")
        
        fcif_dir = _repo_root / "FCIF_to_FC2_Converter"
        if str(fcif_dir) not in sys.path:
            sys.path.insert(0, str(fcif_dir))
        from fcif_to_fc2 import process_campaign
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for fcif_path in fcif_files:
                output_path = Path(tmpdir) / (fcif_path.stem + ".fc2")
                success = process_campaign(str(fcif_path), str(output_path))
                self.assertTrue(success, f"Failed to convert demo campaign: {fcif_path.name}")
                self.assertTrue(output_path.exists(), f"Output file not generated for: {fcif_path.name}")


if __name__ == '__main__':
    unittest.main()
