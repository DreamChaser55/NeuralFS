class EnvironmentChecksMixin:
    def validate_environment(self):
        """
        Validate environment settings (suns, backgrounds, nebula).
        
        Checks that referenced textures and patterns exist in the
        allowed token lists.
        """
        env = self.mission.environment
        
        # Suns
        for i, s in enumerate(env.suns):
            if s.texture not in self.allowed_suns:
                 self.log_error(f"Invalid sun texture '{s.texture}' in environment.suns[{i}]")
            # Warn if sun is at [0, 0, 0] — directly in front of the player at default spawn
            if s.angles and all(abs(a) < 1e-6 for a in s.angles):
                self.log_warning(
                    f"environment.suns[{i}] (texture '{s.texture}') has angles [0, 0, 0], "
                    f"which places the sun directly in front of the player at default spawn "
                    f"orientation. This causes a whiteout blinding effect. "
                    f"Unless it's intended, set a non-zero angles value (in radians)."
                )

        # Starbitmaps
        for i, s in enumerate(env.starbitmaps):
            if s.texture not in self.allowed_backgrounds:
                 self.log_error(f"Invalid starbitmap texture '{s.texture}' in environment.starbitmaps[{i}]")

        if env.nebula and env.nebula.enabled and env.starbitmaps:
            self.log_error(f"environment.starbitmaps must be empty when full nebula is enabled (environment.nebula.enabled: true)")

        mission_flags_lower = {str(flag).strip().lower() for flag in self.mission.mission_info.flags}
        is_subspace_mission = 'subspace' in mission_flags_lower
        is_full_nebula_mission = bool(env.nebula and env.nebula.enabled)

        if is_subspace_mission and env.starbitmaps:
            self.log_error(f"environment.starbitmaps must be empty in subspace missions (they are not visible in subspace)")

        # Sparse normal-space background advisory
        if not is_subspace_mission and not is_full_nebula_mission:
            background_nebula_count = sum(
                1 for bitmap in env.starbitmaps if bitmap.texture in self.allowed_nebulae_bitmaps
            )
            if background_nebula_count < 3:
                self.log_warning(
                    f"This mission has only {background_nebula_count} background nebula "
                    f"starbitmap(s). Good-looking missions usually include at least 3. "
                    f"Consider adding more background nebulae so the sky does not look too empty."
                )

        # Nebula
        if env.nebula.enabled:
            if env.nebula.pattern and env.nebula.pattern not in self.allowed_nebula_patterns:
                self.log_error(f"Invalid nebula pattern '{env.nebula.pattern}'")
            
            for p in env.nebula.poofs:
                if p not in self.allowed_nebula_poofs:
                    self.log_error(f"Invalid nebula poof '{p}'")

        # Asteroid/Debris Field Logic
        af = env.asteroid_field
        if af and af.targets:
            # Targets are only valid for Active Asteroid fields
            if not (af.field_type == 'active' and af.genre == 'asteroid'):
                self.log_warning(f"The asteroid field defines targets but they will be ignored (type='{af.field_type}', genre='{af.genre}'). Targets are only supported for Active Asteroid fields.")

    def validate_asteroid_targets(self):
        af = self.mission.environment.asteroid_field
        if not af or not af.targets:
            return
            
        valid_ships = {s.name for s in self.mission.ships}
        for t in af.targets:
            if t not in valid_ships:
                self.log_error(f"Asteroid field target '{t}' does not exist.")