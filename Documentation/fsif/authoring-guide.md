# FSIF Authoring Guide

## Purpose
- Help mission authors write correct, concise FSIF quickly.
- Provide best practices, common patterns, pitfalls, and curated examples.


## Critical Rules
- **Token fidelity**: Use exact canonical tokens only. Do not invent synonyms, alternative casing, or punctuation variants. SEXP names, wildcard literals, message priority strings, subsystem and dockpoint names must match exactly.
- **Token length limit**: All names (ships, wings, events, messages, etc.) must be < 30 characters.
- **SEXP fidelity**: FSIF embeds SEXP verbatim. The converter does not "fix" invalid SEXP.

## Minimal FSIF skeleton
- These are the minimum fields required for a valid FSIF file.

```yaml
fsif_version: "4.0"

mission_info:
  name: "Minimal Mission"

environment:
  ambient_light_level: [0, 0, 0]

player_setup:
  start_ship: "Player Ship"

entities:
  ships:
    - name: "Player Ship"
      class: "GTF Ulysses"
      team: "Friendly"
      position: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

mission_flow: {}
```

## Standard FSIF skeleton
- Use this skeleton to bootstrap a typical mission. It includes:
  - optional but commonly used sections like `environment` and empty lists for easy expansion.
  - Alpha wing and its ship template, with player being Alpha 1.
  - an example non-wing ship (a cruiser).

```yaml
fsif_version: "4.0"

mission_info:
  name: "Mission name string"
  author: "Author name string"
  description: "Mission description string"
  game_type: "single"
  flags: []
  ai_profile: "FS1 RETAIL"

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
      arrival_cue: |
        ( true )
  wings:
    - name: "Alpha"
      template: "alpha_fighter"
      count: 4
      position: [0.0, 0.0, 0.0]
      arrival_cue: |
        ( true )
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
    object_variants: ["Brown", "Blue", "Orange"]   # can be any subset; omit for all three
    target_ships: ["GTC Fenris 1", "GTFr Poseidon 1"]   # active fields only
```

Valid `object_variants` for asteroid fields:
- `"Brown"` — brown asteroid visuals
- `"Blue"` — blue asteroid visuals
- `"Orange"` — orange asteroid visuals

Default: all three.

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
    object_variants:            # any subset of the nine canonical debris names; omit for all nine
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

Valid `object_variants` for debris fields:
- `"Terran Debris 1"`, `"Terran Debris 2"`, `"Terran Debris 3"`
- `"Vasudan Debris 1"`, `"Vasudan Debris 2"`, `"Vasudan Debris 3"`
- `"Shivan Debris 1"`, `"Shivan Debris 2"`, `"Shivan Debris 3"`

Default: all nine.

### Authoring rules

- Asteroid and debris variant names are **mutually incompatible**. Do not mix names from the two lists (e.g. putting `"Terran Debris 1"` in an asteroid field, or `"Brown"` in a debris field) — the converter will reject this with an error.
- `object_variants: []` (an explicit empty list) is not allowed and will cause a validation error. To use the defaults, omit the `object_variants` key entirely.
- `target_ships` only applies to **active asteroid** fields. It has no effect (and generates a warning) for any other combination of `behavior` and `object_type`.
- Debris fields authored with `behavior: "active"` are automatically coerced to `"passive"` with a warning.
- Only one `asteroid_field` is allowed per mission. The converter supports authoring it as a single YAML mapping.

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
- `ambient_light_level` is authored as `[red, green, blue]`, with each channel in range `0..255`.
- Sun `angles` are `[pitch, heading]` in radians. Bank is omitted because sun sprites are rotationally symmetric.
- Background bitmap `angles` are `[pitch, bank, heading]` in radians.
- **Background richness advisory:** In normal-space missions, try to include at least **3** `background_bitmaps` that use nebula background textures. Missions with fewer than 3 background nebulae often look sparse or empty. This recommendation does **not** apply to full nebula missions or subspace missions, where those background nebulae are not visible.
- **Sun angles warning:** Avoid setting any sun's `angles` to `[0.0, 0.0]`. That direction points **directly in front of the player** when they spawn in the default position and orientation. Looking into a sun in FreeSpace produces a full-screen whiteout/blinding effect, which is highly disorienting and nearly always unintentional. Give every sun a non-zero heading or pitch so it is off to the side or above/below the player's forward view.
- **Maintain background consistency:** If multiple missions in your campaign feature the same star system, background elements (suns, background_bitmaps, ambient light) should be the same or at least similar. Rules for missions that change location within the same star system:
  - Distant nebulae will likely look the same and be in the same positions in the sky.
  - Positions of suns or planet bitmaps could change.
  - Ambient light color will be the same, but intensity will change with distance from the sun.

