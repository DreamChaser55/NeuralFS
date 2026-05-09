# FreeSpace Campaign Intermediate Format (FCIF) Specification

FCIF is a simplified, YAML-based format for defining FreeSpace 2 campaigns. It is designed to be human-readable and easily writable by AI agents, abstracting away the verbose syntax of the legacy `.fc2` format.

## Version
Current version: "1.0"

## File Structure

The file consists of three main sections: `campaign`, `starting_loadout`, and `missions`.

```yaml
fcif_version: "1.0"

campaign:
  name: <string>
  description: |
    <multiline string>

starting_loadout:
  ships:
    - <string>
    - <string>
  weapons:
    - <string>
    - <string>

missions:
  - filename: <string>
    success_goal: <string> (optional)
    success_event: <string> (optional)
    failure_goal: <string> (optional)
    failure_event: <string> (optional)
```

## Field Details

### Campaign Section
- **name**: The display name of the campaign.
- **description**: A description of the campaign. **Must not contain double quotes (`"`).** Any `"` inside the string would break the syntax of the generated `.fc2` file. The converter checks for this and raises an error if any double quotes are found.

The campaign type is always `single` (hardcoded by the converter).

### Starting Loadout
- **ships**: A list of ship classes available to the player at the start of the campaign (e.g., `GTF Apollo`).
- **weapons**: A list of weapons available to the player at the start (e.g., `ML-16 Laser`).

Important: any ship or weapon used in the campaign must be either listed here or explicitly allowed with the appropriate SEXP (`allow-ship` or `allow-weapon`) during the campaign; otherwise it will not appear in the game even if it is defined in the mission files. By default, all ships and weapons are unavailable at campaign start.

**Campaign-wide player loadout constraint**: The converter checks every mission in sequence to ensure that all player-usable ships and weapons (Alpha–Epsilon wings, `start_ship`, `additional_ship_choices`, `additional_weapons`) are either in `starting_loadout` or granted by `allow-ship`/`allow-weapon` SEXPs in a previous mission. The converter verifies this automatically: it infers the `.fsif` path for each mission from its filename, parses it, tracks the granted items, and throws a fatal error if any ship class or weapon is used by the player without being unlocked.

### Missions Section
An ordered list of missions. The order of entries determines campaign progression.

- **filename**: The filename of the mission (e.g., `m01.fs2`). Must include the extension.

#### Advance Condition Fields

Each mission may optionally specify **one** advance condition that determines whether the campaign progresses to the next mission or repeats the current one. If no condition is set, the campaign advances unconditionally.

**At most one** of the following four fields may be set per mission. They are mutually exclusive.

- **success_goal**: The name of a **goal** in the mission that must be **true** (succeeded) to advance.
  - Emits `is-previous-goal-true` in the fc2 formula.
  - Example: `success_goal: "Protect the Orff"` — advance if the "Protect the Orff" goal succeeded.

- **success_event**: The name of an **event** in the mission that must be **true** (succeeded) to advance.
  - Emits `is-previous-event-true` in the fc2 formula.
  - Example: `success_event: "Trap alert!"` — advance if the "Trap alert!" event fired/succeeded.

- **failure_goal**: The name of a **goal** in the mission that must be **false** (failed) to advance.
  - Emits `is-previous-goal-false` in the fc2 formula.
  - Example: `failure_goal: "Base Destroyed"` — advance if the "Base Destroyed" goal failed (i.e., the base survived).

- **failure_event**: The name of an **event** in the mission that must be **false** (failed) to advance.
  - Emits `is-previous-event-false` in the fc2 formula.
  - Example: `failure_event: "Arjuna destroyed"` — advance if the "Arjuna destroyed" event did not occur (i.e., the Arjuna survived).

If none of these fields is set, the campaign advances to the next mission regardless of the outcome (unconditional advancement). **Note:** While this is perfectly valid, the converter will emit a warning for each mission that lacks an advance condition, to help catch potential oversights.

### Goals vs. Events

In FreeSpace missions, **goals** and **events** are distinct concepts:

- **Goals** are objectives visible to the player (primary, secondary, bonus). They appear in the mission objectives list. Use `success_goal` / `failure_goal` when the advance condition depends on a mission objective.
- **Events** are internal mission triggers that control scripted sequences (e.g., enemy arrivals, message sending, AI goal changes). They are not directly visible to the player as objectives. Use `success_event` / `failure_event` when the advance condition depends on an internal event rather than a player-facing objective.

### Example

```yaml
fcif_version: "1.0"
missions:
  # Advance if the "Flight Training" goal succeeded
  - filename: btm-01.fs2
    success_goal: "Flight Training"

  # Advance if the "Trap alert!" event fired
  - filename: sm1-07a.fs2
    success_event: "Trap alert!"

  # Advance if the "Base Destroyed" goal failed (base survived)
  - filename: sm2-05a.fs2
    failure_goal: "Base Destroyed"

  # Advance if the "Arjuna destroyed" event did NOT fire (Arjuna survived)
  - filename: sm2-07a.fs2
    failure_event: "Arjuna destroyed"

  # Unconditional advancement (no condition field)
  - filename: sm2-09a.fs2

  # Last mission — targets end-of-campaign
  - filename: sm3-10a.fs2
```
