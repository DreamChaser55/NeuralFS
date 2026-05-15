# Mission 2_3 Implementation Plan
## Metadata
- **Name**: Vega Requiem
- **Author**: NeuralFS
- **Description**: Final evacuation through the Antares node.
- **Game Type**: single
- **AI Profile**: FS1 RETAIL
- **Flags**: `[]`
- **Fiction Viewer**: `Mission_2_3_story.txt`

## Environment
- **Ambient Light**: `[5, 5, 5]`
- **Suns**: Vega, small scale astern.
- **Bitmaps**: standard. No nebula.

## Entities
- **GTC Stentor** (Fenris): `[0, 0, 0]`. Hull 55%.
- **GTFr Aldrin 1, 2, 3** (Chronos): `[500, 0, -2000]`, `[0, 500, -2000]`, `[-500, 0, -2000]`.
- **GTT Rescue** (Elysium): `[0, 0, -3000]`.
- **Theta 3** (Isis): `[0, 0, -4000]`.
- **GTS Casca** (Centaur): `[-1000, 0, -1000]`.
- **Nav Alpha**: `[0, 0, 6000]`.
- **Node Center** (Terran NavBuoy): `[0, 0, 12000]`.
- **Antares Node** (Jump Node): `[0, 0, 12000]`.
- **SC Malgor** (Cain): `[0, 0, 7000]`. `ai-stay-still "Node Center"`.
- **Alpha Wing**: 4x Valkyrie. `[0, 500, 1000]`.
- **Krishna**: 4x Scorpion. `[-4000, 0, 4000]`. `ai-chase-any`.
- **Indra**: 3x Basilisk. `[0, 0, 6000]`. `ai-chase "GTC Stentor"`.
- **Arjuna**: 2x Dragon. `[0, 1000, 10000]`. `ai-stay-still "Node Center"`. When Stentor < 2000 from Node Center -> `ai-chase-any`.

## SEXP Strategy
- **Departure Cues**: All convoy ships depart when distance to `Node Center` < 2000.
- **Malgor Weapons**: `(when (< (hits-left-subsystem "SC Malgor" "weapons") 20) (turret-lock-all "SC Malgor"))`.
- **Success Condition**: `has-departed-delay 0 "GTC Stentor"`.
- **Secondary**: `percent-ships-departed 60` for the remaining 5 convoy ships (3/5 is 60%).
- **Bonus**: `percent-ships-departed 100` for convoy ships.
- **Failure**: `is-destroyed-delay 0 "GTC Stentor"`.

## Audio
- Commander Okafor: Laomedeia
- Alpha 2: Schedar
- Alpha 3: Fenrir
- Theta 3: Algieba
- Aldrin 1: Puck
- Command: Kore