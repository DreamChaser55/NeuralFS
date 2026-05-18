# FSIF Authoring Guide

## Purpose
- Help mission authors write correct, concise FSIF quickly.
- Provide best practices, common patterns, pitfalls, and curated examples.

## Critical Rules
See `specification.md` for the normative schema and constraints. The three non-negotiable rules are:
- **Token fidelity**: Use exact canonical tokens only. See `../FSO and fs2 format/FSO_Tokens_Reference.md`.
- **Token length limit**: All names (ships, wings, events, messages, etc.) must be < 30 characters.
- **SEXP fidelity**: FSIF embeds SEXP verbatim. The converter does not "fix" invalid SEXP.

## Minimal FSIF skeleton
- These are the minimum fields required for a valid FSIF file.

```yaml
fsif_version: "1.0"

mission_info:
  name: "Minimal Mission"

environment:
  ambient_light_level: [0, 0, 0]

player_setup:
  start_ship: "Alpha 1"

entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]

mission_flow: {}
```

## Standard FSIF skeleton
- Use this skeleton to bootstrap a typical mission. It includes:
  - optional but commonly used sections like `environment` and empty lists for easy expansion.
  - Alpha wing and its ship template, with player being Alpha 1.
  - an example non-wing ship (a cruiser).

```yaml
fsif_version: "1.0"

mission_info:
  name: "Mission name string"
  author: "Author name string"
  description: "Mission description string"
  game_type: "single"
  flags: []

environment:
  ambient_light_level: [0, 0, 0]
  suns: []
  background_bitmaps: []
  nebula:
    enabled: false

player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - class: "GTF Ulysses"
      count: 4
  additional_weapons:
    - "Interceptor"

entities:
  ship_templates:
    alpha_fighter:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  ships:
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      position: [200.0, 0.0, 800.0]
  wings:
    - name: "Alpha"
      template: "alpha_fighter"
      count: 4
      position: [0.0, 0.0, 0.0]
  waypoints: {}
  reinforcement_wings: []
  reinforcement_ships: []

mission_flow:
  command_briefing:
    stages: []
  briefing:
    stages: []
  debriefing:
    stages: []
  events: []
  goals: []
  messages: []

audio:
  tts_provider: "none"
```

## Fiction Viewer
The Fiction Viewer allows you to display a text file before the mission starts. This is useful for lengthy narrative text or logs. If your mission design document contains cutscene descriptions but no cutscenes were actually created, you can write their narrative content here.
```yaml
mission_flow:
  fiction_viewer: "missionname_story.txt"
```
The file `missionname_story.txt` must exist in your mod's data/fiction folder.

Notes:
- The referenced Fiction Viewer content is shown to the player as the **very first** thing before the mission begins (before the Command Briefing).
- The entire referenced file is shown to the player as is. Ensure that any internal or development notes are removed before release.
- Use the **Fiction Viewer Validator** to check the file before release:
  ```
  python Fiction_Viewer_Validator/fiction_viewer_validator.py <path_to_story_txt>
  ```
  It checks for: non-ASCII characters (error), accidental use of the internal "fiction viewer" feature name (warning), and unclosed span-style color tags (warning). See `Fiction_Viewer_Validator/README.md` for details.

## Callable support ships

In FSO, player can call in a support ship at any time. A generic `GTS Centaur` will jump in to rearm and repair the player as well as other friendly fighters. You can disable this option in your mission by setting `mission_info.disallow_support_ships` to `true`. Note that `disallow_support_ships` will not affect any support ships defined in `entities.ships`.

## Asteroid and debris fields

FSO supports two mutually exclusive field genres, selected by `object_type`.

### Asteroid field

Spawns visual asteroid objects. Active asteroid fields will track and strike ships.

```yaml
environment:
  asteroid_field:
    object_type: "asteroid"     # selects the asteroid genre
    behavior: "active"          # "active" = pursues ships; "passive" = drifts
    num_objects: 10
    average_speed: 5.0
    bounds:
      min: [-2500.0, -1500.0, -2500.0]
      max: [2500.0, 1500.0, 2500.0]
    object_variants: ["Brown", "Blue", "Orange"]   # any subset of the three canonical asteroid variant names; omit for all three (default)
    target_ships: ["GTC Fenris 1", "GTFr Poseidon 1"]   # active fields only
```

### Debris field

Spawns ship-debris objects. Debris fields are always passive.

```yaml
environment:
  asteroid_field:
    object_type: "debris"       # selects the debris genre
    behavior: "passive"         # debris fields are always passive; active is coerced to passive
    num_objects: 10
    average_speed: 0.0
    bounds:
      min: [-1000.0, -1000.0, -1000.0]
      max: [1000.0, 1000.0, 1000.0]
    object_variants:            # any subset of the nine canonical debris variant names; omit for all nine (default)
      - "Terran Debris 1"
      - "Terran Debris 2"
      - "Terran Debris 3"
      - "Vasudan Debris 1"
      - "Vasudan Debris 2"
      - "Vasudan Debris 3"
      - "Shivan Debris 1"
      - "Shivan Debris 2"
      - "Shivan Debris 3"
```

