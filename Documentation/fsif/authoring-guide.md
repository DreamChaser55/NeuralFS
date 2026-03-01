# FSIF Authoring Guide

Purpose
- Help mission authors write correct, concise FSIF quickly.
- Provide best practices, common patterns, pitfalls, and curated examples.


Critical rules
- **Token fidelity**: Use exact canonical tokens only. Do not invent synonyms, alternative casing, or punctuation variants. SEXP names, wildcard literals, message priority strings, subsystem and dockpoint names must match exactly.
- **Token length limit**: All names (ships, wings, events, messages, etc.) must be < 30 characters.
- **SEXP fidelity**: FSIF embeds SEXP verbatim. The converter does not "fix" invalid SEXP.

Authoring checklist
- Use FSIF version: "2.5"
- player_setup.start_ship must exist in entities (could be part of a wing, but the referenced player ship name must exist after the wing is spawned).
- Unlike Ships, Wings must use a template.

## Minimal FSIF skeleton
- These are the minimum fields required for a valid FSIF file.

```yaml
fsif_version: "2.5"

mission_info:
  name: "Minimal Mission"

player_setup:
  start_ship: "Alpha 1"

entities:
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0, 0, 0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]

mission_flow: {}
```

## Standard FSIF skeleton
- Use this skeleton to bootstrap a typical mission. It includes optional but commonly used sections like `environment` and empty lists for easy expansion.

```yaml
fsif_version: "2.5"

mission_info:
  name: "Mission name string"
  author: "Author name string"
  description: "Mission description string"
  game_type: "single"
  flags: []
  ai_profile: "FS1 RETAIL"

environment:
  star_count: 500
  ambient_light_level: 0
  fog:
    near_mult: 1.0
    far_mult: 1.0
  suns: []
  starbitmaps: []
  nebula:
    enabled: false

player_setup:
  start_ship: "Alpha 1"
  extra_ships:
    - class: "GTF Ulysses"
      count: 1

entities:
  ship_templates: {}
  ships:
    - name: "Alpha 1"
      class: "GTF Ulysses"
      team: "Friendly"
      location: [0.0, 0.0, 0.0]
      arrival_cue: |
        ( true )
      weapons:
        primary: ["Avenger", "Avenger"]
        secondary: ["MX-50"]
  wings: []
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
```

Note: a valid FSIF mission must contain at least one ship (the player ship).

## Fiction Viewer
The Fiction Viewer allows you to display a text file before the mission starts. This is useful for lengthy narrative text or logs. If your mission design document contains cutscene descriptions but the cutscenes were not created, you can write their narrative content here.
```yaml
# Top-level field
fiction_viewer: "story.txt"
```
The file `story.txt` must exist in your mod's data/fiction folder.

Note: The referenced Fiction Viewer content is shown to the player as the **very first** thing in the course of the mission (before the Command Briefing).

## Environment backgrounds and nebulae
Author background suns and starbitmaps; full nebula is a separate feature and suppresses background bitmaps unless allowed.
```yaml
environment:
  star_count: 500
  ambient_light_level: 0
  fog:
    near_mult: 1.0
    far_mult: 1.0
  suns:
    - texture: SunWhite
      angles: [0.000000, 0.000000, 0.000000]
      scale: 1.0
    - texture: SunSiriusA
      angles: [0.087266, 0.000000, 0.226893]
      scale: 2.5
  starbitmaps:
    - texture: dneb03
      angles: [0.000000, 2.321286, 0.000000]
      scale: { x: 4.0, y: 4.0 }
      div: { x: 2, y: 2 }
    - texture: neb11
      angles: [0.401425, 0.663225, 0.139626]
      scale: { x: 2.0, y: 4.0 }
      div: { x: 1, y: 1 }
```
Notes
- angles are [pitch, bank, heading] in radians.
- **Sun angles warning:** Avoid setting any sun's `angles` to `[0.0, 0.0, 0.0]`. That direction points **directly in front of the player** when they spawn in the default position and orientation. Looking into a sun in FreeSpace produces a full-screen whiteout/blinding effect, which is highly disorienting and nearly always unintentional. Give every sun a non-zero heading or pitch so it is off to the side or above/below the player's forward view. The converter validator will emit a warning if `[0, 0, 0]` sun angles are detected.
- For full (volumetric) nebula authoring fields, see spec; emission details are in Converter Implementation Details.

