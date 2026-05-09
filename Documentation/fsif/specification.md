# FSIF Specification

## Status
- FSIF version: 1.0 (current)
- Scope: Field shapes, required/optional keys, defaults, constraints. This is the canonical contract for authoring FSIF.
- Not in scope: Converter implementation details, extended examples/tutorials, exhaustive FSO operator catalogs.
- This file is the single source of truth for FSIF. Non-normative details will remain in the Authoring Guide and Converter Implementation Details.

## Token fidelity requirement
- Author only the canonical tokens enumerated in this spec or linked references. Do not invent synonyms, alternative casing, or punctuation variants.
- FSIF embeds SEXP strings verbatim; operator names, wildcard literals (e.g., "<any friendly player>"), and message priorities ("Low", "Normal", "High") must match exactly.

## FSIF document structure

- `fsif_version` (String, required): Must be `"1.0"`.
- `mission_info` (Mapping, required):
  - `name` (String, required)
  - `author` (String, optional, default: `"FSIF Converter"`)
  - `description` (String, optional, default: `"No description provided."`)
  - `game_type` (String, optional, default: `"single"`). Enum: `"single"`, `"multiplayer"`, `"training"`.
  - `flags` (List[String], optional, default: `[]`)
  - `disallow_support_ships` (Boolean, optional, default: `false`)
  - `ai_profile` (String, optional, default: `"FS1 RETAIL"`)
- `environment` (Mapping, required):
  - `ambient_light_level` (List[Integer], required). Format: `[red, green, blue]`, each channel `0..255`.
  - `suns` (List[Mapping], optional, default: `[]`):
    - `texture` (String, required)
    - `angles` (List[Float], required). Format: `[pitch, heading]`. Bank is omitted because sun sprites are rotationally symmetric.
    - `scale` (Float, optional, default: `1.0`)
  - `background_bitmaps` (List[Mapping], optional, default: `[]`):
    - `texture` (String, required)
    - `angles` (List[Float], required). Format: `[pitch, bank, heading]`.
    - `scale` (Float or Mapping `{x, y}`, optional, default: `1.0`)
  - `nebula` (Mapping, optional):
    - `enabled` (Boolean, optional, default: `false`)
    - `pattern` (String, optional). Background color pattern. If omitted while `enabled` is `true`, FSO displays a completely black background with no stars.
    - `sensor_range` (Float, optional, default: `3000.0`). AWACS/sensor radius in meters for full-nebula missions.
    - `storm` (String, optional, default: `"none"`)
    - `cloud_sprites` (List[String], optional, default: `[]`). FSO nebula poof sprite names.
  - `asteroid_field` (Mapping, optional):
    - `object_type` (String, optional, default: `"asteroid"`). Enum: `"asteroid"`, `"debris"`. Selects the visual object genre of the field.
    - `behavior` (String, optional, default: `"passive"`). Enum: `"active"`, `"passive"`. Active fields track and strike ships; passive fields drift freely.
    - `num_objects` (Integer, optional, default: `50`)
    - `average_speed` (Float, optional, default: `20.0`)
    - `bounds` (Mapping, optional). Keys: `min`, `max` (Vectors). Default: `min: [-1000, -1000, -1000]`, `max: [1000, 1000, 1000]`.
    - `object_variants` (List[String], optional). Visual variant names. Defaults depend on `object_type`. Must not be empty — omit to get the full default set for the selected `object_type`. Allowed values are mutually incompatible between the two field types.
    - `target_ships` (List[String], optional, default: `[]`). Ship names the field will actively pursue. Active fields only.
- `player_setup` (Mapping, required):
  - `start_ship` (String, required)
  - `additional_ship_choices` (List[Mapping], optional, default: `[]`). Items: `{class: String, count: Integer}`. Loadout-screen alternative ship pool.
  - `additional_weapons` (List[String], optional, default: `[]`). Extra weapons added to the Weaponry Pool for the loadout screen.
