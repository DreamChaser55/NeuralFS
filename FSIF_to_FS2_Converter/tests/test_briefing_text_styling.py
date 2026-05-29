"""Tests for validate_mission_has_briefing_text_styling().

The validator should warn when at least one eligible text field exists in
command briefing, mission briefing, or debriefing, but none of those texts
contain a span-open or single-word color tag.

Eligible texts with actual color tags must not trigger the warning.
Placeholder-only texts ($callsign, $rank, $quote, $semicolon) must not
count as styled and should still trigger the warning.
Missions with no eligible text at all (empty stages) must not warn.

Covers:
- No eligible text at all: no warning.
- Unstyled briefing text triggers the warning.
- Unstyled command briefing text triggers the warning.
- Unstyled debriefing text triggers the warning.
- Multiple unstyled contexts emit exactly one warning.
- Text with only $callsign/$rank (no color tags) still warns.
- Text with only $} (orphan close tag) still warns.
- Text with only $| (color break, no open tag) still warns.
- Briefing text with a span-open tag ($f{) suppresses the warning.
- Briefing text with a single-word color tag ($h) suppresses the warning.
- A color tag in command briefing suppresses the warning even if debriefing is unstyled.
- A color tag in debriefing suppresses the warning even if briefing is unstyled.
- Spot-check several span-open and single-word color letter variants.
"""

import unittest

from data_models import (
    Briefing,
    BriefingStage,
    CommandBriefing,
    CommandBriefingStage,
    Debriefing,
    DebriefingStage,
    Environment,
    Mission,
    MissionInfo,
    PlayerSetup,
    Ship,
    Weapons,
)
from validator import Validator
from _fsif_test_helpers import SilencedTestCase, REPO_ROOT


_WARNING_FRAGMENT = "No text styling color tags were found"


def _make_base_mission() -> Mission:
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


def _has_styling_warning(validator: Validator) -> bool:
    return any(_WARNING_FRAGMENT in w for w in validator.warnings)


