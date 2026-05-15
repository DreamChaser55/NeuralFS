# Implementation Plan for Mission_1_2.fsif Fixes

## Source Material
- `Vega_Requiem/Detailed_Mission_Design_Documents/Act_1/Mission_1_2.txt`
- `Vega_Requiem/Campaign_Bible.txt`

## Current FSIF File
- `Vega_Requiem/fsif/Mission_1_2.fsif`

## Requested Changes & Findings
The validation of the original `Mission_1_2.fsif` succeeded, but produced warnings about missing text styling tags and missing HUD directives for some goals. 
Upon closer inspection against the MDD, we also noticed that the `GTF Valkyrie` is missing its second secondary weapon bank (the `Fury` missiles).
The standalone Epsilon ships warned by the validator (Epsilon 1 to 4) are correctly implemented as standalone ships (to allow staggered departures) because the `GTI Arcadia` class station only has two dockpoints, making it impossible to use the FSO `dock` system for all 4 transports. They are simulated as docked via proximity and `ai-play-dead-persistent` orders.

## Plan

1. **Fix Player Loadout (Secondary Weapons)**:
   - Target section: `entities.ship_templates.valkyrie`
   - Change `secondary: ["MX-50"]` to `secondary: ["MX-50", "Fury"]` to match the MDD requirements.

2. **Add Missing HUD Directives**:
   - Target section: `mission_flow.events`
   - Add two new events to track the "Stentor Survives" and "Deploy Sentry Guns" secondary goals on the player's HUD.
   - `StentorDirective` event using `( is-destroyed-delay 0 "GTC Stentor" )` and `hud_directive_text: "Protect GTC Stentor"`.
   - `ChronosDirective` event using `( has-departed-delay 0 "GTFr Chronos 1" )` and `hud_directive_text: "Escort GTFr Chronos 1"`.

3. **Add Text Styling Tags**:
   - Target section: `mission_flow.briefing` and `mission_flow.debriefing`
   - Apply color tags to important entities in the briefing texts, as requested in the FSIF Converter warnings and the FSIF Authoring Guide.
   - Example tag usage: `$f{ GTI Vega Prime $}`, `$f{ GTC Stentor $}`, `$f{ Epsilon transports $}`, `$h Arjuna`, `$h SC Malgor`.

## Execution
I will perform exact edits to the `.fsif` file to implement these changes, then re-run the FSIF converter to ensure it validates perfectly without warnings.