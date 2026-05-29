"""Tests for the stricter display_class validation on briefing icons.

Rules:
- Ship icon types MUST author display_class with a valid, non-NavBuoy ship class.
- Non-ship icon types MUST NOT author display_class (omit it entirely).

Covers:
- Fighter icon with a valid, non-NavBuoy display_class passes.
- Fighter icon without display_class authored fails.
- Fighter icon explicitly using 'Terran NavBuoy' fails.
- Fighter icon with a non-existent ship class fails.
- Capital Ship icon with GTD Orion passes.
- Waypoint icon without display_class passes.
- Jump Node icon without display_class passes.
- Waypoint icon with any display_class authored fails.
- Planet icon without display_class passes.
- Asteroid Field icon without display_class passes.
- Jump Node icon with a valid ship class still fails.
"""

import unittest

import briefing_icon_types as bit
from data_models import (
    Briefing,
    BriefingIcon,
    BriefingStage,
    Environment,
    Mission,
    MissionInfo,
    PlayerSetup,
    Ship,
    Weapons,
    Wing,
)
from validator import Validator
from _fsif_test_helpers import SilencedTestCase, make_valid_mission, REPO_ROOT


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, REPO_ROOT)


def _make_briefing_with_icon(icon_type: str, display_class=None, display_class_authored: bool = False) -> Briefing:
    """Wrap a single briefing icon in a stage and a Briefing."""
    type_id = bit.parse_icon_type(icon_type)
    icon = BriefingIcon(
        type_id=type_id,
        icon_type=icon_type,
        team="Friendly",
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


class BriefingIconDisplayClassValidation(SilencedTestCase):

    # -------------------------------------------------------------------------
    # Ship icon type tests
    # -------------------------------------------------------------------------

    def test_ship_icon_with_valid_display_class_passes(self):
        """Fighter icon with a valid, non-NavBuoy display_class should pass."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Fighter", display_class="GTF Ulysses", display_class_authored=True
        )
        validator = _make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_ship_icon_missing_display_class_fails(self):
        """Fighter icon without display_class authored must fail."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Fighter", display_class_authored=False
        )
        validator = _make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("is missing display_class" in e for e in validator.errors),
            validator.errors,
        )

    def test_ship_icon_with_navbuoy_display_class_fails(self):
        """Fighter icon explicitly using 'Terran NavBuoy' must fail."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Fighter", display_class="Terran NavBuoy", display_class_authored=True
        )
        validator = _make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("Terran NavBuoy" in e for e in validator.errors),
            validator.errors,
        )

    def test_ship_icon_with_invalid_ship_class_fails(self):
        """Fighter icon with a non-existent ship class must fail."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Fighter", display_class="GTF NonExistentShip", display_class_authored=True
        )
        validator = _make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("not a valid FSO ship class" in e for e in validator.errors),
            validator.errors,
        )

    def test_capital_ship_icon_with_valid_display_class_passes(self):
        """Capital Ship icon with GTD Orion should pass."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Capital Ship", display_class="GTD Orion", display_class_authored=True
        )
        validator = _make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    # -------------------------------------------------------------------------
    # Non-ship icon type tests
    # -------------------------------------------------------------------------

    def test_nonship_icon_without_display_class_passes(self):
        """Waypoint icon without display_class authored must pass."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Waypoint", display_class_authored=False
        )
        validator = _make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_jump_node_icon_without_display_class_passes(self):
        """Jump Node icon without display_class authored must pass."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Jump Node", display_class_authored=False
        )
        validator = _make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_nonship_icon_with_display_class_authored_fails(self):
        """Waypoint icon with any display_class authored must fail."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Waypoint", display_class="Terran NavBuoy", display_class_authored=True
        )
        validator = _make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("must not author display_class" in e for e in validator.errors),
            validator.errors,
        )

    def test_planet_icon_without_display_class_passes(self):
        """Planet icon without display_class authored must pass."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Planet", display_class_authored=False
        )
        validator = _make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_asteroid_field_icon_without_display_class_passes(self):
        """Asteroid Field icon without display_class authored must pass."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Asteroid Field", display_class_authored=False
        )
        validator = _make_validator(mission)
        self.assertTrue(validator.validate(), validator.errors)

    def test_nonship_icon_with_ship_class_authored_fails(self):
        """Jump Node icon with a valid ship class still fails (must omit display_class)."""
        mission = make_valid_mission()
        mission.briefing = _make_briefing_with_icon(
            "Jump Node", display_class="GTF Ulysses", display_class_authored=True
        )
        validator = _make_validator(mission)
        self.assertFalse(validator.validate())
        self.assertTrue(
            any("must not author display_class" in e for e in validator.errors),
            validator.errors,
        )


if __name__ == "__main__":
    unittest.main()