## Templates, ships and wings
```yaml
entities:
  ship_templates:
    ulysses_fighter:
      class: "GTF Ulysses"
      team: "Friendly"
      ai_class: "General"
      flags: ["cargo-known"]
      weapons:
        primary: ["Prometheus", "Avenger"]
        secondary: ["Hornet"]
  ships:
    - name: "GTSC Rosetta"
      class: "GTSC Faustus"
      team: "Friendly"
      location: [542.6, 699.5, 1305.4]
      flags: ["no-shields", "escort"]
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
      ai_goals: |
        ( ai-chase-any 50 )
```

Wings must define `position: [x, y, z]`, which is interpreted as the centroid of all ships in the wing. In the example above, a 4‑ship wing with `position: [0.0, 0.0, 0.0]` will be emitted as four objects along the X axis at:

- Alpha 1: `[-75.0, 0.0, 0.0]`
- Alpha 2: `[-25.0, 0.0, 0.0]`
- Alpha 3: `[25.0, 0.0, 0.0]`
- Alpha 4: `[75.0, 0.0, 0.0]`

The converter spaces wing members 50 m apart by default and centers the line on the specified centroid.

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
      directive_text: "Destroy SF Dragon 1"
  goals:
    - name: "save rosetta"
      type: "Bonus"
      message: "Protect the Rosetta until it departs"
      formula: |
        ( is-event-true-delay "Rosetta departed" 0 )
  messages:
    - name: "Lucifer arrived"
      message: "That's the Lucifer arriving!"
      voice_name: "Fenrir"
```

Note: A mission goal (objective) turns completed when the SEXP formula for it becomes true. Until then, it is marked with TO-DO directive on the HUD. It turns failed when the SEXP formula can no longer logically become true (e.g., a ship that should be protected until departure is destroyed).

## Authoring dialogue (TTS voicing)

**Required field:**
Any **voiced** line (command briefing, briefing, debriefing, message) must provide `voice_name` (Google TTS voice identifier) for automatic TTS voice generation. See `Documentation/Google TTS/male_voices.txt` and `female_voices.txt` for voice names along with their characteristics.

**Optional field:**
- `voice_style_instructions: String` — Optional "Director's Note" for the AI. This allows you to guide the delivery style (e.g. `"Military commander delivering a briefing"`, `"Shouting in panic"`, `"Calm and robotic"`).

Unvoiced lines (text-only) should omit these fields.

Filenames of the resulting audio files are automatically generated from the text content or name, truncated to < 30 characters, and checked for collisions in their directory.

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
      message: "It looks like an ambush!"
      voice_style_instructions: "energetic, agitated"  # optional style prompt
      voice_name: "Charon"                             # Google TTS voice name
```

**Example (briefing stage):**
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Rendezvous at NavPath and scan the marked container."
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
      location: [-181.8, 0.0, 275.8]
      arrival_cue: |
        ( true )
    - name: "GTT Elysium 2"
      class: "GTT Elysium"
      team: "Friendly"
      location: [-230.3, 4.18, 355.34]
      arrival_cue: |
        ( false )
      dock:
        with: "GTC Fenris 1"
        docker_point: "topside docking"
        dockee_point: "Docking bay 1"
```
Strict Rules (Enforced by Validator):
- **Arrival Cues**: The Dockee (Leader) must have `( true )`. The Docker (Follower) must have `( false )`. The converter will abort if this is violated.
- **Pairs Only**: Multi-ship docking trees are not supported.
- **No Player Ships**: Player start ships cannot be pre-docked.
- **Reference Checks**: You must use only the names for ship dockpoints specified in `../FSO and fs2 format/ship-dockpoint-names.md`. Using unknown or malformed dockpoint names will cause validation errors.

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
      num_times: 1
      arrival_delay: 0
  reinforcement_ships:
    - name: "GTC Fenris 10"
      num_times: 1
```

## Briefing, debriefing and fiction viewer text styling
Text in command and mission briefings, debriefings and in the fiction viewer can be styled by special tags. See `\Documentation\FSO and fs2 format\briefing_text_styling.txt` for a guide.

**Recommended color conventions:**
- Friendly ships/wings: `$f{ Name $}` (IFF Friendly color — green by default)
- Hostile ships/wings: `$h{ Name $}` (IFF Hostile color — red by default)
- Locations, nav points, destinations: `$y{ Name $}` (Yellow)
- Key action verbs, commendations: `$W{ text $}` (Bright White)
- Warnings, failures, urgent directives: `$R{ text $}` (Bright Red)
- Positive outcomes: `$G word $|` (Bright Green)
- Atmospheric/flavor notes: `$e{ text $}` (Gray)

