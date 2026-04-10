# **Deconstruction and Analysis of the .fs2 Mission File Format**

## Scope and Intent
- **Technical Reference:** This document provides a comprehensive technical analysis of the legacy **.fs2** file format. It details the file structure, internal property keys (e.g., `$Name`, `+Flags`), and parser behaviors.
- **Audience:** Intended for **converter developers**, tool creators, and power users who need to understand the raw engine format or debug converter output.
- **For FSIF Authors:** If you are writing FSIF missions, **do not** use this file as your primary reference. Instead, consult:
  - **./FSO_Tokens_Reference.md:** For the list of valid tokens, flags, and values you should write in your FSIF files.
  - **../fsif/specification.md:** For the authoritative schema of the FSIF format.

## Overview
A thorough understanding of the target .fs2 format is a prerequisite for designing an effective intermediate representation. The analysis of the format's structure, syntax, and inherent verbosity reveals key areas for optimization and abstraction.

## **1. Fundamental Structure and Syntax**

The .fs2 mission file is a structured, plain-text format that serves as a direct serialization of the mission data as understood by the Freespace Open engine and its mission editor, FRED.

### **Sections as Building Blocks**

The file is partitioned into distinct, ordered sections, each denoted by a `#` prefix. The sequence of these sections is rigid and essential for correct parsing by the game engine. A minimal mission file must contain a specific set of these sections, even if they are empty, to be considered valid. The primary sections observed across the sample missions include:

* `#Mission Info`: Contains mission metadata.
* `#Fiction Viewer`: Contains a reference to an external text file for the Fiction Viewer interface.
* `#Command Briefing`: Contains high-level narrative content presented to the player.
* `#Briefing`: Contains mission-related briefing narrative content presented to the player.
* `#Debriefing_info`: Contains the post-mission debriefing narrative content presented to the player.
* `#Players`: Defines player ship choices and weapon loadouts.  
* `#Objects`: A comprehensive list of every individual entity in the mission space.  
* `#Wings`: Defines logical groupings of ships defined in the `#Objects` section.  
* `#Events`: Contains the mission's trigger-based logic.  
* `#Goals`: Defines primary, secondary, and bonus objectives.   
* `#Waypoints`: Contains navigation waypoint paths for AI ships, as well as Jump Nodes
* `#Messages`: A repository of all in-mission text communications.   
* `#Reinforcements`: Defines reinforcement ships/wings callable by the player during the mission.
* `#Background bitmaps`: Defines background bitmaps (nebulas, planets and suns).
* `#Music`: Specifies the musical score for the briefing and the mission.  
* `#End`: A mandatory terminator for the file.

### **Property Declarations**

Within each section, data is defined using a key-value syntax. Keys are prefixed with either a $ for primary properties (e.g., `$Name: Alpha 1`) or a + for secondary properties or flags (e.g., `+Flags: ( "player-start" )`). This convention is applied consistently throughout the file format.

### **Data Types and Formatting**

The format utilizes a limited set of data types:

* **Strings:** Plain text, often enclosed in double quotes within lists.  
* **Integers:** Used for counts, flags, and identifiers.  
* **Floating-Point Numbers:** Used for coordinates, orientation matrices, and other continuous values. These are typically written with six decimal places of precision (e.g., 1.000000).  
* **Multi-line Text:** Blocks of text, such as mission descriptions or briefing stages, are enclosed by start and end markers like `$Mission Desc:` and `$end_multi_text`.  
* **S-expressions (SEXPs):** The cornerstone of mission logic, SEXPs are Lisp-like expressions enclosed in parentheses. They define conditions for events, goals, arrivals, and departures. For example, an arrival cue might be `( is-event-true-delay "Trap alert!" 3 )`.

### **Localization (XSTR)**

A pervasive feature of the format is its system for handling localizable strings. A function within the FRED save logic reveals that user-facing text is wrapped in an XSTR macro, which takes the string content and a numerical ID. For example, $Name: XSTR("Pandora's Box", 2101). An ID of -1 indicates that the string is new and has not yet been indexed in the game's string table, a critical detail for any tool that generates new mission files.

## **2. Analysis of Redundancy and Verbosity**

The primary motivation for an intermediate format is the significant verbosity of the .fs2 file, which makes it unsuitable for direct generation by a Large Language Model (LLM) due to high token consumption. The sources of this verbosity are systemic to the format's design.

