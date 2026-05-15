# Mission 1_3 Implementation Plan
## Metadata
- **Name**: No Truce With the Tide
- **Author**: NeuralFS
- **Description**: Escort Vasudan refugees and field test the Avenger cannon.
- **Game Type**: single
- **AI Profile**: FS1 RETAIL
- **Environment**: Deep space. Capella node at 5km.
- **Fiction Viewer**: `Mission_1_3_story.txt`
- **Flags**: `["all_attack"]` to make Unknown (HoL) fight Hostile (Shivans).

## Player Setup & Entities
- **Alpha 1**: `GTF Valkyrie` with `Avenger` and `ML-16 Laser`. Standalone ship.
- **Alpha 2, 3, 4**: `GTF Valkyrie` with `ML-16 Laser`. Standalone ships. `ai-guard "Alpha 1"`.
- **PVD Vigil**: `PVD Typhon`, `Friendly`, `[0, 0, 5000]`. Arrives at T+20s. Initial Hull: 35%. Scripted to die. `ai-chase-any 89`.
- **Theta 1, 2, 3**: `PVT Isis`, `Friendly`. Arrive T+20s with Vigil. Wait 5s then `ai-waypoints-once` to `Nav Alpha`.
- **Nav Alpha**: `Terran NavBuoy`, `[0, -500, -10000]`.
- **Brahma**: 4x `SF Scorpion`, `Hostile`. `[3000, 0, 5000]`. Present at start. T+20: `ai-chase "PVD Vigil" 89`. When Vigil dies, `ai-chase-wing "Theta"`.
- **Aquarius**: 4x `PVF Horus`, `Unknown` (HoL). `[0, 0, 12000]`. Present at start. `ai-chase-wing "Theta"`.
- **Pisces**: 3x `PVF Seth`, `Unknown` (HoL). `[0, -500, -9000]`. Present at start. `ai-guard "Nav Alpha"`.
- **Rama**: 3x `SF Basilisk`, `Hostile`. Arrives T+300 or Vigil dies. `[0, 0, 10000]`.
- **GTS Casca**: Arrives T+360.

## SEXP Strategy
- **Vigil Death**: Vigil starts at 35%. Shivans target her. `is-destroyed-delay 0 "PVD Vigil"`. Triggers Message 6 and Brahma retargeting to Theta.
- **Theta Jump**: Departure cue for each Theta: `(< (distance "Theta X" "Nav Alpha") 1000)`.
- **Message 1 (Hethor)**: Fires at T+20s when Vigil arrives. Voice: female Vasudan (use a deep or distorted female voice, or just write instructions "Vasudan voice").
- **Message 3 (Avenger kill)**: We can't track weapon type kills, but we can track the first Shivan kill by player. `has-time-elapsed 60` or `percent-ships-destroyed 25 "Brahma"`.
- **Message 9 (Theta 1 at Nav Alpha)**: When `(< (distance "Theta 1" "Nav Alpha") 2000)`.
- **Success**: 2 or more Theta ships jumped out. `( >= ( percent-ships-departed 100 "Theta 1" "Theta 2" "Theta 3" ) 66 )`. Wait, 2 of 3 is 66%. So `( percent-ships-departed 66 "Theta 1" "Theta 2" "Theta 3" )` will be true when 2 out of 3 depart.
- **Failure**: 2 Theta ships destroyed. `( percent-ships-destroyed 66 "Theta 1" "Theta 2" "Theta 3" )`.

## Audio
- Sub-Imperator Hethor: Use "Pulcherrima" (Forward) or "Kore" with "Vasudan accent, stoic".
- Theta 1 Pilot: "Algieba" (Smooth) with "Vasudan accent, strained".
- Alpha 2: "Schedar".
- Alpha 3: "Fenrir".
- Command: "Kore".

## Considerations
- We must define Alpha 1, 2, 3, 4 as standalone ships to give Alpha 1 the Avenger. FSO automatically puts ships with these names in the Alpha wing in the HUD.
- `all_attack` mission flag will make HoL and Shivans attack each other if they cross paths.
- "no-shields" flag for Alpha 1-4 and Theta transports. (Wait, do PVT Isis transports have shields? Vasudans developed shields after Terrans. I will put no-shields on Isis and Alpha).