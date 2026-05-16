# Mission 1-3 Implementation Plan: No Truce With the Tide

## Source Material and Existing File Paths
- Design Doc: `Vega_Requiem/Detailed_Mission_Design_Documents/Act_1/Mission_1_3.txt`
- Existing FSIF: `Vega_Requiem/fsif/Mission_1_3.fsif`
- Output Path: `Vega_Requiem/fsif/Mission_1_3.fsif`

## Requested Changes and Affected Schema Sections
The mission was already partially implemented. The requested changes are fixes to specific SEXP logic blocks and AI goals to match the design document.
- **Initial Orders for Brahma Wing**: Currently set to `ai-stay-still "Alpha 1" 89`. Must be changed to `ai-chase "PVD Vigil" 89` to execute the scripted early destruction of the Vigil.
- **Initial Orders for Aquarius Wing**: Currently set to `ai-chase-any 89`. Must be changed to chase Theta transports sequentially (`ai-chase "Theta 1" 89`, etc.).
- **Initial Orders for Rama Wing**: Currently set to `ai-chase-any 89`. Must be changed to prioritize `Theta 3` as per the design doc ("Keep them off Theta Three").
- **Message Senders**: `HethorMessage` (Msg1) currently has `#Command` as the sender, but the text is from Sub-Imperator Hethor on the `PVD Vigil`.
- **ThetaAttacked Event Goals**: Currently clears Brahma goals and gives `ai-chase-any`. It must give specific orders to chase the Theta transports (`Theta 1`, `Theta 2`, `Theta 3`).

## Player Setup and Loadout Impacts
No changes needed. Player correctly has `GTF Valkyrie` with `Avenger` cannon in Bank 1 as the only Avenger.

## Entity List Impacts
No new entities or wings need to be added. `PVD Vigil` correctly arrives at 20s. `Theta` transports arrive at 20s and depart at `Nav Alpha`. `GTS Casca` correctly arrives at 360s.

## Briefing, Command Briefing, Debriefing and Message Impacts
No changes needed to the text. The voices map correctly to the providers. However, the sender for `Msg1` in the SEXP logic will be updated to `PVD Vigil`.

## Mission Flow and SEXP Strategy
- **Brahma wing initial_orders**: `( ai-chase "PVD Vigil" 89 )`
- **Aquarius wing initial_orders**:
  ```lisp
  ( ai-chase "Theta 1" 89 )
  ( ai-chase "Theta 2" 89 )
  ( ai-chase "Theta 3" 89 )
  ```
- **Rama wing initial_orders**:
  ```lisp
  ( ai-chase "Theta 3" 89 )
  ( ai-chase "Theta 2" 89 )
  ( ai-chase "Theta 1" 89 )
  ```
- **ThetaAttacked Event**:
  ```lisp
  ( when
    ( is-destroyed-delay 0 "PVD Vigil" )
    ( clear-goals "Brahma" )
    ( add-goal "Brahma" ( ai-chase "Theta 1" 89 ) )
    ( add-goal "Brahma" ( ai-chase "Theta 2" 89 ) )
    ( add-goal "Brahma" ( ai-chase "Theta 3" 89 ) )
    ( send-message "Theta 1" "High" "Msg4" )
  )
  ```
- **HethorMessage Event**:
  ```lisp
  ( when
    ( has-time-elapsed 22 )
    ( send-message "PVD Vigil" "High" "Msg1" )
  )
  ```

## FCIF Campaign / Loadout Impacts
N/A (We are editing a single FSIF mission file).

## Known Risks and Mitigation
- **Risk**: `PVD Vigil` might survive if the player destroys `Brahma` wing too quickly.
- **Mitigation**: The design doc states the Vigil's death is guaranteed by its low 35% hull, which the Typhon class starts with. The Scorpions will focus it heavily. If the player kills them quickly, it's a heroic feat, but standard FreeSpace design doesn't require hardcoding `destroy-instantly` unless absolutely necessary, and the design doc doesn't explicitly mention it.
- **Risk**: `all_attack` behavior with `Unknown` team (HoL).
- **Mitigation**: Setting them to `Unknown` with `all_attack` enabled is the correct way to implement a third faction that is hostile to both Terrans and Shivans.
