import math
from typing import Optional
from common.utils import calculate_briefing_camera_height
from common.text_styling_utils import extract_briefing_style_tags, validate_span_style_tags

class BriefingChecksMixin:
    def _validate_span_style_tags(self, context: str, text: Optional[str]):
        """
        Validate span-style color tags ($c{ ... $}) in briefing/debriefing text.
        """
        for w in validate_span_style_tags(text):
            self.log_warning(f"{context}: {w}")

    def validate_briefing_span_tags(self):
        """
        Validate span-style color-tag balancing in supported styling contexts:
        command briefing, mission briefing and debriefing text.
        """
        for i, stage in enumerate(self.mission.command_briefing.stages, start=1):
            self._validate_span_style_tags(f"Command briefing stage {i} text", stage.text)

        for i, stage in enumerate(self.mission.briefing.stages, start=1):
            self._validate_span_style_tags(f"Briefing stage {i} text", stage.text)

        for i, stage in enumerate(self.mission.debriefing.stages, start=1):
            self._validate_span_style_tags(f"Debriefing stage {i} text", stage.text)

    def validate_briefing_text_styling_scope(self):
        """
        Warn if briefing/debriefing text styling tags are used outside supported contexts.

        Styling tags are intended only for fiction viewer, command briefing,
        mission briefing and debriefing text blocks.
        """
        guidance = (
            "Briefing text styling tags belong only to fiction viewer, "
            "command briefing, mission briefing and debriefing text."
        )

        def warn_if_has_tags(context: str, text: Optional[str]):
            tags = extract_briefing_style_tags(text)
            if tags:
                tags_joined = ", ".join(tags)
                self.log_warning(f"{context} contains briefing styling tags ({tags_joined}). {guidance}")

        # In-mission text channels where styling tags do not belong.
        for idx, msg in enumerate(self.mission.messages, start=1):
            warn_if_has_tags(
                f"mission_flow.messages[{idx}] ('{msg.name}') text",
                msg.message,
            )

        for idx, goal in enumerate(self.mission.goals, start=1):
            warn_if_has_tags(
                f"mission_flow.goals[{idx}] ('{goal.name}') objective_text",
                goal.message,
            )

        for idx, event in enumerate(self.mission.events, start=1):
            if event.directive_text:
                event_name = event.name if event.name else f"Event {idx}"
                warn_if_has_tags(
                    f"mission_flow.events[{idx}] ('{event_name}') hud_directive_text",
                    event.directive_text,
                )

        # Other authored text fields outside supported briefing/debriefing contexts.
        mi = self.mission.mission_info
        warn_if_has_tags("mission_info.name", mi.name)
        warn_if_has_tags("mission_info.description", mi.description)

    def _calculate_briefing_camera_width(self, icons) -> float:
        """
        Replicate the briefing camera width calculation from MissionLoader.

        Returns the camera Y-height (== camera width) that the converter would
        automatically assign to a stage containing the given icons.  This is the
        same value used as the reference distance for the icon proximity check.

        Formula (mirrors _calculate_briefing_camera in mission_loader.py):
          final_width = max(delta_x, 2.5 * delta_z)
          cam_width   = max(final_width * 1.15, 1000.0)

        Args:
            icons: Iterable of BriefingIcon objects (must have .pos as [x, 0, z]).

        Returns:
            float: The computed camera width (minimum 1000.0).
        """
        x_values = [ic.pos[0] for ic in icons]
        z_values = [ic.pos[2] for ic in icons]

        delta_x = max(x_values) - min(x_values)
        delta_z = max(z_values) - min(z_values)

        return calculate_briefing_camera_height(delta_x, delta_z)

    def validate_briefing(self):
        """
        Validate briefing stages and icons.
        
        Checks:
        - Voice name validity.
        - Icon absence, types, teams, and classes.
        - Icon proximity (warns if any two icons are closer than 5% of the
          automatically calculated camera width, which would cause visual overlap).
        """

        for i, stage in enumerate(self.mission.briefing.stages):
            # Validate voice name
            if stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Briefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

            # Check for the absence of icons
            if not stage.icons:
                self.log_warning(f"Briefing stage {i+1} has no icons defined.")

            # Validate icon properties
            if stage.icons:
                for icon in stage.icons:
                    if icon.type not in self.allowed_icons:
                        self.log_error(f"Briefing icon has invalid type '{icon.type}'")
                    
                    # Team check
                    if icon.team and icon.team not in self.allowed_teams:
                        self.log_error(f"Briefing icon has invalid team '{icon.team}'")
                        
                    # Class check
                    if icon.ship_class and icon.ship_class not in self.ship_classes:
                        self.log_error(f"Briefing icon class '{icon.ship_class}' is not a valid ship class.")

                    # Non-ship icon class check
                    if icon.type in self.non_ship_icon_types:
                        # Default is "Terran NavBuoy". If it's anything else, it's an error.
                        if icon.ship_class != "Terran NavBuoy":
                            self.log_error(f"Briefing icon of type '{icon.type}' uses class '{icon.ship_class}'. Non-ship icons must use the safe default class 'Terran NavBuoy' (or omit the class field).")

            # Icon proximity check: warn if any two icons are closer than 5% of the camera width.
            # Camera width calcutated here mirrors the calculation in MissionLoader._calculate_briefing_camera.
            if stage.icons and len(stage.icons) >= 2:
                cam_width = self._calculate_briefing_camera_width(stage.icons)
                threshold = 0.05 * cam_width

                def _icon_label(ic) -> str:
                    """Return a human-readable identifier for an icon."""
                    if ic.label:
                        return f"'{ic.label}' ({ic.type})"
                    return f"(type '{ic.type}')"

                icons_list = stage.icons
                for a_idx in range(len(icons_list)):
                    for b_idx in range(a_idx + 1, len(icons_list)):
                        ic_a = icons_list[a_idx]
                        ic_b = icons_list[b_idx]
                        dx = ic_a.pos[0] - ic_b.pos[0]
                        dz = ic_a.pos[2] - ic_b.pos[2]
                        dist = math.sqrt(dx * dx + dz * dz)
                        if dist < threshold:
                            self.log_warning(
                                f"Briefing stage {i+1}: icons {_icon_label(ic_a)} and "
                                f"{_icon_label(ic_b)} are too close together "
                                f"(distance {dist:.1f}, minimum {threshold:.1f} = 5% of "
                                f"camera width {cam_width:.1f}). "
                                f"Consider spreading them further apart to prevent visual overlap."
                            )

    def validate_debriefing(self):
        for i, stage in enumerate(self.mission.debriefing.stages):
            # Validate SEXP condition
            if stage.condition:
                self._check_sexp_string(f"Debriefing stage {i+1} display_condition", stage.condition)

                # Warn if condition is a bare '( true )' — always-true conditions are
                # insufficiently restrictive and may cause incorrect text to be shown
                normalized_cue = "".join(stage.condition.split()).lower()
                if normalized_cue == '(true)':
                    self.log_warning(
                        f"Debriefing stage {i+1} uses '( true )' as its display_condition. "
                        f"This display_condition is always true and will cause the stage to display "
                        f"regardless of the mission outcome (e.g., a success message will also "
                        f"appear after a failure). "
                        f"Use a specific SEXP (e.g., '( is-event-true-delay \"...\" 0 )') to "
                        f"precisely target the intended outcome."
                    )

            # Validate Voice
            if stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Debriefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

    def validate_command_briefing(self):
        for i, stage in enumerate(self.mission.command_briefing.stages):
            if stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Command Briefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")
