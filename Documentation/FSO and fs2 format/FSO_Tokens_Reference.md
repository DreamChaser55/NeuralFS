# FSO Tokens Reference (Tokens, Flags, and Canonical Literals)

## Scope
- Single source of truth for valid FSO tokens: flags, enumerations, literals, and canonical spellings.
- For FSIF field schema and constraints, see `../fsif/specification.md`.
- For SEXP operator signatures and full catalogs, see `../FSO SEXPs/INDEX.md`.

## Guidance on Token Usage
- Exact token spelling is required. All tokens must be authored exactly as shown — unknown or misspelled tokens cause errors.
- Do not vary case.
- Do / Don't examples:
  - Do: `"<any friendly player>"`   Don't: `"<any player>"`, `"<any Friendly Player>"`
  - Do: `"High"`                    Don't: `"high"`
  - Do: `"ai-guard-wing"`           Don't: `"ai_guard_wing"`
- Token length limit: Custom tokens (ship, message, event names, etc.) must be shorter than 30 characters. Prefer CamelCase for custom event/goal/message names (e.g., `AmbushWarning`, `ScanComplete`) to keep tokens shorter by avoiding spaces or underscores.
- Special selectors like `"<any wingman>"` and `"<any friendly player>"` are ordinary quoted strings; do not escape the angle brackets.

