# FSIF Specification

## Status
- FSIF version: 3.0 (current)
- Scope: Field shapes, required/optional keys, defaults, constraints. This is the canonical contract for authoring FSIF.
- Not in scope: Converter implementation details, extended examples/tutorials, exhaustive FSO operator catalogs.
- This file is the single source of truth for FSIF. Non-normative details will remain in the Authoring Guide and Converter Implementation Details.

## Token fidelity requirement
- Author only the canonical tokens enumerated in this spec or linked references. Do not invent synonyms, alternative casing, or punctuation variants.
- FSIF embeds SEXP strings verbatim; operator names, wildcard literals (e.g., "<any friendly player>"), and message priorities ("Low", "Normal", "High") must match exactly.

## FSIF document structure

- `fsif_version` (String, required): Must be `"3.0"`.
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
    - `angles` (List[Float], required). Format: `[pitch, bank, heading]`.
    - `scale` (Float, optional, default: `1.0`)
  - `starbitmaps` (List[Mapping], optional, default: `[]`):
    - `texture` (String, required)
    - `angles` (List[Float], required). Format: `[pitch, bank, heading]`.
    - `scale` (Float or Mapping `{x, y}`, optional, default: `1.0`)
  - `nebula` (Mapping, optional):
    - `enabled` (Boolean, optional, default: `false`)
    - `pattern` (String, required if `enabled` is `true`)
    - `awacs` (Float, optional, default: `3000.0`)
    - `storm` (String, optional, default: `"s_standard"`)
    - `poofs` (List[String], optional, default: `[]`)
  - `asteroid_field` (Mapping, optional):
    - `genre` (String, optional, default: `"asteroid"`). Enum: `"asteroid"`, `"debris"`.
    - `type` (String, optional, default: `"passive"`). Enum: `"active"`, `"passive"`.
    - `density` (Integer, optional, default: `50`)
    - `average_speed` (Float, optional, default: `20.0`)
    - `bounds` (Mapping, optional). Keys: `min`, `max` (Vectors). Default: `min: [-1000, -1000, -1000]`, `max: [1000, 1000, 1000]`.
    - `debris_types` (List[String], optional). Defaults depend on `genre`.
    - `targets` (List[String], optional, default: `[]`). Active fields only.
- `player_setup` (Mapping, required):
  - `start_ship` (String, required)
  - `extra_ships` (List[Mapping], optional, default: `[]`). Items: `{class: String, count: Integer}`.
  - `extra_weapons` (List[String], optional, default: `[]`). Additional weapons to include in the Weaponry Pool.
- `entities` (Mapping, required):
  - `ship_templates` (Mapping, optional). Keys are template names, values are ship properties mappings.
  - `ships` (List[Mapping], optional). See Ship Properties below.
  - `wings` (List[Mapping], optional):
    - `name` (String, required)
    - `template` (String, required)
    - `count` (Integer, required)
    - `position` (List[Float], required). Format: `[x, y, z]`.
    - `waves` (Integer, optional, default: `1`)
    - `wave_threshold` (Integer, optional, default: `0`)
    - `wave_delay_min` (Integer, optional)
    - `wave_delay_max` (Integer, optional)
    - `arrival_delay` (Integer, optional, default: `0`)
    - `arrival_anchor` (String, optional)
    - `arrival_distance` (Integer, optional)
    - `arrival_cue` (String, optional). SEXP.
    - `departure_location` (String, optional, default: `"Hyperspace"`)
    - `departure_anchor` (String, optional)
    - `departure_cue` (String, optional, default: `"( false )"`). SEXP.
    - `ai_goals` (String, optional).
    - `flags` (List[String], optional, default: `[]`).
    - `spacing` (Float, optional, default: `50.0`)
  - `waypoints` (Mapping, optional). Keys are path names, values are Lists of `[x,y,z]`.
  - `reinforcement_wings` (List[Mapping], optional):
    - `name` (String, required)
    - `num_times` (Integer, optional, default: `1`)
    - `arrival_delay` (Integer, optional, default: `0`)
    - `no_messages` (List[String], optional)
    - `yes_messages` (List[String], optional)
  - `reinforcement_ships` (List[Mapping], optional). Same structure as `reinforcement_wings`.
  - `jump_nodes` (List[Mapping], optional):
    - `name` (String, required)
    - `position` (List[Float], required). Format: `[x, y, z]`.
