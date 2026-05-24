# Freespace Campaign Intermediate Format (FCIF) Implementation

This file documents the implementation details of FCIF and of the fcif->fc2 converter. It is not intended for `.fcif` file authors, but for FCIF converter programmers.

## Campaign Section

The `description` string will be automatically wrapped in `XSTR` for localization support by the converter.
The campaign type is always `single` (hardcoded by the converter).

**Validation:** The converter validates that `campaign.description` contains no double quotes (`"`). If any are found, conversion is aborted with an error. This is required because the description is emitted as `XSTR("...", -1)` — any `"` inside the string would produce invalid `.fc2` syntax.

## Missions Section

The converter always emits `+Flags: 0` and an empty `+Main Hall:` for every mission.

### Mission Filename Validation

The `filename` field on each `CampaignMission` entry is validated by a Pydantic `@field_validator` that enforces three constraints, checked in order:

1. **No path separators**: The filename must not contain `/` or `\`. If either character is present the validator raises a `ValueError` with a message that includes the phrase `path separators` and shows the offending value. This catches a common AI agent mistake of writing `fsif/missionname.fs2` instead of `missionname.fs2`.

2. **`.fs2` extension required**: After the path-separator check passes, the filename must end with `.fs2` (case-insensitive). If it does not, the validator raises a `ValueError` whose message includes `.fs2` and shows a correct-usage example.

3. **No double quotes**: After both structural checks pass, the filename must not contain `"`. The filename is emitted verbatim inside a quoted SEXP string in the `.fc2` output; an embedded `"` would break the FC2 parser.

All three violations are fatal: `load_fcif()` catches the resulting `ValidationError` and logs `[ERROR] Validation Error: ...`, after which `process_campaign()` returns `False` and the converter exits non-zero.

### Advance Condition Field Validation

The four advance condition fields (`success_goal`, `success_event`, `failure_goal`, `failure_event`) are validated by a shared Pydantic `@field_validator` that enforces:

- **No double quotes**: The value must not contain `"`. Each condition name is emitted inside a quoted SEXP string in the `.fc2` formula (e.g., `( is-previous-goal-true "mission.fs2" "Goal Name" )`); an embedded `"` would break the FC2 parser.

This violation is fatal and follows the same error path as the filename validation above.

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

## Advance Condition Reference Check

After the advance conditions warning check, the converter performs a **fatal** reference check: for every mission that has an advance condition field set, it verifies that the referenced goal or event name actually exists in the corresponding `.fsif` file.

### What is checked

For each mission with an advance condition, the converter:

1. Infers the FSIF path as `input_path.parent / "fsif" / f"{mission_stem}.fsif"`.
2. Opens and parses the FSIF YAML file.
3. Reads `mission_flow.goals` (for `success_goal` / `failure_goal`) or `mission_flow.events` (for `success_event` / `failure_event`).
4. Checks that at least one item in the list has a `name` field that exactly matches the referenced string.

Missions with **no advance condition** are silently skipped.

### Fatal conditions

The following situations cause the check to return `False` and abort conversion with an `[ERROR]`:

- The inferred `.fsif` file does not exist or is not a file.
- The `.fsif` file cannot be parsed as YAML.
- The `.fsif` file does not parse as a YAML mapping.
- The referenced goal or event name is not found in `mission_flow.goals` / `mission_flow.events`.

This differs from the loadout check, which treats a missing `.fsif` as a non-fatal warning. Because a typo in a campaign progression condition silently breaks campaign advancement (FSO will simply never advance from the mission), these errors are fatal.

### Output

On failure, the converter emits an `[ERROR]` that includes:
- The offending FCIF field name (e.g., `success_goal`).
- The referenced name that could not be found.
- A list of available goal/event names when the collection exists but the referenced name is absent.
- Actionable advice on how to fix the issue.

On success, an `[INFO]` confirmation is logged.

### Example error

```text
[ERROR] Campaign advance condition reference check failed in mission 'mission_01.fs2':
  Field 'success_goal' references goal 'EscrotConvoy', but no goal with that name exists in '.../fsif/mission_01.fsif'.
  Available goals: 'EscortConvoy', 'ScanTransport'
  Actionable advice: Fix the FCIF condition name to match an existing goal in mission_flow.goals, or define the referenced goal in the FSIF mission file.
```

## Campaign-Wide Player Loadout Check

When the converter is invoked, it performs a pre-conversion check to verify that the player's ships and weapons across the entire campaign are either in `starting_loadout` or explicitly granted by `allow-ship`/`allow-weapon` SEXPs in a previous mission. The converter infers the path to the `.fsif` files by checking the `fsif` directory relative to the input `.fcif` path (e.g., `input_path.parent / "fsif" / f"{mission_stem}.fsif"`).

### Why this matters

For any mission after the first one, an `allow-ship` or `allow-weapon` SEXP executed in a previous mission can make a ship class or weapon available. Every ship class and every weapon used by the player in any mission must therefore be present in `starting_loadout` or granted by an `allow-ship`/`allow-weapon` SEXP in a previous mission — otherwise FSO will simply not load or display those entities in the mission.

### What is checked

The converter iterates through all missions sequentially, parsing the FSIF YAML file (using `yaml.safe_load`) and extracting player loadouts for the current mission:

- **Ship classes** from:
  - Wings named "Alpha", "Beta", "Gamma", "Delta", or "Epsilon" (resolving their `template`). The FSIF validation rule requires `player_setup.start_ship` to be a member of a Friendly Alpha, Beta, or Gamma wing, so the start ship's class is covered by the wing check.
  - `player_setup.additional_ship_choices`
- **Primary weapons** from `weapons.primary` lists on the extracted ships and their templates, as well as `player_setup.additional_weapons`.
- **Secondary weapons** from `weapons.secondary` lists on the extracted ships and their templates, as well as `player_setup.additional_weapons`.

The collected sets are compared against the running "allowed" sets (initialized with `starting_loadout`).
Finally, the converter regex-scans the `.fsif` file for new `allow-ship` and `allow-weapon` SEXPs and adds those to the running "allowed" sets for the subsequent missions.

### Output

- If an un-granted ship or weapon is used by the player, a `[ERROR]` is emitted listing the missing items and providing actionable advice. The conversion process returns `False` and aborts.
- If all player ships and weapons are covered, an `[INFO]` confirmation is printed and the conversion proceeds.

## Version Handling

The converter accepts FCIF version **1.0**. Files with other `fcif_version` values are rejected with a validation error.