### Authoring rules

- Asteroid and debris variant names are **mutually incompatible** — the converter rejects mixing names from the two lists.
- `object_variants: []` (explicit empty list) is not allowed. Omit the key to use defaults.
- `target_ships` only applies to **active asteroid** fields. It generates a warning on any other combination.
- Debris fields authored with `behavior: "active"` are automatically coerced to `"passive"` with a warning.
- Only one `asteroid_field` is allowed per mission.

## Environment: background suns and bitmaps
Author background suns and `background_bitmaps`; full nebula is a separate feature and unconditionally suppresses background bitmaps.
```yaml
environment:
  ambient_light_level: [0, 0, 0]
  suns:
    - texture: SunWhite
      angles: [0.000000, 0.000000]
      scale: 1.0
    - texture: SunSiriusA
      angles: [0.087266, 0.226893]
      scale: 2.5
  background_bitmaps:
    - texture: dneb03
      angles: [0.000000, 2.321286, 0.000000]
      scale: { x: 4.0, y: 4.0 }
    - texture: neb11
      angles: [0.401425, 0.663225, 0.139626]
      scale: { x: 2.0, y: 4.0 }
```
Notes
- Sun `angles` are `[pitch, heading]` in radians. Background bitmap `angles` are `[pitch, bank, heading]` in radians.
- **Background richness advisory:** In normal-space missions, try to include at least **3** `background_bitmaps` that use nebula background textures. Missions with fewer than 3 background nebulae often look sparse or empty. This recommendation does **not** apply to full nebula missions or subspace missions.
- **Sun angles warning:** Avoid setting any sun's `angles` to `[0.0, 0.0]`. That direction points **directly in front of the player** when they spawn in the default position and orientation and produces a full-screen whiteout/blinding effect. Give every sun a non-zero heading or pitch.
- **Maintain background consistency:** If multiple missions feature the same star system, keep suns, background_bitmaps, and ambient light the same or similar. Rules for missions that change location within the same star system:
  - Distant nebulae will likely look the same and be in the same positions in the sky.
  - Positions of suns or planet bitmaps could change.
  - Ambient light color will be the same, but intensity will change with distance from the sun.

## Environment: full (volumetric) nebula
Full nebula fills the entire mission with volumetric fog and cloud sprites, reduces sensor/AWACS range, and replaces normal-space backgrounds with a colored sky pattern. Enable it with `environment.nebula.enabled: true`.

```yaml
environment:
  ambient_light_level: [5, 5, 5]
  suns: []             # optional; suns are still rendered inside the nebula
  background_bitmaps: []    # must be empty in full nebula missions
  nebula:
    enabled: true
    pattern: "nbackblue1"                        # optional; omit for a completely black background with no stars
    cloud_sprites: ["PoofPurp01", "PoofPurp02"]  # optional
    storm: "s_medium"                            # optional; default: none
    sensor_range: 2000.0                         # optional; default: 3000.0
```

**Field notes:**
- `pattern` is the optional background sky color. If omitted while `enabled: true`, the result is a completely black background with no stars (the optional cloud sprites and lightning are still active). Use this only when a featureless pitch black sky is intentional.
- `sensor_range` (Float, default `3000.0`) controls the AWACS/sensor radius. Ships beyond this range are invisible on radar.
- `storm` (String, default `"none"`) sets the lightning-storm intensity. Omitting `storm` (or setting it to `none`) suppresses all storm effects. Set it to `s_standard`, `s_medium`, `s_active`, or `s_emp` to enable progressively more intense lightning.
- `cloud_sprites` is an optional list of FSO nebula poof sprite tokens that fill the space. Omit the list to suppress the moving cloud layer entirely.

**Authoring rules:**
- **Do not add `fullneb` to `mission_info.flags` manually.** The converter injects this flag automatically when `environment.nebula.enabled: true`.
- **`background_bitmaps` must be empty.** Authored background bitmaps are an error when full nebula is enabled.
- **Suns are still allowed.** They are visible inside the nebula and can be authored normally.
- **The "at least 3 background nebula bitmaps" richness advisory does not apply** to full nebula missions.
- **Increase visibility via design.** With reduced sensor range, players cannot easily navigate. Use visible `Terran NavBuoy` ships, clear HUD directives, and in-mission comms to guide the player, or create more compact missions. Do not rely on distant ships being visible or targetable.
- Volumetric nebula is often used to simulate gas giant atmospheres or supernova remnant systems.

**Dynamic nebula changes via SEXPs:**
Use SEXPs like `nebula-change-pattern`, `nebula-change-storm`, `nebula-toggle-poof`, `nebula-change-fog-color`. Consult `Documentation/FSO SEXPs/Backgrounds and Nebulae.txt` for exact arguments.