## Related reference files
- Ship classes: ./spacecraft-classes.md
- Ship subsystem names (per faction): ./Ship subsystems/*.md
- Ship dockpoint names: ./ship-dockpoint-names.md
- SEXP operators: ../FSO SEXPs/INDEX.md

## Enumerations and common literals

### Teams
- Friendly
- Hostile
- Unknown

**Note on "Neutral" IFF team:**
The FSO engine theoretically supports a "Neutral" IFF team, but its implementation is broken — it essentially acts as a second hostile faction and attacks the player. FSIF does not support the "Neutral" team. Use `"Friendly"`, `"Hostile"`, or `"Unknown"` for all ships, objects, and briefing icons.

Context: `team`.

### Arrival/Departure Methods

Context: FSIF `arrival_method`, `departure_method`.

#### Arrival and Departure
- Hyperspace
- Docking Bay
  - requires a ship as `arrival_anchor` / `departure_anchor`
  - `arrival_distance` is forced to `0` and should be omitted.

#### Arrival-only (directional)
All of these require both `arrival_distance` and a ship `arrival_anchor`.
- Near Ship
- In front of ship
- In back of ship
- Above ship
- Below ship
- To left of ship
- To right of ship

Note: with non-Hyperspace arrival methods, ship or wing orientation is always set to face the `arrival_anchor` (`orientation` field is ignored).

Example usage (wing arrival anchored to any friendly player):
```yaml
name: Arjuna
arrival_method: In front of ship
arrival_distance: 1500
arrival_anchor: "<any friendly player>"
arrival_cue: |
  ( is-event-true-delay "CargoBlowinUp" 12 )
```

### Message priorities
- "Low"
- "Normal"
- "High"

Context: `send-message`, `send-random-message`, `send-message-list`.

### AI Class values (worst→best)
- Coward
- Lieutenant
- Captain
- Major
- Colonel
- General

### Goal types
- Primary
- Secondary
- Bonus

## Wildcards and special literals

- `"<any wingman>"`
- `"<any friendly player>"`
- `"<any friendly>"`
- `"<any hostile>"`
- `"<any unknown>"`
- `"#Command"`

Author these literals exactly as shown — including the angle brackets in the `<any ...>` selectors and the leading `#` in `"#Command"`. Do not omit or substitute these characters.

Valid contexts: `send-message` sender, general SEXP entity lists, `arrival_anchor`.

## Flags catalog

This section lists a subset of canonical flags generally useful for mission authors. A complete catalog is available in the converter documentation.

### Mission flags (`mission_info.flags`)

*   `subspace` — Mission takes place in subspace
*   `no_promotion` — Cannot get promoted or badges in this mission
*   `fullneb` — Mission is a full nebula mission (auto-injected when environment.nebula.enabled is true; do not author manually)
*   `no_builtin_msgs` — Disables builtin msgs
*   `no_traitor` — Player cannot become a traitor
*   `toggle_ship_trails` — Toggles ship trails (off in nebula, on outside nebula)
*   `support_repairs_hull` — Toggles support ship repair of ship hulls
*   `beam_free_all_by_default` — Beam-free-all by default
*   `no_briefing` — No briefing, jump right into mission
*   `toggle_debriefing` — Turn off debriefing.
*   `red_alert` — A red-alert mission (player damage and loadout persists from the previous mission, only the first briefing stage text is shown)
*   `scramble` — A scramble mission (no loadout customization)
*   `no_builtin_command` — Turns off Command messages without turning off pilots
*   `all_attack` — All teams at war
*   `toggle_showing_goals` — Show mission goals for training missions, hide otherwise
*   `end_to_mainhall` — Return to the mainhall after debriefing
*   `preload_subspace` — Preload the subspace tunnel for both the sexp and specs checkbox (for scripts)

### Ship flags (`entities.ships[*].flags`)

*   `cargo-known` — Ship's cargo is revealed to all friendly ships
*   `ignore-count` — Ignore this ship when counting ship types for goals
*   `protect-ship` — No AI-controlled ship will attack this ship
*   `reinforcement` — (Deprecated; use `reinforcement_ships` list instead)
*   `no-shields` — Disables shields for this ship (all fighters and bombers have shields by default; use this flag to disable them)
*   `escort` — Ship shown in the HUD escort overview table
*   `no-arrival-music` — Don't play arrival music when ship arrives
*   `invulnerable` — Ship cannot be damaged
*   `hidden-from-sensors` — Ship doesn't show up on sensors, blinks in/out on radar
*   `scannable` — Ship is "scannable". Play scan effect and report as "Scanned" or "Not scanned". Required if your mission demands scanning the ship.
*   `kamikaze` — AI behavior: kamikaze
*   `no-dynamic` — AI behavior: no dynamic goals
*   `red-alert-carry` — Ship status should be stored/restored if red alert mission
*   `guardian` — Ship cannot die (hull stuck at 1%), but can take damage and have subsystems destroyed
*   `special-warp` — Ship arrives via Knossos subspace node
*   `stealth` — Is this particular ship stealth
*   `friendly-stealth-invisible` — When stealth, don't appear on radar even if friendly
*   `no-arrival-warp` — No arrival warp in effect
*   `no-departure-warp` — No departure warp in effect
*   `beam-protected` — Protected against beams
*   `flak-protected` — Protected against flaks
*   `laser-protected` — Protected against lasers (primaries)
*   `missile-protected` — Protected against missiles (secondaries)
*   `vaporize` — Ship is vaporized when destroyed - alternative, quick death sequence
*   `dont-collide-invis` — Does not collide with invisible ships
*   `cannot-arrive` — Used to indicate that this ship's arrival cue will never be true
*   `warp-broken` — Warp engine should be broken for this ship
*   `warp-never` — Warp drive is destroyed
*   `targetable-as-bomb` — Targetable as bomb
*   `no-builtin-messages` — Ship should not send built-in messages
*   `no-death-scream` — Ship has no death scream
*   `always-death-scream` — Ship always screams on death
*   `lock-all-turrets-initially` — Lock all turrets on this ship at mission start or on arrival
*   `force-shields-on` — Force shields on
*   `dont-change-position` — Don't change position
*   `dont-change-orientation` — Don't change orientation
*   `immobile` — Encompasses both `don't-change-position` and `don't-change-orientation`
*   `no-disabled-self-destruct` — Ship will not self-destruct after 90 seconds if engines or weapons destroyed
*   `has-display-name` — Has display name
*   `hide-mission-log` — Mission log events generated for this ship will not be viewable
*   `attackable-if-no-collide` — Prevents turrets from ignoring this ship even if it has `no_collide` set
*   `fail-sound-locked-primary` — Plays fail sound when firing with locked weapons (primary)
*   `fail-sound-locked-secondary` — Plays fail sound when firing with locked weapons (secondary)
*   `aspect-immune` — Ship cannot be locked onto by aspect seeking weapons
*   `cannot-perform-scan` — Ship cannot scan other ships
*   `no-targeting-limits` — Ship is always targetable regardless of AWACS or targeting range limits
*   `primitive-sensors` — Primitive sensor display
*   `no-subspace-drive` — This ship has no subspace drive
*   `toggle-subsystem-scanning` — Switch whether subsystems are scanned
*   `hide-ship-name` — Hides the ship's name
*   `cloaked` — This ship will not be rendered
*   `scramble-messages` — All messages sent from or received by this ship appear scrambled
*   `no_collide` — Other ships don't collide with this ship
*   `primaries-locked` — This ship can't fire primary weapons
*   `secondaries-locked` — This ship can't fire secondary weapons
*   `weapons-locked` — Prevents the player from changing the weapons on the ship on the loadout screen
*   `ship-locked` — Prevents the player from changing the ship class on loadout screen
*   `afterburners-locked` — This ship can't use its afterburners
*   `lock-all-turrets` — Lock all turrets on this ship at mission start or on arrival
*   `primary-linked` — Ship's primary weapons are linked together
*   `secondary-dual-fire` — Ship is firing two missiles from the current secondary bank
*   `glowmaps-disabled` — To disable glow maps
*   `no-secondary-lockon` — Secondary weapons lock-on disabled
*   `subsystem-movement-locked` — Rotating subsystems are locked in place
*   `draw-as-wireframe` — Ship will be rendered in wireframe mode
*   `render-without-diffuse` — Ship will be rendered without diffuse map
*   `render-without-glowmap` — Ship will be rendered without glow map
*   `render-without-specmap` — Ship will be rendered without spec map
*   `render-without-normalmap` — Ship will be rendered without normal map
*   `render-without-heightmap` — Ship will be rendered without height map
*   `render-without-ambientmap` — Ship will be rendered without ambient map
*   `render-without-miscmap` — Ship will be rendered without misc map
*   `render-without-reflectmap` — Ship will be rendered without reflect map
*   `render-full-detail` — Render full detail
*   `render-without-light` — Render without light
*   `render-without-weapons` — Skip weapon model rendering
*   `render-with-alpha-mult` — Render with alpha mult
*   `no-passive-lightning` — Disables ship passive lightning
*   `maneuver-despite-engines` — Ship can move even when engines are disabled or disrupted
*   `no-scanned-cargo` — The cargo will never be revealed, instead always returning "Scanned" or "Not Scanned"

Ancillary per-ship fields frequently seen with flags:
- `escort_list_priority` (Integer; used with `escort`)

### Wing flags (`entities.wings[*].flags`)

*   `reinforcement` — (Deprecated; use `reinforcement_wings` list instead)
*   `no-arrival-music` — Don't play arrival music when wing arrives
*   `no-arrival-message` — Don't play any arrival message
*   `ignore-count` — Ignore all ships in this wing for goal counting purposes
*   `no-arrival-warp` — Don't play warp effect for any arriving ships in this wing
*   `no-departure-warp` — Don't play warp effect for any departing ships in this wing
*   `no-dynamic` — Members of this wing relentlessly pursue their AI goals
*   `departure-ordered` — Departure of this wing was ordered by player
*   `no-first-wave-message` — Don't play arrival message for the first wave
*   `waypoints-no-formation` — Wing will not try to form up when running a waypoint together

## Waypoints and Jump Nodes

**Waypoints** (`entities.waypoints`): invisible AI/logic references. Path name is the YAML key; point reference in SEXPs is `"PathName:N"` (1-based index).

**Jump Nodes** (`entities.jump_nodes`): visible to the player. Fields: `name`, `position`.

## SEXP example patterns

### Messaging from wildcard wingman
```lisp
(when
   (has-arrived-delay 4 "Tantalus")
   (send-message "<any wingman>" "High" "It looks like an ambush")
)
```

### Unlock tech and allow weapon
```lisp
(when
   (true)
   (allow-weapon "Avenger")
   (tech-add-weapons "Avenger")
   (tech-add-ships "SF Manticore" "SF Scorpion" "SB Shaitan" "SC 5" "SAC 2" "SC Cain" "SSG Trident")
)
```

### Protect/unprotect runtime
```lisp
(when
   (has-arrived-delay 6 "Arjuna")
   (send-message "#Command" "High" "Trap alert!")
   (protect-ship "Alpha 1")
   (invalidate-goal "Destroy Sentries")
)
(when
   (true)
   (send-message "#Command" "High" "New orders received")
   (validate-goal "Investigate Remaining Cargo")
   (unprotect-ship "Alpha 4")
)
```

### Percent destroyed / departed
```lisp
(when
   (percent-ships-destroyed 100 "Cain" "Abel")
   (send-message "#Command" "High" "Abel dead")
)
(when
   (percent-ships-departed 66
      "Kappa 4" "Kappa 5" "Kappa 6" "Kappa 9" "Kappa 10" "Kappa 11"
      "Kappa 1" "Kappa 2" "Kappa 3" "Theta 1" "Theta 2" "Theta 3"
   )
   (has-arrived-delay 0 "Mecross")
)
```

### SEXP parameter types quick reference
For detailed operator signatures, see `../FSO SEXPs/INDEX.md`.

| Type | Example |
|---|---|
| Entity name | `"Alpha 1"`, `"GTD Bastion"`, `"<any wingman>"` |
| Waypoint path name | `"Alpha Patrol"` |
| Waypoint point | `"Alpha Patrol:1"` |
| Jump Node name | `"Delta Serpentis Jump Node"` |
| Goal/Event name | Literal name from goals/events |
| Priority integer | `89`, `50`, `40` |
| Seconds integer | `0`, `5`, `30` |
| Subsystem name | `"engine"`, `"communication"`, `"turret01"` |
| Boolean | `( true )`, `( false )` |
| Percent integer | `100`, `66`, `25` |
| Weapon/Class name | `"Avenger"`, `"GTF Ulysses"` (for tech-unlock SEXPs) |

Additional notes:
- 0-delay frame-lag: `"...-true-delay"` and `"...-false-delay"` become true on the frame **after** the state changes due to mission log ordering. See `../FSO SEXPs/Event-Goals.txt`.
- Wing variants: many `ai-*` goals have wing-target variants (e.g., `ai-guard-wing`).
- AI Goals applicability: some goals are fighter/bomber-only; others are large-ship-only. See the spec for the large-ship list.
- Variadic arguments: many operators accept one or more entity names (ships/wings). Always verify the exact argument count and accepted types in the per-operator SEXP documentation before use.

## Weapons

### Primary Banks (lasers)
- Terran: ML-16 Laser, Disruptor, D-Advanced, Avenger, Flail, Prometheus, Banshee, Training
- Vasudan: Vasudan Light Laser
- Shivan: Shivan Light Laser, Shivan Heavy Laser, Shivan Mega Laser, Shivan Uber Laser

### Secondary Banks (missiles)
- Terran: MX-50, Fury, Interceptor, Hornet, Phoenix V, D-Missile, Synaptic, Stiletto, Tsunami, Harbinger
- Vasudan: Enemy MX-50, Fang, Barracuda
- Shivan: MX-50#Shivan, Fury#Shivan, Interceptor#Shivan, Hornet#Shivan, Phoenix V#Shivan, D-Missile#Shivan, Synaptic#Shivan, Stiletto#Shivan, Tsunami#Shivan, Harbinger#Shivan, Unknown Bomb, Unknown Megabomb

CAUTION: Use the weapon name token in full, **without** lore prefixes (write `ML-16 Laser`, not `GTW ML-16 Laser`).

## Background Bitmaps
- Nebulae (the letter 'd' denotes "dark" variants). Grouped by colors:
  - Red: dneb01, dneb02, dneb03, dneb12, dneb18, neb01, neb02, neb03, neb12, neb18
  - Green: dneb04, dneb05, dneb06, neb04, neb05, neb06
  - Grey: dneb06, dneb13, neb06, neb13
  - Blue: dneb07, dneb08, dneb09, dneb10, dneb11, dneb14, dneb15, dneb16, dneb17, neb07, neb08, neb09, neb10, neb11, neb14, neb15, neb16, neb17

- Planets:
Capella1, Capella1-1, Capella1-1b, Capella1b, Capella2, Capella2-1, Capella2-1b, Capella2b, Capella3, Capella3-1, Capella4, Capella4-1, planeta1, planetb, planetc, planetd, planete, planetf, planetg, planeth

- Suns:
SunAdharaA, SunAdharaB, SunAlbireoAa, SunAlbireoAb, SunAlbireoB, SunAldebaranA, SunAldebaranB, SunAlphaAquilae, SunAlphaCentauriA, SunAlphaCentauriB, SunAlphaCrucisAa, SunAlphaCrucisAb, SunAlphardA, SunAlphardB, SunAntaresB, SunBetaAquilaeA, SunBetaAquilaeBa, SunBetaAquilaeBb, SunBetaHydri, SunBetelgeuse, SunBlue, SunCapellaA, SunCapellaB, SunCapellaC, SunDeltaSerpentis, SunGammaDraconis, SunGold, SunGreen, SunMintakaB, SunMintakaCa, SunMintakaCb, SunMirfak, SunNaos, SunPhiEridaniA, SunPhiEridaniB, SunPolarisAa, SunPolarisAb, SunPolarisB, SunProcyonA, SunProcyonB, SunRed, SunSiriusA, SunSiriusB, SunSol, SunVega, SunViolet, SunWhite

## Music
Note: use the literals exactly as written here, including the initial "<number>: " string.

### Mission Music
None, 1: Genesis, 2: Exodus, 3: Leviticus, 4: Numbers, 5: Deuteronomy, 6: Joshua, 7: Revelation, FS1-1: Fortress, FS1-2: March, FS1-3: Chaser, FS1-4: Worlds Apart, FS1-5: Spook, FS1-6: Haunted, FS1-7: Marauder, FS1-8: Strike, FS1-9: Monolith, FS1-10: Darkside

### Briefing Music
None, Brief1, Brief2, Brief3, Brief4, Brief5, Brief6, Brief7, FS1-BRIEF1, FS1-BRIEF2, FS1-BRIEF3, FS1-BRIEF4, FS1-BRIEF5, FS1-BRIEF6, FS1-BRIEF7

## Ships
For example: GTF Ulysses, GTB Medusa, GTC Fenris, PVT Isis, SD Demon.
CAUTION: FSO expects the ship name token in full, including the prefix (write "GTC Fenris" instead of just "Fenris").
For a full list of ships, see ./spacecraft-classes.md.

## Subsystems
For example (GTF Ulysses): engines, communication, navigation, sensors, weapons.

CAUTION: exact subsystem names can differ among the ships ('engine'/'engines', 'communication'/'communications' etc.).
For exact per-ship subsystem names, see: ./Ship subsystems/<faction_name>-ships-subsystem-names.md.

## Dockpoints
For example (GTSC Faustus): port docking, starboard docking.
For canonical ship dockpoint names, see: ./ship-dockpoint-names.md.

## Briefing icon types
Authors must use a canonical `icon_type` string in `icons[*].icon_type`.

For `display_class` rules (conditionally required vs. must omit), see `../fsif/specification.md` — the `briefing.stages[*].icons[*].display_class` field entry.

Allowed canonical icon type strings:
- Fighter
- Fighter Wing
- Cargo
- Cargo Wing
- Science Cruiser
- Science Cruiser Wing
- Capital Ship
- Planet
- Asteroid Field
- Waypoint
- Support Ship
- Freighter (no cargo)
- Freighter (has cargo)
- Freighter Wing (no cargo)
- Freighter Wing (has cargo)
- Installation
- Bomber
- Bomber Wing
- Cruiser
- Cruiser Wing
- Unknown
- Unknown Wing
- Player Fighter
- Player Fighter Wing
- Player Bomber
- Player Bomber Wing
- Small Planet
- Transport Wing
- Transport
- Supercapital Ship
- Sentry Gun
- Jump Node

Note: If `icons[*].map_position` is omitted, it defaults to `[0, 0]`.

## Volumetric (full) nebula parameters
Background Color Patterns: nbackblue1, nbackblue2, nbackcyan, nbackgreen, nbackpurp1, nbackpurp2, nbackred, nblackblack, nbackyellow, nbackblue, nbackorange
Note: `nblackblack` is actually dark grey. A completely black background is achieved by omitting the pattern.
Cloud Sprites (Poofs): PoofGreen01, PoofGreen02, PoofRed01, PoofRed02, PoofPurp01, PoofPurp02
Note: FSO SEXP docs refer to Cloud Sprites as "nebula poofs".
Lightning Storm: none, s_standard, s_medium, s_active, s_emp
Note: Lightning Storm variants are ordered from least active to most active. `s_emp` messes with player's HUD.

## Asteroid and debris field object variants

Context: `environment.asteroid_field.object_variants`.
Asteroid and debris variant names are **mutually incompatible** — mixing them is an error.

**Asteroid field variants** (`object_type: "asteroid"`):
- Brown
- Blue
- Orange

**Debris field variants** (`object_type: "debris"`):
- Terran Debris 1 (small)
- Terran Debris 2 (medium)
- Terran Debris 3 (large)
- Vasudan Debris 1 (small)
- Vasudan Debris 2 (medium)
- Vasudan Debris 3 (large)
- Shivan Debris 1 (small)
- Shivan Debris 2 (medium)
- Shivan Debris 3 (large)

**End of reference**
