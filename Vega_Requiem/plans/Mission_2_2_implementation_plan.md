# Mission 2_2 Implementation Plan

## Discovered Issues from Validation
1. **Collision Warnings**: Escape pods (`Pod 1` to `Pod 9`) and potentially `GTFr Aldrin 4` are currently set to arrive via `Hyperspace` with static locations that overlap or are too close to each other.
   - *Fix*: The mission design document states they emerge from the `GTD Amadeus` fighterbay. We will change their `arrival_method` to `"Docking Bay"` with `arrival_anchor: "GTD Amadeus"` and remove the static `position` and `arrival_distance` parameters. We will adjust the `arrival_delay` and `arrival_cue` to sequence them in groups of 3 over time as specified (Group A at T+0s, Group B at T+45s, Group C at T+90s).

2. **Missing Text Styling**: The briefing and debriefing texts lack standard FreeSpace text color tags (`$f{ ... $}`, `$h{ ... $}`, `$y{ ... $}`).
   - *Fix*: Add appropriate tags to the `text` fields in `mission_flow.briefing.stages` and `mission_flow.debriefing.stages`.
     - `$f{ GTD Amadeus $}`, `$y{ Nav Charlie $}`, `$y{ Nav Bravo $}`, `$f{ GTC Stentor $}`
     - `$f{ Alpha wing $}`, `$h{ SC Ahriman $}`, `$h{ Asura wing $}`, `$f{ Pod One $}`

3. **HUD Directives Mismatch**: The validation warns that there are 4 goals but only 2 events with `hud_directive_text`. Also, the MDD describes an additional bonus goal.
   - *Fix*: Add the missing Bonus goal "Save Admiral's Pod" (Ensure Pod 1 reaches Nav Bravo).
   - *Fix*: Add standalone events with `hud_directive_text` for the primary and main secondary goals. Remove `hud_directive_text` from general messaging events, and instead create dedicated directive events:
     - "DirEvacuatePods": `percent-ships-departed 66 ...` -> "At least 6 pods reach Nav Bravo"
     - "DirSaveAldrin4": `has-departed-delay 0 "GTFr Aldrin 4"` -> "Protect GTFr Aldrin 4"
     - "DirSaveAmadeusCrew" (Optional Bonus): `percent-ships-departed 100 ...` -> "Ensure all pods escape"

## Detailed Plan
1. **Pod and Freighter Arrival Parameters:**
   - Update `GTFr Aldrin 4` and `Pod 1` through `Pod 9` with:
     ```yaml
     arrival_method: "Docking Bay"
     arrival_anchor: "GTD Amadeus"
     ```
   - Ensure the `arrival_cue` logic matches the timings (T=0 for group A, T=45 for group B, T=90 for group C). 
   - Note: Since they use `Docking Bay`, `position` can actually be omitted (or left as a fallback, but removing is cleaner). We will leave `position` as is just in case, but the `arrival_method` overrides it. Wait, the schema says `position` is required for `ships`. We'll just spread their `position` coordinates out by a few hundred meters so that if `position` is validated for bounding boxes, it won't complain. But wait, `Docking Bay` makes them spawn at the fighterbay. We can just spread the initial `position` vector [x, y, z] so they don't overlap in the file's static checker, and `arrival_method` will handle actual game spawning.
     Actually, let's just spread their `position` out (e.g. `[100, 0, 1500]`, `[200, 0, 1500]`, `[300, 0, 1500]`) to bypass the validator warning, and add `arrival_method: "Docking Bay"` and `arrival_anchor: "GTD Amadeus"`.

2. **Goals Updates:**
   - Add:
     ```yaml
     - name: "Save Admiral's Pod"
       type: "Bonus"
       objective_text: "Ensure Pod 1 reaches Nav Bravo."
       formula: |
         ( has-departed-delay 0 "Pod 1" )
     ```

3. **Events Updates:**
   - Add dedicated events for HUD directives to match the goals.
   - Remove `hud_directive_text` from `MissionEndMsg` and `AldrinSafe`.
   - Add:
     ```yaml
     - name: "DirEvacuate"
       formula: |
         ( percent-ships-departed 66 "Pod 1" "Pod 2" "Pod 3" "Pod 4" "Pod 5" "Pod 6" "Pod 7" "Pod 8" "Pod 9" )
       hud_directive_text: "At least 6 pods reach Nav Bravo"
     - name: "DirAldrin"
       formula: |
         ( has-departed-delay 0 "GTFr Aldrin 4" )
       hud_directive_text: "Protect GTFr Aldrin 4"
     ```

4. **Briefing Text Formatting:**
   - Replace plain ship names with styled ones in `mission_flow.briefing.stages` and `debriefing.stages`.
   - Ensure closing tag `$}` is always present.

5. **Re-Run Converter:**
   - Validate the changes fix the warnings and produce a working mission.