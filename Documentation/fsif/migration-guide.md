# FSIF Migration Guide (1.0 → ... → 4.0)

Purpose
- Practical, snippet-led instructions to update existing FSIF files to the latest spec and converter expectations.
- Covers breaking changes and notable behavior shifts.

Status
- Current FSIF version: 4.0. The converter accepts FSIF 4.0 only; use this guide to update older FSIF files to the 4.0 schema before converting.

---

FSIF 4.0: Field clarity pass (breaking)

Change
- 36 FSIF field names have been renamed for improved clarity and consistency. The guiding rule: FSIF field names should describe the author-facing mission concept. The old 3.0 names were often inherited from FSO internal jargon (e.g. `awacs`, `poofs`, `arrival_cue`) or too generic (e.g. `type`, `condition`). The new 4.0 names are longer but self-documenting.
- `fsif_version` must now be `"4.0"`.

Full rename table

| Section | Old name (3.0) | New name (4.0) | Why |
|---|---|---|---|
| `environment` | `starbitmaps` | `background_bitmaps` | Contains nebula backdrops and planets, not only stars. |
| `environment.nebula` | `awacs` | `sensor_range` | Describes the gameplay effect (sensor radius). |
| `environment.nebula` | `poofs` | `cloud_sprites` | FSO jargon; "cloud sprites" explains what they are. |
| `environment.asteroid_field` | `genre` | `object_type` | Selects asteroid vs. debris; "genre" is vague. |
| `environment.asteroid_field` | `type` | `behavior` | Selects active vs. passive; "type" is too generic. |
| `environment.asteroid_field` | `debris_types` | `object_variants` | Applies to all field visuals, not just debris. |
| `environment.asteroid_field` | `targets` | `target_ships` | Makes clear these must be ship names. |
| `player_setup` | `extra_ships` | `additional_ship_choices` | More accurately describes loadout-screen alternatives. |
| `player_setup` | `extra_weapons` | `additional_weapons` | More accurately describes loadout-screen weapons. |
| Ship properties | `location` | `position` | Consistent with wings/jump nodes; more natural. |
| Ship/Wing properties | `arrival_location` | `arrival_method` | Values describe how arrival occurs, not a coordinate. |
| Ship/Wing properties | `arrival_cue` | `arrival_condition` | It is a Boolean SEXP condition, not a "cue". |
| Ship/Wing properties | `departure_location` | `departure_method` | Same rationale as `arrival_method`. |
| Ship/Wing properties | `departure_cue` | `departure_condition` | It is a Boolean SEXP condition, not a "cue". |
| Ship/Wing properties | `ai_goals` | `initial_orders` | Avoids confusion with mission goals. |
| Ship properties | `initial_velocity` | `initial_speed_percent` | Makes units explicit (0–100, not m/s). |
| Ship properties | `initial_hull` | `initial_hull_percent` | Makes units explicit (0–100). |
| Ship properties | `escort_priority` | `escort_list_priority` | Clarifies it controls HUD escort list ordering. |
| Ship properties | `destroy_before_mission` | `destroyed_before_mission_seconds` | Explains the unit and function. |
| `ships[*].weapons` | `secondary_ammo` | `secondary_ammo_counts` | Makes clear it is ordered per secondary bank. |
| `dock` block | `with` | `dockee` | The block is authored on the docker; the other ship is the dockee. |
| `entities.wings[*]` | `waves` | `wave_count` | Avoids confusion with ship count. |
| `entities.wings[*]` | `wave_threshold` | `next_wave_threshold` | Explains it controls when the next wave can arrive. |
| `entities.wings[*]` | `wave_delay_min` | `next_wave_delay_min` | Clearer trigger relationship. |
| `entities.wings[*]` | `wave_delay_max` | `next_wave_delay_max` | Clearer trigger relationship. |
| `entities.wings[*]` | `spacing` | `member_spacing` | Clarifies it spaces wing members, not general objects. |
| `entities.reinforcement_*[*]` | `num_times` | `max_uses` | Clear author-facing meaning. |
| `entities.reinforcement_*[*]` | `yes_messages` | `available_messages` | Explains when these messages are used. |
| `entities.reinforcement_*[*]` | `no_messages` | `unavailable_messages` | Explains when these messages are used. |
| `mission_flow.events[*]` | `directive_text` | `hud_directive_text` | Clearly maps to the HUD Directives list. |
| `mission_flow.goals[*]` | `message` | `objective_text` | Avoids confusion with comms messages. |
| `mission_flow.messages[*]` | `message` | `text` | Cleaner: message object has `name` and displayed `text`. |
| `debriefing.stages[*]` | `condition` | `display_condition` | Explains the stage displays only when the SEXP is true. |
| `briefing.stages[*].icons[*]` | `type` | `icon_type` | Avoids generic `type` key; controls icon silhouette. |
| `briefing.stages[*].icons[*]` | `class` | `display_class` | Clarifies this controls the selected-icon ship class display. |
| `briefing.stages[*].icons[*]` | `pos` | `map_position` | Clarifies this is 2D briefing-map `[x, z]`. |