- `entities` (Mapping, required):
  - `ship_templates` (Mapping, optional). Keys are template names, values are ship properties mappings.
  - `ships` (List[Mapping], optional). See Ship Properties below.
  - `wings` (List[Mapping], optional). See Wing Properties below.
  - `waypoints` (Mapping, optional). Keys are path names, values are Lists of `[x,y,z]`.
  - `reinforcement_wings` (List[Mapping], optional):
    - `name` (String, required)
    - `max_uses` (Integer, optional, default: `1`). Maximum number of times this reinforcement can be called.
    - `arrival_delay` (Integer, optional, default: `0`)
    - `unavailable_messages` (List[String], optional). Messages played when reinforcement cannot be called.
    - `available_messages` (List[String], optional). Messages played when reinforcement is called and accepted.
  - `reinforcement_ships` (List[Mapping], optional). Same structure as `reinforcement_wings`.
  - `jump_nodes` (List[Mapping], optional):
    - `name` (String, required)
    - `position` (List[Float], required). Format: `[x, y, z]`.
- `mission_flow` (Mapping, required):
  - `fiction_viewer` (String, optional): Filename of the text file to display.
  - `events` (List[Mapping], optional):
    - `name` (String, optional)
    - `formula` (String, required). SEXP.
    - `hud_directive_text` (String, optional). Text shown in the HUD Directives list.
  - `goals` (List[Mapping], optional):
    - `name` (String, required)
    - `type` (String, optional, default: `"Primary"`). Enum: `"Primary"`, `"Secondary"`, `"Bonus"`.
    - `objective_text` (String, required). Text shown in the Goals menu.
    - `formula` (String, required). SEXP.
  - `messages` (List[Mapping], optional):
    - `name` (String, required)
    - `text` (String, required). The displayed/spoken message text.
    - `voice_name` (String, optional)
    - `voice_style_instructions` (String, optional)
  - `briefing` (Mapping, optional):
    - `stages` (List[Mapping], optional):
      - `text` (String, required)
      - `voice_name` (String, optional)
      - `voice_style_instructions` (String, optional)
      - `camera_time` (Integer, optional, default: `500`)
      - `icons` (List[Mapping], optional):
        - `icon_type` (String, required). Canonical briefing icon type string. See Tokens Reference.
        - `team` (String, required). Enum: `"Friendly"`, `"Hostile"`, `"Unknown"`.
        - `map_position` (List[Float], optional, default: `[0, 0]`). Format: `[x, z]` on the briefing map.
        - `label` (String, optional)
        - `display_class` (String, conditionally required). Ship class shown when icon is selected in-game.
          - **Ship icon types** (e.g., `"Fighter"`, `"Cruiser"`, `"Capital Ship"`, `"Transport"`, etc.): **required**. Must be a valid ship class from `spacecraft-classes.md`. Must not be `"Terran NavBuoy"`.
          - **Non-ship icon types** (`"Waypoint"`, `"Jump Node"`, `"Planet"`, `"Small Planet"`, `"Asteroid Field"`, `"Unknown"`, `"Unknown Wing"`): **must be omitted**. The converter automatically uses the safe default `"Terran NavBuoy"` for these icon types.
        - `highlighted` (Boolean, optional, default: `false`)
  - `debriefing` (Mapping, optional):
    - `stages` (List[Mapping], optional). Fields: `text`, `voice_name`, `voice_style_instructions`, `display_condition` (SEXP, required), `recommendation`.
  - `command_briefing` (Mapping, optional):
    - `stages` (List[Mapping], optional). Fields: `text`, `voice_name`, `voice_style_instructions`.
- `audio` (Mapping, optional):
  - `mission_music` (String, optional)
  - `briefing_music` (String, optional)
  - `tts_provider` (String, optional). Specifies the Text-to-Speech provider for the mission. Valid options: `"google"`, `"elevenlabs"`, `"inworld"`, `"none"`. Defaults to `"none"` if unspecified.

