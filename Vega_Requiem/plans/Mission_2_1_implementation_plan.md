# Mission 2_1 Implementation Plan
## Metadata
- **Name**: Dead Reckoning
- **Author**: NeuralFS
- **Description**: Convoy escort through a dense asteroid field.
- **Game Type**: single
- **AI Profile**: FS1 RETAIL
- **Flags**: `[]`

## Environment
- **Asteroid Field**: active, `asteroid`, num 100.
- **Nebula**: `enabled: true`, `sensor_range: 2000.0` (simulates sensor interference). This will make the mission claustrophobic and hide the Ahriman from radar unless close.
- **Suns**: none or dim (it's inside a nebula, so suns are hazy). We'll add one.

## Entities
- **GTD Amadeus** (Orion): `[0, 0, 0]`, hull 60%.
- **GTC Stentor** (Fenris): `[1500, -500, 0]`, hull 70%.
- **GTFr Aldrin 1, 2, 3** (Chronos): `[0, 0, 2000]`, `[500, 0, 2000]`, `[-500, 0, 2000]`.
- **GTT Rescue** (Elysium): `[0, 0, 1000]`.
- **Theta 3** (Isis): `[0, 0, -1000]`.
- **GTS Casca** (Centaur): `[-1000, 0, 0]`.
- **SC Ahriman** (Lilith): `[4000, -1000, -2000]`.
- **Nav Alpha**: `[0, 0, 5000]`.
- **Nav Bravo**: `[0, 0, 10000]`.
- **Alpha Wing**: 4x Valkyrie. `[0, 0, 3000]`.
- **Beta Wing**: 4x Apollo. `[0, 0, 500]`.
- **Indra Wing**: 4x Scorpion. `[0, 0, 10000]`, T+90.
- **Kali Wing**: 3x Shaitan. `[0, 0, -6000]`, T+150.
- **Deva Wing**: 3x Basilisk. `[0, 0, -6000]`, T+150.
- **Genma Wing**: 3x Shaitan. `[0, 0, -6000]`, T+360 AND Kali dead.

## SEXP Strategy
- **Movement**: Give all convoy ships `ai-waypoints-once` to Nav Bravo. They'll move forward.
- **Ahriman Movement**: Give it a parallel path `[4000, -1000, 8000]` so it stays at range.
- **Success**: Amadeus distance to Nav Bravo < 2000.
- **Failure**: Amadeus destroyed.
- **Secondary**: At least 3 of 5 convoy ships survive. Use `percent-ships-destroyed 60` for failure of this secondary.
- **Messages**: 
  - Ahriman warning if player gets < 3000m to Ahriman.
  - Genma targets Rescue, play Rescue's panicked voice.

## Audio
- Admiral Wei: Alnilam
- Commander Okafor: Laomedeia
- Amadeus CAG/Command: Kore
- Alpha 2: Schedar
- Alpha 3: Fenrir
- Rescue Pilot: Puck (anxious)

## Mitigations
- Casca should use `ai-stay-near-ship "GTD Amadeus"`.
- Ahriman must not close in to kill the Amadeus. A parallel path guarantees range.
- Asteroid field `num_objects` to 100, `average_speed` 20. Bounds `[-5000, -2000, -5000]` to `[5000, 2000, 15000]`.