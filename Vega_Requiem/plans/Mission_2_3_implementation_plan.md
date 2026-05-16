# Mission 2-3 Implementation Plan

## Objective
Fix issues discovered by the FSIF Validator and verify correct implementation of the source material for `Vega_Requiem/fsif/Mission_2_3.fsif`.

## Identified Issues & Required Fixes

1. **Missing Text Styling Tags (Validator Warning)**
   - Add `$f{ ... $}` (Friendly), `$h{ ... $}` (Hostile), and `$y{ ... $}` (Locations) to briefing and debriefing stages.
   - Example: `$f{ GTC Stentor $}`, `$h{ SC Malgor $}`, `$f{ Alpha wing $}`, `$h Krishna wing`, `$h Indra wing`, `$h Arjuna wing`.

2. **Briefing Icons Overlap (Validator Warning)**
   - The icons for `GTC Stentor`, `Aldrin Wing`, `Rescue`, and `Theta 3` are placed too close to each other on the Y-axis (distance 350, minimum 395).
   - *Fix:* Spread them out along the Z-axis (map Y-axis). E.g., `[0, -500]`, `[0, -1000]`, `[0, -1500]`, `[0, -2000]`.

3. **Missing `hud_directive_text` (Validator Warning)**
   - Mission has 4 goals but only 3 events with `hud_directive_text`.
   - *Fix:* Add `hud_directive_text: "Destroy SC Malgor"` to the `MalgorKillObjective` event.
   - Also add an event `AllSurviveObjective` with `hud_directive_text: "Ensure all convoy ships transit"` to match the "All Survive" bonus goal, if needed, or simply let bonus goals remain hidden directives. Secondary goals definitely need one.

4. **Missing Bonus Goal (Source Material mismatch)**
   - The design document specifies: "Bonus: PVT Theta 3 specifically transits."
   - *Fix:* Add a new goal "Theta 3 Transits" with `type: "Bonus"`.
   - Formula: `( has-departed-delay 0 "Theta 3" )`.

5. **Theta 3 Logic Implementation (Source Material mismatch)**
   - The design doc specifies that when Arjuna wing activates, Theta 3 asks if she should proceed and waits for cover (20 seconds) before proceeding on her own.
   - *Fix:* 
     - Update `ArjunaActivate` event to also clear Theta 3's goals and order her to `ai-stay-still`.
     - Create a new event `Theta3Resumes` that triggers 20 seconds after `ArjunaActivate` to restore her `ai-waypoints-once` order and send the follow-up message.
     - Add `Msg7_followup` to the `messages` list with text: "Theta Three is proceeding to the node. Cover requested."

## Strategy for FSIF Modification
- **Briefing / Debriefing:** Update `mission_flow.briefing` and `mission_flow.debriefing` to include styling tags and adjusted icon coordinates.
- **Events:** Add `Theta3Resumes`. Update `ArjunaActivate`, `MalgorKillObjective`.
- **Goals:** Add `Theta 3 Transits`.
- **Messages:** Add `Msg7_followup`.