**Ship Properties:**
- `name` (String, required for `ships`)
- `template` (String, optional). Name of a template defined in `ship_templates`.
- `class` (String, required)
- `team` (String, required). Enum: `"Friendly"`, `"Hostile"`.
- `position` (List[Float], required for `ships`). Format: `[x, y, z]`. World-space spawn location.
- `orientation` (List[Float], optional, default: Identity matrix). Format: 9 floats.
- `ai_class` (String, optional)
- `cargo` (String, optional, default: `"Nothing"`)
- `initial_speed_percent` (Integer, optional, default: `33`). Ship speed at spawn as a percentage (0–100).
- `initial_hull_percent` (Integer, optional, default: `100`). Starting hull integrity as a percentage (0–100).
- `arrival_method` (String, optional, default: `"Hyperspace"`). Enum: `"Hyperspace"`, `"Docking Bay"`, `"Near Ship"`, `"In front of ship"`, `"In back of ship"`, `"Above ship"`, `"Below ship"`, `"To left of ship"`, `"To right of ship"`.
- `arrival_anchor` (String, optional)
- `arrival_distance` (Integer, optional)
- `arrival_cue` (String, optional, default: `"( false )"`). SEXP. Boolean condition that triggers arrival.
- `arrival_delay` (Integer, optional, default: `0`)
- `departure_method` (String, optional, default: `"Hyperspace"`). Enum: `"Hyperspace"`, `"Docking Bay"`.
- `departure_anchor` (String, optional)
- `departure_delay` (Integer, optional, default: `0`)
- `departure_cue` (String, optional, default: `"( false )"`). SEXP.
- `flags` (List[String], optional, default: `["cargo-known"]`)
- `respawn_priority` (Integer, optional, default: `0`)
- `subsystems` (Mapping, optional). Keys: `status` (`"all_ok"` or `"custom"`), `list` (List of `{name, health}`).
- `weapons` (Mapping, optional). Keys: `primary` (List), `secondary` (List), `secondary_ammo_counts` (List[Integer]). `secondary_ammo_counts` gives per-bank ammo overrides, ordered to match the `secondary` list.
- `dock` (Mapping, optional). Keys: `dockee` (name of the ship being docked to), `docker_point`, `dockee_point`.
- `initial_orders` (String, optional). SEXP. Initial AI orders assigned at mission start. FSO SEXP docs commonly refer to these as "AI goals".
- `escort_list_priority` (Integer, optional, default: `0`). Controls ordering/importance in the HUD escort list. Requires the `escort` flag.
- `destroyed_before_mission_seconds` (Integer, optional, default: `0`). Seconds before mission start when the ship is destroyed to create pre-placed wreckage. `0` means normal spawning.

**Wing Properties:**
- `name` (String, required)
- `template` (String, required). Name of a template defined in `ship_templates`.
- `count` (Integer, required). Number of ships in the wing.
- `position` (List[Float], required). Format: `[x, y, z]`. Centroid of the wing's spawn line.
- `wave_count` (Integer, optional, default: `1`). Number of waves for this wing.
- `next_wave_threshold` (Integer, optional, default: `0`). Minimum surviving ships before the next wave spawns.
- `next_wave_delay_min` (Integer, optional). Minimum delay in seconds before next wave.
- `next_wave_delay_max` (Integer, optional). Maximum delay in seconds before next wave.
- `arrival_method` (String, optional, default: `"Hyperspace"`). Enum: `"Hyperspace"`, `"Docking Bay"`, `"Near Ship"`, `"In front of ship"`, `"In back of ship"`, `"Above ship"`, `"Below ship"`, `"To left of ship"`, `"To right of ship"`.
- `arrival_anchor` (String, optional)
- `arrival_distance` (Integer, optional)
- `arrival_cue` (String, optional, default: `"( true )"`). SEXP. Boolean condition that triggers arrival.
- `arrival_delay` (Integer, optional, default: `0`). Starts to tick after the arrival condition becomes true.
- `departure_method` (String, optional, default: `"Hyperspace"`). Enum: `"Hyperspace"`, `"Docking Bay"`.
- `departure_anchor` (String, optional)
- `departure_cue` (String, optional, default: `"( false )"`). SEXP.
- `departure_delay` (Integer, optional, default: `0`). Starts to tick after the departure condition becomes true.
- `initial_orders` (String, optional). SEXP. Initial AI orders for wing members. FSO SEXP docs commonly refer to these as "AI goals".
- `flags` (List[String], optional, default: `[]`).
- `member_spacing` (Float, optional, default: `50.0`). Distance in meters between adjacent wing members.

## Minimal FSIF skeleton
- Minimal and standard FSIF skeletons are provided in the Authoring Guide.