## Environment: full (volumetric) nebula
Full nebula (also called volumetric nebula) fills the entire mission with volumetric fog and cloud sprites, reduces sensor/AWACS range, and replaces normal-space background bitmaps and stars with a colored sky pattern. Enable it with `environment.nebula.enabled: true`.

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
- `pattern` is the background sky color. It is **optional**. If omitted while `enabled: true`, the result is a completely black background with no stars (the optional cloud sprites and lightning are still active). Use this only when a featureless pitch black sky is intentional.
- `sensor_range` (Float, default `3000.0`) controls the AWACS/sensor radius. Ships beyond this range are invisible on radar.
- `storm` (String, default `"none"`) sets the lightning-storm intensity. Omitting `storm` (or setting it to `none`) suppresses all storm effects. Set it to `s_standard`, `s_medium`, `s_active`, or `s_emp` to enable progressively more intense lightning.
- `cloud_sprites` is an optional list of FSO nebula poof sprite tokens that fill the space. Omit the list to suppress the moving cloud layer entirely.

**Authoring rules:**
- **Do not add `fullneb` to `mission_info.flags` manually.** The converter injects this flag automatically when `environment.nebula.enabled: true`.
- **`background_bitmaps` must be empty.** The validator treats any authored background bitmaps as an error when full nebula is enabled, since they are not visible.
- **Suns are still allowed.** Background suns are visible inside the nebula and can be authored normally. They can be omitted for dense, dark nebula scenes, but a distant sun can add atmosphere.
- **The "at least 3 background nebula bitmaps" richness advisory does not apply** to full nebula missions. That warning is suppressed for missions with `environment.nebula.enabled: true`.
- **Increase visibility via design.** With reduced sensor range, players cannot easily navigate. Use visible `Terran NavBuoy` ships, clear HUD directives, and in-mission comms messages to guide the player, or create more compact missions. Do not rely on distant ships being visible or targetable.
- Volumetric nebula is often used to simulate gas giant atmospheres or supernova remnant systems.

**Dynamic nebula changes via SEXPs:**
You can modify the nebula at runtime using SEXPs — for example, `nebula-change-pattern`, `nebula-change-storm`, `nebula-toggle-poof`, `nebula-change-fog-color`. Consult `Documentation/FSO SEXPs/Backgrounds and Nebulae.txt` for the exact arguments before using them.

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
      arrival_cue: |
        ( true )
      departure_cue: |
        ( is-event-true-delay "Omega 2 done docking" 97 )
  wings:
    - name: "Alpha"
      template: "ulysses_fighter"
      count: 4
      position: [0.0, 0.0, 0.0]
      arrival_cue: |
        ( true )
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
FSIF `entities.waypoints` are invisible to the player in the actual mission. They do not create a HUD marker, radar contact, targetable object, visible model, or any other in-game cue that the player can follow. Use waypoints only for AI movement paths (`ai-waypoints`, `ai-waypoints-once`), hidden distance checks, and internal SEXP references such as `PathName:1`.

If the player needs to rendezvous at a location, fly toward a marker, identify a destination, or otherwise be guided to a point in-game, place an actual navigation buoy ship instead; use the canonical ship class `Terran NavBuoy`.

Refer to that ship name in briefing text, directives, messages, and SEXPs when the player needs a visible or targetable reference. Do not tell the player to "follow the waypoint" unless there is an actual visible object, such as a Nav Buoy, at that location.

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
- An available mission goal (objective) is marked with a grey TO-DO in the Goals menu. It turns completed (green) when the SEXP formula for it becomes true. It turns failed (red) when the SEXP formula can no longer logically become true (e.g., a ship that should be protected until departure is destroyed).
- The same available/completed/failed coloring rules apply to directive texts for events, but these are always visible in the "Directives" section on the HUD, not hidden in a menu. Important objectives should therefore always have a corresponding event with a `hud_directive_text`, not just a goal.
- **Directive text limitation — avoid event/goal references in the formula:** Events intended to display a directive text must use simple, directly-evaluable conditions. If the formula references another event or goal using `is-event-true-delay`, `is-event-false-delay`, `is-event-true-msecs-delay`, `is-event-false-msecs-delay`, `is-goal-true-delay`, or `is-goal-false-delay`, the directive will silently fail: the engine cannot determine at mission start whether such an event could ever become true or false, so the grey "pending" directive is never displayed on the HUD. Use direct object-state SEXPs (e.g., `is-destroyed-delay`, `is-cargo-known-delay`, `has-arrived-delay`, `percent-ships-destroyed`) in events that have a `hud_directive_text`.
- Try to include enough comms chatter (messages) in your missions to make them lively and prevent player boredom.