**Single-word vs. span syntax:**
- For a single word: `$h Rama $|` — colors "Rama" in hostile red; `$|` stops the color before the following punctuation or character.
- For a multi-word phrase: `$f{ GTC Fenris $}` — colors the entire span; requires FSO build 8786+.

**Example:**
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Rendezvous at $y{ Nav Buoy $} and $W scan $| the marked container. $h Rama $| will intercept — protect the $f{ GTC Fenris $}."
        voice_name: "Gacrux"
        icons: []

  debriefing:
    stages:
      - condition: |
          ( is-destroyed-delay 0 "GTC Fenris 1" )
        text: "The $f{ GTC Fenris $} was $R destroyed $|. $R{ We failed the escort. $}"
        voice_name: "Gacrux"
      - condition: |
          ( true )
        text: "$W{ Excellent work, $rank $callsign. $} The convoy withdrew $G successfully $|."
        voice_name: "Gacrux"
```

## Briefing Room Grid View

Unless the mision is very short and trivial, you should always author a briefing schematic view with relevant icons for every briefing stage. Note that briefings are authored from the commanding officer's POV and are depicting his prediction of the mission events. They should not reveal any surprises or show things that the commander has no way of knowing in advance.

### Layout
The briefing room uses a grid on the **XZ plane**.
- **Intended Usage**: Place your icons on this XZ plane using 2D coordinates `[x, z]` (e.g. `pos: [500, 1000]`).
- **Automatic Camera**: The converter automatically positions the briefing camera to ensure that all your icons are in view.

### Icons
Author briefing icons using the string field `type`. The converter maps it to the FS2 numeric `$type`.
- **Type**: Must be a canonical string (e.g., "Fighter", "Jump Node", "Waypoint").
- **Class**: Optional. The displayed ship class text and picture (e.g. "GTF Ulysses") when clicked when the icon is selected in-game.
  - **If omitted:** Defaults to `"Terran NavBuoy"` (safe default).
  - **If specified:** Must be a valid ship class from `spacecraft-classes.md` (strictly validated).
  - **Best practice:** Omit for non-ship icon types (Waypoints, Jump Nodes, Planets, Asteroid Fields) to use the safe default. Non-ship types must only use the `"Terran NavBuoy"` class, to prevent in-game errors.
  - **Invalid values will cause conversion to fail** (prevents FSO crashes).
- **Team**: Must be "Friendly" (shown as green), "Hostile" (red) or "Unknown" (purple).
- **Pos**: List `[x, z]`.

**Example:**
```yaml
mission_flow:
  briefing:
    stages:
      - text: "Alpha, rendezvous at the nav point and inspect the cargo."
        voice_name: "Achernar"
        icons:
          - { type: "Fighter", team: "Friendly", class: "GTF Ulysses", pos: [0, 0], label: "Alpha", highlighted: true }
          - { type: "Cargo", team: "Hostile", pos: [500, 200], label: "Rosetta Cargo" }
          - { type: "Waypoint", team: "Unknown", pos: [1000, 0], label: "Nav" }
```

**Notes:**
- If `pos` is omitted, defaults to `[0, 0]`.

## Message sender and priority literals
- Allowed sender strings include named ships and special senders like "<any wingman>" and "#Command" (Note: the angle brackets/hash must not be omitted)
- Priorities must be authored exactly: "Low", "Normal", "High"

Example
```lisp
(when
  (has-arrived-delay 4 "Tantalus")
  (send-message "<any wingman>" "High" "It looks like an ambush")
)
```

## Introducing new ships and weapons
If the mission is part of a campaign, then by default, all ships and weapons are unavailable to the player. They need to be explicitly allowed, either in the campaign FCIF file (`starting_loadout` section) or with the `allow-ship` and `allow-weapon` SEXPs (see "/FSO SEXPs/Mission and Campaign.txt"). The enabling SEXPs need to be executed **before** the mission that should have the ship/weapon available is loaded (that is, at the end of the previous mission).

## Fighter and bomber weapon hardpoints
All available primary and secondary weapon banks (hardpoints) in fighters and bombers must have assigned weapons. The number of entries in the `weapons.primary` and `weapons.secondary` lists for a given ship must be equal to the number of hardpoints specified in `\Documentation\FSO and fs2 format\fighter_bomber_hardpoints.md`.

## Providing alternative player ships
By default, the player and their wingmen will be restricted to the exact ship classes defined in the mission file for their starting wings. If you want to provide the player with strategic choices before the mission starts, you can use the `extra_ships` field under `player_setup` to provide a pool of alternative ships. The player can then swap these extra ships into their friendly starting wings (Alpha, Beta, Gamma, Delta, Epsilon) using the loadout screen.

```yaml
player_setup:
  start_ship: "Alpha 1"
  extra_ships:
    - { class: "GTF Hercules", count: 4 }
    - { class: "GTB Ursa", count: 2 }