### **Repetitive Object Definitions**

The most substantial source of redundancy is the decoupling of logical ship groupings (`#Wings`) from their physical definitions (`#Objects`). To create a wing of four identical fighters, a mission designer must first define the wing in the `#Wings` section and then create four separate, nearly identical entries in the `#Objects` section. Each of these object entries repeats the same ship class, team, initial hull strength, weapon loadouts, and other boilerplate properties, leading to a multiplicative increase in file size for each ship added to a wing.

### **Explicit Default Values**

The format frequently includes explicit declarations for values that represent a common or default state. For instance, the orientation of a newly placed ship is often the identity matrix, yet this 3x3 matrix is written out in full for each ship. Other common examples include:

* +Initial Hull: 100  
* +Initial Shields: 0 (for ships without shields)  
* $Cargo 1: XSTR("Nothing", -1)

The C++ save routines in missionsave.cpp provide a clear explanation for this behavior. The FRED_ENSURE_PROPERTY_VERSION_WITH_DEFAULT macro is designed to omit a property if its value matches a known default. However, the format's verbosity suggests that many properties are not checked against a default or that the editor's in-memory representation always contains explicit values. The .fs2 format is therefore a direct serialization of the editor's internal state, rather than an optimized storage format. An effective intermediate format must reverse this by establishing a clear set of default values that are assumed unless explicitly overridden.

### **Verbose Subsystem Enumeration**

For capital ships and other large vessels, the format requires an explicit enumeration of every single subsystem, even if they are at full health. The definition for the SD Lucifer in one of the sample missions lists over a dozen turrets and other components, each on its own line with the +Subsystem: tag. This creates large, boilerplate-heavy blocks for every capital ship in a mission, consuming a significant number of tokens for what is essentially default state information.

## **3. Key Section Analysis**

Understanding the interplay between the major sections is crucial for designing a more logical and abstract intermediate format.

### `#Mission Info`

This section contains mandatory metadata. Analysis of a minimal mission file confirms that fields such as `$Version`, `$Name`, `$Author`, `$Created`, `$Modified`, and various global flags like `+Game Type` Flags are required for the file to be parsed correctly by the engine.

### `#Objects` vs. `#Wings`

These two sections are fundamentally coupled yet structurally separate. The `#Wings` section provides a logical grouping for AI and player commands, referencing ships by their unique names (e.g., "Alpha 1", "Alpha 2"). However, the complete definition of each of these ships resides in the `#Objects` section.  
This separation reflects a disconnect between the designer's intent and the file's structure. A designer conceptualizes "a wing of four Ulysses fighters," but the format forces a two-step, disjointed definition process. This structural inefficiency is a primary target for abstraction in the .fsif format, which will unify the concept of a wing with the definition of its constituent ships.

### `#Objects`: Inter-Ship Docking (Docker/Dockee)

FSO supports pre-spawn inter-ship docking relationships that are authored entirely within the `#Objects` section. A docking relationship links a “docker” (the ship that attaches) to a “dockee” (the ship being attached to). The entire group of docked ships is spawned as a single entity when the dock “leader” arrives.

Key facts:
- Authoring location: Only the docker’s object entry contains docking fields. The dockee’s entry is standard with no docking-specific lines.
- Fields on the docker (as seen in .fs2):
  - `+Docked With: <Dockee_Name>` — the name of the ship being docked to.
  - `$Docker Point: <Dockee_Point_Name>` — name of the docking point on the DOCKEE.
  - `$Dockee Point: <Docker_Point_Name>` — name of the docking point on the DOCKER.
- Important quirk (reversed point names): Although the names suggest otherwise, `$Docker Point` refers to the DOCKEE’s docking point and `$Dockee Point` refers to the DOCKER’s docking point. The engine’s parser swaps these internally on read.
- Arrival semantics (leader/follower):
  - Exactly one ship in a docked group must have an `$Arrival Cue:` that evaluates to `( true )`. This ship is the leader; when it arrives, all ships in its docked group spawn simultaneously in the docked configuration.
  - All other ships in the group (followers) should have `$Arrival Cue: ( false )` to prevent independent arrival.
  - The dockee is commonly used as the leader, but the leader can be any ship in the dock tree as long as only one ship is true.