## Templates, ships and wings
```yaml
entities:
  ship_templates:
    ulysses_fighter:
      class: "GTF Ulysses"
      team: "Friendly"
      ai_class: "General"
      flags: ["no-shields"]
      weapons:
        primary: ["Prometheus", "Avenger"]
        secondary: ["Hornet"]
  ships:
    - name: "GTSC Rosetta"
      class: "GTSC Faustus"
      team: "Friendly"
      position: [542.6, 699.5, 1305.4]
      flags: ["cargo-known", "escort"]
      departure_cue: |
        ( is-event-true-delay "Omega 2 done docking" 97 )
  wings:
    - name: "Alpha"
      template: "ulysses_fighter"
      count: 4
      position: [0.0, 0.0, 0.0]
      initial_orders: |
        ( ai-chase-any 50 )
```

Wings must define `position: [x, y, z]`, which is interpreted as the centroid of all ships in the wing. In the example above, a 4‑ship wing with `position: [0.0, 0.0, 0.0]` will be placed as four objects along the X axis at:

- Alpha 1: `[-75.0, 0.0, 0.0]`
- Alpha 2: `[-25.0, 0.0, 0.0]`
- Alpha 3: `[25.0, 0.0, 0.0]`
- Alpha 4: `[75.0, 0.0, 0.0]`

Wing members are spaced 50 m apart by default (`member_spacing: 50.0`) and the line is centered on the specified centroid.

## Waypoints vs. Nav Buoys
FSIF `entities.waypoints` are invisible to the player. They do not create a HUD marker, radar contact, targetable object, visible model, or any in-game cue that the player can follow. Use waypoints only for AI movement paths (`ai-waypoints`, `ai-waypoints-once`), hidden distance checks, and internal SEXP references such as `PathName:1`.

If the player needs to rendezvous at a location, fly toward a marker, or identify a destination, you can place an actual navigation buoy ship instead — use ship class `Terran NavBuoy`. Refer to that ship's name in briefing text, directives, messages, and SEXPs when the player needs a visible or targetable reference. Do not tell the player to "follow the waypoint" unless there is an actual visible object (such as a Nav Buoy) at that location.

Do not overuse NavBuoys: you don't need one if there is already another visible object at the location.

## Events, goals and messages
```yaml
mission_flow:
  events:
    - name: "dragon_destroyed_event"
      formula: |
        ( when 
           ( is-destroyed-delay 0 "SF Dragon 1" ) 
           ( do-nothing ) 
        )
      hud_directive_text: "Destroy SF Dragon 1"
  goals:
    - name: "save rosetta"
      type: "Bonus"
      objective_text: "Protect the Rosetta until it departs"
      formula: |
        ( is-event-true-delay "Rosetta departed" 0 )
  messages:
    - name: "Lucifer arrived"
      text: "That's the Lucifer arriving!"
      voice_name: "Fenrir"
```

Notes:
- An available mission goal is marked grey (TO-DO). It turns completed (green) when its formula is true, or failed (red) when the formula can no longer become true (e.g., a ship that should be protected until departure is destroyed).
- Directive texts for events follow the same coloring rules but are always visible on the HUD. Important objectives should have a corresponding event with `hud_directive_text`, not just a goal.
- **Directive text limitation:** Events with `hud_directive_text` must use simple, directly-evaluable conditions. Formulas referencing another event or goal with `is-event-true-delay`, `is-event-false-delay`, `is-event-true-msecs-delay`, `is-event-false-msecs-delay`, `is-goal-true-delay`, or `is-goal-false-delay` will silently fail — the engine cannot evaluate such conditions at mission start, so the grey "pending" directive is never displayed. Use direct object-state SEXPs (`is-destroyed-delay`, `is-cargo-known-delay`, `has-arrived-delay`, `percent-ships-destroyed`) in events with `hud_directive_text`.
- Try to include enough comms chatter (messages) in your missions to make them lively.
- For wingman messages where specific wingman sender is not important, you should prefer '<any wingman>' wildcard sender parameter. This means the messages will reliably play even if a specific wingman is killed.

## Authoring dialogue (TTS voicing)

**Required fields:**
- Any mission containing voiced lines should explicitly define `tts_provider` under the `audio` section (`"google"`, `"elevenlabs"`, `"inworld"`, or `"none"`). Use one provider consistently across all missions.
- Voiced lines must provide `voice_name` (a valid voice identifier for the chosen provider). See `Documentation/<Provider> TTS/voices.txt`.

**Optional field:**
- `voice_style_instructions: String` — Optional "Director's Note" for the AI.
  - **Google (Gemini TTS):** Supports complex sentence-like prompts (e.g., `"Military commander delivering a briefing with an authoritative tone"`).
  - **ElevenLabs TTS:** Use simple comma-separated emotion tags only (e.g., `"energetic, agitated"`).
  - **Inworld TTS:** Currently does not utilize style instructions.