Migration guidance
- Bump `fsif_version` to `"4.0"` in every `.fsif` file.
- Apply a find-and-replace for each renamed key in the table above. Most renames are unambiguous (e.g. `starbitmaps:` only appears once, at the top level of `environment`). Take care with `message:` → `text:` which only applies inside `mission_flow.messages[*]` items, not briefing stage `text:` fields (briefing stage `text:` is unchanged).
- Note for `dock.with` → `dock.dockee`: only the `with` sub-key inside the `dock:` block changes; `docker_point` and `dockee_point` are unchanged.

Before (3.0) — selected fields
```yaml
fsif_version: "3.0"

environment:
  starbitmaps:
    - texture: dneb03
      angles: [0.0, 2.32, 0.0]
  nebula:
    awacs: 3000.0
    poofs: ["neb01", "neb02"]
  asteroid_field:
    genre: "asteroid"
    type: "passive"
    debris_types: ["Asteroid Small", "Asteroid Medium"]
    targets: []

player_setup:
  start_ship: "Alpha 1"
  extra_ships:
    - { class: "GTF Ulysses", count: 4 }
  extra_weapons:
    - "Hornet"

entities:
  wings:
    - name: "Delta"
      template: "fighter"
      count: 4
      position: [0, 0, 500]
      waves: 2
      wave_threshold: 1
      wave_delay_min: 5
      wave_delay_max: 15
      spacing: 50.0
      arrival_location: "In front of ship"
      arrival_anchor: "GTC Fenris 1"
      arrival_distance: 1500
      arrival_cue: |
        ( true )
      ai_goals: |
        ( ai-chase-any 60 )
  reinforcement_wings:
    - name: "Epsilon"
      num_times: 2
      no_messages: ["Epsilon busy"]
      yes_messages: ["Epsilon inbound"]
  ships:
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      location: [0, 0, 800]
      initial_velocity: 33
      initial_hull: 85
      destroy_before_mission: 0
      arrival_location: "Hyperspace"
      arrival_cue: |
        ( true )
      departure_location: "Hyperspace"
      departure_cue: |
        ( has-departed-delay 0 "GTC Fenris 1" )
      escort_priority: 90
      ai_goals: |
        ( ai-waypoints-once "Path" 89 )
      weapons:
        secondary: ["MX-50"]
        secondary_ammo: [40]
      dock: {}  # (not shown here for brevity)

mission_flow:
  events:
    - name: "dragon dead"
      formula: |
        ( when ( is-destroyed-delay 0 "SF Dragon 1" ) ( do-nothing ) )
      directive_text: "Destroy SF Dragon 1"
  goals:
    - name: "kill dragon"
      message: "Destroy SF Dragon 1"
      formula: |
        ( is-event-true-delay "dragon dead" 0 )
  messages:
    - name: "dragon warning"
      message: "Watch out for SF Dragon 1!"
  briefing:
    stages:
      - text: "Engage Dragon wing."
        icons:
          - { type: "Fighter", team: "Hostile", class: "SF Dragon", pos: [500, 200] }
  debriefing:
    stages:
      - condition: |
          ( is-destroyed-delay 0 "SF Dragon 1" )
        text: "Dragon wing destroyed."
```

