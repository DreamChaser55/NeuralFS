# FSO Tokens Reference (Tokens, Flags, and Canonical Literals)

## Scope
- Single source of truth for valid FSO tokens: flags, enumerations, literals, and canonical spellings.

## Guidance on token usage
- Exact token spelling is required when authoring FSIF missions. All tokens (enums, flags, AI class names, goal types, SEXP operator names, wildcard literals like "<any friendly player>", music file names, background/sun/planet textures...) must be authored exactly as shown. Unknown/misspelled tokens will cause errors.
- Always use canonical tokens as listed here and in the FSIF spec. Do not vary case.
- Do / Don’t (examples):
  - Do: "<any friendly player>"   Don’t: "<any player>", "<any Friendly Player>"
  - Do: "High"                    Don’t: "high"
  - Do: "ai-guard-wing"           Don’t: "ai_guard_wing"
- Token length limit: Custom tokens used inside SEXPs (like ship, message or event names) must be shorter than 30 characters to avoid errors.
- Strings/literals: Treat special selectors like "<any wingman>" and "<any friendly player>" as ordinary quoted strings in SEXPs; do not escape the angle brackets specially.

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
FSO engine theoretically supports a "Neutral" IFF team, but its implementation is broken — it essentially acts as a second Hostile faction and attacks the player. Because this behavior is misleading and redundant, FSIF does not support the "Neutral" team. Use "Friendly", "Hostile" or "Unknown" for all ships, objects or briefing icons.

Context: `team`.

### Arrival/Departure Locations

#### Arrival and Departure
- Hyperspace
- Docking Bay
  - must have a ship as docking bay anchor (`arrival_anchor` / `departure_anchor`)
  - `arrival_distance` is forced to `0` with Docking Bay and should be omitted.

Context:  `arrival_location`, `departure_location`.

#### Arrival-only
- Near Ship
- In front of ship
- In back of ship
- Above ship
- Below ship
- To left of ship
- To right of ship

Context: `arrival_location`.
Requires `arrival_distance` and a ship `arrival_anchor`.

### Message priorities
- "Low"
- "Normal"
- "High"

Context: send-message, send-random-message, send-message-list.

Examples:
    send-message "#Command" "Low" "Msg"
    send-message "#Command" "Normal" "Msg"
    send-message "#Command" "High" "Msg"

### AI Class values (worst→best)
- Coward
- Lieutenant
- Captain
- Major
- Colonel
- General

Example: +AI Class: Captain

### Goal types
- Primary
- Secondary
- Bonus

Example: $Type: Primary

## Wildcards and special literals

Literals:
- "<any wingman>"
- "<any friendly player>"
- "<any friendly>"
- "<any hostile>"
- "<any unknown>"
- "#Command"

Valid contexts:
- send-message sender
- general SEXP entity lists
- arrival anchor

Examples:
- (send-message "<any wingman>" "High" "Ambush_warning")
- (send-message "#Command" "High" "Tactical_update")
- $Arrival Anchor: <any friendly player>
- $Arrival Anchor: <any friendly>
- $Arrival Anchor: <any hostile>

## Flags catalog

This section lists a subset of canonical flags which is generally useful for mission authors. A complete catalog of flags, including the less useful, debug or special ones is available in the converter documentation.

### Mission flags (`mission_info.flags`)
These tokens specify various mission properties and behaviors.

*   `subspace` — Mission takes place in subspace
*   `no_promotion` — Cannot get promoted or badges in this mission
*   `fullneb` — Mission is a full nebula mission (flag set when environment.nebula.enabled is true)
*   `no_builtin_msgs` — Disables builtin msgs
*   `no_traitor` — Player cannot become a traitor
*   `toggle_ship_trails` — Toggles ship trails (off in nebula, on outside nebula)
*   `support_repairs_hull` — Toggles support ship repair of ship hulls
*   `beam_free_all_by_default` — Beam-free-all by default
*   `no_briefing` — No briefing, jump right into mission
*   `toggle_debriefing` — Turn off debriefing.
*   `red_alert` — A red-alert mission (player damage and loadout persists from the previous mission)
*   `scramble` — A scramble mission (no loadout customization)
*   `no_builtin_command` — Turns off Command messages without turning off pilots
*   `all_attack` — All teams at war
*   `toggle_showing_goals` — Show mission goals for training missions, hide otherwise
*   `end_to_mainhall` — Return to the mainhall after debriefing
*   `preload_subspace` — Preload the subspace tunnel for both the sexp and specs checkbox (for scripts)

