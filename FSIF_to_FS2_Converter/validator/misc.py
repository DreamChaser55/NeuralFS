from typing import Dict
import fs_flags_constants

class MiscChecksMixin:
    def validate_global_names(self):
        """
        Validate uniqueness and length of global entity names.
        
        Enforces:
        - Name length < 30 characters (FSO engine limit).
        - Uniqueness within namespaces (Objects, Events, Goals, Messages).
        """
        # Separate namespaces
        objects: Dict[str, str] = {}
        events: Dict[str, str] = {}
        goals: Dict[str, str] = {}
        messages: Dict[str, str] = {}
        
        def check(name, type_, scope):
            if not name: return
            
            # Length Limit
            if len(name) >= 30:
                self.log_error(f"{type_} '{name}' name length {len(name)} exceeds limit (<30).")
            
            # Duplicates in scope
            if name in scope:
                self.log_error(f"{type_} '{name}' conflicts with existing {scope[name]} '{name}'")
            else:
                scope[name] = type_

        # Objects Scope
        for s in self.mission.ships: check(s.name, "Ship", objects)
        for w in self.mission.wings: check(w.name, "Wing", objects)
        for name in self.mission.waypoints: check(name, "Waypoint", objects)
        for j in self.mission.jump_nodes: check(j.name, "Jump Node", objects)
        
        # Events Scope
        for e in self.mission.events: check(e.name, "Event", events)
        
        # Goals Scope
        for g in self.mission.goals: check(g.name, "Goal", goals)
        
        # Messages Scope
        for m in self.mission.messages: check(m.name, "Message", messages)

    def validate_mission_info(self):
        # Validate flags
        for f in self.mission.mission_info.flags:
            # We check if it maps to a known flag bit
            canon = fs_flags_constants.resolve_mission_flag(f)
            if not canon:
                self.log_warning(f"Unknown mission flag: '{f}'")

        # Validate ai_profile
        known_ai_profiles = {"FS1 RETAIL", "FS2 RETAIL"}
        if self.mission.mission_info.ai_profile not in known_ai_profiles:
            self.log_warning(f"Unknown ai_profile: '{self.mission.mission_info.ai_profile}'")

    def validate_messages(self):
        """
        Validate message definitions.
        
        Checks that referenced voice names exist in the TTS registry.
        """
        for msg in self.mission.messages:
            # Voice Name
            if msg.voice_name and msg.voice_name not in self.voices:
                self.log_error(f"Message '{msg.name}' uses unknown voice_name '{msg.voice_name}'")

    def validate_audio(self):
        """
        Validate mission music selections against allowed tracks.
        """
        audio = self.mission.audio
        if audio.mission_music and audio.mission_music not in self.allowed_music_mission:
            self.log_error(f"Invalid mission_music '{audio.mission_music}'")
        if audio.briefing_music and audio.briefing_music not in self.allowed_music_briefing:
            self.log_error(f"Invalid briefing_music '{audio.briefing_music}'")

    def validate_goals_and_directives(self):
        """
        Warn if the number of events with hud_directive_text is less than the number of goals.
        """
        num_goals = len(self.mission.goals)
        if num_goals == 0:
            return

        num_directives = sum(1 for event in self.mission.events if event.directive_text)

        if num_directives < num_goals:
            self.log_warning(
                f"Mission has {num_goals} goal(s) but only {num_directives} event(s) with hud_directive_text. "
                f"It is highly recommended that every important mission goal has a corresponding "
                f"event with hud_directive_text so that the objective is visible on the player's HUD."
            )
