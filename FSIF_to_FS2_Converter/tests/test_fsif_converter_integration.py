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
    CommandBriefing,
    CommandBriefingStage,
    Debriefing,
    DebriefingStage,
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

        self.assertIn("accepts FSIF version '1.0' only", str(ctx.exception))

    def test_old_version_fsif_fails_with_version_error_not_pydantic_wall(self):
        """
        Regression test: a FSIF file with an old version number AND many
        renamed/legacy field names must fail with a clean unsupported-version
        error, NOT with a wall of Pydantic 'Extra inputs are not permitted'
        errors caused by incompatible field names.

        This verifies that _validate_version() runs before _validate_fsif_schema()
        in MissionLoader.load().
        """
        # Combine old fsif_version with several legacy FSIF field names
        # that would each generate a Pydantic error if schema validation ran first.
        fsif_text = """fsif_version: "0.5"

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
        self.assertIn("Unsupported fsif_version '0.5'", error_msg)
        self.assertIn("accepts FSIF version '1.0' only", error_msg)

        # Must NOT contain Pydantic schema error markers — version check must
        # have fired before the schema validator had a chance to run.
        self.assertNotIn("FSIF document validation error", error_msg,
                         "Schema validation ran before version check — Pydantic error wall was not suppressed.")
        self.assertNotIn("Extra inputs are not permitted", error_msg,
                         "Schema validation ran before version check — legacy field names triggered Pydantic errors.")

    def test_loader_rejects_packed_ambient_light_in_fsif_27(self):
        fsif_text = """fsif_version: \"1.0\"

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
fsif_version: "1.0"
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
        fsif_text = """fsif_version: "1.0"

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
fsif_version: "1.0"
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
fsif_version: "1.0"
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
fsif_version: "1.0"
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
fsif_version: "1.0"
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


class BriefingIconDisplayClassValidation(unittest.TestCase):
    """Tests for the stricter display_class validation on briefing icons.

    Rules:
    - Ship icon types MUST author display_class with a valid, non-NavBuoy ship class.
    - Non-ship icon types MUST NOT author display_class (omit it entirely).
    """

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

    def _make_briefing_with_icon(self, icon_type: str, display_class=None, display_class_authored: bool = False):
        """Helper: wrap a single briefing icon in a stage and a Briefing."""
        from data_models import BriefingIcon, BriefingStage, Briefing
        import briefing_icon_types as bit
        type_id = bit.parse_icon_type(icon_type)
        icon = BriefingIcon(
            type_id=type_id,
            icon_type=icon_type,
            team="Friendly",
            # Pass 2-element [x, z] — the validator normalizes to [x, 0, z] internally.
            map_position=[0, 0],
            display_class=display_class if display_class is not None else "Terran NavBuoy",
            display_class_authored=display_class_authored,
        )
        stage = BriefingStage(
            text="Test briefing stage.",
            icons=[icon],
            camera_pos=[0.0, 2000.0, 0.0],
            camera_orient=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0],
        )
        return Briefing(stages=[stage])

    # -------------------------------------------------------------------------
    # Ship icon type tests
    # -------------------------------------------------------------------------

    def test_ship_icon_with_valid_display_class_passes(self):
        """Fighter icon with a valid, non-NavBuoy display_class should pass."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Fighter", display_class="GTF Ulysses", display_class_authored=True
        )
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_ship_icon_missing_display_class_fails(self):
        """Fighter icon without display_class authored must fail."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Fighter", display_class_authored=False
        )
        validator = self.make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("is missing display_class" in e for e in validator.errors),
            validator.errors,
        )

    def test_ship_icon_with_navbuoy_display_class_fails(self):
        """Fighter icon explicitly using 'Terran NavBuoy' must fail."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Fighter", display_class="Terran NavBuoy", display_class_authored=True
        )
        validator = self.make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("Terran NavBuoy" in e for e in validator.errors),
            validator.errors,
        )

    def test_ship_icon_with_invalid_ship_class_fails(self):
        """Fighter icon with a non-existent ship class must fail."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Fighter", display_class="GTF NonExistentShip", display_class_authored=True
        )
        validator = self.make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("not a valid FSO ship class" in e for e in validator.errors),
            validator.errors,
        )

    def test_capital_ship_icon_with_valid_display_class_passes(self):
        """Capital Ship icon with GTD Orion should pass."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Capital Ship", display_class="GTD Orion", display_class_authored=True
        )
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    # -------------------------------------------------------------------------
    # Non-ship icon type tests
    # -------------------------------------------------------------------------

    def test_nonship_icon_without_display_class_passes(self):
        """Waypoint icon without display_class authored must pass."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Waypoint", display_class_authored=False
        )
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_jump_node_icon_without_display_class_passes(self):
        """Jump Node icon without display_class authored must pass."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Jump Node", display_class_authored=False
        )
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_nonship_icon_with_display_class_authored_fails(self):
        """Waypoint icon with any display_class authored must fail."""
        mission = self.make_valid_mission()
        # Authoring display_class on a Waypoint is forbidden, even if the value is the default.
        mission.briefing = self._make_briefing_with_icon(
            "Waypoint", display_class="Terran NavBuoy", display_class_authored=True
        )
        validator = self.make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("must not author display_class" in e for e in validator.errors),
            validator.errors,
        )

    def test_planet_icon_without_display_class_passes(self):
        """Planet icon without display_class authored must pass."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Planet", display_class_authored=False
        )
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_asteroid_field_icon_without_display_class_passes(self):
        """Asteroid Field icon without display_class authored must pass."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Asteroid Field", display_class_authored=False
        )
        validator = self.make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_nonship_icon_with_ship_class_authored_fails(self):
        """Jump Node icon with a valid ship class still fails (must omit display_class)."""
        mission = self.make_valid_mission()
        mission.briefing = self._make_briefing_with_icon(
            "Jump Node", display_class="GTF Ulysses", display_class_authored=True
        )
        validator = self.make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("must not author display_class" in e for e in validator.errors),
            validator.errors,
        )