Unvoiced lines should omit these fields.

**Supported locations:** `command_briefing.stages[*]`, `briefing.stages[*]`, `debriefing.stages[*]`, `messages[*]`.

**Example (message):**
```yaml
mission_flow:
  messages:
    - name: "Ambush warning"
      text: "It looks like an ambush!"
      voice_style_instructions: "energetic, agitated"
      voice_name: "Charon"
```

**Example (briefing stage):**
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Rendezvous at Nav Buoy and scan the marked container."
        icons: [...]
        voice_style_instructions: "commanding, directing"
        voice_name: "Achernar"
```

- Maintain voice consistency: use the same `voice_name` for the same character across the mission.

## Docking (pre-spawn pairs)
Author only on the docker; ensure coherent arrival leadership.
```yaml
entities:
  ships:
    - name: "GTC Fenris 1"
      class: "GTC Fenris"
      team: "Friendly"
      position: [-181.8, 0.0, 275.8]
      arrival_cue: |
        ( true )
    - name: "GTT Elysium 2"
      class: "GTT Elysium"
      team: "Friendly"
      position: [-230.3, 4.18, 355.34]
      arrival_cue: |
        ( false )
      dock:
        dockee: "GTC Fenris 1"
        docker_point: "topside docking"
        dockee_point: "Docking bay 1"
```
Strict Rules:
- **Arrival Conditions**: The Dockee (Leader) must have `arrival_cue: ( true )`. The Docker (Follower) must have `arrival_cue: ( false )`.
- **Pairs Only**: Multi-ship (daisy chained) docking is not supported.
- **No Player Ships**: Player start ships cannot be pre-docked.
- **Reference Checks**: Use only the dockpoint names from `../FSO and fs2 format/ship-dockpoint-names.md`.

Note: If one of the ships in a docked pair departs, it takes the other ship with it.

Note: Do not confuse docking (connects two ships; uses dockpoint names) with the `Docking Bay` arrival/departure method (spawns from a fighterbay or departs to a fighterbay; uses "fighterbay" subsystem names).

## Subsystems
- Subsystem names must match the per-ship canonical lists. See the documentation index for paths to the naming files.
- CAUTION: there are subtle spelling differences among ships (e.g., "communication" vs "communications", "engine" vs "engines"). Always consult the subsystem naming documentation.

Example SEXP referring to a subsystem:
```lisp
( when 
   ( has-arrived-delay 3 "SC Lilith 2" ) 
   ( add-goal 
      "Beta" 
      ( ai-destroy-subsystem 
         "SC Lilith 2" 
         "engine" 
         89 
      )
   )
)
```

## Reinforcements
Author reinforcements in `entities`. Omit `arrival_cue` on the referenced units so they remain callable (defaults to true). Referenced ships/wings must exist in entities.ships/entities.wings.

```yaml
entities:
  reinforcement_wings:
    - name: "Delta"
      max_uses: 1
      arrival_delay: 0
  reinforcement_ships:
    - name: "GTC Fenris 10"
      max_uses: 1
```

## Briefing, debriefing and fiction viewer text styling
Text in command and mission briefings, debriefings and in the fiction viewer can be styled by special tags. See `\Documentation\FSO and fs2 format\text_styling_guide.txt` for a guide.

Note: use the styling tags **only** in the contexts mentioned above. They **do not** work in other places (such as in in-mission messages, directives or goal messages).

**Recommended color conventions:**
- Friendly ships/wings: `$f{ Name $}` (IFF Friendly color — green by default)
- Hostile ships/wings: `$h{ Name $}` (IFF Hostile color — red by default)
- Unknown ships/wings: `$V{ Name $}` (Violet)

Apply these to every named friendly, hostile or unknown ship/wing. Other color tags (such as `$y` for locations/nav points/destinations, `$W` for emphasis, `$R` for warnings) are available but should be used very sparingly. Less is more.

**Single-word vs. span syntax:**
- For a single word: `$h Rama` — colors "Rama" in hostile red. Coloring stops when a space is encountered.
- For a multi-word phrase: `$f{ GTC Fenris $}` — colors the entire span.

Note: Do not forget the closing tag (`$}`). Missing closing tags cause errors.

**Example:**
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Rendezvous at Nav Buoy and scan the marked container. $h Rama will intercept - protect the $f{ GTC Fenris $}."
        voice_name: "Gacrux"
        icons: []

  debriefing:
    stages:
      - display_condition: |
          ( is-destroyed-delay 0 "GTC Fenris 1" )
        text: "The $f{ GTC Fenris $} was destroyed. We failed the escort."
        voice_name: "Gacrux"
      - display_condition: |
          ( has-departed-delay 0 "GTC Fenris 1" )
        text: "Excellent work, $rank $callsign. The convoy withdrew successfully and the $f{ GTC Fenris $} is safe."
        voice_name: "Gacrux"
```

