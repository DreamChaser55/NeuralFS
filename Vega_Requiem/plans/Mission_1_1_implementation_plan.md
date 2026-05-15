# Mission 1_1 Implementation Plan
## Metadata
- **Name**: Strange Fires
- **Author**: NeuralFS
- **Description**: Routine patrol to investigate a missing transport in the Capella approach corridor.
- **Game Type**: single
- **AI Profile**: FS1 RETAIL
- **Environment**: Deep space, dark background (blue-black), Vega sun, Capella node far off.

## Player Setup & Loadout
- **Start Ship**: Alpha 1 (GTF Apollo)
- **Primary**: GTW ML-16 Laser
- **Secondary**: GTM MX-50, GTM Fury
- *No Avenger, no alternative ships, no bombers.*

## Entities
### Waypoints & Nav Buoys
- `Nav Alpha` (Terran NavBuoy) at `[0, 0, 6000]`
- `Jump-Out Point` (Terran NavBuoy) at `[0, 0, -500]`
- Waypoint path: `JumpOutPath` with a point at `[0, 0, -500]` for AI orders.

### Ships & Wings
- **GTT Meridian**: Wreckage. `GTT Elysium`, `[0, 0, 6000]`, `destroyed_before_mission_seconds: 10`.
- **Escape Pod 1**: `GTEP Hermes`, `[200, 0, 6000]`. Initial orders: `ai-waypoints-once "JumpOutPath" 89`. Departure cue: `( < ( distance "Escape Pod 1" "JumpOutPath:1" ) 500 )`.
- **Escape Pod 2**: `GTEP Hermes`, `[-350, 0, 6000]`. Initial orders: `ai-waypoints-once "JumpOutPath" 89`. Departure cue: `( < ( distance "Escape Pod 2" "JumpOutPath:1" ) 500 )`.
- **Alpha Wing**: 4x `GTF Apollo`. Position: `[0, 0, 0]`. Template: `alpha_fighter`. AI Wingmen orders: `ai-guard "Alpha 1" 89`.
- **Brahma Wing**: 4x `SF Scorpion`. Hostile. Arrival cue: `is-event-true-delay "BrahmaArrives" 0`. Position: `[0, 0, 14000]`. Distance from Nav Alpha is 8km. Initial orders: `ai-chase-wing "Alpha" 89`.
- **Vishnu Wing**: 3x `SF Basilisk`. Hostile. Arrival cue: `is-event-true-delay "VishnuArrives" 0`. Position: `[0, 0, 16000]`.

## SEXP Strategy
- **BrahmaArrives**: `( < ( distance "Alpha 1" "Nav Alpha" ) 3000 )`
- **VishnuArrives**: `( or ( is-event-true-delay "BrahmaArrives" 90 ) ( percent-ships-destroyed 50 "Brahma" ) )`
- **Pod1Safe**: `( has-departed-delay 0 "Escape Pod 1" )`
- **Pod2Safe**: `( has-departed-delay 0 "Escape Pod 2" )`
- **BothPodsSafe**: `( and ( is-event-true-delay "Pod1Safe" 0 ) ( is-event-true-delay "Pod2Safe" 0 ) )`

## Messages & Briefings
- **Command Briefing**: Admiral Chen Wei. Voice: `Alnilam` (Firm).
- **Mission Briefing**: Standard Officer. Voice: `Gacrux`.
- **In-Mission**: 
  - Alpha 2: `Schedar` (Even, calm veteran)
  - Alpha 3: `Fenrir` (Excitable young pilot)
  - Alpha 4: `Aoede` (Youthful/breezy)
  - Command: `Kore` (Firm, controlled alarm)

## Risks & Mitigations
- Pods are too slow: `ai-waypoints-once` will make them move at their top speed (which is very slow). Giving them a jump-out point at `-500` means they have to travel 6.5 km. Hermes speed is 40 m/s, so 6500m / 40 = 162 seconds (about 2.5 mins). That's perfect to force the player to defend them while the Vishnu wave hits.
- Alpha wing AI dying too fast: `ai-guard "Alpha 1"` keeps them grouped.
- Using `Terran NavBuoy` for Nav Alpha so it can be targeted and measured by `distance`.

## Known Constraints
- Player weapons intentionally weak.
- No `hud_directive_text` on events that use `is-event-true-delay`. Use direct checks.