## Authoring dialogue (TTS voicing)

**Required fields:**
- Any mission containing voiced lines should explicitly define `tts_provider` under the `audio` section (valid options: `"google"`, `"elevenlabs"`, `"inworld"`, or `"none"`). Choose a provider and consistently use voices from its respective voice list across all missions, or use `"none"` if TTS generation will not be used.
- If TTS will be used, any **voiced** line (command briefing, briefing, debriefing, message) must provide `voice_name` (a valid voice identifier from your chosen TTS provider's documentation) for automatic TTS voice generation. See `Documentation/<Provider> TTS/voices.txt` for voice names along with their characteristics.

**Optional field:**
- `voice_style_instructions: String` — Optional "Director's Note" for the AI. This allows you to guide the delivery style.
  **Important:** The required complexity of this field depends on the chosen TTS provider:
  - **Google (Gemini TTS):** Supports and benefits from complex, sentence-like prompts (e.g., `"Military commander delivering a briefing with an authoritative tone"`, `"Shouting in panic while under heavy fire"`, `"Calm and robotic AI voice"`).
  - **ElevenLabs TTS:** Does *not* support complex sentence prompts. You must use simple, comma-separated word-style emotion tags (e.g., use `"energetic, agitated"`, `"shouting, panic"`, or `"calm, robotic"`).
  - **Inworld TTS:** Currently does not utilize the style instructions.

Unvoiced lines (text-only) should omit these fields.

**Supported locations:**
- `mission_flow.command_briefing.stages[*]`
- `mission_flow.briefing.stages[*]`
- `mission_flow.debriefing.stages[*]`
- `mission_flow.messages[*]`

**Example (message):**
```yaml
mission_flow:
  messages:
    - name: "Ambush warning"
      text: "It looks like an ambush!"
      voice_style_instructions: "energetic, agitated"  # optional style prompt
      voice_name: "Charon"                             # TTS voice name matching the provider
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
- **Pairs Only**: Multi-ship docking trees are not supported.
- **No Player Ships**: Player start ships cannot be pre-docked.
- **Reference Checks**: You must use only the names for ship dockpoints specified in `../FSO and fs2 format/ship-dockpoint-names.md`. Using unknown or malformed dockpoint names will cause errors.

Note: If one of the ships in a docked pair warps out of the mission (departs), it takes the other ship with it.

## Subsystems
- Subsystem names must match the per-ship canonical lists. See the documentation index for paths to the naming files.
- CAUTION: there are subtle spelling differences among ships (e.g., "communication" vs "communications", "engine" vs "engines"). When referring to subsystems (for example, when writing SEXPs), always consult the subsystem naming documentation.

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
Author reinforcements in `entities`. Omit `arrival_cue` on the referenced units so they remain callable (defaults to true). The referenced ships/wings must exist in entities.ships/entities.wings.

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

Apply these to every named friendly, hostile or unknown ship/wing whenever it appears in the relevant context. Other color tags (such as `$y` for locations/nav points/destinations, `$W` for emphasis, `$R` for warnings) are available — see the styling guide — but should be used very sparingly, if at all. Less is more. When in doubt, leave the text plain.

**Single-word vs. span syntax:**
- For a single word: `$h Rama` — colors "Rama" in hostile red.
- For a multi-word phrase: `$f{ GTC Fenris $}` — colors the entire span.

Note: Do not forget the color span closing tag (`$}`). Missing closing tag will result in errors.

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
Unlike briefing stages, debriefing stages are **not** simply displayed in the order they are defined. Instead, each debriefing stage is displayed if its `display_condition` SEXP is met. Authors should be careful to make the conditions for every stage sufficiently restrictive, so that incorrect text is never shown at the wrong time — for example, a stage describing a successful outcome should never use `( true )` as its condition, because that would cause it to display even when the mission was a failure. Prefer specific SEXPs such as `( is-event-true-delay "..." 0 )` to precisely target the intended outcome.

## Briefing Room Grid View

Unless the mission is very short and trivial, you should always author a briefing schematic view with relevant icons for every briefing stage. Note that briefings are authored from the commanding officer's point of view and depict a prediction of the mission events. They should not reveal any surprises or show things that the commander has no way of knowing in advance.

### Layout
The briefing room uses a grid on the **XZ plane**.
- **Intended Usage**: Place your icons on this XZ plane using 2D coordinates `[x, z]` (e.g. `map_position: [500, 1000]`).
- **Automatic Camera**: The briefing camera is automatically positioned to ensure that all your icons are in view.

### Icons
Author briefing icons using the string field `icon_type`.
- **icon_type**: Must be a canonical string (e.g., "Fighter", "Jump Node", "Waypoint").
- **display_class**: Conditionally required. The displayed ship class text and picture (e.g. "GTF Ulysses") when the icon is selected in-game.
  - **Ship icon types** (e.g., `"Fighter"`, `"Fighter Wing"`, `"Cruiser"`, `"Capital Ship"`, `"Transport"`, `"Support Ship"`, `"Bomber"`, `"Installation"`, `"Cargo"`, etc.): **must** author `display_class` with the actual ship class. Using `"Terran NavBuoy"` for a ship icon type is also an error.
  - **Non-ship icon types** (`"Waypoint"`, `"Jump Node"`, `"Planet"`, `"Small Planet"`, `"Asteroid Field"`, `"Unknown"`, `"Unknown Wing"`): **must omit** `display_class`. The converter automatically emits the safe default `"Terran NavBuoy"` for these icon types. Authoring `display_class` on a non-ship icon is an error.
  - **If specified:** Must be a valid ship class from `spacecraft-classes.md`.
- **team**: Must be "Friendly" (shown as green), "Hostile" (red) or "Unknown" (purple).
- **map_position**: List `[x, z]`.

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

**Notes:**
- If `map_position` is omitted, defaults to `[0, 0]`.
- A briefing icon with `icon_type: "Waypoint"` is only a briefing-room schematic symbol. It does **not** create a visible in-mission waypoint or player guidance marker.

## Message sender and priority literals
- Allowed sender strings include named ships and special senders like `"<any wingman>"` and `"#Command"` (Note: the angle brackets and hash character must not be omitted).
- Priorities must be authored exactly: `"Low"`, `"Normal"`, `"High"`.

Example
```lisp
(when
  (has-arrived-delay 4 "Tantalus")
  (send-message "<any wingman>" "High" "It looks like an ambush")
)
```

## Fighter and bomber weapon hardpoints
All available primary and secondary weapon banks (hardpoints) in fighters and bombers must have assigned weapons. The number of entries in the `weapons.primary` and `weapons.secondary` lists for a given ship must be equal to the number of hardpoints specified in `\Documentation\FSO and fs2 format\fighter_bomber_hardpoints.md`.

## Introducing new ships and weapons
If the mission is part of a campaign, then by default, all ships and weapons are unavailable to the player and their wingmen (Alpha, Beta, Gamma, Delta, Epsilon). They need to be explicitly allowed, either in the campaign FCIF file (`starting_loadout` section) or with the `allow-ship` and `allow-weapon` SEXPs (see "/FSO SEXPs/Mission and Campaign.txt"). The enabling SEXPs need to be executed **before** the mission that should have the ship/weapon available is loaded (that is, at the end of the previous mission).

## Providing alternative player ships
By default, the player and their wingmen will be restricted to the exact ship classes defined in the mission file for their starting wings. If you want to provide the player with strategic choices before the mission starts, you can use the `additional_ship_choices` field under `player_setup` to provide a pool of alternative ships. The player can then swap these extra ships into their friendly starting wings (Alpha, Beta, Gamma, Delta, Epsilon) using the loadout screen.

```yaml
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - { class: "GTF Hercules", count: 4 }
    - { class: "GTB Ursa", count: 2 }
