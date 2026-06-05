# Converter Implementation Details

Purpose
- Implementation-focused notes on how the FSIF-to-FS2 converter emits data and normalizes inputs.
- For FSIF schema (fields, defaults, constraints), see ../specification.md
- For practical authoring guidance, see ../authoring-guide.md

---

## Current behavior

Environment: backgrounds and full nebula are emitted to .fs2. FSIF uses separate environment.suns and environment.background_bitmaps lists. Fog is no longer authored in FSIF; the writer always emits `+Fog Near Mult: 1.000000` and `+Fog Far Mult: 1.000000` in `#Mission Info`. Backgrounds are written in `#Background bitmaps` with `$Bitmap List`, +Flags: ( "corrected angles" ). The writer emits all `$Sun` entries first, then all `$Starbitmap` entries (including planets), each with `+Angles` and appropriate +Scale/+ScaleX/+ScaleY and +DivX/+DivY. Ambient light is authored as an RGB triplet `[red, green, blue]`, normalized internally to that same 3-channel representation, and packed back into the single integer required by `$Ambient light level` when writing `.fs2`. The asteroid_field is also written. When environment.nebula.enabled is true, the writer emits +NebAwacs and +Storm in `#Mission Info`, emits `+Neb2: <pattern>` in `#Background bitmaps` (after `$Ambient light level` and before `$Bitmap List`). If no pattern was authored the value is empty, producing a completely black sky with no stars. Optionally emits `+Neb2 Poofs List` when cloud_sprites are present, and suppresses background bitmaps but still emits suns (suns remain visible in full-nebula missions).

Fiction Viewer: if `mission_flow.fiction_viewer` is present, the converter emits `#Fiction Viewer` with `$File: <filename>`.

Ships: per-ship weapons loadouts are emitted in `#Objects` using +Primary Banks and +Secondary Banks; +Sbank Ammo is emitted when secondary ammo is provided (weapons.secondary_ammo_counts). Custom subsystem states are emitted as `+Subsystem: <name>` with optional `$Damage: <percent>` (percent damaged = 100 - health). A minimal `+Subsystem: Pilot` is always written.

Ship and wing orientation: FSIF `orientation` values are emitted directly into FS2 `$Orientation:` blocks in row-major order. The converter does not transpose matrices, infer target-facing vectors, or convert between math-library and FSO/FRED orientation conventions. Authors must provide the FSO/FRED-compatible 9-float matrix themselves; see the FSIF Authoring Guide for the FRED-verified yaw-only formula.

Ship flags: +Flags and +Flags2 are emitted from entities.ships[*].flags (single list; the converter routes tokens to the correct bucket automatically). For a complete list of supported flags and their mapping, see `../../FSO and fs2 format/FSO_Tokens_Reference.md`.

Briefing/loadout lock flags (pre-launch): ship-locked/weapons-locked/primaries-locked/secondaries-locked prevent changing class/weapons for that ship in the loadout screen. Operational locks: afterburners-locked disables afterburner usage; lock-all-turrets disables all turrets until freed at runtime. Note: `no-shields` only affects fighters/bombers; it has no effect on larger ships. Related properties supported: +Respawn priority (respawn_priority), +Escort priority (escort_list_priority; emitted when the `escort` flag is present or `escort_list_priority > 0`; the validator requires the `escort` flag to be set whenever `escort_list_priority` is non-zero), and +Destroy At (destroyed_before_mission_seconds > 0).

AI goals: wing-level and per-ship initial_orders are emitted.

Wings placement:
- Wings carry a single centroid position (entities.wings[*].position). The converter computes individual ship locations during loading by arranging wing members in a straight line along the X axis, centered on the centroid, spaced 50 m apart by default (optionally overridden by a per-wing `member_spacing` value).
- **Wing-member arrival_cue invariant:** Every expanded wing-member Ship object is assigned `arrival_cue: '( false )'` unconditionally during loading, regardless of the runtime `Ship.arrival_cue` default. This ensures that individual ship entries in the FS2 `#Objects` section never trigger independent arrivals; wing arrival is controlled entirely by the wing-level `$Arrival Cue:` in `#Wings`. Authors cannot override per-member cues because `arrival_cue` is forbidden in `ship_templates`.

Wings waves: supported. Emits `$Waves`, `$Wave Threshold`, and optional `+Wave Delay Min`/`+Wave Delay Max` and `+Arrival delay`; `$Special Ship` is always 0 (wing leader is the first ship).

Localization: XSTR wrapping is applied to mission name/description, goals $MessageNew, and messages $MessageNew; other fields are not wrapped.

Mission flags: +Flags is computed from mission_info.flags using the FSO Mission::Mission_Flags order. Flags must be exact canonical tokens (case-sensitive, lowercase) as listed in the FSO Tokens Reference. Unknown flags are ignored with a warning. Examples: red_alert = 65536, scramble = 131072, both → 196608.

Validation: `player_setup.start_ship` must be a member of a Friendly `Alpha`, `Beta`, or `Gamma` wing — standalone player starts are a hard validation error that aborts conversion. The converter preserves SEXP text verbatim and will print an error for any SEXP validation failures it detects.

Briefing/Debriefing/Command Briefing: these sections are optional. If present, their `stages` key may be omitted, set to `null`, or set to an explicit list; omitted and `null` values both normalize to an empty list. Briefing stage `icons` likewise may be omitted or `null` and normalize to an empty list. The writer still emits the corresponding FS2 sections with zero stages when no stages are present.

