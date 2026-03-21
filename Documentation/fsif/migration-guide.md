# FSIF Migration Guide (1.0 → ... → 2.8)

Purpose
- Practical, snippet-led instructions to update existing FSIF files to the latest spec and converter expectations.
- Covers breaking changes and notable behavior shifts.

Status
- Current FSIF version: 2.8. The converter accepts FSIF 2.8 only; use this guide to update older FSIF files to the 2.8 schema before converting.

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
- Authors must now use "Hostile" or "Friendly" (as appropriate) for all ships and briefing icons that were previously "Neutral".
- Briefing icons for landmarks (Jump Nodes, Planets, Asteroid Fields) should generally use "Hostile" (red) or "Friendly" (green) depending on the desired color; "Neutral" is no longer a valid option.

Migration guidance
- Find all instances of `team: "Neutral"` in your FSIF files (ships, wings, and briefing icons).
- Change them to `team: "Hostile"` (recommended for most cases, especially if the object is a target or obstacle) or `team: "Friendly"`.
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
    team: "Hostile"
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
    name: "Field_Main"
    density: 50
```

Migration guidance
- Rename `asteroid_fields` (list) to `asteroid_field` (mapping).
- Remove the list hyphen `-` indentation.
- If you had multiple fields defined (which was invalid in engine terms), keep only the first one.
- Bump `fsif_version` to "2.0".