```

Note: These ships also need to be unlocked for the player in FCIF or in previous missions (see "Introducing new ships and weapons" above).

## Providing the player with extra weapons
If you want to provide the player with alternative weapons in the loadout screen that are not equipped by default on any starting ships, you can list them in the `additional_weapons` field under `player_setup`:
```yaml
player_setup:
  start_ship: "Alpha 1"
  additional_ship_choices:
    - { class: "GTF Ulysses", count: 4 }
  additional_weapons:
    - "Avenger"
    - "Harbinger"
```

Note: These extra weapons also need to be unlocked for the player in FCIF or in previous missions (see "Introducing new ships and weapons" above).

The maximum possible quantities needed to fully equip all available banks of all player wings with these extra weapons are automatically calculated and included in the fs2 mission `Weaponry Pool` with an added 25% safety margin.

## Directional arrivals quick reference
- Directional `arrival_method` requires both `arrival_anchor` and `arrival_distance`.
- Docking Bay: in this case `arrival_distance` is forced to `0` and should be omitted.
- For wildcard anchors, use exact literals like "<any friendly player>".
- FSO SEXP docs refer to `arrival_method` as "arrival location" and `departure_method` as "departure location".

## Maximum mission scale recommendation
- Keep distances between all points of interest (ships, wings, waypoints, jump nodes) **below 20 km** whenever possible.
- Avoid `arrival_distance` values above **20,000** when using `arrival_anchor` on ships or wings.
- Avoid distances between any two objects or anchor-based arrival distances exceeding this recommendation, because large mission spaces can lead to long, uneventful travel times and thus boring missions.

## ASCII-only requirement for FSO-facing strings
FSO only supports ASCII characters reliably.

This rule applies to:
- campaign name and description
- mission metadata and fiction viewer filename
- ship, wing, waypoint, jump node, event, goal, and message names
- briefing, command briefing, debriefing, directive, and message text
- token strings such as ship classes, weapons, flags, music names, dockpoints, subsystem names, and other FSO-facing literals
- all string literals inside SEXPs

This rule does **not** apply to `voice_style_instructions`, because that field is used only for TTS generation and is not written into `.fs2`.

Use ASCII replacements when needed:
- use `'` instead of curly quotes
- use `-` instead of em dash or en dash
- use `...` instead of the single-character ellipsis