After (4.0)
```yaml
fsif_version: "4.0"

environment:
  background_bitmaps:
    - texture: dneb03
      angles: [0.0, 2.32, 0.0]
  nebula:
    sensor_range: 3000.0
    cloud_sprites: ["neb01", "neb02"]
  asteroid_field:
    object_type: "asteroid"
    behavior: "passive"
    object_variants: ["Asteroid Small", "Asteroid Medium"]
    target_ships: []

player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - { class: "GTF Ulysses", count: 4 }
  additional_weapons:
    - "Hornet"

entities:
  wings:
    - name: "Delta"
      template: "fighter"
      count: 4
      position: [0, 0, 500]
      wave_count: 2
      next_wave_threshold: 1
      next_wave_delay_min: 5
      next_wave_delay_max: 15
      member_spacing: 50.0
      arrival_method: "In front of ship"
      arrival_anchor: "GTC Fenris 1"
      arrival_distance: 1500
      arrival_condition: |
        ( true )
      initial_orders: |
        ( ai-chase-any 60 )
  reinforcement_wings:
    - name: "Epsilon"
      max_uses: 2
      unavailable_messages: ["Epsilon busy"]
      available_messages: ["Epsilon inbound"]
  ships:
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      position: [0, 0, 800]
      initial_speed_percent: 33
      initial_hull_percent: 85
      destroyed_before_mission_seconds: 0
      arrival_method: "Hyperspace"
      arrival_condition: |
        ( true )
      departure_method: "Hyperspace"
      departure_condition: |
        ( has-departed-delay 0 "GTC Fenris 1" )
      escort_list_priority: 90
      initial_orders: |
        ( ai-waypoints-once "Path" 89 )
      weapons:
        secondary: ["MX-50"]
        secondary_ammo_counts: [40]
      dock:
        dockee: "GTT Elysium 1"      # 'with' → 'dockee'
        docker_point: "topside docking"
        dockee_point: "Docking bay 1"

mission_flow:
  events:
    - name: "dragon dead"
      formula: |
        ( when ( is-destroyed-delay 0 "SF Dragon 1" ) ( do-nothing ) )
      hud_directive_text: "Destroy SF Dragon 1"
  goals:
    - name: "kill dragon"
      objective_text: "Destroy SF Dragon 1"
      formula: |
        ( is-event-true-delay "dragon dead" 0 )
  messages:
    - name: "dragon warning"
      text: "Watch out for SF Dragon 1!"
  briefing:
    stages:
      - text: "Engage Dragon wing."
        icons:
          - { icon_type: "Fighter", team: "Hostile", display_class: "SF Dragon", map_position: [500, 200] }
  debriefing:
    stages:
      - display_condition: |
          ( is-destroyed-delay 0 "SF Dragon 1" )
        text: "Dragon wing destroyed."
```

---

FSIF 3.0: `environment.starbitmaps.div` removed (breaking)

Change
- The `div` field under `environment.starbitmaps` has been completely removed from the schema because the resulting `+DivX` and `+DivY` flags in modern FSO have no functional effect. The converter now hardcodes these values automatically when writing the `.fs2` file.

Migration guidance
- Find any `div` key inside the `environment.starbitmaps` list in your `.fsif` files and delete it.
- Bump `fsif_version` to `"3.0"`.

Before (2.9)
```yaml
fsif_version: "2.9"

environment:
  starbitmaps:
    - texture: dneb03
      angles: [0.000000, 2.321286, 0.000000]
      scale: { x: 4.0, y: 4.0 }
      div: { x: 2, y: 2 }
```

After (3.0)
```yaml
fsif_version: "3.0"

environment:
  starbitmaps:
    - texture: dneb03
      angles: [0.000000, 2.321286, 0.000000]
      scale: { x: 4.0, y: 4.0 }
```

---

FSIF 2.9: `jump_nodes` moved under `entities` (breaking)

Change
- The `jump_nodes` field has moved from the top level of the FSIF document into the `entities` section.
- This conceptually groups all object definitions (ships, wings, waypoints, and jump nodes) together.

Migration guidance
- Find any top-level `jump_nodes` key in your `.fsif` files and move it to be a sub-key of `entities`.
- Bump `fsif_version` to `"2.9"`.

Before (2.8)
```yaml
fsif_version: "2.8"

entities:
  ships: []

jump_nodes:
  - { name: "Delta Serpentis Jump Node", position: [3200.0, 0.0, 0.0] }
```

After (2.9)
```yaml
fsif_version: "2.9"

entities:
  ships: []
  jump_nodes:
    - { name: "Delta Serpentis Jump Node", position: [3200.0, 0.0, 0.0] }
```

---

FSIF 2.8: `fiction_viewer` moved under `mission_flow` (breaking)