Music: when a top-level `audio` mapping is present in FSIF, the converter emits `#Music` with `$Event Music` and `$Briefing Music`. Both values are written verbatim (e.g., `mission_music: "1: Genesis"` -> `$Event Music: 1: Genesis`, `briefing_music: "Brief1"` -> `$Briefing Music: Brief1`). If neither is provided, `#Music` is omitted.

Reinforcements: FSIF uses canonical, entities-level authoring via `entities.reinforcement_wings` and `entities.reinforcement_ships`. The loader validates names, injects the "reinforcement" flag into the referenced wing/ship, and builds `#Reinforcements` entries. Guidance: reinforcement wings should omit `arrival_cue` so they are callable (defaults to `( true )`); standalone reinforcement ships should also omit `arrival_cue` (it defaults to `( true )`). Member ships of a reinforcement wing do not need per-ship reinforcement flags. `mission_flow.reinforcements` is no longer supported.

Reinforcement $Type emission: The converter chooses `$Type` automatically; authors should not specify a type in FSIF. Rules:
- Wing entry → $Type: Attack/Protect
- Ship entry with class starting with "GTS " or "PVS " (support ships) → $Type: Repair/Rearm
- All other ship entries → $Type: Attack/Protect
Any authored `type` field in FSIF is ignored; overriding the auto-detected reinforcement type is not supported.

Reinforcement $Num times emission: The converter emits `$Num times` for every reinforcement entry because the FSO parser expects it.
- Wing entry → emits `$Num times: <max_uses>` (the authored `max_uses` value; default 1).
- Ship entry → always emits `$Num times: 1` (hardcoded). FSO's `$Num times` field is a no-op for single-ship reinforcements; `max_uses` is therefore not a supported field in `entities.reinforcement_ships`.

Events: if `mission_flow.events[*].hud_directive_text` is present, the converter emits `+Objective: XSTR("...", -1)` under `#Events`. The directive appears on the HUD when it becomes possible for the player to fulfill the event and is greyed out once the event becomes true.

Waypoints/Jump Nodes: waypoint lists are emitted; top-level `jump_nodes` are emitted in `#Waypoints` as `$Jump Node` and `$Jump Node Name` (not counted in "lists total").

Docking: Pre-spawn inter-ship docking pairs are supported. Author docking only on the docker ship via `dock`. The converter:
- validates the pair and strictly enforces that the dockee (leader) has `arrival_cue: ( true )` and the docker (follower) has `arrival_cue: ( false )`; any other configuration (both `( true )`, both `( false )`, or docker `( true )` / dockee `( false )`) is a hard error that aborts conversion,
- emits `+Docked With`, `$Docker Point` (point on DOCKEE), and `$Dockee Point` (point on DOCKER) per FS2's reversed naming,
- aborts conversion with an error if either ship in the docking pair is the player start ship; player ships cannot be pre-spawn docked.
Only pairs (2 ships) are supported; multi-ship docking trees are not supported in this version.
Names for $Docker Point and $Dockee Point must be canonical for the specific ship class; see ../../FSO and fs2 format/ship-dockpoint-names.md.

Subspace missions: Author "subspace" in mission_info.flags to mark a mission as taking place inside subspace. This sets bit 0 of $Mission Desc +Flags. A minimal subspace mission (only "subspace" set) emits "+Flags: 1". A minimal normal mission (no mission flags) emits "+Flags: 0".

Versioning:
- The converter currently emits `$Version: 23.1` in `#Mission Info`. This is the FSO version NeuralFS was developed against.
- **FSIF input support:** the converter accepts FSIF version `"1.0"` only.

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

The converter supports multiple Text-to-Speech providers. The user selects the provider via the CLI (`--tts-provider`), the GUI, or the FSIF `audio.tts_provider` field. If TTS generation is requested but no real provider is selected, or if the resolved provider is `none`, the converter logs a warning and skips TTS generation. There is no implicit default provider.

