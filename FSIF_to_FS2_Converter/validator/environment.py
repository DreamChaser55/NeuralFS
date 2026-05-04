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

        # Background bitmaps
        for i, s in enumerate(env.background_bitmaps):
            if s.texture not in self.allowed_backgrounds:
                 self.log_error(f"Invalid background bitmap texture '{s.texture}' in environment.background_bitmaps[{i}]")

        if env.nebula and env.nebula.enabled and env.background_bitmaps:
            self.log_error(f"environment.background_bitmaps must be empty when full nebula is enabled (environment.nebula.enabled: true)")

        mission_flags_lower = {str(flag).strip().lower() for flag in self.mission.mission_info.flags}
        is_subspace_mission = 'subspace' in mission_flags_lower
        is_full_nebula_mission = bool(env.nebula and env.nebula.enabled)

        if is_subspace_mission and env.background_bitmaps:
            self.log_error(f"environment.background_bitmaps must be empty in subspace missions (they are not visible in subspace)")

        # Sparse normal-space background advisory
        if not is_subspace_mission and not is_full_nebula_mission:
            background_nebula_count = sum(
                1 for bitmap in env.background_bitmaps if bitmap.texture in self.allowed_nebulae_bitmaps
            )
            if background_nebula_count < 3:
                self.log_warning(
                    f"This mission has only {background_nebula_count} background nebula bitmap(s). "
                    f"Good-looking missions usually include at least 3. "
                    f"Consider adding more background nebulae so the sky does not look too empty."
                )

        # Nebula
        if env.nebula.enabled:
            if env.nebula.pattern and env.nebula.pattern not in self.allowed_nebula_patterns:
                self.log_error(f"Invalid nebula pattern '{env.nebula.pattern}'")
            
            for p in env.nebula.cloud_sprites:
                if p not in self.allowed_nebula_poofs:
                    self.log_error(f"Invalid nebula cloud_sprites entry '{p}'")

        # Asteroid/Debris Field Logic
        af = env.asteroid_field
        if af:
            if af.target_ships:
                if not (af.behavior == 'active' and af.object_type == 'asteroid'):
                    self.log_warning(f"The asteroid field defines target_ships but they will be ignored (behavior='{af.behavior}', object_type='{af.object_type}'). target_ships are only supported for active asteroid fields.")

    def validate_asteroid_field_object_variants(self):
        """
        Validate that object_variants contains only canonical names for the
        selected object_type, and that the two variant genres are not mixed.

        Rules:
        - object_variants must not be empty (omit the field to get defaults).
        - For object_type 'asteroid': only 'Brown', 'Blue', 'Orange'.
        - For object_type 'debris': only the canonical 'Terran/Vasudan/Shivan Debris N' names.
        - No cross-genre mixing (asteroid name in a debris field, or vice versa).
        - Duplicate entries are warned, not errored.
        """
        af = self.mission.environment.asteroid_field
        if not af:
            return

        if not af.object_variants:
            self.log_error(
                "environment.asteroid_field.object_variants is empty. "
                "An asteroid/debris field must have at least one object variant. "
                "Omit the field entirely to use the full default set for the selected object_type."
            )
            return

        if af.object_type == 'asteroid':
            allowed = self.allowed_asteroid_field_variants
            genre_label = 'asteroid'
            wrong_allowed = self.allowed_debris_field_variants
            wrong_genre_label = 'debris'
        else:
            allowed = self.allowed_debris_field_variants
            genre_label = 'debris'
            wrong_allowed = self.allowed_asteroid_field_variants
            wrong_genre_label = 'asteroid'

        # Split values into three buckets: correct-genre, wrong-genre, and unknown
        cross_genre = [v for v in af.object_variants if v in wrong_allowed]
        unknown = [v for v in af.object_variants if v not in allowed and v not in wrong_allowed]
        invalid = cross_genre + unknown

        if cross_genre:
            self.log_error(
                f"environment.asteroid_field.object_variants contains "
                f"{wrong_genre_label} field variant(s) but object_type is '{genre_label}': "
                f"{cross_genre}. "
                f"Asteroid and debris field variant names are mutually incompatible. "
                f"Allowed {genre_label} variants: {sorted(allowed)}."
            )
        if unknown:
            self.log_error(
                f"environment.asteroid_field.object_variants contains unrecognised variant name(s): "
                f"{unknown}. "
                f"Allowed {genre_label} variants: {sorted(allowed)}."
            )

        # Warn on duplicates (not an error — FSO ignores them, but they are pointless)
        seen = set()
        duplicates = []
        for v in af.object_variants:
            if v in seen and v not in duplicates:
                duplicates.append(v)
            seen.add(v)
        if duplicates:
            self.log_warning(
                f"environment.asteroid_field.object_variants contains duplicate entries "
                f"(ignored by FSO but redundant): {duplicates}"
            )

    def validate_asteroid_targets(self):
        af = self.mission.environment.asteroid_field
        if not af or not af.target_ships:
            return
            
        valid_ships = {s.name for s in self.mission.ships}
        for t in af.target_ships:
            if t not in valid_ships:
                self.log_error(f"Asteroid field target '{t}' does not exist.")