**Debriefing stage display_condition authoring note:**
Debriefing stages are displayed only when their `display_condition` SEXP is met. Make conditions sufficiently restrictive — a stage describing success should never use `( true )` as its condition, because that would cause it to display even when the mission was a failure.. Prefer specific SEXPs such as `( is-event-true-delay "..." 0 )`.

## Briefing Room Grid View

Unless the mission is very short and trivial, you should always author a briefing schematic view with relevant icons for every briefing stage. Briefings are authored from the commanding officer's point of view and depict a prediction of the mission events. They should not reveal surprises or information the commander couldn't know.

### Layout
The briefing room uses a grid on the **XZ plane**.
- Place icons using 2D coordinates `[x, z]` (e.g. `map_position: [500, 1000]`).
- The briefing camera is automatically positioned to ensure all icons are in view.

### Icons
- **icon_type**: Must be a canonical string (e.g., "Fighter", "Jump Node", "Waypoint"). See `../FSO and fs2 format/FSO_Tokens_Reference.md` for the full list.
- **display_class**: Conditionally required. The displayed ship class when the icon is selected in-game.
  - **Ship icon types** (e.g., `"Fighter"`, `"Fighter Wing"`, `"Cruiser"`, `"Capital Ship"`, `"Transport"`, etc.): **must** author `display_class` with the actual ship class. Using `"Terran NavBuoy"` for a ship icon type is an error.
  - **Non-ship icon types** (`"Waypoint"`, `"Jump Node"`, `"Planet"`, `"Small Planet"`, `"Asteroid Field"`, `"Unknown"`, `"Unknown Wing"`): **must omit** `display_class`. The converter automatically emits `"Terran NavBuoy"` for these types.
  - If specified, must be a valid ship class from `spacecraft-classes.md`.
- **team**: `"Friendly"` (green), `"Hostile"` (red), or `"Unknown"` (purple).
- **map_position**: `[x, z]`. Defaults to `[0, 0]` if omitted.

**Example:**
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Alpha, inspect the cargo at the marked location shown on this briefing schematic."
        voice_name: "Achernar"
        icons:
          - { icon_type: "Fighter", team: "Friendly", display_class: "GTF Ulysses", map_position: [0, 0], label: "Alpha", highlighted: true }
          - { icon_type: "Cargo", team: "Hostile", display_class: "GTFr Poseidon", map_position: [500, 200], label: "Rosetta Cargo" }
          - { icon_type: "Waypoint", team: "Unknown", map_position: [1000, 0], label: "Schematic marker" }
```

Note: A briefing `"Waypoint"` icon is a schematic-only symbol — it does **not** create a visible in-mission waypoint.

## Fighter and bomber weapon hardpoints
All available primary and secondary weapon banks (hardpoints) in fighters and bombers must have assigned weapons. The number of entries in `weapons.primary` and `weapons.secondary` must equal the hardpoint count in `\Documentation\FSO and fs2 format\fighter_bomber_hardpoints.md`.

## Introducing new ships and weapons
If the mission is part of a campaign, all ships and weapons are unavailable by default. They must be explicitly allowed in the FCIF `starting_loadout` or via `allow-ship`/`allow-weapon` SEXPs (see `/FSO SEXPs/Mission and Campaign.txt`) executed at the **end of the previous mission**.

## Providing alternative player ships
Use `additional_ship_choices` to provide a pool of alternative ships the player can swap in on the loadout screen. Player can swap these extra ships into the loadout-screen wings Alpha, Beta, and Gamma.

```yaml
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - { class: "GTF Hercules", count: 4 }
    - { class: "GTB Ursa", count: 2 }
```

Note: These ships also need to be unlocked (see "Introducing new ships and weapons" above).

## Providing the player with extra weapons
Use `additional_weapons` to add extra weapons to the loadout screen Weaponry Pool:
```yaml
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - { class: "GTF Ulysses", count: 4 }
  additional_weapons:
    - "Avenger"
    - "Harbinger"
```
Note: These also need to be unlocked. The maximum quantities needed to fully equip all player wings are calculated automatically with a 25% safety margin.

## Directional arrivals quick reference
- Directional `arrival_method` (Near Ship, In front of/behind/above/below/left/right of ship) requires both `arrival_anchor` and `arrival_distance`.
- `Docking Bay`: `arrival_distance` is forced to `0` and should be omitted.
- FSO SEXP docs refer to `arrival_method` as "arrival location" and `departure_method` as "departure location".

## Maximum mission scale recommendation
- Keep distances between all points of interest **below 20 km** whenever possible.
- Avoid `arrival_distance` values above **20,000** — large mission spaces cause long, uneventful travel.

## ASCII-only requirement for FSO-facing strings
FSO only supports ASCII characters reliably. This applies to all mission metadata, names, text fields, token strings, and SEXP literals. It does **not** apply to `voice_style_instructions`.

Use ASCII replacements when needed:
- use `'` instead of curly quotes
- use `-` instead of em dash or en dash
- use `...` instead of the single-character ellipsis