# ---------------------------------------------------------------------------
# Wing-member arrival_cue regression tests
#
# Regression guard for the bug introduced by commit 3efae8d where the runtime
# Ship.arrival_cue default was changed from '( false )' to '( true )'.  That
# change caused wing-member objects in #Objects to emit $Arrival Cue: ( true ),
# allowing them to spawn independently of the wing arrival mechanism and
# triggering player-wing/loadout errors in FSO.
#
# The correct behaviour:
#   - Expanded wing-member Ship objects always have arrival_cue '( false )'.
#   - The Wing object's own arrival_cue controls when the wing actually arrives.
#   - Standalone ships that omit arrival_cue still default to '( true )'.
# ---------------------------------------------------------------------------

_MINIMAL_FSIF_WING_ARRIVAL_CUE = """\
fsif_version: "1.0"
mission_info:
  name: "Wing Arrival Cue Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - class: "GTF Ulysses"
      count: 4
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 4
      position: [0, 0, 0]
mission_flow: {}
"""

_MINIMAL_FSIF_WING_CONDITIONAL_CUE = """\
fsif_version: "1.0"
mission_info:
  name: "Wing Conditional Arrival Cue Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - class: "GTF Ulysses"
      count: 4
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 4
      position: [0, 0, 0]
    - name: "Rama"
      template: "alpha_t"
      count: 2
      position: [1000, 0, 1000]
      arrival_cue: |
        ( has-time-elapsed 30 )
mission_flow: {}
"""

_MINIMAL_FSIF_STANDALONE_SHIP = """\
fsif_version: "1.0"
mission_info:
  name: "Standalone Ship Arrival Cue Test"
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
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
    - name: "GTFr Poseidon 1"
      class: "GTFr Poseidon"
      team: "Friendly"
      position: [500, 0, 500]
mission_flow: {}
"""


