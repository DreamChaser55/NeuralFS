# Converter Implementation Details

Purpose
- Implementation-focused notes on how the FSIF-to-FS2 converter emits data and normalizes inputs.
- For FSIF schema (fields, defaults, constraints), see ../specification.md
- For practical authoring guidance, see ../authoring-guide.md

---

## Current behavior

Environment: backgrounds and full nebula are emitted to .fs2. FSIF 1.1 uses separate environment.suns and environment.starbitmaps lists. Fog is no longer authored in FSIF; the writer always emits `+Fog Near Mult: 1.000000` and `+Fog Far Mult: 1.000000` in `#Mission Info`. Backgrounds are written in `#Background bitmaps` with `$Bitmap List`, +Flags: ( "corrected angles" ). The writer emits all `$Sun` entries first, then all `$Starbitmap` entries (including planets), each with `+Angles` and appropriate +Scale/+ScaleX/+ScaleY and +DivX/+DivY. Ambient light is authored in FSIF 2.6 as an RGB triplet `[red, green, blue]`, normalized internally to that same 3-channel representation, and packed back into the single integer required by `$Ambient light level` when writing `.fs2`. The asteroid_field is also written. FSIF 1.2 adds environment.nebula authoring; when environment.nebula.enabled is true, the writer emits +NebAwacs and +Storm in `#Mission Info`, emits +Neb2 and +Neb2 Poofs List in `#Background bitmaps` (after `$Ambient light level` and before `$Bitmap List`), and suppresses background starbitmaps. Background suns are still emitted.

Fiction Viewer: if the top-level `fiction_viewer` field is present, the converter emits `#Fiction Viewer` with `$File: <filename>`.

Ships: per-ship weapons loadouts are emitted in `#Objects` using +Primary Banks and +Secondary Banks; +Sbank Ammo is emitted when secondary ammo is provided (weapons.bank_ammo/secondary_ammo). Custom subsystem states are emitted as `+Subsystem: <name>` with optional `$Damage: <percent>` (percent damaged = 100 - health). A minimal `+Subsystem: Pilot` is always written.

Ship flags: +Flags and +Flags2 are emitted from entities.ships[*].flags (single list; the converter routes tokens to the correct bucket automatically). For a complete list of supported flags and their mapping, see `../../FSO and fs2 format/FSO_Tokens_Reference.md`.

Briefing/loadout lock flags (pre-launch): ship-locked/weapons-locked/primaries-locked/secondaries-locked prevent changing class/weapons for that ship in the loadout screen. Operational locks: afterburners-locked disables afterburner usage; lock-all-turrets disables all turrets until freed at runtime. Note: `no-shields` only affects fighters/bombers; it has no effect on larger ships. Related properties supported: +Respawn priority (respawn_priority), +Escort priority (escort_priority; emitted when "escort"), +Kamikaze Damage (kamikaze_damage or defaults to 1000 when "kamikaze" set), +Destroy At (destroy_at > 0), +Orders Accepted (orders_accepted_mask), and +Orders Accepted List (orders_accepted).

AI goals: wing-level and per-ship ai_goals are emitted. `entities.ship_templates` must not author `ai_goals`; initial orders belong to the concrete standalone ship or wing that inherits the template.

Wings placement:
- Wings carry a single centroid position (entities.wings[*].position). The converter computes individual ship locations during loading by arranging wing members in a straight line along the X axis, centered on the centroid, spaced 50 m apart by default (optionally overridden by a per-wing spacing value).

Wings waves: supported. Emits `$Waves`, `$Wave Threshold`, and optional `+Wave Delay Min`/`+Wave Delay Max` and `+Arrival delay`; `$Special Ship` is always 0 (wing leader is the first ship).

Localization: XSTR wrapping is applied to mission name/description, goals $MessageNew, and messages $MessageNew; other fields are not wrapped.

Mission flags: +Flags is computed from mission_info.flags using the FSO Mission::Mission_Flags order. Flags must be exact canonical tokens (case-sensitive, lowercase) as listed in the FSO Tokens Reference. Unknown flags are ignored with a warning. Examples: red_alert = 65536, scramble = 131072, both → 196608.

Validation: If the player's starting ship is standalone (not part of any wing), its arrival_cue must be `( true )` to spawn. The converter preserves SEXP text verbatim and will print a warning if this constraint is violated.

