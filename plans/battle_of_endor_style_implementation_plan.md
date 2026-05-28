# Battle of the Vega Gate - FSIF Implementation Plan

## Approval status

User approved the revised larger plan with the nearby GTI Arcadia-class installation, GTI Aegis, its own fighter wings, and additional Shivan assets engaging the installation.

## Source material and references

- Canon universe source: `Freespace Bibles/FS_Universe_Bible_Condensed.txt`.
- NeuralFS overview: `README.md`, `Documentation/index.md`.
- FSIF schema and authoring rules: `Documentation/fsif/specification.md`, `Documentation/fsif/authoring-guide.md`.
- FSO canonical tokens: `Documentation/FSO and fs2 format/FSO_Tokens_Reference.md`.
- SEXP index and operator docs: `Documentation/FSO SEXPs/INDEX.md`, especially `Objectives.txt`, `Messages and Personas.txt`, `AI Goals.txt`, `AI Control.txt`, `Logical.txt`, and `Damage.txt`.
- Hardpoint reference: `Documentation/FSO and fs2 format/fighter_bomber_hardpoints.md`.
- ElevenLabs voice list: `Documentation/ElevenLabs TTS/voices.txt`.
- Converter docs: `FSIF_to_FS2_Converter/README.md`, `Documentation/fsif/converter/cli.md`.
- Demo mission reference: `missions/Demo_missions/general_demo.fsif`.

## Intended output path

- Mission FSIF: `missions/battle_of_endor_style.fsif`.
- Generated FS2 after validation: `missions/battle_of_endor_style.fs2`.
- No FCIF campaign file is planned; this is a standalone mission.
- No fiction viewer story file is planned; narrative setup will be handled through command briefing and mission briefing.

## Mission concept

- Title: `Battle of the Vega Gate`.
- Setting: late Great War, Vega system, near a contested jump node and a GTI Arcadia-class installation.
- Premise: a Terran fleet line anchored by the GTD Actium and supported by the GTI Aegis installation is attacked by a Shivan destroyer group. The mission aims for a `Battle of Endor` feel: multiple capital ships, fighter screens, bomber waves, cross-battle radio traffic, and competing defensive priorities.
- Player role: Alpha 1, assigned to the Actium fighter screen but retasked throughout the battle to intercept bombers and stabilize the GTI Aegis sector.
- Design stance: intentionally larger and busier than the conservative recommendation, accepting possible performance, target-clutter, and chaos tradeoffs.

## Affected FSIF schema sections

- `mission_info`: standalone single-player mission metadata.
- `environment`: Vega-style normal-space background with SunVega, several nebula bitmaps, and a planet backdrop. No full nebula and no subspace mission flag.
- `player_setup`: Alpha 1 start, player-usable Terran fighters/bombers, and expanded weapon pool.
- `entities`: ship templates, standalone capital ships, installation, fighter/bomber wings, waypoint or reference paths if required, reinforcement wing, and visible jump node.
- `mission_flow`: command briefing, briefing, debriefing, events, goals, and messages.
- `audio`: ElevenLabs TTS and mission/briefing music.

## Player setup and loadout impacts

- Player starts as `Alpha 1`, member of Friendly `Alpha` wing, satisfying FSIF player-start rules.
- Alpha wing: GTF Hercules heavy fighters.
- Friendly loadout-screen wings may include Beta and Gamma, with Beta as fighters and Gamma as bombers.
- Additional ship choices: GTF Ulysses and GTB Medusa.
- Weapon selection will use canonical Great War tokens and hardpoint-safe bank counts:
  - GTF Hercules: two primary banks, two secondary banks.
  - GTF Ulysses: two primary banks, one secondary bank.
  - GTB Medusa: one primary bank, three secondary banks.
- Planned extra weapons: Avenger, Prometheus, Banshee, Interceptor, Hornet, Phoenix V, Tsunami.
- Because this mission is standalone, FCIF starting-loadout unlocks are not needed.

## Entity list impacts

### Friendly Terran fleet

- `GTD Actium`: GTD Orion, Friendly, escort-listed, primary mission-critical flagship.
- `GTC Reliant`: GTC Leviathan, Friendly, escort-listed heavy cruiser.
- `GTC Valiant`: GTC Fenris, Friendly cruiser.
- `GTC Meridian`: GTC Fenris, Friendly cruiser reinforcement/flank ship.

### Friendly GTI installation sector

- `GTI Aegis`: GTI Arcadia, Friendly, escort-listed, primary mission-critical installation.
- `Zeta`: installation defense fighters, likely GTF Apollo or GTF Ulysses.
- `Eta`: station interceptor wing, likely GTF Valkyrie.

### Hostile Shivan main force

- `SD Ravana`: SD Demon, Hostile, escort-listed enemy flagship.
- `SC Malphas`: SC Lilith, Hostile, heavy cruiser.
- `SC Bane`: SC Cain, Hostile cruiser.
- `SC Obsidian`: SC Cain, Hostile flanker.

### Hostile Shivan station-assault force

- `SC Mandara`: SC Lilith or SC Cain, Hostile station-assault cruiser.
- `SC Rakshasa`: SC Cain, Hostile station-sector cruiser.
- `Kali`: Shivan bomber wing attacking GTI Aegis.
- `Asura`: Shivan fighter cover attacking station defense wings.
- Additional late chaos wave: `Deva` or `Bheema`, likely SF Manticore interceptors.

### Hostile Shivan bomber/fighter waves

- `Durga`: SB Nephilim bomber waves attacking GTD Actium.
- `Brahma`: SF Basilisk fighter waves.
- `Vishnu`: SF Manticore interceptor waves.
- Optional elite wing can be added if validation remains clean; otherwise use safer Basilisk/Manticore/Scorpion classes.

