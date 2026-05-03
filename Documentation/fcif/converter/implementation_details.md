# Freespace Campaign Intermediate Format (FCIF) Implementation

This file documents the implementation details of FCIF and of the fcif->fc2 converter. It is not intended for `.fcif` file authors, but for FCIF converter programmers.

## Campaign Section

The `description` string will be automatically wrapped in `XSTR` for localization support by the converter.
The campaign type is always `single` (hardcoded by the converter).

**Validation:** The converter validates that `campaign.description` contains no double quotes (`"`). If any are found, conversion is aborted with an error. This is required because the description is emitted as `XSTR("...", -1)` — any `"` inside the string would produce invalid `.fc2` syntax.

## Missions Section

The converter always emits `+Flags: 0` and an empty `+Main Hall:` for every mission.

## Logic Generation

The converter translates the linear list into `.fc2` S-expression logic.

### Advance Condition Mapping

Each advance condition field maps to a specific SEXP operator:

| FCIF Field | SEXP Operator |
|---|---|
| `success_goal` | `is-previous-goal-true` |
| `success_event` | `is-previous-event-true` |
| `failure_goal` | `is-previous-goal-false` |
| `failure_event` | `is-previous-event-false` |

At most one condition field may be set per mission. This is enforced by a Pydantic model validator.

### Formula Patterns

1.  **Standard Mission (with condition)**:
    - If any advance condition field is present (e.g., `success_goal`, `success_event`, `failure_goal`, or `failure_event`):
      ```scheme
      ( cond
         ( ( <sexp-operator> "current.fs2" "Name" ) ( next-mission "next.fs2" ) )
         ( ( true ) ( next-mission "current.fs2" ) )
      )
      ```
    - Examples:
      - `success_goal: "Primary"` →
        ```scheme
        ( cond
           ( ( is-previous-goal-true "current.fs2" "Primary" ) ( next-mission "next.fs2" ) )
           ( ( true ) ( next-mission "current.fs2" ) )
        )
        ```
      - `success_event: "Trap alert!"` →
        ```scheme
        ( cond
           ( ( is-previous-event-true "current.fs2" "Trap alert!" ) ( next-mission "next.fs2" ) )
           ( ( true ) ( next-mission "current.fs2" ) )
        )
        ```
      - `failure_event: "Arjuna destroyed"` →
        ```scheme
        ( cond
           ( ( is-previous-event-false "current.fs2" "Arjuna destroyed" ) ( next-mission "next.fs2" ) )
           ( ( true ) ( next-mission "current.fs2" ) )
        )
        ```

2.  **Standard Mission (unconditional)**:
    - If no condition field is set:
      ```scheme
      ( cond
         ( ( true ) ( next-mission "next.fs2" ) )
         ( ( true ) ( next-mission "current.fs2" ) )
      )
      ```

3.  **Last Mission**:
    - Targets `end-of-campaign` instead of a next mission filename.

## Advance Conditions Check

When the converter is invoked, it iterates over all missions and checks whether each mission has at least one advance condition defined (`success_goal`, `success_event`, `failure_goal`, or `failure_event`). If a mission does not define any advance conditions, it will log a warning (e.g., `Mission 'demo_m05.fs2' has no advance conditions (success or failure goals/events) defined. It will advance unconditionally.`). This is a non-fatal warning (does not abort conversion) because unconditional advancement is technically valid but often an oversight by campaign authors.

## Campaign-Wide Player Loadout Check

When the converter is invoked, it performs a pre-conversion check to verify that the player's ships and weapons across the entire campaign are either in `starting_loadout` or explicitly granted by `allow-ship`/`allow-weapon` SEXPs in a previous mission. The converter infers the path to the `.fsif` files by checking the `fsif` directory relative to the input `.fcif` path (e.g., `input_path.parent / "fsif" / f"{mission_stem}.fsif"`).

### Why this matters

For any mission after the first one, an `allow-ship` or `allow-weapon` SEXP executed in a previous mission can make a ship class or weapon available. Every ship class and every weapon used by the player in any mission must therefore be present in `starting_loadout` or granted by an `allow-ship`/`allow-weapon` SEXP in a previous mission — otherwise FSO will simply not load or display those entities in the mission.

### What is checked

The converter iterates through all missions sequentially, parsing the FSIF YAML file (using `yaml.safe_load`) and extracting player loadouts for the current mission:

- **Ship classes** from:
  - `player_setup.start_ship` (if it's a standalone ship, resolving its `template` if used)
  - `player_setup.additional_ship_choices`
  - Wings named "Alpha", "Beta", "Gamma", "Delta", or "Epsilon" (resolving their `template`)
- **Primary weapons** from `weapons.primary` lists on the extracted ships and their templates, as well as `player_setup.additional_weapons`.
- **Secondary weapons** from `weapons.secondary` lists on the extracted ships and their templates, as well as `player_setup.additional_weapons`.

The collected sets are compared against the running "allowed" sets (initialized with `starting_loadout`).
Finally, the converter regex-scans the `.fsif` file for new `allow-ship` and `allow-weapon` SEXPs and adds those to the running "allowed" sets for the subsequent missions.

### Output

- If an un-granted ship or weapon is used by the player, a `[ERROR]` is emitted listing the missing items and providing actionable advice. The conversion process returns `False` and aborts.
- If all player ships and weapons are covered, an `[INFO]` confirmation is printed and the conversion proceeds.

## Version Handling

The converter accepts FCIF versions **1.0** and **1.1**. Files with other `fcif_version` values are rejected with a validation error. The new advance condition fields (`success_event`, `failure_goal`, `failure_event`) were introduced in version 1.1, but since they are optional with `None` defaults, version 1.0 files (which only use `success_goal` or no condition) remain fully compatible.