If you use a non-ASCII character in any FSO-facing field, it will cause an error.

## No double quotes allowed in FSO-facing strings
Double quotes `"` are not allowed in FSO-facing text fields, as they break the FSO parser. Use single quotes `'` instead.
Note: This rule does not apply to SEXP fields. Some SEXP tokens need to be wrapped in double quotes.

## SEXP Authoring Guidelines

### **Consult SEXP Documentation:** Always check the documentation in `Documentation/FSO SEXPs/` for the exact signature of any SEXP construct you intend to use.
Pay close attention to:
- **Operator Names:** Ensure exact spelling (e.g. use valid `ai-guard` operator, instead of non-existent `ai-guard-ship`).
- **Argument Types:** Verify the validity of all passed arguments. Does the SEXP operator expect a Ship Name, a Wing Name, or does it support both? Do not pass a wing name to a SEXP that only accepts ships (e.g., `is-cargo-known-delay`). If you need to check a wing, use a wing-compatible SEXP or list all individual ships.
  - **Priorities:** Most AI goals require a priority argument (0-200). Omitting this will cause crashes.
  - **Validate argument order:** Verify that all arguments are passed in the correct order.

Do not use any SEXP construct without reading and understanding its documentation first!

### **Choose the Right Tool**
Actively explore the SEXP documentation to find the best operator for your needs. For example, instead of constructing complex boolean logic to check if any ship in a group of ships is scanned, consider using `percent-ships-scanned`.

### SEXP String Formatting: Use Block Scalars

YAML offers two ways to write string values relevant to FSIF:
- **Flow scalars** — inline quoted strings (e.g., `"( true )"`)
- **Block scalars** — literal strings introduced by `|` (the pipe character), where content is written on indented lines below the key

**Rule: Always use block scalars (`|`) for all SEXP fields** (`arrival_cue`, `departure_cue`, `formula`, `initial_orders`, debriefing `display_condition`, etc.), even for single-line SEXPs.

**Why:** SEXPs frequently contain double quotes around entity names (ship names, message names, wildcards like `"<any wingman>"`). In a flow scalar string, every internal double quote must be escaped with a backslash (`\"`), which is error-prone and hard to read. Block scalars preserve content literally — no escape characters are needed.

**Do (block scalar):**
```yaml
arrival_cue: |
  ( has-arrived-delay 5 "GTD Bastion" )
```

