# Mission 1-1: Strange Fires - Validator and Orientation Fix Plan

## Purpose of this addendum

This addendum preserves the original `Mission_1_1_implementation_plan.md` and documents a new fix pass for `Vega_Requiem/fsif/Mission_1_1.fsif` based on the current FSIF converter validator log and the user's request to add proper ship/wing orientations.

The existing mission converts successfully, but current validation reports two warnings that should be addressed before final conversion.

## Source material and existing file paths

- Campaign bible: `Vega_Requiem/Campaign_Bible.txt`
- Mission design document: `Vega_Requiem/Detailed_Mission_Design_Documents/Act_1/Mission_1_1.txt`
- Existing FSIF mission: `Vega_Requiem/fsif/Mission_1_1.fsif`
- Existing preserved implementation plan: `Vega_Requiem/plans/Mission_1_1_implementation_plan.md`
- This addendum plan: `Vega_Requiem/plans/Mission_1_1_validator_orientation_fix_plan.md`

## Intended output path

- Edit target after plan approval: `Vega_Requiem/fsif/Mission_1_1.fsif`
- Converter validation target: same FSIF file, using validation-only mode first.

## Current validator log summary

Command used:

```powershell
python FSIF_to_FS2_Converter/fsif_to_fs2.py "Vega_Requiem/fsif/Mission_1_1.fsif" --validate-only
```

Result:

- Validation passed.
- Advanced SEXP validation passed.
- Two warnings were reported:
  1. `Escape Pod 1` and `Escape Pod 2` both use the same waypoint movement order path `JumpOutPath`, creating a collision risk when they arrive at the same destination.
  2. `Escape Pod 1` and `Escape Pod 2` are larger-than-fighter/bomber standalone ships with default identity orientation; the validator recommends deliberate `orientation` values.

## Requested changes and affected FSIF schema sections

The requested work affects these FSIF sections:

- `entities.ships`
  - Add deliberate `orientation` values to standalone ships where visually or tactically relevant.
  - Update escape pod waypoint orders and departure cues if separate paths are adopted.
- `entities.wings`
  - Add deliberate `orientation` values to `Alpha`, `Brahma`, and `Vishnu` wings.
- `entities.waypoints`
  - Replace or supplement shared `JumpOutPath` with per-pod paths to remove the waypoint collision warning.
- `mission_flow.events`
  - Review any distance/departure logic that references pod waypoint paths.
- `mission_flow.goals`
  - Confirm the secondary goal remains tied to both pods departing safely.

No changes are planned to the command briefing, mission briefing, debriefing text, messages, audio provider, ship classes, or player loadout unless validation identifies a new issue after implementation.

## Relevant findings from the existing FSIF

- `Alpha` starts at `[0.0, 0.0, 0.0]`, while `GTT Meridian` and `Nav Alpha` are at roughly `[0.0, 0.0, 6000.0]`. The opening patrol direction is therefore world `+Z`.
- `Brahma` starts at `[0.0, 0.0, 14000.0]` and `Vishnu` starts at `[0.0, 0.0, 16000.0]`, arriving from the Capella direction and attacking back toward Alpha and the wreckage. Their natural facing is world `-Z` or toward `Alpha`.
- `Escape Pod 1` starts at `[200.0, 0.0, 6000.0]` and `Escape Pod 2` starts at `[-350.0, 0.0, 6000.0]`; both currently use `JumpOutPath`, whose only point is `[0.0, 0.0, -500.0]`.
- The mission uses `Jump-Out Point`, a visible `Terran NavBuoy`, at `[0.0, 0.0, -500.0]` as the player-facing return marker.
- The mission currently has no `orientation` fields at all, even though opening geometry strongly implies facing directions.

## Player setup and loadout impacts

No player loadout changes are planned.

- `player_setup.start_ship` remains `Alpha 1`.
- `Alpha` remains `GTF Apollo` x4.
- Era-correct loadout remains `ML-16 Laser`, `MX-50`, and `Fury` only.
- No additional ships or weapons are added.
- The campaign unlock event `allow-ship "GTF Valkyrie"` in `Alpha1Safe` remains untouched unless later validation unexpectedly flags it.

## Entity list impacts

### Waypoint path fix

Plan to eliminate the shared-path collision warning by replacing the single shared pod movement path with two slightly offset paths:

```yaml
waypoints:
  Pod1JumpOutPath:
    - [250.0, 0.0, -500.0]
  Pod2JumpOutPath:
    - [-250.0, 0.0, -500.0]
```

The offsets keep both pods within 500 m of the visible `Jump-Out Point` marker while preventing them from converging on exactly the same endpoint.

`Escape Pod 1` initial order should become:

```lisp
( ai-waypoints-once "Pod1JumpOutPath" 89 )
```

`Escape Pod 2` initial order should become:

```lisp
( ai-waypoints-once "Pod2JumpOutPath" 89 )
```

Pod departure cues should prefer the visible central marker to preserve the player-facing objective:

```lisp
( < ( distance "Escape Pod 1" "Jump-Out Point" ) 500 )
( < ( distance "Escape Pod 2" "Jump-Out Point" ) 500 )
```

This maintains the design intent that pods are safe when they reach the jump-out zone, not an invisible exact point.

### Orientation fix

Add deliberate initial facing for all meaningful ships and wings that spawn by `Hyperspace` or are present at mission start.

Proposed orientation strategy:

- `GTT Meridian`: use a hand-authored yaw-only matrix to make the destroyed transport wreck visibly canted rather than grid-aligned. Suggested nose direction is slightly off the patrol lane, roughly world `+Z` with a small `+X` yaw component:
  ```yaml
  orientation: [0.939693, 0.0, -0.342020, 0.0, 1.0, 0.0, 0.342020, 0.0, 0.939693]
  ```