## No double quotes allowed in FSO-facing strings
Double quotes `"` are not allowed in FSO-facing text fields, as they break the FSO parser. Use single quotes `'` instead.
Note: This rule does not apply to SEXP fields. Some SEXP tokens need to be wrapped in double quotes.

## SEXP Authoring Guidelines

### Consult SEXP Documentation
Always check the documentation in `Documentation/FSO SEXPs/` for the exact signature of any SEXP construct you intend to use. Pay close attention to:
- **Operator Names:** Ensure exact spelling (e.g. use valid `ai-guard`, not non-existent `ai-guard-ship`).
  - **Argument Types:** Verify all arguments. Does the SEXP expect a Ship Name, Wing Name, or both? Do not pass a wing name to a ship-only SEXP (e.g., `is-cargo-known-delay`). If you need to cover a whole wing with a ship-only SEXP, either use a wing-compatible alternative operator or list all individual ships explicitly.
  - **Priorities:** Most AI goals require a priority argument (0-200). Omitting it causes crashes.
  - **Argument order:** Verify that all arguments are in the correct order.

Do not use any SEXP construct without reading and understanding its documentation first!

### Choose the Right Tool
Actively explore SEXP documentation to find the best operator. For example, instead of complex boolean logic to check if any ship in a group is scanned, use `percent-ships-scanned`.

### Prefer Common Mission-Logic SEXPs

High-quality FreeSpace 1 missions use a relatively small set of SEXP operators to implement almost all mission logic. You should default to operators from the curated list below before reaching for more obscure alternatives. Obscure operators are acceptable only when they solve a specific problem more cleanly — in which case read their full documentation and, if possible, note the reason in the mission implementation plan.

Note: The following generic glue operators are intentionally omitted from the curated list below, even though they are extremely frequent — they are control-flow or arithmetic primitives, not mission-design building blocks:
true, false, when, and, or, not, <, >, =, <=, >=, +, -, *, do-nothing
These remain valid and essential; they just are not the "interesting" layer of mission logic.

#### Curated and recommended common mission-logic operators

**Objective and state checks**
```text
is-destroyed-delay          — true N sec after all listed ships/wings are destroyed
has-arrived-delay           — true N sec after listed ships/wings have arrived
has-departed-delay          — true N sec after listed ships/wings have departed (warp-out; destroyed = never true)
destroyed-or-departed-delay — true N sec after all listed ships/wings are destroyed or departed
are-waypoints-done-delay    — true N sec after a ship completes a waypoint path
has-docked-delay            — true N sec after two ships have docked N times
has-undocked-delay          — true N sec after two ships have undocked N times
percent-ships-destroyed     — true when a given % of listed ships/wings are destroyed
percent-ships-departed      — true when a given % of listed ships/wings have departed
percent-ships-scanned       — true when a given % of listed ships are scanned (ship-only, not wings)
is-cargo-known-delay        — true N sec after a ship's cargo is revealed (ship-only, not wings)
is-subsystem-destroyed-delay — true N sec after a specific subsystem is destroyed
is-disabled-delay           — true N sec after listed ships lose all engine subsystems
is-disarmed-delay           — true N sec after listed ships lose all turret subsystems
```

**Event and goal chaining**
```text
is-event-true-delay    — true N sec after an event in this mission succeeds
is-event-false-delay   — true N sec after an event in this mission fails
is-event-incomplete    — true while an event has not yet fired (useful only with has-time-elapsed)
is-goal-true-delay     — true N sec after a goal succeeds
is-goal-false-delay    — true N sec after a goal fails
is-goal-incomplete     — true while a goal is still pending
```

> Note: events with `hud_directive_text` must use **direct** object-state checks (`is-destroyed-delay`, `has-arrived-delay`, `distance`, etc.) — they cannot use `is-event-true-delay` or `is-goal-true-delay`. See the Events section.

**Messages and comms**
```text
send-message       — send a single message; args: sender, priority, message-name
send-message-list  — send a sequence of delayed messages; args in groups of FOUR
send-random-message — pick one message at random from a list
```

**AI orders and dynamic retasking**
```text
add-goal              — assign an AI goal to a ship or wing at runtime
clear-goals           — clear all AI goals from a ship or wing (use before add-goal when retasking)
ai-chase              — chase and attack a specific ship
ai-chase-any          — chase and attack any enemy
ai-chase-wing         — chase and attack ships in a wing
ai-guard              — guard a specific ship from enemies (fighter/bomber only)
ai-waypoints-once     — fly a waypoint path once then stop
ai-waypoints          — fly a waypoint path repeatedly
ai-dock               — dock with a target ship
ai-undock             — undock from the currently docked ship
ai-warp-out           — immediately warp out of the mission
ai-play-dead          — stop all movement and attack
ai-destroy-subsystem  — attack and destroy a named subsystem on a target ship
ai-disable-ship       — destroy all engine subsystems to disable a ship
ai-disarm-ship        — destroy all turret subsystems to disarm a ship
ai-ignore             — ignore a specific target
ai-stay-still         — stop and stay in place
```