Briefing/Debriefing: if present, a `stages` key must exist (can be an empty list).

Music: when a top-level `audio` mapping is present in FSIF, the converter emits `#Music` with `$Event Music` and `$Briefing Music`. Both values are written verbatim (e.g., `mission_music: "1: Genesis"` -> `$Event Music: 1: Genesis`, `briefing_music: "Brief1"` -> `$Briefing Music: Brief1`). If neither is provided, `#Music` is omitted.

Reinforcements: FSIF 1.3 introduces canonical, entities-level authoring via `entities.reinforcement_wings` and `entities.reinforcement_ships`. The loader validates names, injects the "reinforcement" flag into the referenced wing/ship, and builds `#Reinforcements` entries. Guidance: reinforcement wings should omit `arrival_cue` so they are callable (defaults to `( true )`); standalone reinforcement ships should have `( true )` arrival cues. Member ships of a reinforcement wing do not need per-ship reinforcement flags. `mission_flow.reinforcements` is no longer supported.

Reinforcement $Type emission: The converter chooses `$Type` automatically; authors should not specify a type in FSIF. Rules:
- Wing entry → $Type: Attack/Protect
- Ship entry with class starting with "GTS " or "PVS " (support ships) → $Type: Repair/Rearm
- All other ship entries → $Type: Attack/Protect
Any authored `type` field in FSIF is ignored; FSIF 1.5 no longer supports overriding the auto-detected reinforcement type.

Events: if `mission_flow.events[*].directive_text` is present, the converter emits `+Objective: XSTR("...", -1)` under `#Events`. The directive appears on the HUD when it becomes possible for the player to fulfill the event and is greyed out once the event becomes true.

Waypoints/Jump Nodes: waypoint lists are emitted; top-level `jump_nodes` are emitted in `#Waypoints` as `$Jump Node` and `$Jump Node Name` (not counted in "lists total").

Docking: Pre-spawn inter-ship docking pairs are supported. Author docking only on the docker ship via `dock`. The converter:
- validates the pair and ensures exactly one leader with `$Arrival Cue: ( true )` (the dockee) and sets the docker to `( false )` if needed,
- emits `+Docked With`, `$Docker Point` (point on DOCKEE), and `$Dockee Point` (point on DOCKER) per FS2’s reversed naming,
- discards docking that involves the player start ship, with a warning.
Only pairs (2 ships) are supported; multi-ship docking trees are not supported in this version.
Names for $Docker Point and $Dockee Point must be canonical for the specific ship class; see ../../FSO and fs2 format/ship-dockpoint-names.md.

Subspace missions: Author "subspace" in mission_info.flags to mark a mission as taking place inside subspace. This sets bit 0 of $Mission Desc +Flags. A minimal subspace mission (only "subspace" set) emits "+Flags: 1". A minimal normal mission (no mission flags) emits "+Flags: 0".

Versioning:
- The converter currently emits `$Version: 23.1` in `#Mission Info`. This is the FSO version NeuralFS was developed against.
- **FSIF input support:** the converter accepts FSIF version `"2.7"` only.
  - Files authored against older FSIF versions must be updated before conversion; see the FSIF Migration Guide.

---

## Voice Filename Generation

The converter enforces automatic generation of voice filenames to ensure compatibility with FSO engine limits and filesystem uniqueness.

**Generation Logic:**
1.  **Source**: A "slug" is derived from the message name (if available) or the text content.
2.  **Sanitization**: Text is converted to lowercase, and non-alphanumeric characters are replaced with underscores.
3.  **Truncation**: The slug is strictly truncated to **25 characters**. This ensures that the final filename (including the `.wav` extension) never exceeds 29 characters, complying with the engine limit (< 30 chars).
4.  **Collision Handling**: The behavior depends on the configured **Voice Filename Strategy** (see below). By default ("Unique" mode), the converter checks recursively for existing files and renames the new file to avoid collision.

### Voice Filename Generation Strategies
The converter supports three strategies for managing voice filename collisions (when a generated filename matches a file that already exists on disk). These can be selected via the CLI (`--tts-mode`) or the GUI.

1.  **Unique (Default)**:
    -   **Behavior**: If `message.wav` exists, the converter generates a new unique filename by appending a deterministic counter (e.g., `message_1.wav`, `message_2.wav`). The base filename is truncated if necessary to respect the engine's length limits.
    -   **Use Case**: Preserves old assets; useful when converting multiple missions in a batch that might share common message names (like "Arrival") to prevent them from overwriting each other's audio files.

