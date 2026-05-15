# Mission 1_2 Implementation Plan
## Metadata
- **Name**: Breakwater
- **Author**: NeuralFS
- **Description**: Evacuation cover operation at GTI Vega Prime.
- **Game Type**: single
- **AI Profile**: FS1 RETAIL
- **Environment**: Warm amber-orange starfield. Vega star. Bitmaps: `neb02`, `neb11`, `dneb13`.
- **Fiction Viewer**: `Mission_1_2_story.txt`

## Player Setup
- **Start Ship**: Alpha 1 (GTF Valkyrie)
- **Additional Ships**: None
- **Weapons**: GTW ML-16 Laser, GTM MX-50, GTM Fury

## Entities
- **GTI Vega Prime** (GTI Arcadia): `[0, 0, 0]`. Hull 100%. (Can't be saved, will die to bombers + cruiser).
- **GTC Stentor** (GTC Fenris): `[1000, -500, 3000]`.
- **Nav Alpha** (Terran NavBuoy): `[0, -200, 2000]`. (Rally point).
- **Nav Bravo** (Terran NavBuoy): `[0, 500, 9000]`. (Jump node approach).
- **Epsilon 1..4** (GTT Elysium):
  - Ep 1: `[-200, 100, 200]`. Orders: `ai-play-dead` then waypoints.
  - Ep 2: `[200, -100, 200]`.
  - Ep 3: `[-200, -100, -200]`.
  - Ep 4: `[200, 100, -200]`.
- **GTFr Chronos 1**: Starts at `[500, 0, 1000]`. Deploys 2 Watchdogs.
- **Watchdog 1, 2**: Near Nav Alpha.
- **TAC-1 Containers**: 3x at `[-300, 0, 500]`, scan bonus.
- **GTS Casca** (GTS Centaur): Arrives `has-time-elapsed 240`.
- **Alpha Wing**: 4x GTF Valkyrie.
- **Durga Wing**: 4x SF Scorpion. At mission start. `[0, 0, 3000]`. Attack station/Stentor.
- **Arjuna Wave 1**: 3x SF Basilisk. Arrives `has-time-elapsed 150` at 12km (`[0, 0, 12000]`).
- **Arjuna Wave 2**: 3x SF Basilisk. Arrives `or (has-time-elapsed 330) (percent-ships-destroyed 66 "Arjuna Wave 1")`.
- **Krishna Wing**: 3x SF Scorpion. Arrives `has-time-elapsed 270`.
- **SC Malgor** (SC Cain): Arrives `has-time-elapsed 390` at 12km.

## SEXP Strategy
- **Epsilon Movement**: 
  - `when-argument` or individual `when` blocks to clear `ai-play-dead` and `add-goal` `ai-waypoints-once "EpsPath"`.
  - Ep 1: `has-time-elapsed 90`
  - Ep 2: `has-time-elapsed 120`
  - Ep 3: `has-time-elapsed 165`
  - Ep 4: `has-time-elapsed 210`
- **Malgor Target Change**: At T+480 (8 mins), clear goals and `ai-chase-any` or `ai-waypoints-once` to Antares node.
- **Epsilon Jump**: Departure cues for each: `(< (distance "Epsilon 1" "Nav Bravo") 1000)`

## Audio & Text
- Briefing & Debriefings with corresponding audio personas.
- `voice_name`: Gacrux, Kore, Alnilam, Schedar...

## Mitigations
- To avoid early deaths of Epsilon ships, give them `ai-play-dead-persistent` and invulnerability for the first few seconds? No, just keep them close to the station.
- Add "no-shields" flag to all allied fighters/bombers.