- `mission_flow` (Mapping, required):
  - `fiction_viewer` (String, optional): Filename of the text file to display.
  - `events` (List[Mapping], optional):
    - `name` (String, optional)
    - `formula` (String, required). SEXP.
    - `directive_text` (String, optional)
  - `goals` (List[Mapping], optional):
    - `name` (String, required)
    - `type` (String, optional, default: `"Primary"`). Enum: `"Primary"`, `"Secondary"`, `"Bonus"`.
    - `message` (String, required)
    - `formula` (String, required). SEXP.
  - `messages` (List[Mapping], optional):
    - `name` (String, required)
    - `message` (String, required)
    - `voice_name` (String, optional)
    - `voice_style_instructions` (String, optional)
  - `briefing` (Mapping, optional):
    - `stages` (List[Mapping], optional):
      - `text` (String, required)
      - `voice_name` (String, optional)
      - `voice_style_instructions` (String, optional)
      - `camera_time` (Integer, optional, default: `500`)
      - `icons` (List[Mapping], optional):
        - `type` (String, required). See Tokens Reference.
        - `team` (String, required). Enum: `"Friendly"`, `"Hostile"`, `"Unknown"`.
        - `pos` (List[Float], optional, default: `[0, 0]`). Format: `[x, z]`.
        - `label` (String, optional)
        - `class` (String, optional, default: `"Terran NavBuoy"`). Ship class name.
        - `highlighted` (Boolean, optional, default: `false`)
  - `debriefing` (Mapping, optional):
    - `stages` (List[Mapping], optional). Fields: `text`, `voice_name`, `voice_style_instructions`, `condition` (SEXP, required), `recommendation`.
  - `command_briefing` (Mapping, optional):
    - `stages` (List[Mapping], optional). Fields: `text`, `voice_name`, `voice_style_instructions`, `ani` (default `"<default>"`).
- `audio` (Mapping, optional):
  - `mission_music` (String, optional)
  - `briefing_music` (String, optional)
  - `tts_provider` (String, optional). Specifies the Text-to-Speech provider for the mission. Valid options: `"google"`, `"elevenlabs"`, `"inworld"`, `"none"`. Defaults to `"none"` if unspecified.

**Ship Properties:**
- `name` (String, required for `ships`)
- `template` (String, optional). Name of a template defined in `ship_templates`.
- `class` (String, required)
- `team` (String, required). Enum: `"Friendly"`, `"Hostile"`.
- `location` (List[Float], required for `ships`). Format: `[x, y, z]`.
- `orientation` (List[Float], optional, default: Identity matrix). Format: 9 floats.
- `ai_class` (String, optional)
- `cargo` (String, optional, default: `"Nothing"`)
- `initial_velocity` (Integer, optional, default: `33`)
- `initial_hull` (Integer, optional, default: `100`)
- `arrival_location` (String, optional, default: `"Hyperspace"`)
- `arrival_anchor` (String, optional)
- `arrival_distance` (Integer, optional)
- `arrival_cue` (String, optional, default: `"( false )"`). SEXP.
- `arrival_delay` (Integer, optional, default: `0`)
- `departure_location` (String, optional, default: `"Hyperspace"`)
- `departure_anchor` (String, optional)
- `departure_cue` (String, optional, default: `"( false )"`). SEXP.
- `flags` (List[String], optional, default: `["cargo-known"]`)
- `respawn_priority` (Integer, optional, default: `0`)
- `subsystems` (Mapping, optional). Keys: `status` (`"all_ok"` or `"custom"`), `list` (List of `{name, health}`).
- `weapons` (Mapping, optional). Keys: `primary` (List), `secondary` (List), `secondary_ammo` (List[Integer]).
- `dock` (Mapping, optional). Keys: `with`, `docker_point`, `dockee_point`.
- `ai_goals` (String, optional).
- `escort_priority` (Integer, optional, default: `0`)
- `destroy_before_mission` (Integer, optional, default: `0`)