class WingMemberArrivalCueRegression(unittest.TestCase):
    """Regression tests for wing-member arrival_cue behaviour.

    Guard against the bug introduced in commit 3efae8d that caused expanded
    wing-member Ship objects to carry arrival_cue '( true )' instead of
    '( false )', causing FSO wing/loadout errors.
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
    # Helpers
    # ------------------------------------------------------------------

    def _load(self, fsif_text: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.fsif"
            path.write_text(fsif_text, encoding="utf-8")
            return load_mission_from_fsif(str(path))

    def _write_fs2(self, mission: Mission) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.fs2"
            FS2Writer(mission, str(out)).write_mission()
            return out.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Wing member ship objects must have arrival_cue '( false )'
    # ------------------------------------------------------------------

    def test_wing_member_ships_have_false_arrival_cue_after_load(self):
        """All expanded wing-member Ship objects must have arrival_cue '( false )'."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        self.assertEqual(len(mission.wings), 1)
        wing = mission.wings[0]
        self.assertEqual(len(wing.ships), 4)
        for ship in wing.ships:
            self.assertEqual(
                ship.arrival_cue, '( false )',
                f"Wing member '{ship.name}' has arrival_cue '{ship.arrival_cue}'; expected '( false )'"
            )

    def test_wing_level_arrival_cue_defaults_to_true(self):
        """Wing object arrival_cue should default to '( true )' when not authored."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        wing = mission.wings[0]
        self.assertEqual(
            wing.arrival_cue, '( true )',
            f"Wing arrival_cue '{wing.arrival_cue}'; expected '( true )'"
        )

    def test_conditional_wing_arrival_cue_is_preserved(self):
        """Authored conditional wing arrival_cue must be preserved unchanged."""
        mission = self._load(_MINIMAL_FSIF_WING_CONDITIONAL_CUE)
        rama_wing = next(w for w in mission.wings if w.name == "Rama")
        self.assertIn(
            "has-time-elapsed",
            rama_wing.arrival_cue,
            f"Conditional wing cue not preserved: '{rama_wing.arrival_cue}'"
        )

    def test_conditional_wing_member_ships_still_have_false_cue(self):
        """Members of a wing with a conditional arrival_cue must still have '( false )'."""
        mission = self._load(_MINIMAL_FSIF_WING_CONDITIONAL_CUE)
        rama_wing = next(w for w in mission.wings if w.name == "Rama")
        for ship in rama_wing.ships:
            self.assertEqual(
                ship.arrival_cue, '( false )',
                f"Wing member '{ship.name}' has arrival_cue '{ship.arrival_cue}'; expected '( false )'"
            )

    # ------------------------------------------------------------------
    # FS2 output: #Objects entries must emit '( false )' for wing members
    # ------------------------------------------------------------------

    def test_fs2_objects_section_emits_false_for_wing_members(self):
        """The emitted FS2 file must contain '$Arrival Cue: ( false )' for every wing member."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        content = self._write_fs2(mission)

        # Locate the #Objects and #Wings boundary so we only check #Objects.
        objects_start = content.find("#Objects")
        wings_start = content.find("#Wings")
        self.assertGreater(objects_start, -1, "#Objects section not found")
        self.assertGreater(wings_start, -1, "#Wings section not found")

        objects_section = content[objects_start:wings_start]

        # Every ship entry in #Objects (Alpha 1..4) must have '( false )' cue.
        for i in range(1, 5):
            name_marker = f"$Name: Alpha {i}"
            self.assertIn(
                name_marker, objects_section,
                f"'{name_marker}' not found in #Objects section"
            )

        # Count occurrences of '( true )' vs '( false )' in #Objects only.
        true_count = objects_section.count("$Arrival Cue: ( true )")
        false_count = objects_section.count("$Arrival Cue: ( false )")

        self.assertEqual(
            true_count, 0,
            f"#Objects section contains {true_count} '$Arrival Cue: ( true )' entries; expected 0"
        )
        self.assertEqual(
            false_count, 4,
            f"#Objects section contains {false_count} '$Arrival Cue: ( false )' entries; expected 4"
        )

    def test_fs2_wings_section_emits_true_cue_for_wing(self):
        """The emitted FS2 file must contain '$Arrival Cue: ( true )' in the #Wings entry."""
        mission = self._load(_MINIMAL_FSIF_WING_ARRIVAL_CUE)
        content = self._write_fs2(mission)

        wings_start = content.find("#Wings")
        self.assertGreater(wings_start, -1, "#Wings section not found")

        wings_section = content[wings_start:]
        self.assertIn(
            "$Arrival Cue: ( true )",
            wings_section,
            "#Wings section does not contain '$Arrival Cue: ( true )' for the wing"
        )

    # ------------------------------------------------------------------
    # Standalone ship defaults must remain unaffected
    # ------------------------------------------------------------------

    def test_standalone_ship_omitting_arrival_cue_defaults_to_true(self):
        """A standalone ship that omits arrival_cue must default to '( true )'."""
        mission = self._load(_MINIMAL_FSIF_STANDALONE_SHIP)
        player_ship = next(s for s in mission.ships if s.name == "Player Ship")
        self.assertEqual(
            player_ship.arrival_cue, '( true )',
            f"Standalone player ship arrival_cue '{player_ship.arrival_cue}'; expected '( true )'"
        )

    def test_standalone_npc_ship_omitting_arrival_cue_defaults_to_true(self):
        """Any standalone ship omitting arrival_cue defaults to '( true )'."""
        mission = self._load(_MINIMAL_FSIF_STANDALONE_SHIP)
        npc = next(s for s in mission.ships if s.name == "GTFr Poseidon 1")
        self.assertEqual(
            npc.arrival_cue, '( true )',
            f"Standalone NPC ship arrival_cue '{npc.arrival_cue}'; expected '( true )'"
        )

    def test_fs2_objects_standalone_ship_emits_true_cue(self):
        """Standalone ships must still emit '$Arrival Cue: ( true )' in #Objects."""
        mission = self._load(_MINIMAL_FSIF_STANDALONE_SHIP)
        content = self._write_fs2(mission)

        objects_start = content.find("#Objects")
        wings_start = content.find("#Wings")
        if wings_start == -1:
            wings_start = len(content)
        objects_section = content[objects_start:wings_start]

        self.assertIn(
            "$Arrival Cue: ( true )",
            objects_section,
            "Standalone ship should emit '$Arrival Cue: ( true )' in #Objects"
        )


