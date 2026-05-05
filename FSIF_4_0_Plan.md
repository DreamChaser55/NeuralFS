## FSIF 4.0 clarity upgrade plan

I recommend a breaking version bump from `fsif_version: "3.0"` to `"4.0"`, with the converter accepting FSIF 4.0 only after the migration. This keeps the schema clean and avoids carrying aliases.

The guiding rule should be:

> FSIF field names should describe the author-facing mission concept. Documentation can mention the underlying `.fs2`/FRED field name, but the YAML key should not be confusing just because FSO uses confusing terminology.

---

## Proposed FSIF 4.0 renames

### Environment

| Current FSIF 3.0 | Proposed FSIF 4.0 | Why |
|---|---|---|
| `environment.starbitmaps` | `environment.background_bitmaps` | The list contains nebula backdrops and planets too, not only stars. |
| `environment.nebula.awacs` | `environment.nebula.sensor_range` | Describes the gameplay effect in full nebula missions. |
| `environment.nebula.poofs` | `environment.nebula.cloud_sprites` | “Poofs” is FSO jargon; “cloud sprites” explains what they are. |
| `environment.asteroid_field.genre` | `environment.asteroid_field.object_type` | Selects `asteroid` vs `debris`; “genre” is vague. |
| `environment.asteroid_field.type` | `environment.asteroid_field.behavior` | Selects `active` vs `passive`; “type” is too generic. |
| `environment.asteroid_field.debris_types` | `environment.asteroid_field.object_variants` | Applies to field visuals/objects even when the field is asteroid-based. |
| `environment.asteroid_field.targets` | `environment.asteroid_field.target_ships` | Makes clear these must be ship names and only matter for active asteroid fields. |

### Player setup

| Current | Proposed | Why |
|---|---|---|
| `player_setup.extra_ships` | `player_setup.additional_ship_choices` | More accurately describes loadout-screen alternatives. |
| `player_setup.extra_weapons` | `player_setup.additional_weapons` | More accurately describes extra loadout weapons added to the Weaponry Pool. |

### Ships and wings

| Current | Proposed | Why |
|---|---|---|
| `ships[*].location` | `ships[*].position` | Consistent with wings/jump nodes and more natural for authors. |
| `ships[*].arrival_location` / `wings[*].arrival_location` | `arrival_method` | Values like `Hyperspace`, `Docking Bay`, `In front of ship` describe how/where arrival occurs, not a coordinate location. |
| `ships[*].departure_location` / `wings[*].departure_location` | `departure_method` | Same rationale. |
| `ai_goals` | `initial_orders` | Avoids confusion with mission goals; describes initial AI orders. |
| `initial_velocity` | `initial_speed_percent` | Converter model constrains this to `0..100`; this is not meters/second. |
| `initial_hull` | `initial_hull_percent` | Makes units explicit. |
| `escort_priority` | `escort_list_priority` | Clarifies this controls HUD escort list ordering/importance and requires the `escort` flag. |
| `destroy_before_mission` | `destroyed_before_mission_seconds` | Explains the unit and function. |
| `weapons.secondary_ammo` | `weapons.secondary_ammo_counts` | Makes clear it is ordered per secondary bank. |
| `dock.with` | `dock.dockee` | The dock block is authored on the docker; the other ship is the dockee. |

I would keep `arrival_anchor`, `arrival_distance`, `arrival_delay`, `departure_anchor`, and `departure_delay` because those are already reasonably clear once paired with `arrival_method`/`departure_method`.

### Wing wave fields

| Current | Proposed | Why |
|---|---|---|
| `wings[*].waves` | `wave_count` | Avoids confusion with ship count. |
| `wings[*].wave_threshold` | `next_wave_threshold` | Explains it controls when the next wave can arrive. |
| `wings[*].wave_delay_min` | `next_wave_delay_min` | Clearer trigger relationship. |
| `wings[*].wave_delay_max` | `next_wave_delay_max` | Clearer trigger relationship. |
| `wings[*].spacing` | `member_spacing` | Clarifies it spaces wing members, not mission objects generally. |

### Mission flow

| Current | Proposed | Why |
|---|---|---|
| `events[*].directive_text` | `events[*].hud_directive_text` | Clearly maps to the HUD Directives list. |
| `goals[*].message` | `goals[*].objective_text` | Avoids confusion with comms messages. |
| `messages[*].message` | `messages[*].text` | Cleaner: message object has `name` and displayed `text`. |
| `debriefing.stages[*].condition` | `display_condition` | Explains that the debrief stage displays only when the SEXP is true. |