Change
- The `fiction_viewer` field has moved from the top level of the FSIF document into the `mission_flow` section.
- This reflects chronological ordering: the fiction viewer is shown to the player **before** the Command Briefing, so it belongs in `mission_flow` alongside the other mission-flow content.

Migration guidance
- Find any top-level `fiction_viewer` key in your `.fsif` files and move it to be a sub-key of `mission_flow`.
- Bump `fsif_version` to `"2.8"`.

Before (2.7)
```yaml
fsif_version: "2.7"

fiction_viewer: "story.txt"

mission_info:
  name: "My Mission"
  # ...

mission_flow:
  command_briefing:
    stages: []
  # ...
```

After (2.8)
```yaml
fsif_version: "2.8"

mission_info:
  name: "My Mission"
  # ...

mission_flow:
  fiction_viewer: "story.txt"
  command_briefing:
    stages: []
  # ...
```

---

FSIF 2.7: Removal of full nebula background bitmaps (breaking)

Change
- The `show_backgrounds` property under `environment.nebula` has been removed.
- The `fullneb_background_bitmaps` mission flag is no longer supported.
- When full nebula is enabled (`environment.nebula.enabled: true`), starbitmaps are unconditionally suppressed and the validator will emit an error if any are authored. Background suns are still permitted and emitted.

Migration guidance
- Remove `show_backgrounds` from the `nebula` section.
- Remove `fullneb_background_bitmaps` from `mission_info.flags`.
- If your mission has full nebula enabled, remove all `starbitmaps` from the `environment` section.
- Bump `fsif_version` to `"2.7"`.

Before (2.6)
```yaml
mission_info:
  flags: ["fullneb_background_bitmaps"]
environment:
  starbitmaps:
    - { texture: dneb03, angles: [0, 0, 0] }
  nebula:
    enabled: true
    pattern: "nbackblue1"
    show_backgrounds: true
```

After (2.7)
```yaml
mission_info:
  flags: []
environment:
  starbitmaps: []
  nebula:
    enabled: true
    pattern: "nbackblue1"
```

---

FSIF 2.6: ambient_light_level changed from packed integer to RGB list (breaking)

Change
- The `environment.ambient_light_level` field is now authored as a standard RGB triplet instead of a packed integer.
- New syntax: `[red, green, blue]`, with each channel in range `0..255`.
- This makes the field match how ambient light is exposed in FRED and how authors naturally think about color.

Migration guidance
- Replace any integer `ambient_light_level` values with a 3-item list.
- If the old integer was intended as a neutral brightness value, migrate it to equal RGB channels. For example:
  - `10` → `[10, 10, 10]`
  - `5` → `[5, 5, 5]`
  - `20` → `[20, 20, 20]`
- Bump `fsif_version` to `"2.6"`.

Before (2.5)
```yaml
environment:
  ambient_light_level: 10
```

After (2.6)
```yaml
environment:
  ambient_light_level: [10, 10, 10]
```

---

FSIF 2.5: weapon_pool removed, automatically calculated (breaking)

Change
- The `weapon_pool` field under `player_setup` has been entirely removed from the FSIF format.
- Mission authors no longer need to manually calculate and specify the quantities of primary and secondary weapons. The converter now automatically calculates the required `Weaponry Pool` based on the armaments of the starting Friendly wings (Alpha, Beta, Gamma, Delta, Epsilon), adds a 25% safety margin, and emits it into the FS2 file directly.

Migration guidance
- Remove the entire `weapon_pool` block from the `player_setup` mapping in your `.fsif` files.
- Bump `fsif_version` to "2.5".

Before (2.4)
```yaml
player_setup:
  start_ship: "Alpha 1"
  extra_ships:
    - { class: "GTF Ulysses", count: 4 }
  weapon_pool:
    - { name: "Prometheus", count: 8 }
    - { name: "MX-50", count: 160 }
```

After (2.5)
```yaml
player_setup:
  start_ship: "Alpha 1"
  extra_ships:
    - { class: "GTF Ulysses", count: 4 }
```

---

FSIF 2.4: audio.event_music renamed to audio.mission_music (breaking)

Change
- The FSIF field `audio.event_music` has been renamed to `audio.mission_music` to better reflect its purpose (music that plays throughout the whole mission, not just during events).
- The emitted FS2 field (`$Event Music`) is unchanged — this is a FSIF authoring surface change only.