### Waypoints, jump nodes, and reinforcements

- `Vega Jump Node`: visible jump node near the far side of the battle.
- Hidden waypoint/reference paths may be added only if needed for distance checks or large-ship conservative movement.
- Reinforcement wing: `Delta`, likely GTF Valkyrie interceptors, callable or timed. If authored as reinforcement, omit arrival cue so the wing remains callable.

## Briefing, command briefing, debriefing, and message impacts

### Command briefing

- Establish Vega gate crisis.
- Explain GTD Actium as the Terran battle-line anchor.
- Explain GTI Aegis as the nearby Arcadia-class command/logistics installation committing its own fighter reserves.
- Warn of Shivan bomber waves and the possibility of the station sector being hit separately.

### Mission briefing

- Stage 1: Show Terran line, Alpha/Beta/Gamma, GTD Actium, GTI Aegis, and Vega Jump Node.
- Stage 2: Show Shivan destroyer/cruiser line and expected bomber approach vectors.
- Stage 3: Show station-assault vector and GTI Aegis defense wings.
- Use valid briefing icon types and display classes for ship icons.
- Apply FSO text styling only in briefing/debriefing contexts, using friendly and hostile color spans.

### Debriefing

- Conditional stage if GTD Actium is destroyed.
- Conditional stage if GTI Aegis is destroyed.
- Success stage if both GTD Actium and GTI Aegis survive through battle end.
- Additional praise if the Shivan bomber force is destroyed.
- Bonus praise if SD Ravana is destroyed.

### Messages and TTS

- `audio.tts_provider`: `elevenlabs`.
- Use only voices from `Documentation/ElevenLabs TTS/voices.txt`.
- Planned voice assignments:
  - Command: Adam or Daniel.
  - Actium captain: Rachel or Lily.
  - Aegis control: Emily or Serena.
  - Wingman chatter: Josh, Callum, Bella, Elli.
- ElevenLabs style instructions must be simple comma-separated emotion tags.
- Keep in-mission messages ASCII-only and do not use text color tags in messages.

## Mission flow and SEXP strategy

### Objectives

- Primary: Protect GTD Actium.
- Primary: Protect GTI Aegis.
- Primary/secondary: Destroy or drive off the Shivan bomber wings attacking the capital line and installation.
- Secondary: Destroy the station-assault cruiser or reduce pressure on the installation.
- Bonus: Destroy SD Ravana if feasible.

### Planned operators

- Event triggers: `when`, `has-time-elapsed`.
- Dialogue: `send-message`, `send-message-list`.
- Objective state checks: `is-destroyed-delay`, `percent-ships-destroyed`, `has-arrived-delay`, `has-departed-delay`, `destroyed-or-departed-delay`.
- Damage-threshold chatter: `hits-left`.
- AI behavior: `ai-chase`, `ai-chase-any`, `ai-chase-wing`, `ai-guard`, `ai-waypoints-once`, plus `clear-goals` and `add-goal` for retasking if needed.

### SEXP authoring constraints

- Use block scalar style for every SEXP field.
- Do not put event-chaining checks in HUD directive formulas; directive events should use directly evaluable object/wing state checks.
- Keep `send-message-list` arguments in exact groups of four.
- Do not use invalid fighter-only AI goals on cruisers, destroyers, or the Arcadia installation.
- Avoid checking player destruction/departure in goal/event logic.

## Spatial and gameplay plan

- Keep main engagement inside roughly 15-18 km to avoid long travel times.
- Put Terran and Shivan capital lines several kilometers apart, close enough for turret engagement but far enough to reduce collision risk.
- Offset GTI Aegis several kilometers from the main line, creating a second fight space within reachable distance.
- Stage some Shivan station-assault arrivals after the initial fleet battle begins.
- Use escort flags only for the most important ships: GTD Actium, GTI Aegis, SD Ravana, and possibly key assault cruisers.

## FCIF campaign/loadout impacts

- None. This is a standalone FSIF mission.
- No campaign advance conditions are required.
- No FCIF file will be created or edited.

## Known risks and mitigation

- Performance/clutter risk: accepted by user. Mitigation: staged arrivals and bounded but busy entity counts.
- AI chaos risk: use simple orders and clear player directives.
- Collision risk: generous capital spacing, no shared large-ship waypoint path, limited large-ship movement.
- Objective overload risk: make Actium and Aegis defense central, while total enemy fleet destruction remains secondary/bonus.
- Token risk: use canonical ship/weapon/music/background tokens only.
- SEXP risk: restrict to common documented operators and validate through the converter.
- TTS risk: use only ElevenLabs voices and simple style tags.
- Converter risk: run the FSIF converter and fix all errors/warnings before final completion.

## Final validation plan

1. Create `missions/battle_of_endor_style.fsif` according to this plan.
2. Run `python FSIF_to_FS2_Converter/fsif_to_fs2.py "missions/battle_of_endor_style.fsif"`.
3. Fix all converter errors and warnings unless there is a strong reason not to.
4. Perform a final manual review for references, SEXP syntax, names under 30 characters, hardpoint counts, and player-start validity.

## Addendum: orientation improvement pass

After playtesting, the mission was revised to avoid every ship spawning with the default identity orientation. Standalone capital ships and the GTI Aegis installation now author explicit 9-float `orientation` matrices so Terran and Shivan capital ships face each other or their primary targets. Fighter and bomber wings are oriented by an opening `SetInitialFacing` event using `set-object-facing-object`; this avoids invalid template-level `orientation` fields while still giving friendly wings, Shivan attack wings, and station-defense wings initial facing directions that better match their tactical sectors.