### Briefing icons

| Current | Proposed | Why |
|---|---|---|
| `icons[*].type` | `icon_type` | Avoids a generic `type` key; controls silhouette. |
| `icons[*].class` | `display_class` | Clarifies this controls selected-icon ship class display, not the icon silhouette. |
| `icons[*].pos` | `map_position` | Clarifies this is 2D briefing-map `[x, z]`, not a 3D mission position. |

### Reinforcements

| Current | Proposed | Why |
|---|---|---|
| `num_times` | `max_uses` | Clear author-facing meaning. |
| `yes_messages` | `available_messages` | Explains these are used when reinforcement is available/accepted. |
| `no_messages` | `unavailable_messages` | Explains these are used when reinforcement cannot be used. |

---

## Fields I would keep and explain rather than rename

Some names are already clear or valuable because they align with FreeSpace concepts:

- `mission_info.flags`
- `mission_info.ai_profile`
- `environment.ambient_light_level`
- `suns[*].angles`
- `briefing.stages[*].camera_time` — add units/meaning note only
- `ship_templates`
- `class` on ships/templates — FSO ship class is a core concept
- `team`
- `cargo` — add note that this is the ship cargo label revealed/scanned, not a docked cargo object
- `flags`
- `subsystems` — maybe refine later, but not essential for this clarity pass
- `voice_name` / `voice_style_instructions`
- `tts_provider`

---

## Implementation plan for Act mode

### 1. Bump FSIF to 4.0
Update:

- `Documentation/fsif/specification.md`
- `Documentation/fsif/migration-guide.md`
- `FSIF_to_FS2_Converter/README.md`
- `Documentation/fsif/converter/cli.md` if it mentions supported versions
- `FSIF_to_FS2_Converter/mission_loader.py` version validation

### 2. Update converter schema and loader
Modify:

- `FSIF_to_FS2_Converter/data_models.py`
- `FSIF_to_FS2_Converter/mission_loader.py`

### 3. Update writer and validators
Modify all references in:

- `FSIF_to_FS2_Converter/fs2_writer.py`
- `FSIF_to_FS2_Converter/validator/ascii_checks.py`
- `FSIF_to_FS2_Converter/validator/briefing.py`
- `FSIF_to_FS2_Converter/validator/environment.py`
- `FSIF_to_FS2_Converter/validator/ship_wing_checks.py`
- `FSIF_to_FS2_Converter/validator/spatial.py`
- `FSIF_to_FS2_Converter/validator/sexp_checks.py`
- `FSIF_to_FS2_Converter/validator/misc.py`
- `FSIF_to_FS2_Converter/validate_sexp_scalar_styles.py`
- `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/advanced_sexp_validator.py`

### 4. Update all docs and examples
Modify documentation:

- `Documentation/fsif/specification.md`
- `Documentation/fsif/authoring-guide.md`
- `Documentation/fsif/converter/implementation_details.md`
- `Documentation/FSO and fs2 format/FSO_Tokens_Reference.md`

Modify demo missions:

- `missions/Demo_missions/*.fsif`

Note: Do **not** upgrade the Vega Requiem missions; this is a large task that will be done later.

### 5. Add migration-guide section
Add a prominent FSIF 3.0 → 4.0 table with before/after snippets for major renamed sections:

- environment backgrounds/nebula/asteroid field
- ship arrival/departure/orders
- wing waves
- events/goals/messages
- briefing icons
- reinforcements

### 6. Validate
Run conversions for demo missions, at minimum:

```cmd
python FSIF_to_FS2_Converter\fsif_to_fs2.py "missions\Demo_missions\general_demo.fsif"
python FSIF_to_FS2_Converter\fsif_to_fs2.py "missions\Demo_missions\evacuation_demo.fsif"
python FSIF_to_FS2_Converter\fsif_to_fs2.py "missions\Demo_missions\subspace_demo.fsif"
python FSIF_to_FS2_Converter\fsif_to_fs2.py "missions\Demo_missions\nebula_demo.fsif"
```

If tests exist and are practical, run the relevant converter tests too.

---

## Updated success criteria

The FSIF 4.0 clarity pass is complete when:

- The schema accepts only `fsif_version: "4.0"`.
- Poorly named external YAML fields are replaced with clearer names, internal variable names are replaced to match.
- Docs explain any remaining FSO-specific terms.
- Demo missions use the new field names and convert successfully.
- Migration guide includes clear 3.0 → 4.0 instructions.