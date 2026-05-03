# NeuralFS: FSIF & FCIF Documentation Home

This is an index for the available documentation of FSIF, FCIF, FSO and the Converters.

Where to begin
1) Read FSIF specification for the exact schema
2) Use Authoring Guide for practical usage explanations, patterns and pitfalls
3) Consult References for valid tokens and exact SEXP operator strings
4) Study the demo missions for full practical examples
5) Learn to use the FSIF Converter CLI in cli.md
6) FSIF Converter emission details are consolidated under Converter Implementation Details
7) Read the FCIF specification for campaign file authoring
8) Learn to use the FCIF Converter CLI

Main README file: ../README.md

FSIF core docs
- FSIF Specification (normative): ./fsif/specification.md
  - Canonical schema: fields, required/optional, defaults, constraints
- Authoring Guide (practical): ./fsif/authoring-guide.md
  - Minimal skeletons, common patterns, Do/Don't, pitfalls
  - Curated examples
- Migration Guide: ./fsif/migration-guide.md
  - Breaking changes and notable additions with before/after snippets

FSIF Converter docs
- README.md: ../FSIF_to_FS2_Converter/README.md
- Converter Implementation Details: ./fsif/converter/implementation_details.md
  - FS2 emission mapping, normalization, warnings, FSO engine limits
  - Validation messages catalog
- Converter CLI: ./fsif/converter/cli.md
  - Installation, invocation, I/O behavior and examples

FCIF core docs
- FCIF Specification (normative): ./fcif/specification.md
  - Campaign file schema: fields, required/optional, constraints, advance conditions

FCIF Converter docs
- README.md: ../FCIF_to_FC2_Converter/README.md
- Converter Implementation Details: ./fcif/converter/implementation_details.md
  - FC2 emission mapping, SEXP logic generation, version handling
- Converter CLI: ./fcif/converter/cli.md
  - Installation, invocation, I/O behavior and examples

Fiction Viewer Validator docs
- README.md: ../Fiction_Viewer_Validator/README.md

Parsers and Generators docs
- parsers_and_generators.md: ../common/parsers_and_generators/parsers_and_generators.md

References
- FSO Tokens Reference: ./FSO and fs2 format/FSO_Tokens_Reference.md
  - Practical list of valid FSO tokens/literals (canonical spellings)
- Comprehensive SEXPs index: ./FSO SEXPs/INDEX.md
  - see per-category '.txt' files in the ./FSO SEXPs/ folder for details about specific SEXP constructs
- FS2 file format analysis: ./FSO and fs2 format/FS2-File-Format-Analysis.md
  - Deeper technical analysis of the FS2 file format (for Converter developers)
- List of all Freespace ship class names: ./FSO and fs2 format/spacecraft-classes.md
- Ship subsystem names (per faction): documents in ./FSO and fs2 format/Ship subsystems/ folder
  - terran-ships-subsystem-names.md
  - vasudan-ships-subsystem-names.md
  - shivan-ships-subsystem-names.md
- Ship dockpoint names: ./FSO and fs2 format/ship-dockpoint-names.md
- Fighter and bomber primary/secondary hardpoint configuration: ./FSO and fs2 format/fighter_bomber_hardpoints.md
- Text styling guide (for command and mission briefings, debriefings and fiction viewer): .\FSO and fs2 format\text_styling_guide.txt

User manuals (for humans)
- ./User manuals/Using NeuralFS with VS Code.md
- ./User manuals/Using NeuralFS with OpenCode.md

Voice names:
- Google voices:
  - .\Google TTS\male_voices.txt
  - .\Google TTS\female_voices.txt
- ElevenLabs voices: .\ElevenLabs TTS\voices.txt
- Inworld voices: .\Inworld TTS\voices.txt

Demo missions (FSIF feature showcases): in ../missions/Demo_missions/ folder
- general_demo.fsif
- nebula_demo.fsif
- subspace_demo.fsif

Demo campaign (FCIF feature showcase): in ../campaigns/Demo_campaigns/ folder
- campaign_demo.fcif