```

## Automatic Weaponry Pool Generation
FSIF converter calculates the required weapon pool automatically based on the weapons equipped on the starting friendly wings (Alpha, Beta, Gamma, Delta, Epsilon). It adds a 25% safety margin and emits the pool data directly into the FS2 file. This prevents crashes and undersupply issues in-game.

## Providing the player with extra weapons
If you want to provide the player with alternative weapons in the loadout screen that are not equipped by default on any starting ships, you can list them in the `extra_weapons` field under `player_setup`:
```yaml
player_setup:
  start_ship: "Alpha 1"
  extra_ships:
    - { class: "GTF Ulysses", count: 4 }
  extra_weapons:
    - "Avenger"
    - "Harbinger"
```
The converter will automatically calculate the maximum possible quantities needed to fully equip all available banks of all player wings with these extra weapons, add the 25% safety margin, and include them in the mission Weaponry Pool.

## Directional arrivals quick reference
- Directional arrival_location requires both arrival_anchor and arrival_distance.
- Docking Bay typically uses arrival_distance 0.
- For wildcard anchors, use exact literals like "<any friendly player>".

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

**Rule: Always use block scalars (`|`) for all SEXP fields** (`arrival_cue`, `departure_cue`, `formula`, `ai_goals`, debriefing `condition`, etc.), even for single-line SEXPs.

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

### **Avoid Optional Arguments in Initial AI Goals:**
- The `ai_goals` field in ship/wing definitions is parsed by a restricted parser that fails if optional SEXP arguments are used.
- If you need to use optional arguments for an AI goal (e.g., the distance argument in `ai-stay-near-ship`), **do not** put it in the `ai_goals` field.
- **Workaround:** Create a `when-true` event that runs immediately at mission start and assigns the goal using `add-goal`.
- **Example:**
```lisp
( when
   ( true )
   ( add-goal "GTSC Kepler" ( ai-stay-near-ship "GTD Stalwart" 89 1000 ) )
)
```

### Multiple initial AI goals
To assign multiple initial AI goals, simply list the SEXP operators line-by-line using a YAML block scalar. The orders will be executed consecutively, from first to last.

**Example:**
```yaml
ships:
  - name: "Beta 1"
    # ... other properties ...
    ai_goals: |
      ( ai-chase-any 89 )
      ( ai-guard "GTC Pollux" 60 )
      ( ai-warp-out 50 )
```

## Basic SEXP Validation
The converter initially performs basic structural checks on all SEXP formulas (Events, Goals, AI Goals, Arrival/Departure Cues). While it does not fully compile the SEXP code, it catches common syntax errors that would crash the game engine.

### Checks Performed:
1.  **Parenthesis Balancing**: Ensures every opening `(` has a matching closing `)`.
    *   *Error*: `Mismatched parentheses (Open: 5, Close: 4)`
2.  **YAML Comment Leakage**: Detects if a YAML comment (`# `) was accidentally included in a multiline SEXP block.
    *   *Error*: `Likely YAML comment leakage ('# ' found).`
    *   *Fix*: Move YAML comments outside the block scalar.
3.  **Token Length**: Scans for tokens longer than 30 characters.
    *   *Error*: `Token 'VeryLongName...' length 35 exceeds limit (<30).`
    *   *Note*: Quoted strings (like messages) are ignored by this check.

## Advanced SEXP Validation
The converter also checks all SEXPs with the Advanced SEXP Validator, which parses them and checks them against a set of FSO engine rules, returning actionable warning/error messages if any errors are found.

## Best practices
- Use templates for repeated ships and wings; avoid repeating class/team/weapon configs.
- Escort list hygiene: only flag important ships with "escort"; set priorities to keep the HUD useful.
- Message priorities: use canonical "Low", "Normal", "High". Do not vary case.
- Reinforcements: keep arrival_cue at default (implicitly true) for callable units; avoid blocking conditions.
- Waypoints: name paths clearly; reference points with "PathName:N" (1-based).
- If your mission design calls for a navigation buoy, use the 'Terran NavBuoy' spacecraft class
- When writing SEXPs, always use YAML block scalars (`|`) instead of flow scalar (quoted) strings, even for single-line SEXPs. Block scalars preserve content literally and eliminate the need for escape characters. See the "SEXP String Formatting: Use Block Scalars" section for details.
- Use double quotes (`"`) for all entity names inside SEXPs.

