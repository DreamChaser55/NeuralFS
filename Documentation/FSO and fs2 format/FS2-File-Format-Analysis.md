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
Important note: Any object that is in a wing must have `$Arrival Cue: ( false )`! Its arrival is controlled by the corresponding wing section in `#Wings`.

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