Migration guidance
- Find all instances of `event_music:` inside the `audio:` block of your FSIF files and rename the key to `mission_music:`.
- Bump `fsif_version` to "2.4".

Before (2.3)
```yaml
audio:
  event_music: "1: Genesis"
  briefing_music: "Brief1"
```

After (2.4)
```yaml
audio:
  mission_music: "1: Genesis"
  briefing_music: "Brief1"
```

---

FSIF 2.3: Removal of "Neutral" IFF (breaking)

Change
- The "Neutral" team has been removed from the FSIF specification because its implementation in FSO is broken (it essentially acts as a second "Hostile" team).
- Authors must now use "Hostile", "Friendly" or "Unknown" (as appropriate) for all ships and briefing icons that were previously "Neutral".
- Briefing icons for landmarks (Jump Nodes, Planets, Asteroid Fields) should generally use "Hostile" (red), "Friendly" (green) or "Unknown" (purple) depending on the desired color; "Neutral" is no longer a valid option.

Migration guidance
- Find all instances of `team: "Neutral"` in your FSIF files (ships, wings, and briefing icons).
- Change them to `team: "Hostile"`, `team: "Unknown"` or `team: "Friendly"`.
- Bump `fsif_version` to "2.3".

Before (2.2)
```yaml
ships:
  - name: "Nav Buoy"
    team: "Neutral"
briefing:
  icons:
    - { type: "Jump Node", team: "Neutral" }
```

After (2.3)
```yaml
ships:
  - name: "Nav Buoy"
    team: "Friendly"
briefing:
  icons:
    - { type: "Jump Node", team: "Hostile" }
```

---

FSIF 2.2: AI Goals simplification (breaking)

Change
- The `ai_goals` field in ship and wing definitions MUST NOT contain the `( goals ... )` wrapper.
- The converter now automatically wraps the content in `( goals ... )`.
- Including the wrapper explicitly will cause a validation error to prevent double-wrapping issues.

Migration guidance
- Locate all `ai_goals` blocks in your FSIF file.
- Remove the opening `( goals` line and the corresponding closing parenthesis `)`.
- Ensure the remaining content is a list of SEXP operators (e.g. `( ai-chase ... )`).
- Bump `fsif_version` to "2.2".

Before (2.1)
```yaml
wings:
  - name: "Alpha"
    ai_goals: |
      ( goals
        ( ai-chase-any 89 )
      )
```

After (2.2)
```yaml
wings:
  - name: "Alpha"
    ai_goals: |
      ( ai-chase-any 89 )
```

---

FSIF 2.1: Automated Briefing Camera (breaking)

Change
- Removed manual `camera_pos` and `camera_orient` fields from briefing stages. The converter now automatically positions the camera overhead based on icon layout.
- Briefing icon positions are now 2D `[x, z]`. The Y coordinate is ignored and forced to 0.

Migration guidance
- Remove `camera_pos` and `camera_orient` from all `briefing.stages`.
- Update `icons[*].pos` to `[x, z]` (removing the Y coordinate).
- Bump `fsif_version` to "2.1".

Before (2.0)
```yaml
briefing:
  stages:
    - text: "Stage 1"
      camera_pos: [0, 15000, 0]
      icons:
        - { type: "Fighter", pos: [0, 0, 0] }
```

After (2.1)
```yaml
briefing:
  stages:
    - text: "Stage 1"
      icons:
        - { type: "Fighter", pos: [0, 0] }
```

---

FSIF 2.0: Asteroid fields cleanup (breaking)

Change
- Removed support for `environment.asteroid_fields` (plural list).
- FSIF 2.0 requires using the singular mapping `environment.asteroid_field`.
- The `name` property under `asteroid_field` has been removed as the engine only supports one asteroid field per mission.
- The legacy plural key was deprecated in earlier versions and is now rejected.

Before (1.x legacy)
```yaml
environment:
  asteroid_fields:
    - name: "Field_Main"
      density: 50
```

After (2.0)
```yaml
environment:
  asteroid_field:
    density: 50
```

Migration guidance
- Rename `asteroid_fields` (list) to `asteroid_field` (mapping).
- Remove the list hyphen `-` indentation.
- If you had multiple fields defined (which was invalid in engine terms), keep only the first one.
- Bump `fsif_version` to "2.0".
