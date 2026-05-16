# Implementation Plan: Mission 2-3 (Vega Requiem) fixes

## Source Material and Context
- **Mission**: `Vega_Requiem/fsif/Mission_2_3.fsif`
- **Design Document**: `Vega_Requiem/Detailed_Mission_Design_Documents/Act_2/Mission_2_3.txt`
- **Campaign Bible**: `Vega_Requiem/Campaign_Bible.txt`

## Issues Discovered
1. **Goal 3 (All Survive) logic**: The `AllThroughMsg` event uses `percent-ships-departed 100` on the whole convoy. However, `percent-ships-departed` ignores destroyed ships. This means if *any* ship is destroyed, this event will never fire, and the mission could stall if there's no alternative trigger for the final jump message. Since the message is "That's everyone. Alpha Lead - your turn. Go." it should fire when all surviving ships have transited. Using `destroyed-or-departed-delay` evaluates to true once the fate of all listed ships is sealed (all are either destroyed or departed). This is the proper trigger for the final jump call.
2. **AI Goal error - `ai-stay-still`**: `Arjuna` wing, `SC Malgor`, and `Theta 3` are given `ai-stay-still` with `"Node Center"` as the argument. The FSO `ai-stay-still` SEXP expects a *waypoint name*, but `"Node Center"` is actually a ship (`Terran NavBuoy`). The appropriate SEXP for staying near a ship is `ai-stay-near-ship`. For `Theta 3`, simply clearing goals (`clear-goals`) effectively tells her to stop and fight, which perfectly matches her intended behavior of pausing upon detecting Dragons until ordered to resume.
3. **Malgor initial position**: In the MDD, Malgor is "Stationary at the node, 5000m from node mouth". The FSIF positions her at `[1000.0, 0.0, 7000.0]`, which is exactly 5000m from the node center at `[0.0, 0.0, 12000.0]`. This is correct.
4. **AllThroughMsg sender**: The sender is "Alpha 2", which works, but if Alpha 2 is destroyed, the message won't play. We should keep it as Alpha 2 since there's no `<any wingman>` fallback for an exact persona, and we can rely on the engine's fallback logic if available, but it's not a critical bug. We will just fix the trigger condition.

## Intended Fixes
- Edit `mission_flow.events.AllThroughMsg`: Replace `percent-ships-departed 100` with `destroyed-or-departed-delay 0` so Alpha 2 correctly tells the player to jump when the fate of the entire convoy is decided.
- Edit `entities.ships` for `SC Malgor`: Change `initial_orders` from `( ai-stay-still "Node Center" 89 )` to `( ai-stay-near-ship "Node Center" 89 )`.
- Edit `entities.wings` for `Arjuna`: Change `initial_orders` from `( ai-stay-still "Node Center" 89 )` to `( ai-stay-near-ship "Node Center" 89 )`.
- Edit `mission_flow.events.ArjunaActivate`: For `Theta 3`, remove the `add-goal` that tells her to `ai-stay-still "Node Center" 89` and leave just `clear-goals`. This will naturally pause her pathing without forcing an invalid goal.

## Execution
1. Perform exact string edits in `Vega_Requiem/fsif/Mission_2_3.fsif`.
2. Run FSIF Converter to validate changes.
3. Complete the task.