- `Nav Alpha`: face the retreat lane / jump-out marker:
  ```yaml
  orientation: "Jump-Out Point"
  ```
- `Jump-Out Point`: face back toward the investigation site:
  ```yaml
  orientation: "Nav Alpha"
  ```
- `Escape Pod 1`: face its own outbound path:
  ```yaml
  orientation: "Pod1JumpOutPath:1"
  ```
- `Escape Pod 2`: face its own outbound path:
  ```yaml
  orientation: "Pod2JumpOutPath:1"
  ```
- `Alpha` wing: face the investigation site at mission start:
  ```yaml
  orientation: "Nav Alpha"
  ```
- `Brahma` wing: face back toward Alpha on arrival:
  ```yaml
  orientation: "Alpha"
  ```
- `Vishnu` wing: face back toward Alpha on arrival:
  ```yaml
  orientation: "Alpha"
  ```

Notes:

- The authoring guide states that authored `orientation` is ignored for non-Hyperspace arrivals. All affected entities are mission-start or Hyperspace arrivals, so the fields should apply.
- Target-name orientation is preferred where possible because the converter computes the matrix and avoids manual sign errors.
- The hand-authored `GTT Meridian` matrix uses the documented safe yaw-only formula and is orthonormal within normal rounding tolerances.

## Briefing, command briefing, debriefing, and message impacts

No text changes are planned.

The existing briefings already describe the simple there-and-back geometry:

- `Alpha` investigates `Nav Alpha` / `GTT Meridian`.
- `Jump-Out Point` marks the return location.
- Escape pod survival is reported in debriefing based on pod departure state.

The per-pod path offsets are invisible implementation details and should not need briefing text changes.

## Mission flow and SEXP strategy

Relevant SEXP operators checked:

- `ai-waypoints-once`: valid ship goal, takes waypoint path name and priority; current priority `89` is valid.
- `distance`: accepts ships, wings, or waypoints; therefore checking pod distance to the visible `Jump-Out Point` ship is valid.
- `has-departed-delay`: true only for ships that warp out and false forever if destroyed; this remains appropriate for pod-safe events and debriefing.
- `percent-ships-destroyed`: current Vishnu trigger using `50` percent of `Brahma` remains valid.
- `is-event-true-delay`: current event chaining remains valid and advanced validation already passed.

Planned SEXP-level changes are intentionally minimal:

1. Change each pod's `ai-waypoints-once` path name to its new unique path.
2. Change each pod's departure cue to distance from the visible `Jump-Out Point` marker rather than from the old shared `JumpOutPath:1` point.
3. Keep `Pod1Safe`, `Pod2Safe`, and `Save Escape Pods` logic unchanged because they correctly depend on pod departure.

## FCIF campaign/loadout/advance-condition impacts

No FCIF changes are planned.

The proposed FSIF changes do not rename goals/events referenced by the campaign and do not alter player ship or weapon availability. The campaign loadout implications remain unchanged.

## Known risks and mitigation

### Risk: pod rescue timing changes

Offset pod endpoints may slightly change travel time and departure timing.

Mitigation:

- Keep offsets small (`250 m` left/right of the visible marker).
- Use the central `Jump-Out Point` distance check at `500 m` so pods depart when they reach the same general safe zone as before.

### Risk: target-name orientation resolution error

If any orientation target name is misspelled, conversion will fail.

Mitigation:

- Use only existing names: `Jump-Out Point`, `Nav Alpha`, `Alpha`, `Pod1JumpOutPath:1`, and `Pod2JumpOutPath:1`.
- Run validation-only conversion immediately after implementation.

### Risk: unnecessary orientation on nav buoys

Nav buoy model facing is usually not important.

Mitigation:

- Adding orientation to nav buoys is harmless and satisfies the request for proper ship/wing orientations. If validation or visual review suggests it is unnecessary, these can be omitted, but the first implementation will favor completeness.

### Risk: preserving mission difficulty

Changing pod paths could make pod survival easier or harder.

Mitigation:

- Use lateral offsets only; do not shorten the route materially.
- Do not change enemy arrival timing, AI class, weapons, or pod hull values in this fix pass.

## Validation and conversion checklist

After FSIF changes are approved and implemented:

1. Run validation-only conversion:
   ```powershell
   python FSIF_to_FS2_Converter/fsif_to_fs2.py "Vega_Requiem/fsif/Mission_1_1.fsif" --validate-only
   ```
2. Confirm zero errors and zero warnings.
3. If validation-only is clean, run normal conversion:
   ```powershell
   python FSIF_to_FS2_Converter/fsif_to_fs2.py "Vega_Requiem/fsif/Mission_1_1.fsif"
   ```
4. Do not read or analyze the generated `.fs2` file.
5. If warnings/errors remain, inspect the FSIF and iterate only with documented fixes.

## Self-review of this plan

- Schema compliance: proposed edits use documented FSIF fields under `entities.ships`, `entities.wings`, and `entities.waypoints`.
- SEXP validity: all changed SEXPs use existing operators and documented argument forms.
- Orientation validity: target-name orientations reference defined ships/wings/waypoints; the one matrix uses the documented yaw-only formula.
- Converter risk: the most likely failure would be a typo in a target-name orientation, mitigated by validation-only conversion.
- Mission-design alignment: the opening scene remains a routine patrol toward the wreck, followed by hostile arrivals from the Capella direction and retreat to the jump-out zone.
- Scope control: no mission-flow rewrites, briefing rewrites, loadout changes, event renames, or campaign changes are included.

## Approval gate

Do not edit `Vega_Requiem/fsif/Mission_1_1.fsif` until the user explicitly approves this addendum plan for implementation.
