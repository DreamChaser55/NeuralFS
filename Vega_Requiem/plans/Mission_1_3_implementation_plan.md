# Mission 1-3 Implementation Plan

## Discovered Issues
1. **Background Nebulae**: The mission only has 2 background bitmaps, triggering a warning about the environment feeling sparse.
2. **Standalone Alpha Wing**: Alpha 1, 2, 3, and 4 are defined as standalone ships rather than a wing, triggering warnings about non-standard player starts. 
3. **Briefing Icon Proximity**: Icons in the briefing stages are placed too closely together, causing visual overlap.
4. **Missing Text Styling**: The mission and command briefings lack FSO text styling color tags (`$f`, `$h`, `$y`, etc.).
5. **HUD Directives**: The bonus goal lacks a corresponding event with `hud_directive_text`, triggering a recommendation warning.

## Fix Strategy
1. **Background Nebulae**: Add a 3rd nebula bitmap (`dneb03`) to the `background_bitmaps` array.
2. **Standalone Alpha Wing**: Intentionally ignore the standalone ship warnings. The design document explicitly dictates an asymmetric loadout for Alpha wing: Alpha 1 must start with the field-test Avenger cannon, while Alpha 2-4 must start with standard ML-16 Lasers. FSIF does not support weapon overrides for individual wing members within a `wings` definition, so standalone ships are the only way to achieve this canonical loadout constraint.
3. **Briefing Icon Proximity**: Adjust the `map_position` vectors for the Capella Node and Pisces Wing icons to increase the separation distance.
4. **Missing Text Styling**: Add `$f{ ... $}` and `$h{ ... $}` tags to the briefing text strings for ships and wings.
5. **HUD Directives**: The missing directive is for a `Bonus` goal ("Full Evacuation"). Bonus goals typically do not have HUD directives in FreeSpace. This warning will be intentionally ignored.

## Execution
Apply the FSIF edits and re-run the FSIF Converter to ensure the remaining warnings are only the intentionally suppressed ones.
