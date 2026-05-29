# nebula_demo.fsif Orientation Fix Implementation Plan

## Source material and existing file paths
- Universe and format references consulted:
  - `Freespace Bibles/FS_Universe_Bible_Condensed.txt`
  - `Documentation/fsif/specification.md`
  - `Documentation/fsif/authoring-guide.md`
  - `Documentation/FSO and fs2 format/FSO_Tokens_Reference.md`
  - `Documentation/FSO SEXPs/INDEX.md`
  - `FSIF_to_FS2_Converter/README.md`
  - `Documentation/fsif/converter/cli.md`
- Existing mission file to edit: `missions/Demo_missions/nebula_demo.fsif`
- Reference demo mission: `missions/Demo_missions/general_demo.fsif`

## Intended output path
- Updated mission file: `missions/Demo_missions/nebula_demo.fsif`
- This implementation plan: `missions/Demo_missions/plans/nebula_demo_implementation_plan.md`

## Requested changes and affected schema sections
- The requested issue is that `nebula_demo.fsif` does not follow the FSIF Authoring Guide advice about deliberate initial ship and wing orientations.
- Affected FSIF schema sections:
  - `entities.ships[*].orientation`
  - `entities.wings[*].orientation`
  - Optionally `audio.tts_provider`, because the mission already has voiced lines but does not explicitly specify the provider.

## Relevant findings from the existing FSIF
- `Alpha` starts at `[0.0, 0.0, 0.0]` and lacks an explicit orientation. Its implicit identity orientation points toward world `+Z`, which happens to face the `Nav Buoy`, but only accidentally.
- `Beta` starts at `[-500.0, 0.0, 500.0]` and lacks an explicit orientation. Its implicit identity orientation does not clearly face the patrol reference or combat area.
- `Cancer` starts at `[2000.0, 0.0, 2000.0]` and lacks an explicit orientation, causing the hostile fighter wing to point away from the player-area ambush vector.
- `SC Dakini` lacks an explicit orientation. As the ambush cruiser, it should face the player or player wing rather than use the default world `+Z` orientation.
- `Nav Buoy` lacks an explicit orientation, but it is a static navigation object and is low priority for this fix.
- `audio.tts_provider` is missing despite multiple voiced lines.

## Player setup and loadout impacts
- No changes to `player_setup.start_ship`.
- No changes to player-usable ship classes, weapon banks, `additional_ship_choices`, or `additional_weapons`.
- No campaign-loadout implications because this is a standalone demo mission edit.

## Entity list impacts
- Standalone ships:
  - Add `orientation: "Alpha 1"` to `SC Dakini` so the ambush cruiser faces the player start ship.
  - Leave `Nav Buoy` unchanged unless later visual review shows a need to orient the buoy model.
- Wings:
  - Add `orientation: "Nav Buoy"` to `Alpha` so the player wing deliberately faces the patrol reference.
  - Add `orientation: "Alpha"` to `Cancer` so hostile fighters face the player wing as they arrive for the ambush.
  - Add `orientation: "Nav Buoy"` to `Beta` so reinforcement fighters face the patrol/action area.
- No changes to waypoints, jump nodes, reinforcement definitions, arrival cues, or docking.

## Briefing, command briefing, debriefing, and message impacts
- No briefing text changes are required for orientation.
- No command briefing, debriefing, or message text changes are required.
- No message or briefing voice changes are required.
- Add `tts_provider: "google"` under `audio` to make the existing Google-style voice names explicit and compliant with the authoring guide.

## Mission flow and SEXP strategy
- No mission event, goal, or SEXP flow changes are required.
- The fix relies on the FSIF target-name `orientation` form, not runtime SEXPs.
- Relevant SEXP documentation remains unchanged; no new operators are introduced.
- If target-name orientation proves unsuitable for a directionally arriving ship, replace only `SC Dakini` with a hand-authored yaw-only orientation matrix using the Authoring Guide formula.

## FCIF campaign/loadout/advance-condition impacts
- None. This mission is in `missions/Demo_missions/`, not a campaign `fsif/` folder.
- No `.fcif` files reference this mission for campaign progression.

## Known risks and mitigation
- Risk: target-name `orientation` for `SC Dakini` may be resolved from authored static positions rather than the final directional-arrival placement. Mitigation: run the FSIF converter and inspect for errors/warnings; if necessary, replace with a safe yaw-only matrix.
- Risk: target-name orientation references must resolve exactly. Mitigation: use existing object names: `Alpha 1`, `Alpha`, and `Nav Buoy`.
- Risk: the demo mission may intentionally omit `audio.tts_provider` for brevity. Mitigation: set it explicitly to `google`, matching the voice naming pattern used in the demo mission set.
- Risk: adding orientation to reinforcement `Beta` affects its visual spawn facing but not mission balance. Mitigation: no AI orders are changed.