- Groups and trees:
  - Multiple docking relations can form larger “docking trees” (more than two ships). FSO parses the entire `#Objects` section, collects all requested dockings, builds a forest of docking trees, and identifies the single leader for each tree.
  - When a leader’s arrival cue becomes true, the engine spawns the whole tree; followers do not arrive independently.
- Processing order:
  - Parsing occurs in two phases: object entries are read first and docking intents are recorded; then a post-processing step links dockers to dockees, validates points, builds docking trees, and enforces arrival cohesion at runtime.
- Example snippet (.fs2 excerpt; docker only):
```
$Name: GTT Elysium 2
$Class: GTT Elysium
$Team: Friendly
...
+Docked With: GTC Fenris 1
$Docker Point: Docking bay 1      ; point on DOCKEE (Fenris)
$Dockee Point: topside docking    ; point on DOCKER (Elysium)
$Arrival Cue: ( false )
...
```
Dock leader example (common pattern):
```
$Name: GTC Fenris 1
$Class: GTC Fenris
$Team: Friendly
...
$Arrival Cue: ( true )            ; leader (causes both to arrive docked)
...
```

Authoring guidance:
- Ensure exactly one leader per docking tree has `$Arrival Cue: ( true )`. Followers should use `( false )`.
- Do not place docking lines on the dockee; only the docker’s entry should contain the docking fields.
- Use valid docking point names as defined by the ship models for both the docker and dockee.

### `#Events`, `#Goals`, `#Briefing`, `#Debriefing`

These sections govern the mission's narrative and logical progression. Their structure is highly verbose, with repeated blocks for each stage, icon, or event. For example, a multi-stage briefing will contain a separate block for each stage, often with identical camera settings or other metadata that is copied from one stage to the next. The core logic is contained within S-expressions in the $Formula property, which must be preserved.

## **4. Implicit Engine Validation Logic**

Beyond parsing the file structure, the FSO engine performs several "implicit" validation checks that are not obvious from the file format itself but are critical for mission stability.

### **Weaponry Pool Supply and Demand**

One of the most strict validation checks involves the **Weaponry Pool**. Upon loading a mission, the engine (and FRED) performs a "Supply and Demand" calculation:

1.  **The Demand**: The engine scans all ships assigned to **Player Starting Wings** (Team 1: Alpha, Beta, Gamma). It calculates the total demand for each weapon type based on:
    *   **Primary Weapons**: Count of *weapon banks* (not individual mounts).
    *   **Secondary Weapons**: Total *ammunition capacity* of the banks.
2.  **The Supply**: The engine reads the `+Weaponry Pool` list from the `#Players` section.
3.  **The Conflict**: If the Demand for a specific weapon is greater than zero, but that weapon is **completely missing** from the Supply list, the engine triggers a critical validation error (often a crash in retail, or a hard error in debug builds).

**Technical nuance:**
*   **Existence vs. Quantity**: The validation primarily checks for the *existence* of the weapon definition in the pool. If the weapon is listed but the quantity is insufficient (supply < demand), the engine typically handles this gracefully (ships spawn with empty banks) without crashing. However, if the weapon is *absent*, the validation logic fails.
*   **Scope**: This check applies specifically to **Team 1 (Friendly) Wings**. Standalone ships and non-player teams (Hostile/Neutral) are exempt from this specific pool validation logic, as their loadouts are not drawn from the player's logistic pool.

---

## Contextual parameters

### Arrival and departure (ships and wings)
- `$Arrival Location`: Location token. Directional locations require `+Arrival Distance` and `$Arrival Anchor`.
- `+Arrival Distance`: Distance in meters. Should be 0 for Docking Bay.
- `$Arrival Anchor`: Anchor entity literal or wildcard E.g., docking bay, a specific ship, wing, or "<any friendly player>".
- `+Arrival Delay`: Integer delay before arrival. Case sometimes seen as "+Arrival delay" in retail (case-insensitive).
- `$Arrival Cue`: SEXP controlling arrival. Authored as a SEXP expression
- `$Departure Location`: Hyperspace or Docking Bay.
- `$Departure Anchor`: Anchor for Docking Bay departure. Must be a docking bay.
- `$Departure Cue`: SEXP controlling departure.

### Waypoints and Jump Nodes

