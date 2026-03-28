# Freespace Campaign Intermediate File (FCIF) Implementation

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

## First Mission Loadout Check

When the converter is invoked with `--first-mission <path>` (CLI) or the equivalent GUI field, it performs an optional pre-conversion check to verify that the first mission's ships and weapons are all covered by `starting_loadout`.

### Why this matters

For any mission after the first one, an `allow-ship` or `allow-weapon` SEXP executed in a previous mission can make a ship class or weapon available. The first mission has no prior mission, so no such SEXP can have run. Every ship class and every weapon used in the first mission must therefore be present in `starting_loadout` — otherwise FSO will simply not load or display those entities in the mission.

### What is checked

The converter parses the FSIF YAML file (using `yaml.safe_load`) and extracts:

- **Ship classes** from:
  - `entities.ships[*].class` (standalone ships, including those that reference a template via `template:`)
  - Templates referenced by `entities.wings[*].template` → resolved `entities.ship_templates[name].class`
- **Primary weapons** from `weapons.primary` lists on standalone ships and their templates.
- **Secondary weapons** from `weapons.secondary` lists on standalone ships and their templates.

The collected sets are compared against `starting_loadout.ships` and `starting_loadout.weapons` in the FCIF.

### Output

- For each **ship class** present in the mission but absent from `starting_loadout.ships`, a `[WARNING]` is emitted listing the missing class and instructing the author to add it.
- For each **weapon** (primary or secondary) present in the mission but absent from `starting_loadout.weapons`, a `[WARNING]` is emitted similarly.
- If all ships and weapons are covered, an `[INFO]` confirmation is printed.
- The check issues **warnings only** and never aborts or affects the generated `.fc2` output.

## Version Handling

The converter accepts FCIF versions **1.0** and **1.1**. Files with other `fcif_version` values are rejected with a validation error. The new advance condition fields (`success_event`, `failure_goal`, `failure_event`) were introduced in version 1.1, but since they are optional with `None` defaults, version 1.0 files (which only use `success_goal` or no condition) remain fully compatible.
