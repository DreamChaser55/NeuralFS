import math
from typing import Optional
from common.utils import calculate_briefing_camera_height
from common.text_styling_utils import extract_briefing_style_tags, validate_span_style_tags, has_color_styling_tag

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
                msg.text,
            )

        for idx, goal in enumerate(self.mission.goals, start=1):
            warn_if_has_tags(
                f"mission_flow.goals[{idx}] ('{goal.name}') objective_text",
                goal.objective_text,
            )

        for idx, event in enumerate(self.mission.events, start=1):
            if event.hud_directive_text:
                event_name = event.name if event.name else f"Event {idx}"
                warn_if_has_tags(
                    f"mission_flow.events[{idx}] ('{event_name}') hud_directive_text",
                    event.hud_directive_text,
                )

        # Other authored text fields outside supported briefing/debriefing contexts.
        mi = self.mission.mission_info
        warn_if_has_tags("mission_info.name", mi.name)
        warn_if_has_tags("mission_info.description", mi.description)

    def validate_mission_has_briefing_text_styling(self):
        """
        Warn when eligible mission text exists but none of it contains color
        styling tags (span-open or single-word color tags).

        Eligible contexts: command briefing, mission briefing, debriefing.

        Rationale: FSO text styling is mandatory in player-facing mission texts
        to visually distinguish ships, wings, and locations. An AI authoring agent
        that forgets to add styling tags at all is a common and silent error — this
        check catches that case at mission level rather than per-field.

        The check fires only when at least one eligible text field is non-empty, so
        minimal or test missions with no briefing/debriefing text are not warned.
        Placeholder-only texts ($callsign, $rank, $quote, $semicolon) do not count
        as styled because they contain no color tags.
        """
        all_texts = []

        for stage in self.mission.command_briefing.stages:
            if stage.text:
                all_texts.append(stage.text)

        for stage in self.mission.briefing.stages:
            if stage.text:
                all_texts.append(stage.text)

        for stage in self.mission.debriefing.stages:
            if stage.text:
                all_texts.append(stage.text)

        if not all_texts:
            # No eligible text at all — skip the check (minimal/no-briefing mission).
            return

        if not any(has_color_styling_tag(t) for t in all_texts):
            self.log_warning(
                "No text styling color tags were found in any eligible mission text "
                "(command briefing, mission briefing, debriefing). "
                "If this mission has player-facing briefing or debriefing text, add "
                "appropriate FSO styling tags for ships, wings, locations, and warnings "
                "(e.g. '$f{ GTC Fenris $}' for a friendly ship, '$h Rama' for a hostile wing)."
            )

    def _calculate_briefing_camera_width(self, icons) -> float:
        """
        Replicate the briefing camera width calculation from MissionLoader.

        Returns the camera Y-height (== camera width) that the converter would
        automatically assign to a stage containing the given icons.  This is the
        same value used as the reference distance for the icon proximity check.

        See ``common.utils.calculate_briefing_camera_height`` for the formula.

        Args:
            icons: Iterable of BriefingIcon objects (must have .map_position as [x, 0, z]).

        Returns:
            float: The computed camera width (minimum 1000.0).
        """
        x_values = [ic.map_position[0] for ic in icons]
        z_values = [ic.map_position[2] for ic in icons]

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
        validate_voice_names = self.should_validate_voice_names()

        for i, stage in enumerate(self.mission.briefing.stages):
            # Validate voice name
            if validate_voice_names and stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Briefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

            # Check for the absence of icons
            if not stage.icons:
                self.log_warning(f"Briefing stage {i+1} has no icons defined.")

            # Validate icon properties
            if stage.icons:
                for icon in stage.icons:
                    if icon.icon_type not in self.allowed_icons:
                        self.log_error(f"Briefing icon has invalid type '{icon.icon_type}'")

                    # Team check
                    if icon.team and icon.team not in self.allowed_teams:
                        self.log_error(f"Briefing icon has invalid team '{icon.team}'")

                    # Validate display_class based on icon type classification.
                    if icon.icon_type in self.non_ship_icon_types:
                        # Non-ship icons (Waypoint, Jump Node, Planet, Small Planet,
                        # Asteroid Field) must OMIT display_class in FSIF. Authors
                        # should not try to show a ship class for a landmark icon.
                        if icon.display_class_authored:
                            self.log_error(
                                f"Briefing icon of non-ship type '{icon.icon_type}' must not author display_class. "
                                f"Omit the display_class field — the converter will use the safe default "
                                f"'Terran NavBuoy' automatically."
                            )
                    else:
                        # Ship icon types MUST explicitly author display_class with a
                        # valid, non-NavBuoy ship class so the selected icon shows the
                        # correct ship in-game instead of a navigation buoy.
                        if not icon.display_class_authored:
                            self.log_error(
                                f"Briefing icon of ship type '{icon.icon_type}' is missing display_class. "
                                f"Author display_class with the ship class this icon represents "
                                f"(e.g., display_class: \"GTF Ulysses\")."
                            )
                        elif icon.display_class == "Terran NavBuoy":
                            self.log_error(
                                f"Briefing icon of ship type '{icon.icon_type}' uses display_class 'Terran NavBuoy'. "
                                f"Replace with the actual ship class this icon represents."
                            )
                        elif icon.display_class not in self.ship_classes:
                            self.log_error(
                                f"Briefing icon of ship type '{icon.icon_type}' uses display_class "
                                f"'{icon.display_class}' which is not a valid FSO ship class."
                            )

            # Icon proximity check: warn if any two icons are closer than 5% of the camera width.
            # Camera width calculated here mirrors the calculation in MissionLoader._calculate_briefing_camera.
            if stage.icons and len(stage.icons) >= 2:
                cam_width = self._calculate_briefing_camera_width(stage.icons)
                threshold = 0.05 * cam_width

                def _icon_label(ic) -> str:
                    """Return a human-readable identifier for an icon."""
                    if ic.label:
                        return f"'{ic.label}' ({ic.icon_type})"
                    return f"(type '{ic.icon_type}')"

                icons_list = stage.icons
                for a_idx in range(len(icons_list)):
                    for b_idx in range(a_idx + 1, len(icons_list)):
                        ic_a = icons_list[a_idx]
                        ic_b = icons_list[b_idx]
                        dx = ic_a.map_position[0] - ic_b.map_position[0]
                        dz = ic_a.map_position[2] - ic_b.map_position[2]
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
        """
        Validate debriefing stage definitions.

        Invariants:
        - ``display_condition`` must be a structurally valid SEXP boolean
          expression (checked via ``_check_sexp_string``).
        - A bare ``( true )`` display_condition is warned against because it
          causes the stage to display after every mission outcome, regardless
          of success or failure.  Authors should use specific SEXPs that target
          the intended outcome (e.g. ``is-event-true-delay``,
          ``has-departed-delay``).
        - ``voice_name`` must exist in the TTS voice registry for the active
          provider.
        """
        validate_voice_names = self.should_validate_voice_names()

        for i, stage in enumerate(self.mission.debriefing.stages):
            # Validate SEXP condition
            if stage.display_condition:
                self._check_sexp_string(f"Debriefing stage {i+1} display_condition", stage.display_condition)

                # Warn if condition is a bare '( true )' — always-true conditions are
                # insufficiently restrictive and may cause incorrect text to be shown
                normalized_cue = "".join(stage.display_condition.split()).lower()
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
            if validate_voice_names and stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Debriefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")

    def validate_command_briefing(self):
        """
        Validate command briefing stage definitions.

        Invariant: ``voice_name`` on each stage must exist in the TTS voice
        registry for the active provider.  Other structural constraints (text
        content, ASCII encoding) are handled by the ASCII and briefing-span
        checks.
        """
        validate_voice_names = self.should_validate_voice_names()

        for i, stage in enumerate(self.mission.command_briefing.stages):
            if validate_voice_names and stage.voice_name and stage.voice_name not in self.voices:
                self.log_error(f"Command Briefing stage {i+1} uses unknown voice_name '{stage.voice_name}'")
