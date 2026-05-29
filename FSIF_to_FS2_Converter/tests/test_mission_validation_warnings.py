"""Tests for mission-level validation warnings and ASCII enforcement.

Covers:
- ASCII-only validation passes for a clean mission.
- Non-ASCII characters in briefing text are rejected with a clear error.
- voice_style_instructions are excluded from ASCII validation.
- Objects placed more than 20 km apart trigger a scale-recommendation warning.
- ship arrival_distance and wing arrival_distance over 20 km trigger warnings.
- Distances/arrival distances at exactly 20 km do NOT warn.
- All-objects-on-XZ-plane (Y=0) triggers a 3D-design warning.
- Having at least one object with non-zero Y suppresses the 3D-design warning.
"""

import unittest
from data_models import (
    Briefing,
    BriefingStage,
    JumpNode,
    Ship,
    Weapons,
    Wing,
)
from _fsif_test_helpers import SilencedTestCase, make_valid_mission, make_validator


class MissionValidationWarningsTesting(SilencedTestCase):

    # ------------------------------------------------------------------
    # ASCII validation
    # ------------------------------------------------------------------

    def test_ascii_mission_passes_validation(self):
        mission = make_valid_mission()
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_non_ascii_briefing_text_is_rejected(self):
        mission = make_valid_mission()
        mission.briefing = Briefing(
            stages=[
                BriefingStage(text="Hold position \u2014 protect the convoy.")
            ]
        )
        validator = make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any(
                "briefing.stages[0].text" in error and "U+2014" in error
                for error in validator.errors
            ),
            validator.errors,
        )

    def test_voice_style_instructions_are_excluded_from_ascii_validation(self):
        mission = make_valid_mission()
        mission.briefing = Briefing(
            stages=[
                BriefingStage(
                    text="Hold position and protect the convoy.",
                    voice_style_instructions="Calm \u2014 authoritative",
                )
            ]
        )
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    # ------------------------------------------------------------------
    # Distance / scale warnings
    # ------------------------------------------------------------------

    def test_distance_over_20km_between_objects_warns(self):
        mission = make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="Far Node", position=[25000.0, 0.0, 0.0])
        ]
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: 1 object pair(s) exceed" in warning
                and "Far Node" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_arrival_distance_over_20km_warns_for_ship_and_wing(self):
        mission = make_valid_mission()
        mission.ships.append(
            Ship.model_validate(
                {
                    "name": "Escort 1",
                    "class": "GTC Fenris",
                    "team": "Friendly",
                    "position": [500.0, 0.0, 0.0],
                    "arrival_method": "In front of ship",
                    "arrival_anchor": "Alpha 1",
                    "arrival_distance": 25001,
                    "arrival_cue": "( true )",
                }
            )
        )
        beta_ship = Ship.model_validate(
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
        mission.ships.append(beta_ship)
        mission.wings.append(
            Wing(
                name="Beta",
                count=1,
                ships=[beta_ship],
                position=[1000.0, 0.0, 0.0],
                arrival_method="In front of ship",
                arrival_anchor="Alpha 1",
                arrival_distance=22000,
                arrival_cue="( true )",
            )
        )
        validator = make_validator(mission)
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
        mission = make_valid_mission()
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
                    "arrival_anchor": "Alpha 1",
                    "arrival_distance": 20000,
                    "arrival_cue": "( true )",
                }
            )
        )
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any("Mission scale recommendation:" in warning for warning in validator.warnings),
            validator.warnings,
        )

    # ------------------------------------------------------------------
    # 3D design warnings
    # ------------------------------------------------------------------

    def test_3d_mission_design_warns_when_all_objects_on_xz_plane(self):
        mission = make_valid_mission()
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "All objects are currently placed on the 2D XZ plane (Y=0)" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_3d_mission_design_does_not_warn_when_objects_spread_in_y(self):
        mission = make_valid_mission()
        mission.jump_nodes = [
            JumpNode(name="High Node", position=[0.0, 500.0, 0.0])
        ]
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "Mission design recommendation: All objects are placed on the 2D XZ plane (Y=0)" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )


if __name__ == "__main__":
    unittest.main()