## Pitfalls and how to avoid them
- Player start not spawning:
  - If the start_ship is standalone (not in a wing), its arrival_cue must be "( true )".
- Ships spawning inside other ships:
  - Ensure sufficient separation between ships. Clearance should be kept in mind particularly around large ships. Cruisers are ~300 m long, destroyers are ~2000 m long.
- Mistakenly including YAML "#" inside SEXP blocks:
  - Never place YAML-style comments inside block scalars; add comments on lines outside the block. The validator will flag this as an error.
- Avoid long tokens in SEXPs:
  - Names used in SEXPs must fit engine token limits; keep them short (less than 30 chars). The validator enforces this limit strictly.
- Name collisions:
  - Do not use the same name for different types of objects (e.g., a Ship and a Wing with the same name). The validator ensures names are unique within their namespace (Objects, Events, Goals, Messages).
- Multiple asteroid/debris fields are not allowed:
  - Engine constraint: FSO supports only one asteroid/debris field. The converter enforces this.
  - Requirement: Use a single mapping for `environment.asteroid_field` (singular).
- Docking leadership conflicts:
  - Exactly one ship in the pair should have arrival_cue true; prefer the dockee (leader).
- Mistakenly using `ship-create` to spawn a defined ship/wing:
  - `ship-create` is for creating brand new dynamic objects. To delay the arrival of a ship you authored in YAML, simply use its `arrival_cue`.
  - In general, you should only use SEXPs if the thing you are trying to do cannot be accomplished by other means.
- Using Wing names in Ship-only SEXPs:
  - Many SEXPs (like `change-iff`, `percent-ships-scanned`, `distance`) require **Ship** names and will fail if given a **Wing** name. Check the SEXP documentation carefully. If needed, target a specific ship in the wing (e.g. "Alpha 1") or use a wing-compatible alternative.
- Using Jump Nodes in SEXPs:
  - Jump Nodes are special objects and cannot be targeted by most SEXPs that accept Ships or Wings (e.g., `distance`). If you need to measure distance to a jump node, place a Waypoint or NavBuoy at the same coordinates and target that instead.
- Correct weapon name token strings:
  - In Freespace lore, weapon names are sometimes mentioned with the "GTW" prefix. This prefix should **not** be used in FSO weapon token strings (e.g., use `ML-16 Laser` instead of `GTW ML-16 Laser`). Consult any used token strings with the exact spellings in `FSO_Tokens_Reference.md`.
- mission_flow.goals that immediately become true at the start of the mission:
  - A common mistake. Always verify that the SEXP formula for the goal is not immediately true at the start of the mission.

## Final checks
- Ensure that all used tokens are valid FSO tokens rerefenced in the documentation files.
- Make sure that all referenced ship class names, subsystem names, dockpoint names, weapons, background bitmaps etc. are valid and documented FSO token strings. Referencing a non-existent or malformed token string will cause crashes!
- Verify that all used SEXP operators are valid and documented SEXP operators. Double-check all their arguments for any omissions or type mismatches.
- Ensure that all your custom tokens are shorter than 30 characters. This applies to names of mission files, ships, wings, events, messages, goals, mission_info.name and description etc.. When in doubt, always prefer shorter names/designations to avoid the risk of exceeding the token string length limit.
- Ensure that all ship/wing names referenced in entities.reinforcement_ships/entities.reinforcement_wings are actually defined in entities.ships/entities.wings.
- Ensure that all message names referenced in events are actually defined in mission_flow.messages.

Important: after you first complete a mission file, always do at least one final review/checking pass (using the above checklist) to uncover and fix any possible mistakes.

## Troubleshooting (symptoms → likely cause)
- Start ship doesn’t appear at mission start → standalone start_ship missing arrival_cue "( true )"
- Reinforcement cannot be called → explicit arrival_cue set to a blocking condition; omit it
- Docked pair fails or separates on arrival → player ship involved; missing/incorrect dock.* fields; conflicting arrival leadership
- Errors about "redundant ship" → Do not author a standalone ship with the same name as a ship that would result from an existing wing expansion. For example: if there is a wing named "Alpha", which will create a ship named "Alpha 1" when spawned, you must not author a separate "Alpha 1" ship.

## Note on "Neutral" IFF
- The FSO engine theoretically supports a "Neutral" IFF team, but its implementation is broken — it essentially acts as a second Hostile faction and attacks the player. Because this behavior is misleading and redundant, FSIF does not support the "Neutral" team.
- Use "Friendly", "Hostile" or "Unknown" for all ships, objects or briefing icons.
