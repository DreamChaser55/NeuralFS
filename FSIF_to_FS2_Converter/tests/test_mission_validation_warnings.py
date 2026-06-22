"""Tests for mission-level validation warnings and ASCII enforcement.

Covers:
- ASCII-only validation passes for a clean mission.
- Non-ASCII characters in briefing text are rejected with a clear error.
- voice_style_instructions are excluded from ASCII validation.
- Objects placed more than 20 km apart trigger a scale-recommendation warning.
- ship arrival_distance over 20 km triggers a warning; between 10 km and 20 km does NOT.
- wing arrival_distance over 10 km triggers a warning (tighter threshold than ships).
- wing arrival_distance at exactly 10 km does NOT warn; at 10,001 m it does.
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

    def test_wing_arrival_distance_over_10km_warns(self):
        """Wing arrival_distance between 10 km and 20 km triggers the wing-specific warning."""
        mission = make_valid_mission()
        wing_ship = Ship.model_validate(
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
        mission.ships.append(wing_ship)
        mission.wings.append(
            Wing(
                name="Beta",
                count=1,
                ships=[wing_ship],
                position=[1000.0, 0.0, 0.0],
                arrival_method="In front of ship",
                arrival_anchor="Alpha 1",
                arrival_distance=15000,
                arrival_cue="( true )",
            )
        )
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: Wing 'Beta' arrival_distance 15000 m" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_ship_arrival_distance_between_10km_and_20km_does_not_warn(self):
        """Ship arrival_distance between 10 km and 20 km does NOT warn (ship threshold stays 20 km)."""
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
                    "arrival_distance": 15000,
                    "arrival_cue": "( true )",
                }
            )
        )
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "Mission scale recommendation: Ship 'Escort 1' arrival_distance 15000 m" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_wing_arrival_distance_at_exactly_10km_does_not_warn(self):
        """Wing arrival_distance at exactly 10,000 m is at the threshold and must NOT warn."""
        mission = make_valid_mission()
        wing_ship = Ship.model_validate(
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
        mission.ships.append(wing_ship)
        mission.wings.append(
            Wing(
                name="Beta",
                count=1,
                ships=[wing_ship],
                position=[1000.0, 0.0, 0.0],
                arrival_method="In front of ship",
                arrival_anchor="Alpha 1",
                arrival_distance=10000,
                arrival_cue="( true )",
            )
        )
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "Wing 'Beta' arrival_distance" in warning
                for warning in validator.warnings
            ),
            validator.warnings,
        )

    def test_wing_arrival_distance_above_10km_warns_at_boundary(self):
        """Wing arrival_distance at 10,001 m (just above 10 km) triggers the warning."""
        mission = make_valid_mission()
        wing_ship = Ship.model_validate(
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
        mission.ships.append(wing_ship)
        mission.wings.append(
            Wing(
                name="Beta",
                count=1,
                ships=[wing_ship],
                position=[1000.0, 0.0, 0.0],
                arrival_method="In front of ship",
                arrival_anchor="Alpha 1",
                arrival_distance=10001,
                arrival_cue="( true )",
            )
        )
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Mission scale recommendation: Wing 'Beta' arrival_distance 10001 m" in warning
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


class OrientationIgnoredForNonHyperspaceWarningTests(SilencedTestCase):
    """Tests for the advisory warning that fires when a ship/wing has a
    deliberate orientation but uses a non-Hyperspace arrival method."""

    # Non-identity orientation matrix (facing +X direction).
    _NON_IDENTITY = [0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0]
    # Identity orientation (default; should NOT trigger the warning).
    _IDENTITY = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

    # ------------------------------------------------------------------
    # Ship: positive cases (warning should fire)
    # ------------------------------------------------------------------

    def test_ship_nonhyperspace_arrival_with_nontrivial_orientation_matrix_warns(self):
        """Standalone ship with non-Hyperspace arrival and non-identity orientation warns."""
        mission = make_valid_mission()
        ship = Ship.model_validate(
            {
                "name": "SC Cain 1",
                "class": "SC Cain",
                "team": "Hostile",
                "position": [2000.0, 0.0, 3000.0],
                "orientation": self._NON_IDENTITY,
                "arrival_method": "In front of ship",
                "arrival_anchor": "Alpha 1",
                "arrival_distance": 1500,
                "arrival_cue": "( true )",
            }
        )
        mission.ships.append(ship)
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "SC Cain 1" in w and "orientation" in w and "In front of ship" in w
                for w in validator.warnings
            ),
            validator.warnings,
        )

    def test_ship_nonhyperspace_arrival_with_orientation_target_warns(self):
        """Standalone ship with non-Hyperspace arrival and orientation_target set warns."""
        mission = make_valid_mission()
        ship = Ship.model_validate(
            {
                "name": "SC Cain 2",
                "class": "SC Cain",
                "team": "Hostile",
                "position": [2000.0, 0.0, 3000.0],
                "arrival_method": "Near Ship",
                "arrival_anchor": "Alpha 1",
                "arrival_distance": 500,
                "arrival_cue": "( true )",
            }
        )
        # Simulate the loader having resolved an orientation target name.
        ship.orientation_target = "Alpha 1"
        mission.ships.append(ship)
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "SC Cain 2" in w and "orientation" in w and "Near Ship" in w
                for w in validator.warnings
            ),
            validator.warnings,
        )

    # ------------------------------------------------------------------
    # Wing: positive case (warning should fire)
    # ------------------------------------------------------------------

    def test_wing_nonhyperspace_arrival_with_nontrivial_orientation_warns(self):
        """Wing with non-Hyperspace arrival and non-identity orientation warns."""
        mission = make_valid_mission()
        wing_ship = Ship.model_validate(
            {
                "name": "Rama 1",
                "class": "SF Scorpion",
                "team": "Hostile",
                "position": [500.0, 0.0, 1500.0],
                "arrival_cue": "( true )",
                "weapons": {"primary": ["Shivan Light Laser", "Shivan Light Laser"], "secondary": ["MX-50#Shivan"]},
            }
        )
        hostile_wing = Wing(
            name="Rama",
            count=1,
            ships=[wing_ship],
            position=[500.0, 0.0, 1500.0],
            orientation=self._NON_IDENTITY,
            arrival_method="Above ship",
            arrival_anchor="Alpha 1",
            arrival_distance=1800,
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        mission.ships.append(wing_ship)
        mission.wings.append(hostile_wing)
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertTrue(
            any(
                "Rama" in w and "orientation" in w and "Above ship" in w
                for w in validator.warnings
            ),
            validator.warnings,
        )

    # ------------------------------------------------------------------
    # Negative cases (warning should NOT fire)
    # ------------------------------------------------------------------

    def test_ship_hyperspace_arrival_with_nontrivial_orientation_does_not_warn(self):
        """Ship with Hyperspace arrival and non-identity orientation must NOT warn."""
        mission = make_valid_mission()
        ship = Ship.model_validate(
            {
                "name": "SC Cain 3",
                "class": "SC Cain",
                "team": "Hostile",
                "position": [2000.0, 0.0, 3000.0],
                "orientation": self._NON_IDENTITY,
                "arrival_method": "Hyperspace",
                "arrival_cue": "( true )",
            }
        )
        mission.ships.append(ship)
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "SC Cain 3" in w and "orientation" in w and "arrival_method" in w
                for w in validator.warnings
            ),
            validator.warnings,
        )

    def test_ship_nonhyperspace_arrival_with_identity_orientation_does_not_warn(self):
        """Ship with non-Hyperspace arrival but identity orientation must NOT warn."""
        mission = make_valid_mission()
        ship = Ship.model_validate(
            {
                "name": "SC Cain 4",
                "class": "SC Cain",
                "team": "Hostile",
                "position": [2000.0, 0.0, 3000.0],
                "orientation": self._IDENTITY,
                "arrival_method": "In front of ship",
                "arrival_anchor": "Alpha 1",
                "arrival_distance": 1500,
                "arrival_cue": "( true )",
            }
        )
        mission.ships.append(ship)
        validator = make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)
        self.assertFalse(
            any(
                "SC Cain 4" in w and "orientation" in w and "arrival_method" in w
                for w in validator.warnings
            ),
            validator.warnings,
        )


if __name__ == "__main__":
    unittest.main()