### Ship flags (`entities.ships[*].flags`)
These tokens specify various ship properties and behaviors.

*   `cargo-known` — Ship's cargo is revealed to all friendly ships
*   `ignore-count` — Ignore this ship when counting ship types for goals
*   `protect-ship` — No AI-controlled ship will attack this ship
*   `reinforcement` — This ship is a reinforcement ship (Note: explicit usage of this flag is deprecated. Reinforcement ships are authored only via `reinforcement_ships` list)
*   `no-shields` — Disables shields for this ship
*   `escort` — This ship is an escorted ship (shown in the HUD escort overview table)
*   `no-arrival-music` — Don't play arrival music when ship arrives
*   `invulnerable` — Ship cannot be damaged
*   `hidden-from-sensors` — Ship doesn't show up on sensors, blinks in/out on radar
*   `scannable` — Ship is "scannable". Play scan effect and report as "Scanned" or "not scanned". If your mission scenario demands scanning the ship, you must set this flag
*   `kamikaze` — AI behavior: kamikaze
*   `no-dynamic` — AI behavior: no dynamic goals
*   `red-alert-carry` — Ship status should be stored/restored if red alert mission
*   `guardian` — A guardianed ship cannot die, but it can take damage and have subsystems destroyed. This makes it much less obvious (compared to `invulnerable`) that a mission designer is keeping a ship alive artificially. At 1% hull a guardianed ship will take no further damage to the hull, but subsystems may still be killed.
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
*   `aspect-immune` — Ship cannot be locked onto by aspect seeking weapons (secondaries like Interceptor, Hornet)
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
- `escort_priority` (Integer; used with `escort`)
- `kamikaze_damage` (Integer; used with `kamikaze`)
- `orders_accepted` (List of strings)

### Wing flags (`entities.wings[*].flags`)

*   `reinforcement` — Is this wing a reinforcement wing (Note: explicit usage of this flag is deprecated. Reinforcement wings are authored only via `reinforcement_wings` list)
*   `no-arrival-music` — Don't play arrival music when wing arrives
*   `no-arrival-message` — Don't play any arrival message
*   `ignore-count` — Ignore all ships in this wing for goal counting purposes
*   `no-arrival-warp` — Don't play warp effect for any arriving ships in this wing
*   `no-departure-warp` — Don't play warp effect for any departing ships in this wing
*   `no-dynamic` — Members of this wing relentlessly pursue their AI goals
*   `departure-ordered` — Departure of this wing was ordered by player
*   `no-first-wave-message` — Don't play arrival message for the first wave
*   `waypoints-no-formation` — Wing will not try to form up when running a waypoint together

## Contextual parameters (FSIF fields)

### Arrival and departure (ships and wings)
These fields are authored in `entities.ships` and `entities.wings`.

- `arrival_location`: Location token.
  - Values: "Hyperspace", "Docking Bay" (requires `arrival_anchor`), "Near Ship", "In front of ship", "In back of ship", "Above ship", "Below ship", "To left of ship", "To right of ship".
  - Directional locations (all except Hyperspace) require `arrival_distance` and `arrival_anchor`.
- `arrival_distance`: Distance in meters (Integer). Should be 0 for Docking Bay.
- `arrival_anchor`: Anchor entity literal or wildcard.
  - Examples: "MyShip", "MyWing", "<any friendly player>", "Docking bay 1" (if docking).
- `arrival_delay`: Integer delay before arrival (seconds).
- `arrival_cue`: SEXP controlling arrival (Boolean expression).
- `departure_location`: Location token.
  - Values: "Hyperspace", "Docking Bay".
- `departure_anchor`: Anchor for Docking Bay departure. Must be a docking bay.
- `departure_cue`: SEXP controlling departure (Boolean expression).