**Don't (flow scalar — requires escaping):**
```yaml
arrival_cue: "( has-arrived-delay 5 \"GTD Bastion\" )"
```

Both produce the same string value for the converter, but the block scalar is clearer, less error-prone, and is the required style for FSIF authoring.

### **Boolean Literals:** Always use `( true )` and `( false )` for boolean arguments. Do not use integer literals `1` or `0`.
- **Incorrect:** `( ai-waypoints-once "Path" 89 0 3 )`
- **Correct:** `( ai-waypoints-once "Path" 89 ( false ) 3 )`
- Note: All booleans in SEXPs must be surrounded by spaces and enclosed in parentheses.

### **Avoid Optional Arguments in Initial Orders:**
- The `initial_orders` field in ship/wing definitions is parsed by a restricted parser that fails if optional SEXP arguments are used.
- If you need to use optional arguments for an AI goal (e.g., the distance argument in `ai-stay-near-ship`), **do not** put it in the `initial_orders` field.
- **Workaround:** Create a `when-true` event that runs immediately at mission start and assigns the goal using `add-goal`.
- **Example:**
```lisp
( when
   ( true )
   ( add-goal "GTSC Kepler" ( ai-stay-near-ship "GTD Stalwart" 89 1000 ) )
)
```

### Multiple initial AI orders
To assign multiple initial AI orders, simply list the SEXP operators line-by-line using a YAML block scalar. The orders will be executed consecutively, from first to last.

**Example:**
```yaml
ships:
  - name: "Beta 1"
    # ... other properties ...
    initial_orders: |
      ( ai-chase-any 89 )
      ( ai-guard "GTC Pollux" 60 )
      ( ai-warp-out 50 )
```

## Using the escort flag (monitoring list)
The `escort` ship flag adds the ship to the player's HUD monitoring list, displaying its hull integrity at all times. Despite the name, this feature should be used for **any ship of interest that needs to be monitored**, not just friendly escorted ships.

You should use the `escort` flag for:
- Friendly ships that the player needs to protect.
- Important enemy ships whose status the player needs to track (e.g., a fleeing enemy transport or a capital ship that must be destroyed).
- Any key mission-critical object where constant visibility of its health is beneficial to the player.

Note: Maintain escort list hygiene. Flag only the most important ships to prevent cluttering the HUD. If you have multiple escorted ships, you can use the `escort_list_priority` property to control their display order.

## Creating ship debris
You can use the optional `destroyed_before_mission_seconds` field to create ship debris at mission start. The value is the number of seconds before the mission start when the ship will be destroyed. Zero value (default) results in no destruction (normal ship spawning).

## Pitfalls, best practices and recommendations
Use this section as a practical sanity guide: each item describes the preferred authoring pattern and the common mistake or failure it prevents.

### Spawning, arrivals and authored entities
- `player_setup.start_ship` must exist in `entities`. It can be a standalone ship in `entities.ships` or a ship created by a starting wing such as `Alpha 1`.
- If the start ship is standalone, give it `arrival_cue: ( true )`; otherwise the player ship will not spawn at mission start.
- Do not put `arrival_method`, `arrival_anchor`, `arrival_distance`, `arrival_delay`, `arrival_cue`, `departure_method`, `departure_anchor`, `departure_delay`, `departure_cue`, `initial_orders`, `dock`, `docked_with`, `docker_point`, or `dockee_point` into `entities.ship_templates`. For standalone ships, author them on the ship; for wing members, author them on the wing.
- Use `arrival_cue` to control when an authored ship or wing appears. Do not use `ship-create` to spawn a ship or wing that already exists in YAML; `ship-create` is for creating brand-new dynamic objects.
- Leave enough physical clearance between spawned objects, especially around large ships. Tight placement can cause ships to spawn inside each other; cruisers are roughly 300 m long and destroyers roughly 2000 m long.

### Templates, names and references
- Use templates for repeated ship configurations to avoid repeating class/team/weapon data. Wings must use a template.
- Name waypoint paths clearly and reference individual points as `PathName:N` (1-based). Remember that waypoint points are hidden AI/logic references, not visible player navigation markers.
- Keep custom names short: ship, wing, waypoint, jump node, event, goal, message, and mission names should stay under 30 characters to avoid engine token-limit problems.
- Avoid name collisions across authored objects. Do not reuse the same name for different entities, and do not author a standalone ship whose name would already be created by a wing expansion such as `Alpha 1`.
- If your mission design calls for a player-visible navigation marker, use an actual ship with the `Terran NavBuoy` ship class. Do not use `entities.waypoints` for player guidance; they are invisible in-game.
- Reinforcement entries must reference ships and wings that are actually defined in `entities.ships` and `entities.wings`.
- Message names referenced from events must exist in `mission_flow.messages`.