class BriefingTextStylingValidationTesting(SilencedTestCase):

    # ------------------------------------------------------------------
    # No eligible text: must not warn
    # ------------------------------------------------------------------

    def test_no_eligible_text_does_not_warn(self):
        """A mission with no briefing/debriefing text must not trigger the warning."""
        mission = _make_base_mission()
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertFalse(
            _has_styling_warning(validator),
            f"Unexpected styling warning on mission with no eligible text: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # Eligible text with no color tags: must warn
    # ------------------------------------------------------------------

    def test_briefing_text_without_tags_warns(self):
        """Briefing text with no color tags must trigger the warning."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Escort the convoy to the jump node.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning for unstyled briefing text, got: {validator.warnings}",
        )

    def test_command_briefing_text_without_tags_warns(self):
        """Command briefing text with no color tags must trigger the warning."""
        mission = _make_base_mission()
        mission.command_briefing = CommandBriefing(
            stages=[CommandBriefingStage(text="All wings, report to the rally point.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning for unstyled command briefing text, got: {validator.warnings}",
        )

    def test_debriefing_text_without_tags_warns(self):
        """Debriefing text with no color tags must trigger the warning."""
        mission = _make_base_mission()
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="The mission was a success.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning for unstyled debriefing text, got: {validator.warnings}",
        )

    def test_multiple_eligible_contexts_none_styled_warns(self):
        """Multiple eligible contexts all without tags should still warn (once)."""
        mission = _make_base_mission()
        mission.command_briefing = CommandBriefing(
            stages=[CommandBriefingStage(text="Orders have been issued.")]
        )
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Escort the convoy.")]
        )
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="Good work.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning when no eligible text is styled, got: {validator.warnings}",
        )
        warning_count = sum(1 for w in validator.warnings if _WARNING_FRAGMENT in w)
        self.assertEqual(
            warning_count, 1,
            f"Expected exactly 1 styling warning, got {warning_count}: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # Placeholders only: must still warn
    # ------------------------------------------------------------------

    def test_placeholder_only_text_still_warns(self):
        """Text with only $callsign and $rank but no color tags must still warn."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Excellent work, $rank $callsign.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning for placeholder-only briefing text, got: {validator.warnings}",
        )

    def test_close_tag_only_text_still_warns(self):
        """Text with only $} (orphan close tag, no open tag) must still warn."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Some text $} here.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning for close-tag-only text, got: {validator.warnings}",
        )

    def test_color_break_only_text_still_warns(self):
        """Text with only $| (color break) but no open color tag must still warn."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Text $| here.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertTrue(
            _has_styling_warning(validator),
            f"Expected styling warning for color-break-only text, got: {validator.warnings}",
        )

    # ------------------------------------------------------------------
    # Color tags present: must NOT warn
    # ------------------------------------------------------------------

    def test_briefing_text_with_span_open_tag_does_not_warn(self):
        """Briefing text containing a span-open tag must not trigger the warning."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Protect the $f{ GTC Fenris $} convoy.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertFalse(
            _has_styling_warning(validator),
            f"Unexpected styling warning for briefing text with '$f{{': {validator.warnings}",
        )

    def test_briefing_text_with_single_word_tag_does_not_warn(self):
        """Briefing text containing a single-word color tag must not trigger the warning."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Intercept $h Rama wing before it reaches the convoy.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertFalse(
            _has_styling_warning(validator),
            f"Unexpected styling warning for briefing text with '$h': {validator.warnings}",
        )

    def test_command_briefing_with_tag_does_not_warn(self):
        """A color tag in command briefing is enough to suppress the warning."""
        mission = _make_base_mission()
        mission.command_briefing = CommandBriefing(
            stages=[CommandBriefingStage(text="$f{ Alpha Wing $}, proceed to the objective.")]
        )
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="Mission complete.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertFalse(
            _has_styling_warning(validator),
            f"Unexpected styling warning when command briefing has a color tag: {validator.warnings}",
        )

    def test_debriefing_with_tag_does_not_warn(self):
        """A color tag in any debriefing stage is enough to suppress the warning."""
        mission = _make_base_mission()
        mission.briefing = Briefing(
            stages=[BriefingStage(text="Escort the convoy.")]
        )
        mission.debriefing = Debriefing(
            stages=[DebriefingStage(text="The $f{ GTC Dauntless $} survived.")]
        )
        validator = Validator(mission, REPO_ROOT)
        validator.validate()
        self.assertFalse(
            _has_styling_warning(validator),
            f"Unexpected styling warning when debriefing has a color tag: {validator.warnings}",
        )

    def test_various_color_letters_do_not_warn(self):
        """Spot-check several other canonical color letters as span-open tags."""
        for tag in ("$h{", "$y{", "$W{", "$R{", "$V{"):
            with self.subTest(tag=tag):
                mission = _make_base_mission()
                mission.briefing = Briefing(
                    stages=[BriefingStage(text=f"Head to {tag} rally point $}}.")]
                )
                validator = Validator(mission, REPO_ROOT)
                validator.validate()
                self.assertFalse(
                    _has_styling_warning(validator),
                    f"Unexpected warning for tag '{tag}': {validator.warnings}",
                )

    def test_various_single_word_color_letters_do_not_warn(self):
        """Spot-check several canonical single-word color tags (followed by space)."""
        for tag in ("$h", "$y", "$W", "$R"):
            with self.subTest(tag=tag):
                mission = _make_base_mission()
                mission.briefing = Briefing(
                    stages=[BriefingStage(text=f"Protect {tag} Convoy.")]
                )
                validator = Validator(mission, REPO_ROOT)
                validator.validate()
                self.assertFalse(
                    _has_styling_warning(validator),
                    f"Unexpected warning for single-word tag '{tag}': {validator.warnings}",
                )


if __name__ == "__main__":
    unittest.main()