# ---------------------------------------------------------------------------
# Text styling validation tests
# ---------------------------------------------------------------------------


class BriefingTextStylingValidationTesting(unittest.TestCase):
    """Tests for validate_mission_has_briefing_text_styling().

    The validator should warn when at least one eligible text field exists in
    command briefing, mission briefing, or debriefing, but none of those texts
    contain a span-open or single-word color tag.

    Eligible texts with actual color tags must not trigger the warning.
    Placeholder-only texts ($callsign, $rank, $quote, $semicolon) must not
    count as styled and should still trigger the warning.
    Missions with no eligible text at all (empty stages) must not warn.
    """

    _WARNING_FRAGMENT = "No text styling color tags were found"

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _make_base_mission(self) -> Mission:
        """Minimal valid mission with no briefing/debriefing text."""
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

    def _has_styling_warning(self, validator: Validator) -> bool:
        return any(self._WARNING_FRAGMENT in w for w in validator.warnings)

    # ------------------------------------------------------------------
    # No eligible text: must not warn
    # ------------------------------------------------------------------

    def test_no_eligible_text_does_not_warn(self):
        """A mission with no briefing/debriefing text must not trigger the warning."""
        mission = self._make_base_mission()
        # All stage lists empty by default — no eligible text at all.
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertFalse(
            self._has_styling_warning(validator),
            f"Unexpected styling warning on mission with no eligible text: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # Eligible text with no color tags: must warn
    # ------------------------------------------------------------------

    def test_briefing_text_without_tags_warns(self):
        """Briefing text with no color tags must trigger the warning."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Escort the convoy to the jump node.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning for unstyled briefing text, got: {validator.warnings}",
        )

    def test_command_briefing_text_without_tags_warns(self):
        """Command briefing text with no color tags must trigger the warning."""
        mission = self._make_base_mission()
        mission.command_briefing = CommandBriefing(
            stages=[CommandBriefingStage(text="All wings, report to the rally point.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning for unstyled command briefing text, got: {validator.warnings}",
        )

    def test_debriefing_text_without_tags_warns(self):
        """Debriefing text with no color tags must trigger the warning."""
        mission = self._make_base_mission()
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="The mission was a success.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning for unstyled debriefing text, got: {validator.warnings}",
        )

    def test_multiple_eligible_contexts_none_styled_warns(self):
        """Multiple eligible contexts all without tags should still warn (once)."""
        mission = self._make_base_mission()
        mission.command_briefing = CommandBriefing(
            stages=[CommandBriefingStage(text="Orders have been issued.")]
        )
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Escort the convoy.")]
        )
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="Good work.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning when no eligible text is styled, got: {validator.warnings}",
        )
        # Warning should be emitted exactly once (mission-level, not per-stage).
        warning_count = sum(1 for w in validator.warnings if self._WARNING_FRAGMENT in w)
        self.assertEqual(
            warning_count, 1,
            f"Expected exactly 1 styling warning, got {warning_count}: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # Placeholders only: must still warn
    # ------------------------------------------------------------------

    def test_placeholder_only_text_still_warns(self):
        """Text with only $callsign and $rank but no color tags must still warn."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Excellent work, $rank $callsign.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning for placeholder-only briefing text, got: {validator.warnings}",
        )

    def test_close_tag_only_text_still_warns(self):
        """Text with only $} (orphan close tag, no open tag) must still warn."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Some text $} here.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning for close-tag-only text, got: {validator.warnings}",
        )

    def test_color_break_only_text_still_warns(self):
        """Text with only $| (color break) but no open color tag must still warn."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Text $| here.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertTrue(
            self._has_styling_warning(validator),
            f"Expected styling warning for color-break-only text, got: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # Color tags present: must NOT warn
    # ------------------------------------------------------------------

    def test_briefing_text_with_span_open_tag_does_not_warn(self):
        """Briefing text containing a span-open tag must not trigger the warning."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Protect the $f{ GTC Fenris $} convoy.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertFalse(
            self._has_styling_warning(validator),
            f"Unexpected styling warning for briefing text with '$f{{': {validator.warnings}",
        )

    def test_briefing_text_with_single_word_tag_does_not_warn(self):
        """Briefing text containing a single-word color tag must not trigger the warning."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Intercept $h Rama wing before it reaches the convoy.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertFalse(
            self._has_styling_warning(validator),
            f"Unexpected styling warning for briefing text with '$h': {validator.warnings}",
        )

    def test_command_briefing_with_tag_does_not_warn(self):
        """A color tag in command briefing is enough to suppress the warning."""
        mission = self._make_base_mission()
        mission.command_briefing = CommandBriefing(
            stages=[CommandBriefingStage(text="$f{ Alpha Wing $}, proceed to the objective.")]
        )
        # Add unstyled debriefing — the tag in command briefing should be enough.
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="Mission complete.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertFalse(
            self._has_styling_warning(validator),
            f"Unexpected styling warning when command briefing has a color tag: {validator.warnings}",
        )

    def test_debriefing_with_tag_does_not_warn(self):
        """A color tag in any debriefing stage is enough to suppress the warning."""
        mission = self._make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Escort the convoy.")]
        )
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="The $f{ GTC Dauntless $} survived.")]
        )
        validator = Validator(mission, _repo_root)
        validator.validate()
        self.assertFalse(
            self._has_styling_warning(validator),
            f"Unexpected styling warning when debriefing has a color tag: {validator.warnings}",
        )

    def test_various_color_letters_do_not_warn(self):
        """Spot-check several other canonical color letters as span-open tags."""
        for tag in ("$h{", "$y{", "$W{", "$R{", "$V{"):
            with self.subTest(tag=tag):
                mission = self._make_base_mission()
                mission.briefing = Briefing(
                    stages=[BriefingStage(text=f"Head to {tag} rally point $}}.")]
                )
                validator = Validator(mission, _repo_root)
                validator.validate()
                self.assertFalse(
                    self._has_styling_warning(validator),
                    f"Unexpected warning for tag '{tag}': {validator.warnings}",
                )

    def test_various_single_word_color_letters_do_not_warn(self):
        """Spot-check several canonical single-word color tags (followed by space)."""
        for tag in ("$h", "$y", "$W", "$R"):
            with self.subTest(tag=tag):
                mission = self._make_base_mission()
                mission.briefing = Briefing(
                    stages=[BriefingStage(text=f"Protect {tag} Convoy.")]
                )
                validator = Validator(mission, _repo_root)
                validator.validate()
                self.assertFalse(
                    self._has_styling_warning(validator),
                    f"Unexpected warning for single-word tag '{tag}': {validator.warnings}",
                )


if __name__ == '__main__':
    unittest.main()