#### Waypoints
- `$Name`: Waypoint path N
- Waypoint point literal: Address specific point index "Waypoint path N:M" (e.g., "Waypoint path 1:1")

#### Jump Nodes
- `$Jump Node`: Node XYZ position, Example: $Jump Node: x, y, z
- `$Jump Node Name`:Node display name, Example: $Jump Node Name: "Delta Serpentis Jump Node"

### Messages
- `$Name`: Message identifier, Example:`$Name: "Lucifer arrived"`
- `$Team`: Team index, Example: `$Team: -1`
- `$MessageNew`: Localized text payload, Example: `$MessageNew: XSTR("...", id)`
- `+Persona`: Speaker persona or <None>, Example: `+Persona: "Wingman 4"`
- `+AVI Name`: Head animation id or <None>, Example:`+AVI Name: "<None>"`
- `+Wave Name`: WAV file or <None>, Example:`+Wave Name: "4_a3m5_j.wav"`

Note: Message `$Name` is referenced by send-message SEXP; sender strings may be ships, wildcards like "<any wingman>", or "#Command".

### Observed per-ship/wing/mission property keys
Ships (#Objects):
- $Name, $Class, $Team, $Location, $Orientation, +AI Class
- $AI Goals: ( goals ... )
- $Cargo 1: XSTR(...) (cargo label)
- +Initial Velocity, +Initial Hull, +Initial Shields
- +Subsystem: <name> (repeats)
- +Primary Banks: ( "WeaponA" "WeaponB" )
- +Secondary Banks: ( "MissileA" ["MissileB" ...] )
- $Arrival Location, +Arrival Distance, $Arrival Anchor, $Arrival Cue
- $Departure Location, $Departure Anchor, $Departure Cue
- +Flags: ( ... )
- +Hotkey, +Escort priority, +Respawn priority, +Group, +Score
- +Orders Accepted: <bitfield int> (note: bitfield)
- +Docked With, $Docker Point, $Dockee Point (for docked cargo)
- +Persona Index: <int> (occasionally)

Wings (#Wings):
- $Name, $Waves, $Wave Threshold, $Special Ship
- $Arrival Location, +Arrival Distance, $Arrival Anchor, $Arrival Cue
- $Departure Location, $Departure Anchor, $Departure Cue
- $Ships: ( "Ship 1" ... )
- $AI Goals: ( goals ... )
- +Flags: ( ... )
- +Hotkey
- +Wave Delay Min / +Wave Delay Max

Mission-level (#Mission Info):
- $Version, $Name, $Author, $Created, $Modified, $Notes, $Mission Desc
- +Game Type Flags, +Flags, +Red Alert, +Scramble, +Disallow Support
- +Player Entry Delay
- +Viewer pos, +Viewer orient
- +SquadReassignName, +SquadReassignLogo

## Converter Notes and TODOs

Converter behavior (current tooling):
- Version: The converter emits `$Version: 23.1` in the `#Mission Info` section.
- Mission flags mapping: Named flags are resolved using the FSO Mission::Mission_Flags order (with alias support like "scramble_mission" → Scramble) into a numeric +Flags bitmask. Unknown flags are ignored with a warning.
- Ship flags mapping: entities.ships[*].flags tokens are routed automatically to +Flags and +Flags2 (case-insensitive; separators like spaces/hyphens/underscores normalized). Examples:
  - +Flags: cargo-known, ignore-count, protect-ship, reinforcement, no-shields, escort, no-arrival-music, invulnerable, hidden-from-sensors, scannable, kamikaze, no-dynamic, red-alert-carry, guardian, special-warp, stealth, friendly-stealth-invisible, player-start
  - +Flags2: primitive-sensors, no-subspace-drive, toggle-subsystem-scanning, hide-ship-name, cloaked, scramble-messages, no_collide, primaries-locked, secondaries-locked, weapons-locked, ship-locked, afterburners-locked, lock-all-turrets
- Ancillary per-ship emission: +Respawn priority, +Escort priority (when "escort" or explicitly provided), +Kamikaze Damage (defaults to 1000 when "kamikaze" present and value omitted), +Destroy At (emitted when > 0), +Orders Accepted (bitmask) and +Orders Accepted List (textual form).
- Behavior notes (selected flags):
  - Destroy Before Mission: `+Destroy At: <seconds>` destroys the ship this many seconds before mission start; debris remains in-mission.
    - Constraint: Do not set this on the player's starting ship; FSO will error. The converter clears this and emits a warning.
  - Scannable, Cargo Known;
  - Briefing ship/loadout lock flags (pre-launch effects on ship class and loadout for this ship):
    - ship-locked: prevents changing the ship’s class for this ship in the pre-launch loadout screen
    - weapons-locked: prevents changing any weapons (both primary and secondary) for this ship
    - primaries-locked: prevents changing primary weapons for this ship
    - secondaries-locked: prevents changing secondary weapons for this ship
  - Operational lock flags (in-mission effects):
    - afterburners-locked: disables afterburner usage during the mission
    - lock-all-turrets: disables all turrets until freed at runtime (e.g., via turret-free-all/beam/turret free SEXPs)
  - No Shields (no-shields): Unchecking “Has Shield System” renders a fighter or bomber shieldless; this has no effect on larger ships
  - Scannable enables scanning a ship (state: Not Scanned → Scanned), distinct from inspecting cargo (which reveals cargo when Cargo Known is false).
  - Toggle-subsystem-scanning flips defaults: big ships normally require subsystem scanning; small craft normally can’t have subsystems scanned—use this to invert those behaviors.
  - Reinforcement: Player-callable reinforcement (commonly authored on wings; per-ship also supported, with gameplay differences).
  - Protect Ship vs Beam Protect Ship:
    - Protect Ship prevents AI from attacking this ship (can be overridden via protect-ship/unprotect-ship SEXPs).
    - Beam Protect is a narrower variant that blocks beam turrets; use SEXPs until mapped as a flag.
  - Ignore For Counting Goals (ignore-count): Excludes the ship from SEXP operators that count ships (e.g., percent-ships-destroyed).
  - Escort (and +Escort priority): Escorted ships populate the Escort/Monitor HUD with the highest priorities; assign priorities to all important capitals. Asteroids on a collision course with an escorted ship are highlighted.
  - No Arrival Music: Disables the arrival fanfare for this ship.
  - Invulnerable vs Guardian:
    - Invulnerable takes no damage (including collisions).
    - Guardian caps hull at 1% (subsystems can still be destroyed). More granular thresholds via ship-guardian-threshold / ship-subsys-guardian-threshold SEXPs.
  - No Subspace Drive: Prevents warp/jump; ensure missions retain a valid end condition.
  - Hidden From Sensors vs Stealth vs Friendly-stealth-invisible:
    - Hidden-from-sensors: player radar flicker and non-targetable for the player; AI are not affected.
    - Stealth: invisible on radar and untargetable to both players and AI; firing/afterburners increase detectability to AI. This is not a visual cloak; the ship remains visible to the eye.
    - Friendly-stealth-invisible: hides friendly stealth craft from friendly sensors as well (default allows them to be seen by friendlies).
  - Kamikaze: Causes a ship to ram and self-destruct, applying the indicated damage to the target.
  - No Dynamic Goals: Ship will not abandon assigned orders to self-defend when threatened.
  - Red Alert Carry: In red-alert campaign missions, carries the ship’s state forward from the previous mission.
  - Respawn Priority: In multiplayer, players respawn near the ship with the highest respawn priority.
  - Hide Ship Name: Suppresses the ship’s proper name on the HUD (e.g., present a generic class label).
  - Other FRED options not yet mapped by this converter:
    - Targetable as Bomb: allows bomb-targeting shortcuts to target this ship.
    - Per-ship “Disable Built-in Messages”, “Never/Always Scream on Death”, and “Vaporize on Death”.
    - Workaround: use SEXPs/mission logic (and Mission Specs for mission-wide behavior) until these are mapped.
- XSTR wrapping: Applied to mission name, mission description, goals `$MessageNew`, and messages `$MessageNew`. Other string fields are not wrapped at this time.
- If your mission is part of a campaign, any weapon used must also be included in the `+Starting Weapons` section of the campaign (`.fc2`) file. Any weapon not listed in the campaign file will not work, even if correctly listed in the mission file.

TODO:
- Expand mission flag mappings and document a comprehensive table with tests.
- Make the emitted `$Version` configurable and document compatibility implications.
- Evaluate extending XSTR coverage to additional user-facing fields where appropriate (e.g., briefing labels).
