# Mission 1-2 Implementation Plan

## Discovered Issues and Fixes

1. **Epsilon Transports Setup:**
   - **Issue:** The transports (Epsilon 1-4) had wing-member-style names which triggered warnings. Also, their initial setup used `ai-play-dead-persistent` instead of true docking because GTI Arcadia only has 2 dockpoints, making it impossible to dock 4 transports natively using pairs. 
   - **Fix:** Renamed the transports to `Epsilon Transport 1`, `Epsilon Transport 2`, `Epsilon Transport 3`, and `Epsilon Transport 4` to avoid naming warnings. Maintained `ai-play-dead-persistent` and precise initial positioning to simulate their moored status reliably without hitting the hard limits of FSO dockpoints.

2. **Arjuna Wave 2 Target Logic:**
   - **Issue:** According to the design document, Arjuna Wave 2 transitions from attacking the station to attacking the Epsilon transports. The original FSIF gave them an `initial_orders` SEXP to chase the player's wing (`Alpha`) and had a redundant retargeting event (`Arjuna2Retarget`).
   - **Fix:** Updated Arjuna Wave 2's `initial_orders` to chase all four `Epsilon Transport` ships directly. Deleted the redundant `Arjuna2Retarget` event.

3. **Stentor Directive Logic:**
   - **Issue:** The `StentorDirective` HUD directive originally used `( is-destroyed-delay 0 "GTC Stentor" )`. If this were true, the directive would turn green (success) upon Stentor's destruction, confusing the player.
   - **Fix:** Redesigned the directive formula. It now evaluates to true if the transports jump while the Stentor's hull is above 50% (`( and ( percent-ships-departed 75 ... ) ( > ( hits-left "GTC Stentor" ) 50 ) )`). By incorporating the `hits-left` constraint directly, if Stentor drops below 50% the condition can no longer become true, properly causing the engine to fail the event and turn the directive red.

4. **Stentor Secondary Goal Integration:**
   - **Issue:** The secondary goal `Stentor Survives` relied on a redundant event (`StentorCheck`), which could leave the goal indefinitely pending if the primary objective failed.
   - **Fix:** Hooked the goal directly to the redesigned `StentorDirective` event and removed the extraneous `StentorCheck` event, streamlining the mission flow.

5. **Malgor Retargeting and Engagement:**
   - **Issue:** The SC Malgor retargeting event (`MalgorMove`) was occurring at 480 seconds, but Stentor was not given matching orders to engage the cruiser as the design doc specified ("Stentor engages Malgor at close range").
   - **Fix:** Expanded the `MalgorMove` event to also clear Stentor's initial station-guarding orders and assign it an `ai-chase` goal targeting the `SC Malgor`.

6. **Player Loadout (Valkyrie Weapon Banks):**
   - **Issue:** The GTF Valkyrie template was erroneously assigned two secondary weapon banks (`MX-50` and `Fury`). The FSO engine mandates strictly 1 secondary bank for the Valkyrie, which caused a validation failure.
   - **Fix:** Removed `Fury` from the template's loadout and instead placed it in `additional_weapons` under `player_setup` so the player can manually choose to equip it instead of the `MX-50`.

## Final Validation Status
The mission cleanly converts via `fsif_to_fs2.py` and passes the Advanced SEXP Validator with 0 errors.