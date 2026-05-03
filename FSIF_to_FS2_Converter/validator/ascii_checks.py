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
        Validate only FSO-facing string fields.

        Excluded intentionally:
        - voice_name
        - voice_style_instructions
        - internal converter-only helper fields such as wing template names
        """
        self._validate_ascii_text('mission_flow.fiction_viewer', self.mission.fiction_viewer)

        info = self.mission.mission_info
        self._validate_xstr_text('mission_info.name', info.name)
        self._validate_ascii_text('mission_info.author', info.author)
        self._validate_xstr_text('mission_info.description', info.description)
        self._validate_ascii_text('mission_info.game_type', info.game_type)
        self._validate_ascii_text('mission_info.ai_profile', info.ai_profile)
        self._validate_ascii_text_list('mission_info.flags', info.flags)

        env = self.mission.environment
        for i, sun in enumerate(env.suns):
            self._validate_ascii_text(f'environment.suns[{i}].texture', sun.texture)

        for i, bitmap in enumerate(env.starbitmaps):
            self._validate_ascii_text(f'environment.starbitmaps[{i}].texture', bitmap.texture)

        if env.nebula:
            self._validate_ascii_text('environment.nebula.pattern', env.nebula.pattern)
            self._validate_ascii_text('environment.nebula.storm', env.nebula.storm)
            self._validate_ascii_text_list('environment.nebula.poofs', env.nebula.poofs)

        if env.asteroid_field:
            self._validate_ascii_text_list('environment.asteroid_field.debris_types', env.asteroid_field.debris_types)
            self._validate_ascii_text_list('environment.asteroid_field.targets', env.asteroid_field.targets)

        setup = self.mission.player_setup
        self._validate_ascii_text('player_setup.start_ship', setup.start_ship)
        for i, choice in enumerate(setup.extra_ships):
            self._validate_ascii_text(f'player_setup.extra_ships[{i}].class', choice.ship_class)
        self._validate_ascii_text_list('player_setup.extra_weapons', setup.extra_weapons)

        for i, ship in enumerate(self.mission.ships):
            prefix = f'ships[{i}]'
            self._validate_ascii_text(f'{prefix}.name', ship.name)
            self._validate_ascii_text(f'{prefix}.class', ship.ship_class)
            self._validate_ascii_text(f'{prefix}.team', ship.team)
            self._validate_ascii_text(f'{prefix}.ai_class', ship.ai_class)
            self._validate_xstr_text(f'{prefix}.cargo', ship.cargo)
            self._validate_ascii_text(f'{prefix}.arrival_location', ship.arrival_location)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', ship.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', ship.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_location', ship.departure_location)
            self._validate_ascii_text(f'{prefix}.departure_anchor', ship.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', ship.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', ship.flags)
            self._validate_ascii_text(f'{prefix}.ai_goals', ship.ai_goals)
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
            self._validate_ascii_text(f'{prefix}.arrival_location', wing.arrival_location)
            self._validate_ascii_text(f'{prefix}.arrival_anchor', wing.arrival_anchor)
            self._validate_ascii_text(f'{prefix}.arrival_cue', wing.arrival_cue)
            self._validate_ascii_text(f'{prefix}.departure_location', wing.departure_location)
            self._validate_ascii_text(f'{prefix}.departure_anchor', wing.departure_anchor)
            self._validate_ascii_text(f'{prefix}.departure_cue', wing.departure_cue)
            self._validate_ascii_text_list(f'{prefix}.flags', wing.flags)
            self._validate_ascii_text(f'{prefix}.ai_goals', wing.ai_goals)

        for waypoint_name in self.mission.waypoints.keys():
            self._validate_ascii_text(f'waypoints key {waypoint_name!r}', waypoint_name)

        for i, event in enumerate(self.mission.events):
            prefix = f'events[{i}]'
            self._validate_ascii_text(f'{prefix}.name', event.name)
            self._validate_ascii_text(f'{prefix}.formula', event.formula)
            self._validate_xstr_text(f'{prefix}.directive_text', event.directive_text)

        for i, goal in enumerate(self.mission.goals):
            prefix = f'goals[{i}]'
            self._validate_ascii_text(f'{prefix}.name', goal.name)
            self._validate_ascii_text(f'{prefix}.type', goal.type)
            self._validate_xstr_text(f'{prefix}.message', goal.message)
            self._validate_ascii_text(f'{prefix}.formula', goal.formula)

        for i, message in enumerate(self.mission.messages):
            prefix = f'messages[{i}]'
            self._validate_ascii_text(f'{prefix}.name', message.name)
            self._validate_xstr_text(f'{prefix}.message', message.message)

        for i, stage in enumerate(self.mission.command_briefing.stages):
            prefix = f'command_briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)

        for i, stage in enumerate(self.mission.briefing.stages):
            prefix = f'briefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            for j, icon in enumerate(stage.icons):
                icon_prefix = f'{prefix}.icons[{j}]'
                self._validate_ascii_text(f'{icon_prefix}.type', icon.type)
                self._validate_ascii_text(f'{icon_prefix}.team', icon.team)
                self._validate_ascii_text(f'{icon_prefix}.class', icon.ship_class)
                self._validate_xstr_text(f'{icon_prefix}.label', icon.label)

        for i, stage in enumerate(self.mission.debriefing.stages):
            prefix = f'debriefing.stages[{i}]'
            self._validate_xstr_text(f'{prefix}.text', stage.text)
            self._validate_ascii_text(f'{prefix}.condition', stage.condition)
            self._validate_xstr_text(f'{prefix}.recommendation', stage.recommendation)

        for i, reinforcement in enumerate(self.mission.reinforcements):
            prefix = f'reinforcements[{i}]'
            self._validate_ascii_text(f'{prefix}.name', reinforcement.name)
            self._validate_ascii_text_list(f'{prefix}.no_messages', reinforcement.no_messages)
            self._validate_ascii_text_list(f'{prefix}.yes_messages', reinforcement.yes_messages)

        for i, jump_node in enumerate(self.mission.jump_nodes):
            self._validate_ascii_text(f'entities.jump_nodes[{i}].name', jump_node.name)

        audio = self.mission.audio
        self._validate_ascii_text('audio.mission_music', audio.mission_music)
        self._validate_ascii_text('audio.briefing_music', audio.briefing_music)