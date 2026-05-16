# Mission 1-1: Strange Fires - Implementation Plan

## Objective
Analyze `Vega_Requiem/fsif/Mission_1_1.fsif` against the Campaign Bible and Mission Design Document (Act 1, Mission 1-1) and fix any discovered discrepancies or SEXP logic issues.

## Source Material
- `Vega_Requiem/Campaign_Bible.txt`
- `Vega_Requiem/Detailed_Mission_Design_Documents/Act_1/Mission_1_1.txt`
- `Vega_Requiem/fsif/Mission_1_1.fsif`

## Intended Output Path
`Vega_Requiem/fsif/Mission_1_1.fsif`

## SEXP Strategy and Logic Analysis
After reviewing the source files, the implementation is highly accurate to the MDD. The ship placements, timing, wave logic, and loadouts correspond properly to the constraints established in the campaign bible (e.g., standard ML-16 Lasers without Avengers).

However, during SEXP logic analysis, several timing issues related to distance checks were identified:
1. **Premature Message Triggers (Bug):** `Alpha2PodsMsg` and `CommandJumpReady` relied on distance checks `< 4000` and `< 2000` from the `Jump-Out Point`. Since the player starts 500m away from the `Jump-Out Point` at mission start, these messages would trigger instantly at `T+00:00`.
   - **Fix:** Added `( is-event-true-delay "CommandRetreatMsg" 0 )` to both message events to ensure they only trigger during the retreat phase.
2. **End Message SEXP:** `Alpha2EndMsg` used `has-departed-delay` for `Alpha 1`. As this message is meant to be heard during the jump-out sequence, the player might miss the comms if they warp out instantly.
   - **Fix:** Switched logic to trigger when distance to the jump-out point is `< 1000`, matching the condition style of other retreat messages, combined with the retreat order event `( is-event-true-delay "CommandRetreatMsg" 0 )`.
3. **Wreckage Message Distance:** `Alpha2WreckageMsg` was set to trigger at 1500m, while the MDD specified 1000m.
   - **Fix:** Adjusted the trigger distance to 1000m.

## Entity List Impacts
No changes necessary. Ship templates, starting loadouts, and wings correctly adhere to Act 1 constraints.

## Briefing / Debriefing
All messages and briefings align precisely with MDD. Voice provider (`google`) correctly implemented.

## Execution
The aforementioned fixes were applied directly to the `Mission_1_1.fsif` file. A successful pass through the `fsif_to_fs2.py` converter yielded zero errors and zero warnings, confirming structural and logic integrity.