**Distance, timing, and damage thresholds**
```text
distance         — current distance in meters between two objects; use with < for proximity triggers
has-time-elapsed — true N seconds after mission start; useful for timed delays not tied to events
hits-left        — current hull strength of a ship (0–100); use with < for damage-threshold triggers
hits-left-subsystem — current health of a specific subsystem (0–100)
```

**Ship protection and state changes**
```text
protect-ship      — no AI ship will attack this ship
unprotect-ship    — remove protect-ship
ship-invulnerable — ship takes no damage (permanent; remove with ship-vulnerable)
ship-vulnerable   — remove ship-invulnerable
ship-guardian     — hull is stuck at 1%; ship can take damage but cannot die
ship-no-guardian  — remove ship-guardian
change-iff        — change a ship's IFF team at runtime
ship-visible      — make a ship visible after ship-invisible
ship-invisible    — make a ship invisible
```

**Campaign and goal management**
```text
validate-goal    — make a mission goal active (shows as pending)
invalidate-goal  — remove a mission goal (hides it completely)
allow-ship       — unlock a ship class for the player's loadout
allow-weapon     — unlock a weapon for the player's loadout
tech-add-ships   — add ships to the tech room database
tech-add-weapons — add weapons to the tech room database
red-alert        — trigger a red-alert transition to the next mission
```

#### Task-to-operator quick reference

| Mission task | Preferred operator(s) |
|---|---|
| Trigger when ship(s) die | `is-destroyed-delay`, `percent-ships-destroyed` |
| Trigger when ships arrive | `has-arrived-delay` |
| Trigger when ships depart | `has-departed-delay`, `percent-ships-departed` |
| Convoy success (all escaped) | `has-departed-delay` (all ships) |
| Convoy failure (any destroyed) | `is-destroyed-delay` |
| Either destroyed or escaped | `destroyed-or-departed-delay` |
| Scan objective | `is-cargo-known-delay`, `percent-ships-scanned` |
| Patrol path completed | `ai-waypoints-once` + `are-waypoints-done-delay` |
| Docking sequence | `has-docked-delay`, `has-undocked-delay` |
| Retask AI during mission | `clear-goals` + `add-goal` + appropriate `ai-*` goal |
| Proximity trigger (distance-based) | `distance` with `<` |
| Timed delay (not event-tied) | `has-time-elapsed` |
| Damage-threshold trigger | `hits-left` with `<` |
| Protect a ship temporarily | `protect-ship` / `unprotect-ship`, or `ship-invulnerable` / `ship-vulnerable` |
| Prevent ship from dying | `ship-guardian` / `ship-no-guardian` |
| Send dialogue | `send-message`, `send-message-list` |
| Campaign unlocks | `allow-ship`, `allow-weapon`, `tech-add-ships`, `tech-add-weapons` |

### SEXP String Formatting: Use Block Scalars
**Rule: Always use block scalars (`|`) for all SEXP fields** (`arrival_cue`, `departure_cue`, `formula`, `initial_orders`, `display_condition`, etc.), even for single-line SEXPs.

**Why:** SEXPs frequently contain double quotes around entity names. In a flow scalar, every `"` must be escaped (`\"`), which is error-prone. Block scalars preserve content literally.

**Do (block scalar):**
```yaml
arrival_cue: |
  ( has-arrived-delay 5 "GTD Bastion" )
```

**Don't (flow scalar — requires escaping):**
```yaml
arrival_cue: "( has-arrived-delay 5 \"GTD Bastion\" )"
```

### Boolean Literals
Always use `( true )` and `( false )` for boolean arguments. Do not use `1` or `0`.
- **Incorrect:** `( ai-waypoints-once "Path" 89 0 3 )`
- **Correct:** `( ai-waypoints-once "Path" 89 ( false ) 3 )`
- Note: All booleans in SEXPs must be surrounded by spaces and enclosed in parentheses.

### Avoid Optional Arguments in Initial Orders
The `initial_orders` field is parsed by a restricted parser that fails on optional SEXP arguments. If you need optional arguments for an AI goal (e.g., distance in `ai-stay-near-ship`), use a `when-true` event instead:
```lisp
( when
   ( true )
   ( add-goal "GTSC Kepler" ( ai-stay-near-ship "GTD Stalwart" 89 1000 ) )
)
```

### Multiple initial AI orders
List SEXP operators line-by-line in a block scalar:
```yaml
ships:
  - name: "Beta 1"
    # ... other properties ...
    initial_orders: |
      ( ai-chase-any 89 )
      ( ai-guard "GTC Pollux" 60 )
      ( ai-warp-out 50 )
```
The orders will be executed consecutively.