### Waypoints and Jump Nodes

#### Waypoints (`entities.waypoints`)
Waypoints are authored as a mapping of path names to a list of [x,y,z] coordinates. They are invisible to the player and used only to guide AI-controlled ships.
- Path Name (Map Key): Literal string (e.g. "Alpha Patrol").
- Point reference in SEXPs: "PathName:N" (1-based index).
  - Example: "Alpha Patrol:1" refers to the first point in the path "Alpha Patrol".

#### Jump Nodes (`entities.jump_nodes`)
Jump nodes are authored as a list of objects. They are visible to the player.
- `name`: Node display name (e.g. "Delta Serpentis Jump Node").
- `position`: [x, y, z] coordinates.

### Messages (`mission_flow.messages`)
Messages are authored as a list of objects.
- `name`: Message identifier (referenced by `send-message` SEXP).
- `message`: Localized text payload (displayed to player).
- `voice_name`: Google TTS voice identifier (e.g. "Wavenet-A").

Note: Message `name` is referenced by `send-message` SEXP; sender strings in SEXPs may be ships, wildcards like "<any wingman>", or "#Command".

### SEXP Operators quick-reference (token-relevant subset only)
- For full SEXP documentation by category, see "/Documentation/FSO SEXPs/INDEX.md".

Selected SEXP tokens/literals:
- `has-arrived-delay`
  - Boolean operator. Becomes true `<delay>` seconds after the specified ship(s) or wing(s) have arrived.
  - Parameters: `Delay` (seconds), `Ship/Wing` (one or more).
- `depart-node-delay`
  - Boolean operator. Becomes true `<delay>` seconds after specified ships depart within the radius of a specific jump node.
  - Parameters: `Delay` (seconds), `Jump Node Name`, `Ship` (one or more).
- `mission-time`
  - Time operator. Returns the current mission time in seconds.
  - Parameters: None.
- `has-time-elapsed`
  - Boolean operator. Becomes true when the mission time is greater than or equal to the specified time.
  - Parameters: `Time` (seconds).
- `is-iff`
  - Boolean operator. True if all specified ship(s) or wing(s) are of the specified team.
  - Parameters: `Team` ("Friendly", "Hostile", "Unknown"), `Ship/Wing` (one or more).
- `distance`
  - Numeric operator. Returns the distance between two objects (ships, wings, or waypoints).
  - Parameters: `Object 1`, `Object 2`.
- `send-message`
  - Action operator. Sends a message to the player from a specific sender.
  - Parameters: `Sender` (Ship name, "#Command", "<any wingman>"), `Priority` ("High", "Normal", "Low"), `Message Name`.
- `send-message-list`
  - Action operator. Sends a sequence of messages with delays (accumulated).
  - Parameters: Repeating groups of 4: `Sender`, `Priority`, `Message Name`, `Delay` (milliseconds).
- `when`
  - Conditional operator. Performs a list of actions when a boolean condition becomes true. Standard top-level operator for Events.
  - Parameters: `Condition` (Boolean expression), `Action` (one or more).
- `goals`
  - Container operator. Used within ship/wing definitions (e.g., `ai_goals`) to wrap a list of initial AI goals.
  - Parameters: List of AI goal SEXPs (e.g., `ai-chase`, `ai-guard`).
- `ai-chase-any`
  - AI Goal operator. Causes the ship to chase and attack any ship on the opposite team.
  - Parameters: `Priority` (0-89 for AI, 90+ for player orders), `Afterburn` (optional boolean).

Additional important notes:
- 0-delay frame-lag: For a delay of 0 (evaluated in-mission), event/goal "...-true-delay" and "...-false-delay" become true on the frame after the underlying state changes, due to mission log update ordering. See /Documentation/FSO SEXPs/Event-Goals.txt.
- Wing variants: Many ai-* goals have wing-target variants (e.g., ai-guard-wing).
- AI Goals applicability: Some AI Goals are only valid for fighters/bombers, others are only valid for bigger ships.
- Variadic arguments: Many operators accept one-or-more entities (ships/wings). Both singular and list forms are valid.
- Debriefing: debriefing condition uses SEXPs.

