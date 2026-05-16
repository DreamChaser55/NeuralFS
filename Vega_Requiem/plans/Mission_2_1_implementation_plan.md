# Implementation Plan: Mission 2-1

## 1. Fix Briefing Icon Overlaps
- The FSIF converter reported warnings about briefing icons in Stage 1 being too close together (Amadeus, Rescue, Theta 3, Aldrin Wing).
- Update the `map_position` of these icons in `briefing.stages[0]` to space them out vertically (z-axis) by at least 300 units each.

## 2. Apply Text Styling Tags
- Go through the `command_briefing`, `briefing`, and `debriefing` sections.
- Apply FSO color tags to highlight ships, wings, and locations, according to the Text Styling Guide:
  - Friendly entities (Amadeus, Stentor, Aldrin One/Two/Three, Rescue, Theta Three, Alpha wing): `$f{ ... $}`
  - Hostile entities (Ahriman, Shaitans, Scorpions, bombers, fighters, Indra, Kali, Deva, Genma): `$h{ ... $}`
  - Locations (Nav Alpha, Nav Bravo, Capella, Deneb, Antares): `$y{ ... $}`
  - Important warnings: `$r{ ... $}`

## 3. Add Missing Goals from MDD
- Add Secondary Goal: "Surgical Strike" (Disable SC Ahriman's weapons subsystem).
  - Formula: `( is-subsystem-destroyed-delay "SC Ahriman" "weapons" 0 )`
- Add Bonus Goal: "Flawless Escort" (All 5 convoy ships survive).
  - Formula: `( and ( < ( distance "GTD Amadeus" "Nav Bravo" ) 2500 ) ( not ( percent-ships-destroyed 20 "GTFr Aldrin 1" "GTFr Aldrin 2" "GTFr Aldrin 3" "GTT Rescue" "Theta 3" ) ) )`
- Add Bonus Goal: "Ahriman Damaged" (SC Ahriman hull reduced below 50%).
  - Formula: `( < ( hits-left "SC Ahriman" ) 50 )`

## 4. Run FSIF Converter
- Run the FSIF to FS2 converter on `Vega_Requiem/fsif/Mission_2_1.fsif` to verify that all warnings are resolved and SEXP validation still passes.