# Mission 2_2 Implementation Plan
## Metadata
- **Name**: The Last Full Measure
- **Author**: NeuralFS
- **Description**: Escape pod defense at Nav Charlie.
- **Game Type**: single
- **AI Profile**: FS1 RETAIL
- **Flags**: `[]`
- **Fiction Viewer**: `Mission_2_2_story.txt`

## Environment
- **Ambient Light**: `[5, 5, 5]`
- **Bitmaps**: standard.

## Entities
- **GTD Amadeus** (Orion): `[0, 0, 0]`. Hull 40%. `ai-stay-still "Nav Bravo" 89`.
- **Nav Charlie**: Implicit `[0, 0, 0]`.
- **Nav Bravo** (Terran NavBuoy): `[0, 0, 7000]`.
- **GTS Casca** (Centaur): `[-500, 0, 500]`. `ai-stay-near-ship "Pod Group A 1" 89`.
- **Alpha Wing**: 4x Valkyrie. `[0, 500, 2000]`.
- **SC Ahriman** (Lilith): `[0, -1000, -5000]`. `ai-chase "GTD Amadeus" 89`.
- **Pod Group A**: 3x Hermes. `[0, 0, 500]`.
- **Pod Group B**: 3x Hermes. `[0, -100, 500]`. Arrives T+45.
- **Pod Group C**: 3x Hermes. `[0, 100, 500]`. Arrives T+90.
- **GTFr Aldrin 4** (Chronos): `[500, 0, 500]`. Arrives T+45.
- **TAC-1 Tech Cargo**: `docked` to Aldrin 4. `arrival_cue: (false)`.
- **Asura**: 3x Scorpion. `[0, 500, 5000]`. `ai-chase-wing "Pod Group A" 89`.
- **Brahma**: 3x Shaitan. `[5000, 0, -5000]`. Arrives T+90. `ai-chase "GTD Amadeus" 89`.
- **Vishnu**: 4x Scorpion. `[0, 0, -10000]`. Arrives T+180. `ai-chase-wing "Pod Group B" 89`.
- **Bheema**: 3x Dragon. `[0, 1000, 8000]`. Arrives T+360 or 5 pods at Nav Bravo. `ai-chase-wing "Pod Group C" 89`.

## SEXP Strategy
- **Pod Arrival & Departure**: 
  - `departure_cue` for pods: `(< (distance "<pod name>" "Nav Bravo") 1000)`. Wait, we can't do this for individual wing members easily unless we explicitly define them or use `percent-ships-departed`. If we just give the whole wing the `departure_cue: (< (distance "Pod Group A 1" "Nav Bravo") 1000)`? FSO wing departure cue applies to the whole wing at once. But pods might be at different distances.
  It's better to explicitly define Pod 1 through Pod 9 as standalone ships! Yes, the design doc says "Pod 1 through Pod 9 (GTEP Hermes x9)". Explicit definitions allow individual departure cues and tracking!
  - Pod 1, 2, 3: `[100, 0, 500]`, `[-100, 0, 500]`, `[0, 100, 500]`. Arrive T+0.
  - Pod 4, 5, 6: Arrive T+45.
  - Pod 7, 8, 9: Arrive T+90.
  - Initial orders for all: `ai-waypoints-once "BravoPath" 89`.
- **Amadeus Death sequence**:
  - `(< (hits-left "GTD Amadeus") 15)` -> "Amadeus structural failure imminent — clear the ship's immediate area."
  - `(< (hits-left "GTD Amadeus") 5)` -> Msg11.
  - 15 seconds after Msg11 -> `self-destruct "GTD Amadeus"`.
- **Success / Failure**:
  - Track departed pods. `(percent-ships-departed 66 "Pod 1" "Pod 2" ... "Pod 9")` means 6/9 departed.
  - Track destroyed pods. `(percent-ships-destroyed 44 "Pod 1" ... "Pod 9")` means 4/9 destroyed (which means < 6 survive).

## Audio
- Admiral Wei: Alnilam
- Alpha 2: Schedar
- Alpha 3: Fenrir
- Command/Amadeus CAG: Kore
- Stentor/Okafor: Laomedeia