### SEXP and token hygiene
- Use only canonical FSO tokens from the specification and reference docs. This applies to ship classes, weapons, subsystem names, dockpoint names, background textures, message priorities, and wildcard literals.
- Message priorities must be spelled exactly `"Low"`, `"Normal"`, and `"High"`.
- Use double quotes (`"`) for entity names inside SEXPs.
- Never place YAML-style `#` comments inside SEXP block scalars; put comments on surrounding YAML lines instead.
- Check every SEXP operator against the SEXP documentation: verify the operator name, argument order, argument count, and whether it expects ship names, wing names, or both.
- Many SEXPs are ship-only. If a SEXP does not accept a wing name, target a specific ship in the wing or choose a wing-compatible alternative.
- Jump nodes are not interchangeable with ships/wings/waypoints in SEXPs like `distance`. If you need a hidden reference point for internal distance/logic checks, place a waypoint there. If the player needs a visible or targetable reference at that location, place a `Terran NavBuoy` ship there instead.
- Use exact FSO weapon token strings as defined in the Tokens reference. Make sure to omit the lore prefixes. For example, write `ML-16 Laser`, not `GTW ML-16 Laser`.
- Check that goal formulas are not already true at mission start unless that is explicitly intended.
- Events with `hud_directive_text` must use simple, directly-evaluable conditions. Do **not** use `is-event-true-delay`, `is-event-false-delay`, `is-event-true-msecs-delay`, `is-event-false-msecs-delay`, `is-goal-true-delay`, or `is-goal-false-delay` in the formula of an event that has a `hud_directive_text`. The engine cannot initially evaluate whether such an event could ever become true, so the grey "pending" directive is never shown on the HUD. Use direct object-state checks (e.g., `is-destroyed-delay`, `has-arrived-delay`) instead.

### Docking
- Pre-spawn docking is for pairs only. Author docking only on the docker ship, as described in the dedicated Docking section above.
- Do not involve the player start ship in pre-spawn docking.
- Keep docking leadership coherent: the dockee should be the arrival leader with `arrival_cue: ( true )`, and the docker should use `arrival_cue: ( false )`. If this is wrong, the pair may fail to dock correctly or separate on arrival.
- Do not confuse docking (used to connect two ships; uses dockpoint names) with the `Docking Bay` arrival/departure method (which is used to spawn a new ship from another ship or make an existing ship depart into another ship; uses the "fighterbay" subsystem names).

### Reinforcements
- Keep reinforcements callable by not giving them a blocking `arrival_cue`. Reinforcement wings should omit `arrival_cue`; standalone reinforcement ships should use `arrival_cue: ( true )`.

### Collision checks for waypoint paths
- The Converter checks for potential collisions between larger ships moving along waypoint paths and **initial positions** of other larger ships. This check can produce spurious warnings because it does not account for the fact that ships may move from their initial positions during the mission. Always consider the planned mission flow movement of the referenced ships when reviewing these collision warnings.

### Red alert missions
- Missions with the `red_alert` flag inherit player ship (hull integrity and loadout) from the previous mission (they represent a mission that begins immediately after the previous mission ends). The briefing view shows only the first briefing stage text with no icons. If you want to carry more ships between missions, use the `red_alert_carry` flag on them (in both missions).

### Distance checks
- If your event SEXPs use distance check triggers, verify that they will not be triggered prematurely. Visalize the triggering object's initial location and predicted movement, then make sure it will not be in range of the trigger immediately at mission start, or come into range before the trigger should actually fire. Premature triggering of events with distance conditions is a common source of errors.

### Final review before conversion
After completing a mission file, do one deliberate review pass and confirm that:
- all referenced tokens are canonical and documented
- all custom names are unique and under 30 characters
- all reinforcement, event, and message cross-references resolve to defined objects
- all SEXPs use valid operators with compatible argument types and correct argument order
- standalone player starts, docking setups, and reinforcements are correctly defined