### Parameter types observed in SEXPs

Entity name
    Ship/wing literal (e.g., "Alpha 1", "GTD Bastion", "Krishna", "Omega") or wildcards ("<any friendly>", "<any hostile>", "<any wingman>")
Waypoint path name
    Literal (e.g., "Waypoint path 3")
Waypoint point literal
    "Waypoint path N:M"
Jump Node Name
    Literal (e.g., "Delta Serpentis Jump Node")
Goal Name
    Literal name from goals or event names
Event Name
    Literal name assigned to events
Priority Integer
    Integer (e.g., 89, 50, 40)
Seconds Integer
    Integer seconds (0+)
Percent Integer
    Integer percent
Weapon/Class Name
    For tech unlock SEXPs
Subsystem Name
    "engine", "communication", "navigation", "weapons", "sensors", turret01, turret02, etc.
    See per-ship canonical lists for exact names (including turrets): ./Ship subsystems/terran-ships-subsystem-names.md, ./Ship subsystems/vasudan-ships-subsystem-names.md, ./Ship subsystems/shivan-ships-subsystem-names.md.
Boolean
	'(true)' or '(false)'

Note: any literal names in SEXPs must be shorter than 30 characters.

### Example patterns

#### Arrival anchored to any friendly player (wing)
(In `entities.wings`)
name: Arjuna
arrival_location: In front of ship
arrival_distance: 1500
arrival_anchor: <any friendly player>
arrival_cue: ( is-event-true-delay "Cargo is blowin' up" 12 )

#### Messaging from wildcard wingman
(when
   (has-arrived-delay 4 "Tantalus")
   (send-message "<any wingman>" "High" "It looks like an ambush")
)

#### Unlock tech and allow weapon
(when
   (true)
   (allow-weapon "Avenger")
   (tech-add-weapons "Avenger")
   (tech-add-ships "SF Manticore" "SF Scorpion" "SB Shaitan" "SC 5" "SAC 2" "SC Cain" "SSG Trident")
)

#### Protect/unprotect runtime
(when
   (has-arrived-delay 6 "Arjuna")
   (send-message "#Command" "High" "Trap alert!")
   (protect-ship "Alpha 1")
   (invalidate-goal "Destroy Sentries")
)

(when
   (true)
   (send-message "#Command" "High" "new orders 3")
   (validate-goal "Investigate Remaining Cargo")
   (unprotect-ship "Alpha 4")
)

#### Percent destroyed and departed
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

### Weapons
- Primary Banks (lasers):
  - Terran: ML-16 Laser, Disruptor, D-Advanced, Avenger, Flail, Prometheus, Banshee, Training
  - Vasudan: Vasudan Light Laser
  - Shivan: Shivan Light Laser, Shivan Heavy Laser, Shivan Mega Laser, Shivan Uber Laser

- Secondary Banks (missiles):
  - Terran: MX-50, Fury, Interceptor, Hornet, Phoenix V, D-Missile, Synaptic, Stiletto, Tsunami, Harbinger
  - Vasudan: Enemy MX-50, Fang, Barracuda
  - Shivan: MX-50#Shivan, Fury#Shivan, Interceptor#Shivan, Hornet#Shivan, Phoenix V#Shivan, D-Missile#Shivan, Synaptic#Shivan, Stiletto#Shivan, Tsunami#Shivan, Harbinger#Shivan, Unknown Bomb, Unknown Megabomb

### Background Bitmaps
- Nebulae (the letter 'd' denotes “dark” variants). Grouped by colors:
  - Red: dneb01, dneb02, dneb03, dneb12, dneb18, neb01, neb02, neb03, neb12, neb18
  - Green: dneb04, dneb05, dneb06, neb04, neb05, neb06
  - Grey: dneb06, dneb13, neb06, neb13
  - Blue: dneb07, dneb08, dneb09, dneb10, dneb11, dneb14, dneb15, dneb16, dneb17, neb07, neb08, neb09, neb10, neb11, neb14, neb15, neb16, neb17

