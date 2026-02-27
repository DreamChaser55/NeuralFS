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

## Version Handling

The converter accepts FCIF versions **1.0** and **1.1**. Files with other `fcif_version` values are rejected with a validation error. The new advance condition fields (`success_event`, `failure_goal`, `failure_event`) were introduced in version 1.1, but since they are optional with `None` defaults, version 1.0 files (which only use `success_goal` or no condition) remain fully compatible.
