# NeuralFS: FSIF & FCIF Documentation Home

This is the index for all available documentation on FSIF, FCIF, FSO, and the converters.

## Where to Begin
1. Read the FSIF specification for the exact schema.
2. Use the Authoring Guide for practical explanations, patterns, and pitfalls.
3. Consult the References for valid tokens and exact SEXP operator strings.
4. Study the demo missions for complete practical examples.
5. Learn to use the FSIF Converter CLI in `cli.md`.
6. FSIF Converter emission details are consolidated under Converter Implementation Details.
7. Read the FCIF specification for campaign file authoring.
8. Learn to use the FCIF Converter CLI.

Main README file: ../README.md

## FSIF Core Docs
- FSIF Specification (normative): ./fsif/specification.md
  - Canonical schema: fields, required/optional, defaults, constraints
- Authoring Guide (practical): ./fsif/authoring-guide.md
  - Minimal skeletons, common patterns, do/don't, pitfalls
  - Curated examples
- Migration Guide: ./fsif/migration-guide.md
  - FSIF 1.0 is the initial public release; no migration steps required

## FSIF Converter Docs
- README.md: ../FSIF_to_FS2_Converter/README.md
- Converter Implementation Details: ./fsif/converter/implementation_details.md
  - FS2 emission mapping, normalization, warnings, FSO engine limits
  - Validation messages catalog
- Converter CLI: ./fsif/converter/cli.md
  - Installation, invocation, I/O behavior, and examples

## FCIF Core Docs
- FCIF Specification (normative): ./fcif/specification.md
  - Campaign file schema: fields, required/optional, constraints, advance conditions

## FCIF Converter Docs
- README.md: ../FCIF_to_FC2_Converter/README.md
- Converter Implementation Details: ./fcif/converter/implementation_details.md
  - FC2 emission mapping, SEXP logic generation, version handling
- Converter CLI: ./fcif/converter/cli.md
  - Installation, invocation, I/O behavior, and examples

## Fiction Viewer Validator Docs
- README.md: ../Fiction_Viewer_Validator/README.md

## Parsers and Generators Docs
- parsers_and_generators.md: ../common/parsers_and_generators/parsers_and_generators.md

## References
- FSO Tokens Reference: ./FSO and fs2 format/FSO_Tokens_Reference.md
  - Practical list of valid FSO tokens/literals (canonical spellings)
- Comprehensive SEXPs index: ./FSO SEXPs/INDEX.md
  - See the per-category `.txt` files in the `./FSO SEXPs/` folder for details on specific SEXP constructs
- FS2 file format analysis: ./FSO and fs2 format/FS2-File-Format-Analysis.md
  - Deeper technical analysis of the FS2 file format (for converter developers)
- List of all FreeSpace ship class names: ./FSO and fs2 format/spacecraft-classes.md
- Ship bounding box dimensions: ./FSO and fs2 format/ship_bounding_boxes.md
- Ship subsystem names (per faction): documents in `./FSO and fs2 format/Ship subsystems/`
  - terran-ships-subsystem-names.md
  - vasudan-ships-subsystem-names.md
  - shivan-ships-subsystem-names.md
- Ship dockpoint names: ./FSO and fs2 format/ship-dockpoint-names.md
- Fighter and bomber primary/secondary hardpoint configuration: ./FSO and fs2 format/fighter_bomber_hardpoints.md
- Text styling guide (for command briefings, mission briefings, debriefings, and the fiction viewer): ./FSO and fs2 format/text_styling_guide.txt

## User Manuals (for humans)
- ./User manuals/Using NeuralFS with VS Code.md
- ./User manuals/Using NeuralFS with OpenCode.md

## Voice Names
- Google voices:
  - ./Google TTS/male_voices.txt
  - ./Google TTS/female_voices.txt
- ElevenLabs voices: ./ElevenLabs TTS/voices.txt
- Inworld voices: ./Inworld TTS/voices.txt

## Demo Missions (FSIF feature showcases)
Located in `../missions/Demo_missions/`:
- general_demo.fsif
- nebula_demo.fsif
- subspace_demo.fsif

## Demo Campaign (FCIF feature showcase)
Located in `../campaigns/Demo_campaigns/`:
- campaign_demo.fcif