- Planets:
Capella1, Capella1-1, Capella1-1b, Capella1b, Capella2, Capella2-1, Capella2-1b, Capella2b, Capella3, Capella3-1, Capella4, Capella4-1, planeta1, planetb, planetc, planetd, planete, planetf, planetg, planeth

- Suns:
SunAdharaA, SunAdharaB, SunAlbireoAa, SunAlbireoAb, SunAlbireoB, SunAldebaranA, SunAldebaranB, SunAlphaAquilae, SunAlphaCentauriA, SunAlphaCentauriB, SunAlphaCrucisAa, SunAlphaCrucisAb, SunAlphardA, SunAlphardB, SunAntaresB, SunBetaAquilaeA, SunBetaAquilaeBa, SunBetaAquilaeBb, SunBetaHydri, SunBetelgeuse, SunBlue, SunCapellaA, SunCapellaB, SunCapellaC, SunDeltaSerpentis, SunGammaDraconis, SunGold, SunGreen, SunMintakaB, SunMintakaCa, SunMintakaCb, SunMirfak, SunNaos, SunPhiEridaniA, SunPhiEridaniB, SunPolarisAa, SunPolarisAb, SunPolarisB, SunProcyonA, SunProcyonB, SunRed, SunSiriusA, SunSiriusB, SunSol, SunVega, SunViolet, SunWhite

### Music
- Note: use the literals exactly as written here, including the initial "<number>: " string

#### Mission Music:
None
1: Genesis
2: Exodus
3: Leviticus
4: Numbers
5: Deuteronomy
6: Joshua
7: Revelation
FS1-1: Fortress
FS1-2: March
FS1-3: Chaser
FS1-4: Worlds Apart
FS1-5: Spook
FS1-6: Haunted
FS1-7: Marauder
FS1-8: Strike
FS1-9: Monolith
FS1-10: Darkside

#### Briefing Music:
None
Brief1
Brief2
Brief3
Brief4
Brief5
Brief6
Brief7
FS1-BRIEF1
FS1-BRIEF2
FS1-BRIEF3
FS1-BRIEF4
FS1-BRIEF5
FS1-BRIEF6
FS1-BRIEF7

### Ships
For example: GTF Ulysses, GTB Medusa, GTC Fenris, PVT Isis, SD Demon.
CAUTION: FSO expects the ship name token in full, including the prefix (write "GTC Fenris" instead of just "Fenris").
For a full list of ships, see ./spacecraft-classes.md.

### Subsystems
For example (GTF Ulysses): engines, communication, navigation, sensors, weapons.

CAUTION: exact subsystem names can differ among the ships ('engine'/'engines', 'communication'/'communications' etc.).
For exact per-ship subsystem names, see: ./Ship subsystems/<faction_name>-ships-subsystem-names.md.

### Dockpoints
For example (GTSC Faustus): port docking, starboard docking.

For canonical ship dockpoint names, see: ./ship-dockpoint-names.md.

### Briefing icon types
- Authors must use a canonical icon string in icons[*].type.

**Icon Fields:**
- **Type**: Must be a canonical string from the allowed list below (e.g., "Fighter", "Jump Node"). Controls the icon's visual silhouette.
- **Class**: Optional (defaults to "Terran NavBuoy"). The displayed ship class text and picture when the icon is clicked in-game.
  - **Validation:** If specified, must be a valid ship class from `spacecraft-classes.md` (strictly enforced)
  - **Recommendation:** Omit for non-ship icons (Waypoints, Jump Nodes, Planets, Asteroid Fields) to use the safe default
- **Team**: Must be "Friendly", "Hostile" or "Unknown"

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

Note: If icons[*].pos is omitted, it defaults to 0.0, 0.0, 0.0.

### Volumetric (full) nebula parameters
Pattern: nbackblue1, nbackblue2, nbackcyan, nbackgreen, nbackpurp1, nbackpurp2, nbackred, nblackblack, nbackyellow, nbackblue, nbackorange
Poofs: PoofGreen01, PoofGreen02, PoofRed01, PoofRed02, PoofPurp01, PoofPurp02
Lighting Storm: none, s_standard, s_medium, s_active, s_emp

**End of reference**