## Minimal FSIF skeleton
- A minimal and a standard FSIF skeletons are provided in the Authoring Guide.

## Section details
1. mission_info
  - Flags are authored as names; unknown flags are ignored.
  - Subspace missions: use the "subspace" flag.
2. environment
  - ambient_light_level is authored as `[red, green, blue]` with integer channels in range `0..255`.
  - Angles order is [pitch, bank, heading] in radians.
  - Only one asteroid/debris field is allowed.
3. player_setup
  - If the start_ship is standalone (not in a wing), its ships[*].arrival_cue must be "( true )".
4. entities
  - ship_templates: Any allowed shared property present in a template can be overridden on ships referencing it. Override semantics are **shallow**: a top-level key on the ship replaces the entire value from the template, so nested mappings such as `weapons` and `subsystems` are replaced wholesale — to override only `weapons.primary`, you must re-specify the complete `weapons` block. Ships in wings are defined solely by the referenced template (overrides are not supported on wing definitions).
    - **Important Note:** The following fields are **not allowed** in ship templates and must be authored elsewhere (in the ships themselves or in wings referencing the template): `arrival_location`, `arrival_anchor`, `arrival_distance`, `arrival_delay`, `arrival_cue`, `departure_location`, `departure_anchor`, `departure_cue`, `ai_goals`, `dock`, `docked_with`, `docker_point`, `dockee_point`.
  - ships:
    - subsystems: Names must match the per-ship canonical lists.
    - docking: Author only on the docker under dock.with, dock.docker_point, dock.dockee_point; pairs only; player ships cannot be pre-spawn docked.
  - wings:
    - Reinforcement wings should omit arrival_cue (defaults to true) to remain callable.
    - wings must define position ([x,y,z]) as the centroid of the wing. Individual ship locations are computed as a straight line along the X axis centered on position, spaced 50 m apart by default.
5. mission_flow
  - SEXPs are embedded verbatim.
  - events[*].directive_text maps to an in-HUD directive.

## Constraints quicklist
- Player start spawning: standalone start_ship requires arrival_cue "( true )"
- Docking: pairs only; not allowed for player start; author on docker only; ensure arrival leadership is coherent
- Author only canonical per-ship subsystem and dockpoint names (see references)
- Reinforcements: author in entities.reinforcement_wings / entities.reinforcement_ships. The reinforcement type is determined automatically (support ships with classes starting "GTS "/"PVS " → "Repair/Rearm"; all other ships and wings → "Attack/Protect").
- Message priorities: "Low", "Normal", "High" (canonical spellings)
- Names used inside SEXPs must remain under engine token length limits (less than 30 chars)
- avoid YAML "#" inside SEXP blocks

## Tokens and SEXPs:
- This spec intentionally does not replicate exhaustive FSO operator/token catalogs.
- For exact spelling of tokens, wildcards, music file names, background bitmaps, etc., consult ../FSO and fs2 format/FSO_Tokens_Reference.md.
- For an exhaustive catalog of FSO SEXPs, consult ../FSO SEXPs/INDEX.md.

### Notes about selected SEXPs:
- Applicability of AI Goals SEXPs:
  - Larger ships (cruisers, destroyers, utility) can only use: ai-chase, ai-dock, ai-undock, ai-warp-out, ai-stay-near-ship, ai-stay-still, ai-play-dead.
  - All other goals (Fighter/bomber-only goals like ai-guard) are invalid on larger ships and will cause FRED validation errors. Prefer waypoint/warp orders for capitals, or give them no orders (turrets fire automatically).
  - Wing-target goal variants exist for common behaviors (e.g., ai-guard-wing, ai-chase-wing).
- send-message-list argument signature: ( "<sender>", "<priority>", "<msg>", <delay_ms>, ... repeated 4-tuples ... )
  - Arguments are provided in groups of four and the total argument count MUST be a multiple of four. Each 4-tuple is one message.