2.  **Overwrite**:
    -   **Behavior**: The converter uses the canonical filename (e.g., `message.wav`) even if it exists. The TTS engine forces generation, replacing the file on disk.
    -   **Use Case**: Updating voice lines after text changes; regenerating assets with a new voice model.

3.  **Keep**:
    -   **Behavior**: The converter uses the canonical filename (e.g., `message.wav`) even if it exists. The TTS engine *skips* generation for that file, preserving the existing audio.
    -   **Use Case**: Rapid iteration where only new lines need voicing; saving API costs.

**Output Location:**
Generated voice files are automatically sorted into FSO-compliant subfolders within the `voice` directory:
-   **Command Briefings**: `voice/command_briefings/`
-   **Mission Briefings**: `voice/briefing/`
-   **Debriefings**: `voice/debriefing/`
-   **Messages**: `voice/special/`

---

## Voice Generation Engine

The converter supports multiple Text-to-Speech providers. The user selects the provider at conversion time via the CLI (`--tts-provider`) or the GUI.

### 1. Google Gemini TTS (Default)
*   **Engine**: Google GenAI (`google-genai` library)
*   **Model**: `gemini-2.5-pro-preview-tts`
*   **Audio Format**: 24kHz, 16-bit Mono WAV
*   **Authentication Priority**:
    1. Key explicitly provided as an argument.
    2. `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) environment variable.
    3. `Gemini_API_key.txt` file in the converter directory.
    4. Vertex AI Application Default Credentials.

### 2. ElevenLabs TTS
*   **Engine**: ElevenLabs API (`elevenlabs` library)
*   **Model**: `eleven_multilingual_v2` (default, configurable via CLI)
*   **Audio Format**: `pcm_24000` (raw 24kHz PCM wrapped into WAV container by the converter)
*   **Authentication Priority**:
    1. Key explicitly provided as an argument.
    2. `ELEVENLABS_API_KEY` environment variable.
    3. `Elevenlabs_API_key.txt` file in the converter directory.

**Voice Lists and Parsing**:
The system loads allowed voices from the documentation folder corresponding to the selected provider:
*   **Google**: `Documentation/Google TTS/male_voices.txt` & `female_voices.txt`
*   **ElevenLabs**: `Documentation/ElevenLabs TTS/voices.txt`

Both use the `Name -- Characteristic` format. For ElevenLabs, the internal converter maps these human-readable names to their specific Voice IDs.

---

## Strict Validation System

The converter now employs a comprehensive **Strict Validation** system via a dedicated `Validator` class. Unlike previous versions which often emitted warnings and continued, the new system **aborts conversion** if any critical errors are found. This ensures that generated FS2 files are valid and crash-free.

### Validation Checks
The validator checks the following areas:

#### **Reference Integrity**:
*   **Ship Classes**: Must exist in `spacecraft-classes.md`.
*   **Dockpoints**: Must match the specific ship class in `ship-dockpoint-names.md`.
*   **Subsystems**: Must match the specific ship class in `Ship subsystems/*.md`.
*   **Voices**: TTS voice names must exist in `Google TTS/*_voices.txt`.

#### **Hardcoded Token Lists**:
*   Validates against stable lists for: Music, Briefing Icons, Background Textures (Suns, Planets, Nebulae), and Weapon Names.

#### **Docking Logic**:
*   **Completeness**: Requires both `docker_point` and `dockee_point`.
*   **Self-Docking**: Checks if a ship tries to dock with itself.
*   **Conflicts**: Ensures ships aren't involved in multiple pre-spawn docking definitions.
*   **Arrival Cues**: Strictly enforces that the **Dockee (Leader)** has `arrival_cue: ( true )` and the **Docker (Follower)** has `( false )`. Invalid configurations cause an error.
*   **Player Constraints**: Player ships cannot be involved in pre-spawn docking.

#### **Weapon Supply and Demand**:
*   The converter automatically calculates and generates the required primary and secondary weapon pool for all **Friendly** player starting wings, ensuring adequate supply: it reads secondary weapon bank capacities of all fighters and bombers and secondary weapon sizes, goes over the player wings and determines the weapon supplies needed to fill the banks with specified weapons. Before writing the values into .fs2, they are increased by a 25% safety margin.
*   If the FSIF author specifies `extra_weapons` under `player_setup`, the converter calculates the maximum possible quantities needed to fully equip all available banks of all player wings with these extra weapons. For primary extra weapons, the demand is based on the total number of primary banks across all ships in the player wings. For secondary extra weapons, the demand is based on the sum of capacities of all secondary banks across all ships in the player wings. This demand is merged with the existing demand (using the maximum value to avoid unnecessary double-counting) and also receives the 25% safety margin before emission.

#### **Detection of Empty Hardpoints**:
*   Checks all fighters and bombers for primary/secondary hardpoints with unassigned weapons: checks if the number of specified primary/secondary weapons is different than the number of hardpoints on the ship. Empty hardpoints can cause errors in FSO.

#### **Standalone Ship Wing-Name Pattern**:
*   Warns if a standalone ship (defined in `entities.ships`, not part of any wing) has a name that matches the common Terran wing-member pattern: `<Prefix> <Number>` where *Prefix* is one of **Alpha, Beta, Gamma, Delta, Epsilon** (e.g. `Alpha 1`, `Beta 3`).
*   This is almost always an authoring mistake — the intended approach is to define a wing via `entities.wings`. The warning is advisory and does not abort conversion.

#### **Reinforcements**:
*   Ensures all referenced ships and wings in `reinforcement_ships`/`reinforcement_wings` actually exist in the mission.

#### **Entities & Environment**:
*   Checks for valid team names, message priorities, and mission flags.
*   Validates background bitmaps and nebula patterns.
*   Warns if any sun in `environment.suns` has `angles: [0, 0, 0]` — this places the sun directly in front of the player at default spawn orientation, causing a whiteout blinding effect.
*   Warns if distances between any two objects or anchor-based arrival distances exceed 20,000 meters, as large mission spaces can lead to long travel times.

#### **ASCII Enforcement for FSO-facing Strings**:
*   FreeSpace Open only supports ASCII reliably for mission-facing content written into `.fs2`.
*   The validator rejects non-ASCII characters in FSO-facing FSIF strings before writing the output file.
*   This applies to authored strings that are emitted into `.fs2` or otherwise consumed by FSO mission parsing, including mission metadata, fiction viewer filename, ship/wing/object names, waypoint and jump node names, event/goal/message names and text, briefing/debriefing/command briefing text, briefing icon strings, audio tokens, docking/subsystem/weapon/token references, and all SEXP strings.
*   This does **not** apply to TTS-only fields such as `voice_name` and `voice_style_instructions`, because they are not written into `.fs2`.
*   On failure, the validator emits an error containing the field path and the offending character(s) with Unicode code points (for example `U+2014`) and aborts conversion.

#### **Double Quote Prohibition in XSTR Text**:
*   The validator strictly forbids double quotes (`"`) in any text field that is emitted into the `.fs2` file wrapped in an `XSTR("...", -1)` macro (such as `mission_info.name`, `mission_info.description`, event/goal/message text, and briefing/debriefing text).
*   This is because the FSO engine string parser does not properly handle escaped double quotes (`\"`) inside `XSTR` blocks, leading to "malformed string" debug errors.
*   Authors must use single quotes (`'`) instead of double quotes for quoting text or dialogue.
*   Note: Double quotes are still allowed (and required) inside S-expression strings (e.g., `arrival_cue`, `formula`).

#### **Text styling tags outside supported contexts**:
*   Warns if text styling tags are used outside supported contexts. These tags are intended only for fiction viewer, command briefing, mission briefing, and debriefing text. Usage in in-mission messages, goal text, directive text, or mission metadata fields triggers validator warnings.

#### **Span-style tag validation**:
*   Validates span-style color tags (e.g., `$c{ ... $}`) in supported text contexts (command briefing, mission briefing, and debriefing).
*   Warns if an opened span tag is left unclosed at the end of the text.
*   Warns if another style tag or a different color span opening tag is encountered before the current span is explicitly closed with `$}`.

#### **Global Name Integrity**:
*   Ensures names are unique within their respective namespaces: **Objects** (Ships, Wings, Waypoints, Jump Nodes), **Events**, **Goals**, and **Messages**.
*   Enforces a strict length limit of **< 30 characters** for all names to prevent engine truncation issues.

#### **SEXP Validation**:
*   **Parenthesis Integrity**: Checks for mismatched parentheses in formulas (Events, Goals, AI).
*   **YAML Leak Detection**: Checks for accidental inclusion of YAML comments (string `# `) inside SEXP blocks. Valid token strings like "#Command" don't trigger this, since they don't contain a space after the hash.
*   **Token Length**: Scans SEXP strings for individual tokens exceeding the 30-character limit.
*   **Note**: Voice filename length validation has been removed from the validator as it is strictly enforced by the generator logic.

#### **Debriefing Integrity**:
*   **Trivial `( true )` condition**: Warns if any debriefing stage uses `( true )` as its condition. An always-true condition causes the stage to display regardless of the mission outcome.

#### **Directive Text SEXP Compatibility**:
*   **Event/goal-referencing SEXPs in directive formulas**: Warns if an event with a `directive_text` uses `is-event-true-delay`, `is-event-false-delay`, `is-event-true-msecs-delay`, `is-event-false-msecs-delay`, `is-goal-true-delay`, or `is-goal-false-delay` in its formula.

#### **Briefing Integrity**:
*   **Teams**: Validates `icon.team` against allowed factions (Friendly, Hostile, Unknown).
*   **Classes**: Warns if `icon.class` appears to be a ship class (e.g. starts with "GT", "PV") but is not a known class.

#### **Strict Field Validation**:
*   **Extra Fields Forbidden**: The converter now strictly rejects *any* unknown fields in the FSIF YAML.
*   **Typo Detection**: If you make a typo in a field name (e.g., `arrival_dealy` instead of `arrival_delay`), the converter will abort with an "Extra inputs are not permitted" error. This ensures that no authored data is silently ignored.

#### **Ship Template Authoring Rules**:
*   `entities.ship_templates` may only contain reusable shared ship properties.
*   The loader rejects template-level authoring of `arrival_location`, `arrival_anchor`, `arrival_distance`, `arrival_delay`, `arrival_cue`, `departure_location`, `departure_anchor`, `departure_cue`, and `ai_goals`.
*   This is a hard error because those fields do not work correctly or are not semantically appropriate when inherited by ships that are part of a wing.
*   Correct authoring locations:
    *   Standalone ship: author the fields directly on the `entities.ships[*]` entry.
    *   Wing member: author the fields on the corresponding `entities.wings[*]` entry.

### Error Reporting
*   **Errors**: Critical issues (e.g., invalid ship class, broken docking logic, non-ASCII characters in FSO-facing fields) will print an error message and **fail the validation**, aborting the conversion.
*   **Warnings**: Minor issues (e.g., unknown mission flags, potential logic oddities) are logged but do not stop conversion.

## Advanced SEXP Validation

The converter includes an **Advanced SEXP Validator** that is enabled by default.

Unlike the standard validation which primarily checks structure (parentheses balance, token length), this layer performs full **semantic analysis** using the same logic as the FSO engine source code.

**Capabilities:**
*   **Recursive Type Checking:** It validates that every argument provided to a SEXP operator matches the expected type (e.g., ensuring `ai-chase` receives a Ship/Wing, a Priority number, and a Boolean, in that order). It understands return types (e.g., `when` returns Action/Void, `distance` returns Number) and enforces type safety throughout the formula tree.
*   **Atom Reference Validation:**
    *   **Ships/Wings:** Validates that names referenced in SEXPs actually exist in the mission.
    *   **Events/Goals/Messages:** Validates that event/goal/message names referenced in operators refer to valid entities.
*   **Operator Signatures:** Enforces minimum and maximum argument counts for all 670+ supported FSO operators.

---

## Environment emission notes (summary)

- Fog: always emits `+Fog Near Mult: 1.000000` and `+Fog Far Mult: 1.000000` in `#Mission Info`; FSIF no longer exposes fog authoring fields.
- Ambient light: internally normalized to `[red, green, blue]` and emitted into `$Ambient light level` as the packed FS2 integer.
- Backgrounds: all `$Sun` entries first, then `$Starbitmap` entries; `+Flags` includes "corrected angles".
- Nebula: when enabled, `+NebAwacs`, `+Storm`, `+Neb2`, optionally `+Neb2 Poofs List`.
- Full nebula results in background starbitmap suppression.

## Briefing emission and normalization

- Briefing camera calculation: The converter computes the tightest axis-aligned bounding box for the icons in the XZ plane, expands it if necessary to meet the 2.5 aspect ratio requirement, and positions the camera at XZ equal to the bounding box center and Y equal to the bounding box width with a 15% safety factor (clamped to a minimum of 1000m), looking directly down.

**Icon type normalization:**
- Authoring: icons[*].type is a canonical string; mission_loader normalizes it to the FS2 numeric `$type` using briefing_icon_types.py.
- Writer: emits `$type` from the normalized type_id and does not apply heuristic class/type coercions.
- Waypoint is 9; Jump Node is 33. The converter warns if older nav-buoy heuristics are detected.

**FS2 `$type` numeric mapping:**
- Canonical source of truth: `FSIF_to_FS2_Converter/briefing_icon_types.py`.
- The converter resolves `icons[*].type` strings to numeric IDs using that module and emits the resulting numeric `$type`.
- FSIF authors should provide canonical string names only; they do not author numeric codes directly.

**Class emission:**
- icons[*].class is emitted as `$class` (defaults to "Terran NavBuoy" when omitted). **If specified, it must be a valid ship class from `spacecraft-classes.md` (strict validation enforced to prevent FSO crashes).** The class value does not affect the icon silhouette; the silhouette is controlled solely by `icons[*].type`.
- **Important:** Authors should omit the `class` field for non-ship icons (Waypoints, Jump Nodes, Planets, Asteroid Fields) to use the safe default. Specifying an arbitrary string will cause validation failure.

Notes
- If an icon `pos` is omitted, the converter defaults the emitted position to 0.0, 0.0, 0.0.

## Arrival/Departure emission order

Ships (#Objects)
- Arrival emission order:
  1) $Arrival Location
  2) +Arrival Distance (if any)
  3) $Arrival Anchor (if any)
  4) $Arrival Cue
- Departure emission order:
  1) $Departure Location (Hyperspace | Docking Bay)
  2) $Departure Anchor (only when Docking Bay)
  3) $Departure Cue

Wings (#Wings)
- Arrival emission order:
  1) $Arrival Location
  2) +Arrival Distance (if any)
  3) $Arrival Anchor (if any)
  4) +Arrival delay (if provided)
  5) $Arrival Cue
- Departure emission order mirrors ships:
  1) $Departure Location
  2) $Departure Anchor (only when Docking Bay)
  3) $Departure Cue

Constraints and guidance
- Directional $Arrival Location values require both +Arrival Distance and $Arrival Anchor.
- Docking Bay commonly uses +Arrival Distance: 0.
- Player start spawning rule (recap): if the starting ship is standalone (not in a wing), its $Arrival Cue must be `( true )`.

## Asteroid/Debris Fields mapping

FS2 emission mapping (#Asteroid Fields)
- Section header remains `#Asteroid Fields` (FSO format requirement).
- $Density: <int>
- +Field Type: <0 active | 1 passive>
- +Debris Genre: <0 asteroid | 1 debris>
- +Field Debris Type Name: <string> (repeated for each entry)
- $Average Speed: <float>
- $Minimum: x, y, z
- $Maximum: x, y, z
- $Asteroid Targets: ( "Ship1" "Ship2" ... ) (only for active asteroid fields with non-empty targets)

Constraints and normalization (recap)
- Retail/FRED limitation: one asteroid/debris field per mission. The converter supports authoring as a single Mapping `asteroid_field`.
- Debris fields cannot be active; if authored as active, they are coerced to passive with a warning.
- Targets only apply to active asteroid fields; ignored otherwise (warning for debris).
- Divisors and bounds are normalized; min/max are swapped if authored inverted (warning).

## Internal Data Architecture

This section documents the internal data structures used by the converter (specifically the Pydantic models in `data_models.py`).

### Mission.ships vs Mission.wings
- **Mission.ships**: This list is a **comprehensive, flat collection of every ship object** in the mission. It includes:
  - Standalone ships (authored in `entities.ships`).
  - Individual members of wings (expanded from `entities.wings`).
  - This "flat list" design facilitates operations that need to iterate over all physical objects linearly, such as global validation or emitting the FS2 `#Objects` section.

- **Mission.wings**: This list preserves the logical grouping of wings.
  - Each `Wing` object contains a `ships` list referencing the specific `Ship` objects that belong to it.
  - **Shared References**: Ship objects that are part of a wing are referenced in **both** `Mission.ships` and `Mission.wings[i].ships`. They are the same object instances in memory.