### 1. Google Gemini TTS
*   **Engine**: Google GenAI (`google-genai` library)
*   **Model**: `gemini-3.1-flash-tts-preview`
*   **Audio Format**: 24kHz, 16-bit Mono WAV
*   **Authentication Priority**:
    1. Key explicitly provided as an argument.
    2. `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) environment variable.
    3. `Gemini_API_key.txt` file in the `API_keys` directory.
    4. Vertex AI Application Default Credentials.

### 2. ElevenLabs TTS
*   **Engine**: ElevenLabs API (`elevenlabs` library)
*   **Model**: `eleven_v3` (default, configurable via CLI)
*   **Audio Format**: `pcm_24000` (raw 24kHz PCM wrapped into WAV container by the converter)
*   **Authentication Priority**:
    1. Key explicitly provided as an argument.
    2. `ELEVENLABS_API_KEY` environment variable.
    3. `Elevenlabs_API_key.txt` file in the `API_keys` directory.

**Voice Lists and Parsing**:
Allowed voice names for each provider are loaded from the documentation folder by `common/parsers_and_generators/generate_fs_data.py` and stored in `common/fs_data.py` as provider-specific sets:
*   **Google**: `Documentation/Google TTS/male_voices.txt` & `female_voices.txt` → `ALLOWED_VOICES_GOOGLE`
*   **ElevenLabs**: `Documentation/ElevenLabs TTS/voices.txt` → `ALLOWED_VOICES_ELEVENLABS`
*   **Inworld**: `Documentation/Inworld TTS/voices.txt` → `ALLOWED_VOICES_INWORLD`

All three files use the `Name -- Characteristic` format. For ElevenLabs, the internal converter maps these human-readable names to their specific Voice IDs.

**Provider-aware voice validation**: `Validator.load_reference_data()` selects the correct voice set when a real provider is explicitly specified: `google` → `ALLOWED_VOICES_GOOGLE`, `elevenlabs` → `ALLOWED_VOICES_ELEVENLABS`, and `inworld` → `ALLOWED_VOICES_INWORLD`. Voice-name validation runs against the selected set for all voiced lines in messages, briefing, debriefing, and command briefing even when TTS generation is disabled. If no real provider is specified, voice-name validation is skipped because the converter cannot know which provider catalogue to use.

---

## Strict Validation System

The converter employs a comprehensive **Strict Validation** system via a modular `Validator` class (implemented using Mixins across the `validator/` package). This system accumulates all critical errors found during the validation pass, logs them comprehensively, and then aborts the conversion before generating the final FS2 file. This ensures that generated FS2 files are valid and crash-free.

### Validator Architecture
The validator is structured as a single `Validator` class built using a Python Mixin pattern across a dedicated `validator/` package. The base state and execution flow are managed in `core.py`, while specific validation domains are separated into specialized mixin modules:

| Mixin (`validator/*.py`) | Primary responsibilities |
|---|---|
| `ascii_checks` | ASCII-only enforcement and double-quote prohibition in XSTR text for all FSO-facing string fields |
| `sexp_checks` | SEXP parenthesis balance, YAML comment leakage, token length, basic operator validity; directive-text SEXP compatibility |
| `spatial` | Mission scale and 3D design advisories; hyperspace spawn collisions; waypoint path collisions; shared waypoint order conflicts |
| `ship_wing_checks` | Ship class/team/flag/AI class/weapon compatibility/hardpoint validation; wing count and flag checks; standalone wing-name pattern advisory; docking pair validation; reinforcement reference validation; arrival/departure anchor validation with fighterbay check; player setup and start-ship validation; large-ship escort recommendation |
| `environment` | Sun, background bitmap, and full-nebula token validation; asteroid/debris field object-variant and target-ship validation |
| `briefing` | Span-style tag balancing; text-styling scope and mission-level color-tag presence checks; briefing stage voice/icon/proximity validation; debriefing stage condition and voice validation; command briefing stage voice validation |
| `misc` | Global name uniqueness and length enforcement (Objects, Events, Goals, Messages namespaces); mission-info flag validation; message voice-name validation; audio music-token validation; goals-vs-directives count advisory |

This modular design prevents a monolithic class structure while allowing all checks to seamlessly share and modify the internal validation state.

### Validation Checks
The validator checks the following areas:

#### **Reference Integrity**:
*   **Ship Classes**: Must exist in `spacecraft-classes.md`.
*   **Dockpoints**: Must match the specific ship class in `ship-dockpoint-names.md`.
*   **Subsystems**: Must match the specific ship class in `Ship subsystems/*.md`.
*   **Voices**: TTS `voice_name` values are validated against the provider-specific voice registry loaded by `Validator.load_reference_data()` when a real provider is specified: `ALLOWED_VOICES_GOOGLE` for Google, `ALLOWED_VOICES_ELEVENLABS` for ElevenLabs, and `ALLOWED_VOICES_INWORLD` for Inworld. Voice-name validation also runs when TTS generation is disabled as long as a real provider was specified by CLI/GUI or FSIF. If no provider is specified, voice-name validation is skipped. Voice registries are derived from the provider documentation files in `Documentation/<Provider> TTS/`. See the Voice Generation Engine section above for details.

#### **Hardcoded Token Lists**:
*   Validates against stable lists for: Music, Briefing Icons, Background Textures (Suns, Planets, Nebulae), and Weapon Names.

#### **Docking Logic**:
*   **Completeness**: Requires both `docker_point` and `dockee_point`.
*   **Self-Docking**: Checks if a ship tries to dock with itself.
*   **Conflicts**: Ensures ships aren't involved in multiple pre-spawn docking definitions.
*   **Arrival Conditions**: Strictly enforces that the **Dockee (Leader)** has `arrival_cue: ( true )` and the **Docker (Follower)** has `arrival_cue: ( false )`. Invalid configurations cause an error.
*   **Player Constraints**: Player ships cannot be involved in pre-spawn docking.

#### **Weapon Supply and Demand**:
*   The converter automatically calculates and generates the required primary and secondary weapon pool for all **Friendly Alpha, Beta, and Gamma wings** (the only three wings shown on the FSO loadout screen), ensuring adequate supply: it reads secondary weapon bank capacities of all fighters and bombers and secondary weapon sizes, goes over those wings and determines the weapon supplies needed to fill the banks with specified weapons. Before writing the values into .fs2, they are increased by a 25% safety margin.
*   If the FSIF author specifies `additional_weapons` under `player_setup`, the converter calculates the maximum possible quantities needed to fully equip all available banks of the Alpha/Beta/Gamma player wings with these extra weapons. For primary extra weapons, the demand is based on the total number of primary banks across all ships in those wings. For secondary extra weapons, the demand is based on the number of missiles that can fit into all secondary banks across all ships in those wings (calculated by dividing each bank's capacity by the weapon's cargo size). This demand is merged with the existing demand (using the maximum value to avoid unnecessary double-counting) and also receives the 25% safety margin before emission.

#### **Detection of Empty Hardpoints**:
*   Checks all fighters and bombers for primary/secondary hardpoints with unassigned weapons: checks if the number of specified primary/secondary weapons is different than the number of hardpoints on the ship. Empty hardpoints can cause errors in FSO.

#### **Ship-Weapon Class Compatibility**:
*   Validates whether each weapon assigned to a player-loadout wing fighter or bomber is allowed on that ship class, using data extracted directly from the FSO ship tables (`WEAPON_COMPATIBILITY`).
*   **Scope**: Compatibility is enforced as a **hard error** only for ships that belong to Friendly **player-loadout wings** — wings named `Alpha`, `Beta`, or `Gamma`. These are the only wings shown on the FSO loadout screen, where FSO enforces compatibility. For all other ships (Delta/Epsilon wings, non-player/NPC wings, standalone NPC ships, or enemy ships), an incompatible weapon assignment is not a problem and is ignored.

#### **Cargo Field Constraints**:
*   **Error** — `cargo` is defined on a ship whose class is not a transport (`GTT Elysium`, `PVT Isis`, `ST Azrael`) or a cargo container (`TC 2`, `TSC 2`, `TAC 1`, `TTC 1`, `VC 3`, `VAC 4`, `SC 5`, `SAC 2`). Only transports and cargo containers support the `cargo` string in FSO; defining it on any other class (fighters, bombers, cruisers, freighters, etc.) is an error. Fix: remove the `cargo` field from the ship.
*   **Warning** — A *Friendly* transport or cargo container does not have `cargo` defined (i.e., `cargo` is absent or set to the default `"Nothing"`). Such ships almost always carry cargo in playable missions; the missing value is likely an authoring oversight. If intentional (e.g., a decoy transport), the warning can be ignored.
*   **Warning** — A *Friendly* ship has `cargo` defined but is missing the `cargo-known` flag. Friendly ships generally have their cargo visible to the player immediately. If the intent is to require the player to actively scan the ship to reveal its cargo, this warning can be ignored. Otherwise, add `cargo-known` to the ship's `flags`.
*   **Error** — A ship has both the `scannable` flag and a `cargo` field defined. These two mechanisms are mutually exclusive: the `scannable` flag completely overrides the cargo system, making the ship show only "Scanned"/"Not Scanned" on the HUD, never the cargo string. Fix: remove either `scannable` (if cargo scanning via `is-cargo-known-delay` is desired) or the `cargo` field (if the `scannable` flag mechanic is desired).

#### **Standalone Ship Wing-Name Pattern**:
*   Warns if a standalone ship (defined in `entities.ships`, not part of any wing) has a name that matches the canonical FreeSpace wing-member pattern: `<Prefix> <Number>` where *Prefix* is any of the Terran, Vasudan, or Shivan wing names from the FreeSpace Universe Bible (e.g. `Alpha 1`, `Rama 4`, `Theta 2`).
*   This is almost always an authoring mistake — the intended approach is to define a wing via `entities.wings`. The warning is advisory and does not abort conversion.

#### **Invalid Player Start Ship**:
*   **Hard error (aborts conversion)** when `player_setup.start_ship` is not a member of a Friendly `Alpha`, `Beta`, or `Gamma` wing.
*   **Why only Alpha/Beta/Gamma?** FSO's team loadout screen reads player-wing data exclusively from the first three Friendly wings (Team 1: Alpha, Beta, Gamma). Starting the player anywhere else — as a standalone ship, in a `Delta` or `Epsilon` wing, in a hostile wing, or in any other non-standard wing — causes the FSO loadout screen to malfunction.
*   Non-leader positions within Alpha/Beta/Gamma are fully supported: `Alpha 2`, `Beta 3`, `Gamma 4`, etc. do **not** trigger this error.

#### **Reinforcements**:
*   Ensures all referenced ships and wings in `reinforcement_ships`/`reinforcement_wings` actually exist in the mission.

#### **Entities & Environment**:
*   Checks for valid team names, message priorities, and mission flags.
*   Validates background bitmaps and nebula patterns.
*   Warns if any sun in `environment.suns` has `angles: [0, 0]` — this places the sun directly in front of the player at default spawn orientation, causing a whiteout blinding effect. Sun angles are `[pitch, heading]`; bank is always hardcoded to `0.0` during FS2 emission.
*   **Sparse background advisory**: warns when a non-subspace, non-full-nebula mission has fewer than 3 nebula bitmaps in `environment.background_bitmaps`. A sky with very few background nebulae looks unusually empty.
*   **Background bitmaps forbidden in subspace or full-nebula missions**: emits an error if `environment.background_bitmaps` is non-empty when the `subspace` mission flag is set or when `environment.nebula.enabled: true` — background bitmaps are not visible in those contexts.
*   **Mission scale recommendation**: warns when any pair of positioned objects (standalone ships, wing centroids, jump nodes, waypoint points) or any authored `arrival_distance` exceeds 20,000 meters, as large mission spaces lead to long travel times. The check is **arrival-method-aware**:
    *   Objects arriving via `Hyperspace` use their authored `position` directly.
    *   Objects arriving via `Docking Bay` inherit the effective position of their `arrival_anchor` ship (resolved recursively with cycle detection).
    *   Objects arriving via any directional method (e.g., `Near Ship`, `In front of ship`) have no fixed initial position and are **excluded** from the distance check.

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

#### **Missing color styling tags (mission-level)**:
*   Warns when at least one eligible text field exists (in command briefing, mission briefing, or debriefing stages) but **none** of those texts contain an actual color-applying tag — either a span-opening tag (e.g. `$f{`) or a single-word color tag (e.g. `$h`).
*   This is a mission-level check designed to catch the likely AI authoring mistake of forgetting to add text styling entirely. Close tags (`$}`), color breaks (`$|`), and placeholder substitutions (`$callsign`, `$rank`, `$quote`, `$semicolon`) are intentionally excluded from the check and do not count as styled.
*   The check is skipped entirely when no eligible text fields are present (minimal or no-briefing missions), to avoid spurious noise.

#### **Global Name Integrity**:
*   Ensures names are unique within their respective namespaces: **Objects** (Ships, Wings, Waypoints, Jump Nodes), **Events**, **Goals**, and **Messages**.
*   Enforces a strict length limit of **< 30 characters** for all names to prevent engine truncation issues.

#### **SEXP Validation**:
*   **Parenthesis Integrity**: Checks for mismatched parentheses in formulas (Events, Goals, AI).
*   **YAML Leak Detection**: Checks for accidental inclusion of YAML comments (string `# `) inside SEXP blocks. Valid token strings like "#Command" don't trigger this, since they don't contain a space after the hash.
*   **Token Length**: Scans SEXP strings for individual tokens exceeding the 30-character limit.
*   **Note**: Voice filename length validation has been removed from the validator as it is strictly enforced by the generator logic.

#### **Debriefing Integrity**:
*   **Trivial `( true )` condition**: Warns if any debriefing stage uses `( true )` as its `display_condition`. An always-true condition causes the stage to display regardless of the mission outcome.

#### **Directive Text SEXP Compatibility**:
*   **Event/goal-referencing SEXPs in directive formulas**: Warns if an event with a `hud_directive_text` uses `is-event-true-delay`, `is-event-false-delay`, `is-event-true-msecs-delay`, `is-event-false-msecs-delay`, `is-goal-true-delay`, or `is-goal-false-delay` in its formula.

#### **Briefing Integrity**:
*   **Teams**: Validates `icon.team` against allowed factions (Friendly, Hostile, Unknown).
*   **display_class — ship icon types** (`"Fighter"`, `"Fighter Wing"`, `"Bomber"`, `"Bomber Wing"`, `"Cruiser"`, `"Cruiser Wing"`, `"Capital Ship"`, `"Supercapital Ship"`, `"Transport"`, `"Transport Wing"`, `"Freighter (no cargo)"`, `"Freighter (has cargo)"`, `"Freighter Wing (no cargo)"`, `"Freighter Wing (has cargo)"`, `"Cargo"`, `"Cargo Wing"`, `"Science Cruiser"`, `"Science Cruiser Wing"`, `"Support Ship"`, `"Installation"`, `"Sentry Gun"`, `"Player Fighter"`, `"Player Fighter Wing"`, `"Player Bomber"`, `"Player Bomber Wing"`): `display_class` is **required** and must be a valid ship class from `spacecraft-classes.md`. Using `"Terran NavBuoy"` on a ship icon type is also an error (it must be the actual ship class the icon represents).
*   **display_class — non-ship icon types** (`"Waypoint"`, `"Jump Node"`, `"Planet"`, `"Small Planet"`, `"Asteroid Field"`, `"Unknown"`, `"Unknown Wing"`): `display_class` must **not** be authored. The converter automatically emits `$class: Terran NavBuoy` for these icon types. Authoring `display_class` on a non-ship icon is an error.

#### **Strict Field Validation**:
*   **Extra Fields Forbidden**: The converter now strictly rejects *any* unknown fields in the FSIF YAML.
*   **Typo Detection**: If you make a typo in a field name (e.g., `arrival_dealy` instead of `arrival_delay`), the converter will abort with an "Extra inputs are not permitted" error. This ensures that no authored data is silently ignored.

#### **Ship Template Authoring Rules**:
*   `entities.ship_templates` may only contain reusable shared ship properties.
*   The loader rejects template-level authoring of `arrival_method`, `arrival_anchor`, `arrival_distance`, `arrival_delay`, `arrival_cue`, `departure_method`, `departure_anchor`, `departure_cue`, `initial_orders`, `dock`, `docked_with`, `docker_point`, and `dockee_point`.
*   This is a hard error because those fields do not work correctly or are not semantically appropriate when inherited by ships that are part of a wing.
*   Correct authoring locations:
    *   Standalone ship: author the fields directly on the `entities.ships[*]` entry.
    *   Wing member: author the fields on the corresponding `entities.wings[*]` entry.

#### **3D Mission Design**:
*   Warns if all positioned objects in the mission (standalone ships, wing centroids, jump nodes, waypoint points) have Y-coordinate exactly 0 — i.e., the entire mission is laid out on the flat XZ plane.
*   FreeSpace is a fully 3D game. Spreading objects along the Y-axis creates more interesting geometry and prevents unintended collisions between ships that are otherwise stacked on the same plane. The warning is advisory and does not abort conversion.

#### **Hyperspace Spawn Collisions**:
*   Warns when two ships or wings that both arrive via `Hyperspace` at static positions have **Oriented Bounding Boxes (OBBs)** that intersect at mission start.
*   Bounding boxes are derived from `fs_data.SHIP_BOUNDING_BOXES` (accurate per-class data) or from a heuristic radius based on the ship class prefix when no accurate data is available.
*   Pre-spawn docking pairs are excluded: if ship A is docked to ship B, their overlap is intentional and not flagged.
*   The warning is advisory and does not abort conversion.

#### **Waypoint Path Collisions**:
*   Warns when a standalone ship's or large-ship wing's `ai-waypoints` or `ai-waypoints-once` path is likely to pass through or very close to the initial position of another large ship or installation.
*   **Scope**: standalone ships with waypoint AI orders are checked using the existing radius cutoff. Wing-level waypoint orders are checked when the wing's single NeuralFS template class is not present in `FIGHTER_BOMBER_CLASSES` (that is, when the wing is not fighter/bomber scale). Fighter/bomber-only wings remain excluded because their formation and collision-avoidance AI is sufficient for this advisory check.
*   **Collision test**: a segment OBB is constructed for each waypoint leg and tested against the static OBBs of potential obstacles. Large-ship wings use the leader/member template class as the representative OBB and add conservative formation padding from wing member count and `member_spacing`.
*   **Exclusions**: ships with a radius ≤ 50 m (fighters, bombers, small craft) are excluded from the standalone mover and obstacle sets. Large-ship wing eligibility uses `FIGHTER_BOMBER_CLASSES` rather than the radius cutoff. Docking-bay-arrival ships are excluded from checks against their own arrival anchor.
*   The effective start position of the moving ship or wing is resolved recursively for Docking Bay arrivals (inherits anchor position). Ships and wings with directional arrival methods are excluded (no fixed initial position).
*   The warning is advisory and does not abort conversion.

#### **Anchor Validation**:
*   Validates `arrival_anchor` and `departure_anchor` references for all ships and wings. The anchor must refer to a known ship, wing, or a valid special token (e.g., `<no anchor>`).
*   **Directional arrival methods** (`Near Ship`, `In front of ship`, `In back of ship`, `Above ship`, `Below ship`, `To left of ship`, `To right of ship`) require **both** `arrival_anchor` and `arrival_distance` to be specified — missing either is an error.
*   **Docking Bay arrival/departure** requires `arrival_anchor` / `departure_anchor` to be specified.
*   **Fighterbay requirement**: when a ship or wing uses `Docking Bay` arrival or departure, the validator checks that the referenced anchor ship class has a `fighterbay` subsystem. A fighterbay is required for ships to emerge from or land in a bay; using a class without one is an error.

#### **Wings Without Initial Orders**:
*   Warns if a wing has no `initial_orders` (empty or missing). AI-controlled ships in such a wing will sit idle.
*   The warning is advisory and does not abort conversion.

#### **Escort Priority Requires `escort` Flag**:
*   Error if `escort_list_priority > 0` is set on a ship that does not have the `escort` flag. The `+Escort priority` field is only meaningful for escort-flagged ships; setting a non-zero priority without the flag is almost certainly an authoring mistake.

#### **No Escort-Flagged Large Ships**:
*   Warns when a mission contains ships larger than fighter/bomber scale but **none** of them have the `escort` flag.
*   In FreeSpace it is customary to add important larger ships (cruisers, destroyers, transports, freighters, science vessels, support ships, etc.) to the HUD escort list so the player can always see their hull integrity. Having zero escort-flagged large ships is unusual and is often an oversight.
*   **"Larger than fighter/bomber"** is defined as: any ship whose class is **not** in `fs_data.FIGHTER_BOMBER_CLASSES` **and** is not in the small-utility exclusion set (nav buoys, sentry guns, cargo containers, escape pods, training drones).
*   The check requires **at least one** large ship to carry the `escort` flag. It does not require all large ships to be flagged — only the most important one(s) need to be visible on the HUD.
*   Having a fighter or bomber with `escort` does **not** satisfy the check; the flag must appear on a large ship.
*   The warning is advisory and does not abort conversion. If all larger ships in the mission are minor background objects that the player has no gameplay reason to monitor, you may ignore it.

#### **Goals vs. Directives Count**:
*   Warns when a mission has more `mission_flow.goals` than events with `hud_directive_text`. It is strongly recommended that every important goal has a matching event with a `hud_directive_text` so the player can see the objective on the HUD.
*   The warning is advisory and does not abort conversion.

#### **Briefing Icon Proximity**:
*   Warns if any two briefing icons in the same stage are closer than **5 % of the auto-computed camera width** for that stage. Icons that close visually overlap, making them hard to distinguish on the briefing map.
*   Camera width is calculated using the same formula as `MissionLoader._calculate_briefing_camera` (tight bounding box → 2.5 aspect ratio clamp → 15 % safety factor → 1000 m minimum).
*   The warning is advisory and does not abort conversion.

#### **SEXP YAML Scalar Style**:
*   All SEXP-bearing FSIF fields (`arrival_cue`, `departure_cue`, `initial_orders`, `formula`, `display_condition`) **must** be authored using the YAML **literal block scalar style** (`|`). Flow scalars (`"..."`) and folded block style (`>`) are not accepted.
*   The check is performed by `validate_sexp_scalar_styles.validate_sexp_styles()` which reads the raw YAML AST of the `.fsif` file and inspects the node style for each SEXP field.
*   A mismatch produces a validation error that aborts conversion.
*   Example correct usage: `arrival_cue: |` followed by the SEXP on the next line.

### Error Reporting
*   **Errors**: Critical issues (e.g., invalid ship class, broken docking logic, non-ASCII characters in FSO-facing fields) will print an error message and **fail the validation**, aborting the conversion.
*   **Warnings**: Minor issues (e.g., unknown mission flags, potential logic oddities) are logged but do not stop conversion.

## Advanced SEXP Validation

The converter includes an **Advanced SEXP Validator** that is enabled by default.

Unlike the standard validation which primarily checks structure (parentheses balance, token length), this layer performs deep **semantic analysis** using rules derived from the FSO engine source code.

**Capabilities:**
*   **Recursive Type Checking:** It validates that every argument provided to a SEXP operator matches the expected type (e.g., ensuring `ai-chase` receives a Ship/Wing, a Priority number, and a Boolean, in that order). It understands return types (e.g., `when` returns Action/Void, `distance` returns Number) and enforces type safety throughout the formula tree.
*   **Atom Reference Validation:**
    *   **Ships/Wings:** Validates that names referenced in SEXPs actually exist in the mission.
    *   **Events/Goals/Messages:** Validates that event/goal/message names referenced in operators refer to valid entities.
*   **Operator Signatures:** Enforces minimum and maximum argument counts for all 670+ supported FSO operators.

**Coverage caveat — `map_opf_to_opr` string-like fallback:**

The type-checking system maps each FSO Argument Type (`OPF_*`) to a Return Type (`OPR_*`) via `map_opf_to_opr()`. Only five OPF classes receive precise, structurally distinct mappings: `OPF_BOOL → BOOL`, `OPF_NUMBER → NUMBER`, `OPF_POSITIVE → POSITIVE`, `OPF_NULL → NULL`, and `OPF_AI_GOAL → AI_GOAL`. All other OPF classes — including `OPF_SHIP`, `OPF_WING`, `OPF_MESSAGE`, `OPF_WEAPON_NAME`, `OPF_WAYPOINT_PATH`, `OPF_CONTAINER_NAME`, `OPF_ANYTHING`, `OPF_FLEXIBLE_ARGUMENT`, and many more — map to a generic `STRING` return type.

*   **For literal atoms**, this has no negative impact: the validator's dedicated atom-content checkers (`_validate_atom_content`) run separately and enforce domain-specific rules (ship name lookup, weapon name lookup, subsystem validation, etc.) with full precision.
*   **For nested operator expressions** placed in string-like argument slots, the validator only confirms that the expression returns *something string-like* rather than checking full OPF-semantic equivalence. In practice FSO has no operators that return a typed "Ship name" or "Weapon name" as a value, so this case almost never arises in real missions — but it is possible to author a nested expression that passes validation here yet fails in FRED or at FSO runtime.

**Conclusion:** A clean Advanced SEXP validation pass is strong evidence of correctness and will catch nearly all real-world authoring errors. It is not, however, a formal guarantee that FRED or FSO will accept every SEXP. When in doubt, open the converted `.fs2` in FRED to perform a final check.

For full details on the validator architecture and the complete coverage table, see `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/README and Documentation.md`.

---

## Briefing emission and normalization

- Briefing camera calculation: The converter computes the tightest axis-aligned bounding box for the icons in the XZ plane, expands it if necessary to meet the 2.5 aspect ratio requirement, and positions the camera at XZ equal to the bounding box center and Y equal to the bounding box width with a 15% safety factor (clamped to a minimum of 1000m), looking directly down.

**Icon type normalization:**
- Authoring: `icons[*].icon_type` is a canonical string; mission_loader normalizes it to the FS2 numeric `$type` using briefing_icon_types.py.
- Writer: emits `$type` from the normalized type_id and does not apply heuristic class/type coercions.
- Waypoint is 9; Jump Node is 33. The converter warns if older nav-buoy heuristics are detected.

**FS2 `$type` numeric mapping:**
- Canonical source of truth: `FSIF_to_FS2_Converter/briefing_icon_types.py`.
- The converter resolves `icons[*].icon_type` strings to numeric IDs using that module and emits the resulting numeric `$type`.
- FSIF authors should provide canonical string names only; they do not author numeric codes directly.

**Class emission:**
- `icons[*].display_class` is emitted as `$class`. The class value does not affect the icon silhouette; the silhouette is controlled solely by `icons[*].icon_type`.
- **Ship icon types**: `display_class` is **required** and must be a valid, non-`Terran NavBuoy` ship class from `spacecraft-classes.md`. Omitting it or setting it to `"Terran NavBuoy"` is a validation error.
- **Non-ship icon types** (Waypoints, Jump Nodes, Planets, Small Planets, Asteroid Fields): `display_class` **must be omitted** in FSIF. Authoring it is a validation error. The converter always emits `$class: Terran NavBuoy` for these types internally.

Notes
- If an icon `map_position` is omitted, the converter defaults the emitted position to 0.0, 0.0, 0.0.

## Arrival/Departure emission order

> **Label note:** The labels used in this section (e.g. `$Arrival Cue`, `$Departure Cue`, `$AI Goals`) are the literal `.fs2` output labels. The parenthesised names are the corresponding FSIF authoring fields. Authors edit FSIF fields; the converter translates them to FS2 labels.

Ships (#Objects)
- Arrival emission order:
  1) $Arrival Location (from arrival_method)
  2) +Arrival Distance (if any)
  3) $Arrival Anchor (if any)
  4) +Arrival Delay (if provided)
  5) $Arrival Cue (from arrival_cue)
- Departure emission order:
  1) $Departure Location (from departure_method: Hyperspace | Docking Bay)
  2) $Departure Anchor (only when Docking Bay)
  3) $Departure Cue (from departure_cue)

Wings (#Wings)
- Arrival emission order:
  1) $Arrival Location (from arrival_method)
  2) +Arrival Distance (if any)
  3) $Arrival Anchor (if any)
  4) +Arrival delay (if provided)
  5) $Arrival Cue (from arrival_cue)
- Departure emission order mirrors ships:
  1) $Departure Location (from departure_method)
  2) $Departure Anchor (only when Docking Bay)
  3) $Departure Cue (from departure_cue)

Constraints and guidance
- Directional $Arrival Location values (arrival_method) require both +Arrival Distance and $Arrival Anchor.
- Docking Bay commonly uses +Arrival Distance: 0.
- **Validation warning — arrival_distance below minimum:** When a ship or wing uses a directional `arrival_method` (Near Ship, In front of/behind/above/below/left/right of ship) and `arrival_distance` is set but less than **300 m**, the validator emits a non-fatal warning. Values below 300 risk spawning arriving ships dangerously close to or clipping inside the arrival anchor. The conversion proceeds; authors should increase `arrival_distance` to at least 300. This warning does NOT fire for Hyperspace or Docking Bay arrivals.

## Asteroid/Debris Fields mapping

The `environment.asteroid_field` FSIF mapping is converted to the `#Asteroid Fields` section in `.fs2`.

### FS2 emission (both field types)

```
#Asteroid Fields

$Density: <int>
+Field Type: <0 = active | 1 = passive>           (from behavior)
+Debris Genre: <0 = asteroid | 1 = debris>         (from object_type)
+Field Debris Type Name: <name>                    (repeated for each entry in object_variants)
...
$Average Speed: <float>
$Minimum: <x>, <y>, <z>
$Maximum: <x>, <y>, <z>
$Asteroid Targets: ( "Ship1" "Ship2" ... )         (only for active asteroid fields with target_ships)
```

### Example: asteroid field output

```
#Asteroid Fields

$Density: 10
+Field Type: 0
+Debris Genre: 0
+Field Debris Type Name: Brown
+Field Debris Type Name: Blue
+Field Debris Type Name: Orange
$Average Speed: 5.000000
$Minimum: -2500.000000, -1500.000000, -2500.000000
$Maximum: 2500.000000, 1500.000000, 2500.000000
$Asteroid Targets: ( "GTC Fenris 1" "GTFr Poseidon 1" )
```

### Example: debris field output

```
#Asteroid Fields

$Density: 10
+Field Type: 1
+Debris Genre: 1
+Field Debris Type Name: Terran Debris 1
+Field Debris Type Name: Terran Debris 2
+Field Debris Type Name: Terran Debris 3
+Field Debris Type Name: Vasudan Debris 1
+Field Debris Type Name: Vasudan Debris 2
+Field Debris Type Name: Vasudan Debris 3
+Field Debris Type Name: Shivan Debris 1
+Field Debris Type Name: Shivan Debris 2
+Field Debris Type Name: Shivan Debris 3
$Average Speed: 0.000000
$Minimum: -1000.000000, -1000.000000, -1000.000000
$Maximum: 1000.000000, 1000.000000, 1000.000000
```

### object_variants defaults and validation

**Defaults:** When `object_variants` is omitted from FSIF, the loader injects the full default set for the selected `object_type`:
- `object_type: "asteroid"` → `["Brown", "Blue", "Orange"]`
- `object_type: "debris"` → `["Terran Debris 1", "Terran Debris 2", "Terran Debris 3", "Vasudan Debris 1", "Vasudan Debris 2", "Vasudan Debris 3", "Shivan Debris 1", "Shivan Debris 2", "Shivan Debris 3"]`

An explicitly authored empty list (`object_variants: []`) is NOT automatically replaced with defaults — the validator will reject it with an error.

**Validation errors (abort conversion):**
- Empty `object_variants` list.
- Cross-genre mixing: asteroid variant name (`Brown`, `Blue`, `Orange`) in a debris field, or debris variant name in an asteroid field.
- Unknown variant name that belongs to neither genre.

**Validation warnings (non-fatal):**
- Duplicate entries in `object_variants` (FSO ignores them at runtime).

**Constraints and coercion:**
- Retail/FRED limitation: one asteroid/debris field per mission. The converter supports authoring as a single YAML mapping `asteroid_field`.
- Debris fields cannot be active; if authored with `behavior: "active"`, the loader coerces `behavior` to `"passive"` and logs a warning.
- `target_ships` only applies to active asteroid fields; for any other combination of `behavior` and `object_type`, the field is ignored with a warning.
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
