# FSIF Migration Guide (1.0 → ... → 2.6)

Purpose
- Practical, snippet-led instructions to update existing FSIF files to the latest spec and converter expectations.
- Covers breaking changes and notable behavior shifts.

Status
- Current FSIF version: 2.6. The converter accepts FSIF 2.6 only; use this guide to update older FSIF files to the 2.6 schema before converting.

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

---

FSIF 1.9: voice field removal (breaking)

Change
- The `voice` field has been removed from the authoring surface for all dialogue types:
  - `mission_flow.command_briefing.stages[*]`
  - `mission_flow.briefing.stages[*]`
  - `mission_flow.debriefing.stages[*]`
  - `mission_flow.messages[*]`
- The `voice` field is now purely derived internally from `voice_filename` for backward compatibility with the FS2 writer.
- Authors must use `voice_filename` to specify the target `.wav` file; the converter sets `voice` = `voice_filename` during normalization.

Before (FSIF 1.8)
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Pilots, your mission is to defend the cargo depot."
        voice: "fafdemo_brief1"
        voice_filename: "fafdemo_brief1"
        voice_name: "en-US-Journey-F"
```

After (FSIF 1.9)
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Pilots, your mission is to defend the cargo depot."
        voice_filename: "fafdemo_brief1"
        voice_name: "en-US-Journey-F"
```

Impact
- Eliminates redundancy: `voice` and `voice_filename` always contained the same value after normalization
- Simplifies authoring: one less field to maintain
- The converter continues to populate `voice` internally for fs2_writer and TTS compatibility

Migration guidance
- Remove all `voice:` fields from command briefing stages, briefing stages, debriefing stages, and messages
- Ensure `voice_name` is present for all voiced lines (FSIF 1.8+ requirement)
- Do NOT author `voice_filename`. This field is now auto-generated by the converter based on the text content or name of the node.
- Bump `fsif_version` to "1.9"
