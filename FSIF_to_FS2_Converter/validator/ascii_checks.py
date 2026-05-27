from typing import Optional, List
from common.validation_utils import find_non_ascii_characters

class AsciiChecksMixin:
    def _validate_ascii_text(self, path: str, text: Optional[str]):
        """
        Reject non-ASCII text in FSO-facing FSIF fields.

        ASCII control characters such as '\n', '\r' and '\t' are allowed
        naturally because they are part of the 7-bit ASCII range.
        """
        if text is None:
            return

        offenders_details = find_non_ascii_characters(str(text))
        if offenders_details:
            self.log_error(f"{path} contains non-ASCII character(s): {offenders_details}")

    def _validate_xstr_text(self, path: str, text: Optional[str]):
        """
        Validates text that will be wrapped in XSTR("...", -1) in the emitted .fs2 file.
        Rejects non-ASCII characters and double quotes (").
        Double quotes break the FSO stuff_string parser when embedded inside an XSTR macro.
        """
        if text is None:
            return
            
        self._validate_ascii_text(path, text)
        
        if '"' in text:
            self.log_error(
                f"{path} contains double quote (\") characters. "
                f"These are not allowed in text fields displayed to the player, as they break "
                f"the FSO engine parser when wrapped in XSTR. Please use single quotes (') instead."
            )

    def _validate_ascii_text_list(self, path: str, values: Optional[List[str]]):
        if not values:
            return
        for i, value in enumerate(values):
            self._validate_ascii_text(f"{path}[{i}]", value)

    def validate_ascii_text_fields(self):
        """
        Enforce that all FSO-facing FSIF string fields contain only ASCII characters.

        Invariant: the FSO engine only supports ASCII reliably.  Any field that
        will be embedded in the emitted ``.fs2`` file must be pure ASCII.
        Additionally, fields wrapped in an XSTR macro (player-visible text such
        as mission name, goal objective_text, message text, cargo labels, etc.)
        must not contain double quotes ``"``, because those break the FSO
        ``stuff_string`` parser when embedded inside ``XSTR("...", -1)``.

        Excluded intentionally from this check:
        - ``voice_name`` and ``voice_style_instructions`` — not emitted into the
          ``.fs2`` file; consumed only by the TTS generation pipeline.
        - Internal converter-only fields such as wing template names.
        """
        self._validate_ascii_text('mission_flow.fiction_viewer', self.mission.fiction_viewer)

        info = self.mission.mission_info
        self._validate_xstr_text('mission_info.name', info.name)
        self._validate_ascii_text('mission_info.author', info.author)
        self._validate_xstr_text('mission_info.description', info.description)
        self._validate_ascii_text('mission_info.game_type', info.game_type)
        self._validate_ascii_text_list('mission_info.flags', info.flags)

        env = self.mission.environment
        for i, sun in enumerate(env.suns):
            self._validate_ascii_text(f'environment.suns[{i}].texture', sun.texture)

        for i, bitmap in enumerate(env.background_bitmaps):
            self._validate_ascii_text(f'environment.background_bitmaps[{i}].texture', bitmap.texture)

        if env.nebula:
            self._validate_ascii_text('environment.nebula.pattern', env.nebula.pattern)
            self._validate_ascii_text('environment.nebula.storm', env.nebula.storm)
            self._validate_ascii_text_list('environment.nebula.cloud_sprites', env.nebula.cloud_sprites)

        if env.asteroid_field:
            self._validate_ascii_text_list('environment.asteroid_field.object_variants', env.asteroid_field.object_variants)
            self._validate_ascii_text_list('environment.asteroid_field.target_ships', env.asteroid_field.target_ships)

        setup = self.mission.player_setup
        self._validate_ascii_text('player_setup.start_ship', setup.start_ship)
        for i, choice in enumerate(setup.additional_ship_choices):
            self._validate_ascii_text(f'player_setup.additional_ship_choices[{i}].class', choice.ship_class)
        self._validate_ascii_text_list('player_setup.additional_weapons', setup.additional_weapons)

        for i, ship in enumerate(self.mission.ships):
            prefix = f'ships[{i}]'
            self._validate_ascii_text(f'{prefix}.name', ship.name)
            self._validate_ascii_text(f'{prefix}.class', ship.ship_class)
            self._validate_ascii_text(f'{prefix}.team', ship.team)
            self._validate_ascii_text(f'{prefix}.ai_class', ship.ai_class)
            self._validate_xstr_text(f'{prefix}.cargo', ship.cargo)
            self._validate_ascii_text(f'{prefix}.arrival_method', ship.arrival_method)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', ship.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', ship.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_method', ship.departure_method)
            self._validate_ascii_text(f'{prefix}.departure_anchor', ship.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', ship.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', ship.flags)
            self._validate_ascii_text(f'{prefix}.initial_orders', ship.initial_orders)
            self._validate_ascii_text(f'{prefix}.docked_with', ship.docked_with)
            self._validate_ascii_text(f'{prefix}.docker_point', ship.docker_point)
            self._validate_ascii_text(f'{prefix}.dockee_point', ship.dockee_point)
            for j, subsystem in enumerate(ship.subsystems.list):
                self._validate_ascii_text(f'{prefix}.subsystems.list[{j}].name', subsystem.name)
            self._validate_ascii_text_list(f'{prefix}.weapons.primary', ship.weapons.primary)
            self._validate_ascii_text_list(f'{prefix}.weapons.secondary', ship.weapons.secondary)

        for i, wing in enumerate(self.mission.wings):
            prefix = f'wings[{i}]'
            self._validate_ascii_text(f'{prefix}.name', wing.name)
            self._validate_ascii_text(f'{prefix}.arrival_method', wing.arrival_method)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', wing.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', wing.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_method', wing.departure_method)
            self._validate_ascii_text(f'{prefix}.departure_anchor', wing.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', wing.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', wing.flags)
            self._validate_ascii_text(f'{prefix}.initial_orders', wing.initial_orders)

        for waypoint_name in self.mission.waypoints.keys():
            self._validate_ascii_text(f'waypoints key {waypoint_name!r}', waypoint_name)

        for i, event in enumerate(self.mission.events):
            prefix = f'events[{i}]'
            self._validate_ascii_text(f'{prefix}.name', event.name)
            self._validate_ascii_text(f'{prefix}.formula', event.formula)
            self._validate_xstr_text(f'{prefix}.hud_directive_text', event.hud_directive_text)

        for i, goal in enumerate(self.mission.goals):
            prefix = f'goals[{i}]'
            self._validate_ascii_text(f'{prefix}.name', goal.name)
            self._validate_ascii_text(f'{prefix}.type', goal.type)
            self._validate_xstr_text(f'{prefix}.objective_text', goal.objective_text)
            self._validate_ascii_text(f'{prefix}.formula', goal.formula)

        for i, message in enumerate(self.mission.messages):
            prefix = f'messages[{i}]'
            self._validate_ascii_text(f'{prefix}.name', message.name)
            self._validate_xstr_text(f'{prefix}.text', message.text)

        for i, stage in enumerate(self.mission.command_briefing.stages):
            prefix = f'command_briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)

        for i, stage in enumerate(self.mission.briefing.stages):
            prefix = f'briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            for j, icon in enumerate(stage.icons):
                icon_prefix = f'{prefix}.icons[{j}]'
                self._validate_ascii_text(f'{icon_prefix}.icon_type', icon.icon_type)
                self._validate_ascii_text(f'{icon_prefix}.team', icon.team)
                self._validate_ascii_text(f'{icon_prefix}.display_class', icon.display_class)
                self._validate_xstr_text(f'{icon_prefix}.label', icon.label)

        for i, stage in enumerate(self.mission.debriefing.stages):
            prefix = f'debriefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.display_condition', stage.display_condition)
            self._validate_xstr_text(f'{prefix}.recommendation', stage.recommendation)

        for i, reinforcement in enumerate(self.mission.reinforcements):
            prefix = f'reinforcements[{i}]'
            self._validate_ascii_text(f'{prefix}.name', reinforcement.name)
            self._validate_ascii_text_list(f'{prefix}.unavailable_messages', reinforcement.unavailable_messages)
            self._validate_ascii_text_list(f'{prefix}.available_messages', reinforcement.available_messages)

        for i, jump_node in enumerate(self.mission.jump_nodes):
            self._validate_ascii_text(f'entities.jump_nodes[{i}].name', jump_node.name)

        audio = self.mission.audio
        self._validate_ascii_text('audio.mission_music', audio.mission_music)
        self._validate_ascii_text('audio.briefing_music', audio.briefing_music)