## Using the escort flag (monitoring list)
The `escort` flag adds the ship to the player's HUD monitoring list. Use it for **any ship the player needs to monitor**, not just friendly escorts:
- Friendly ships the player needs to protect.
- Important enemy ships the player needs to track.
- Any key mission-critical object.

Note: Flag only the most important ships to avoid cluttering the HUD. Use `escort_list_priority` to control display order.

## Creating ship debris
Use `destroyed_before_mission_seconds` to create ship debris at mission start. The value is the number of seconds before mission start when the ship is destroyed. Zero (default) results in normal ship spawning.

## Pitfalls, best practices and recommendations

### Spawning, arrivals and authored entities
- `player_setup.start_ship` **must** be a member of a Friendly `Alpha`, `Beta`, or `Gamma` wing (e.g. `Alpha 1`, `Beta 3`, `Gamma 2`). Standalone player ships and starts in any other wing (including `Delta`, `Epsilon`, hostile wings, or non-standard wings) are a **validation error** that aborts conversion: FSO's team loadout screen only works for the first three Friendly wings.
- Do not put arrival/departure/initial_orders/dock fields into `entities.ship_templates` — see the spec. Author them on the ship or on the wing.
- Use `arrival_cue` to control when a ship appears. Do not use `ship-create` for ships already in YAML.
- Leave enough physical clearance between spawned objects, especially around large ships — cruisers are ~300 m long, destroyers ~2000 m.

### Templates, names and references
- Use templates for repeated ship configurations. Wings must use a template.
- Keep custom names short and unique (under 30 characters). Do not reuse names for different entities. Do not author a standalone ship whose name would already be created by a wing expansion such as `Alpha 1`.
- Waypoint points are hidden AI/logic references — not visible player navigation markers. If your mission design calls for a player-visible navigation marker, use an actual ship with the `Terran NavBuoy` ship class.
- Reinforcement entries must reference ships/wings defined in `entities.ships`/`entities.wings`.
- Message names referenced from events must exist in `mission_flow.messages`.

### SEXP and token hygiene
- Use only canonical FSO tokens (ship classes, weapons, subsystem names, dockpoint names, background textures, message priorities, wildcard literals).
- Message priorities: exactly `"Low"`, `"Normal"`, `"High"`.
- Use double quotes (`"`) for entity names inside SEXPs.
- Never place YAML-style `#` comments inside SEXP block scalars.
- Many SEXPs are ship-only — use wing-compatible alternatives or target specific ships.
- AI goals for larger ships (cruisers, destroyers, utility): only `ai-chase`, `ai-dock`, `ai-undock`, `ai-warp-out`, `ai-stay-near-ship`, `ai-stay-still`, `ai-play-dead` are valid. Prefer waypoint or warp orders for capital ships, or give them no orders at all — turrets fire automatically.
- Jump nodes cannot be used as distance-check anchors; use waypoints for hidden references, `Terran NavBuoy` for visible ones.
- Use exact FSO weapon token strings (e.g., `ML-16 Laser`, not `GTW ML-16 Laser`).
- Check that goal formulas are not already true at mission start.
- Events with `hud_directive_text` must use directly-evaluable conditions, not `is-event-true-delay`, `is-event-false-delay` (see Events section above).
- Operator `is-destroyed-delay` or `has-departed-delay` must never check the player ship. FreeSpace ends the mission immediately when the player ship is destroyed or departs, so this condition can never trigger any downstream logic.

### Docking
- See the dedicated Docking section above for rules and the worked example.
- Keep docking leadership coherent: dockee uses the default `arrival_cue: ( true )`; docker must explicitly set `arrival_cue: ( false )`.

### Reinforcements
- Keep reinforcements callable: both reinforcement wings and standalone reinforcement ships should omit `arrival_cue` — it defaults to `( true )`, making the reinforcement available to call from mission start.

### Waypoint paths
- The converter checks for potential collisions between larger ships on waypoint paths and other ships' **initial positions**. This check can produce spurious warnings because ships may move from their initial positions. Consider the planned mission flow when reviewing these warnings.
- Multiple ships must not share the same waypoint movement order. Ships ordered to the same waypoint destination will collide when they arrive. For convoys, give each ship its own waypoint path with a slightly offset final destination.

### Red alert missions
- Missions with the `red_alert` flag inherit player ship hull and loadout from the previous mission. Only the first briefing stage text is shown, with no icons. Use `red_alert_carry` on ships you want to carry between missions (in **both** the previous and the red-alert mission).

### Distance checks
- Verify distance-check SEXPs will not fire prematurely. Visualize the triggering object's initial location and movement to ensure it is not in trigger range at mission start or before the trigger should actually fire.

### Final review before conversion
After completing a mission file, confirm:
- all referenced tokens are canonical and documented
- all custom names are unique and under 30 characters
- all reinforcement, event, and message cross-references resolve to defined objects
- all SEXPs use valid operators with compatible argument types and correct argument order
- player start ship is a member of a Friendly Alpha, Beta, or Gamma wing
- docking setups and reinforcements are correctly defined