## Section details
1. mission_info
  - Flags are authored as names; unknown flags are ignored.
  - Subspace missions: use the `"subspace"` flag.
2. environment
  - `ambient_light_level` is authored as `[red, green, blue]` with integer channels in range `0..255`.
  - Sun `angles` are ordered as `[pitch, heading]` in radians. Bank is excluded because sun sprites are rotationally symmetric.
  - Background bitmap `angles` are ordered as `[pitch, bank, heading]` in radians.
  - Only one asteroid/debris field is allowed per mission.
3. player_setup
  - If the `start_ship` is standalone (not in a wing), its `arrival_cue` must be `"( true )"`.
4. entities
  - ship_templates: Any allowed shared property present in a template can be overridden on ships referencing it. Override semantics are **shallow**: a top-level key on the ship replaces the entire value from the template, so nested mappings such as `weapons` and `subsystems` are replaced wholesale — to override only `weapons.primary`, you must re-specify the complete `weapons` block. Ships in wings are defined solely by the referenced template (overrides are not supported on wing definitions).
    - **Important Note:** The following fields are **not allowed** in ship templates and must be authored elsewhere (in the ships themselves or in wings referencing the template): `arrival_method`, `arrival_anchor`, `arrival_distance`, `arrival_delay`, `arrival_cue`, `departure_method`, `departure_anchor`, `departure_delay`, `departure_cue`, `initial_orders`, `dock`, `docked_with`, `docker_point`, `dockee_point`.
  - ships:
    - subsystems: Names must match the per-ship canonical lists.
    - docking: Author only on the docker under `dock.dockee`, `dock.docker_point`, `dock.dockee_point`; pairs only; player ships cannot be pre-spawn docked.
  - wings:
    - Reinforcement wings should omit `arrival_cue` (defaults to true) to remain callable.
    - wings must define `position` ([x,y,z]) as the centroid of the wing. Individual ship locations are computed as a straight line along the X axis centered on `position`, spaced `member_spacing` meters apart (default 50 m).
5. mission_flow
  - SEXPs are embedded verbatim.
  - `events[*].hud_directive_text` maps to an in-HUD directive.

## Constraints quicklist
- Player start spawning: standalone start_ship requires `arrival_cue: "( true )"`
- Docking: pairs only; not allowed for player start; author on docker only; ensure arrival leadership is coherent
- Author only canonical per-ship subsystem and dockpoint names (see references)
- Reinforcements: author them in `entities.reinforcement_wings` / `entities.reinforcement_ships`. The reinforcement type is determined automatically: support ships whose class starts with `"GTS "` or `"PVS "` become "Repair/Rearm" reinforcements; all other ships and wings become "Attack/Protect" reinforcements.
- Message priorities: `"Low"`, `"Normal"`, `"High"` (canonical spellings)
- Names used inside SEXPs must stay under the engine token length limit (fewer than 30 characters).
- Avoid YAML `#` comments inside SEXP blocks.

## Tokens and SEXPs:
- This spec intentionally does not replicate exhaustive FSO operator/token catalogs.
- For exact spelling of tokens, wildcards, music file names, background bitmaps, etc., consult ../FSO and fs2 format/FSO_Tokens_Reference.md.
- For an exhaustive catalog of FSO SEXPs, consult ../FSO SEXPs/INDEX.md.

### Notes about selected SEXPs:
- Applicability of AI Goals SEXPs:
  - Larger ships (cruisers, destroyers, utility) can only use: `ai-chase`, `ai-dock`, `ai-undock`, `ai-warp-out`, `ai-stay-near-ship`, `ai-stay-still`, `ai-play-dead`.
  - All other goals (fighter/bomber-only goals such as `ai-guard`) are invalid on larger ships and will cause FRED validation errors. Prefer waypoint/warp orders for capital ships, or give them no orders (turrets fire automatically).
  - Wing-target goal variants exist for common behaviors (e.g., `ai-guard-wing`, `ai-chase-wing`).
- `send-message-list` argument signature: `( "<sender>", "<priority>", "<msg>", <delay_ms>, ... repeated 4-tuples ... )`
  - Arguments are provided in groups of four; the total argument count **must** be a multiple of four. Each 4-tuple is one message.
