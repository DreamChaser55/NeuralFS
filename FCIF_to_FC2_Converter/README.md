# FCIF to FC2 Converter (part of NeuralFS)

## Overview
This tool converts campaign files from the concise Freespace Campaign Intermediate Format (.fcif) into the standard, engine-readable FreeSpace Open campaign format (.fc2).
FCIF is a YAML-based, human-readable, and LLM-friendly representation that abstracts .fc2 boilerplate for rapid campaign definition and AI-driven content creation.

## Features (high level)
- Concise YAML syntax for campaign definition
- Pydantic-based schema validation with strict field checking
- Checks if all text fields only use ASCII characters
- Automatic S-Expression (SEXP) logic generation for mission progression (conditional and unconditional branching)
- Localization of campaign description via XSTR
- Linear campaign progression with optional per-mission advance conditions
- Four advance condition types: goal true/false, event true/false (`is-previous-goal-true`, `is-previous-event-true`, `is-previous-goal-false`, `is-previous-event-false`)
- **Campaign-wide player loadout check**: the converter automatically infers the path to the `.fsif` files and verifies that all player ship classes and weapons used in each mission are present in `starting_loadout` or explicitly granted by `allow-ship`/`allow-weapon` SEXPs in previous missions. The check also validates that `template` references on player ships and wings are strings.

## Versions
FCIF and converter versions:
- **FCIF**: 1.1 (current)
- **FCIF version support**: converter accepts FCIF **1.0** and **1.1**. Files with other `fcif_version` values are rejected.

## Requirements
- Python 3.9+
- PyYAML
- pydantic>=2.0

## Installation
Install the required libraries:
```bash
pip install PyYAML pydantic
```

## Documentation
- [FCIF Specification](../Documentation/fcif/specification.md)
- [CLI Usage](../Documentation/fcif/converter/cli.md)
- [Converter Implementation Details](../Documentation/fcif/converter/implementation_details.md)

## Usage (CLI)
See [CLI Usage](../Documentation/fcif/converter/cli.md).

## Usage (GUI)
A graphical user interface (`fcif_converter_gui.py`) is available for users who prefer not to use the command line.

Run the GUI script:
```bash
python fcif_converter_gui.py
```
This tool allows you to:
- Select a single `.fcif` file.
- Configure output path.
- View real-time conversion logs.

## Project Structure
- `fcif_to_fc2.py` — CLI entry: loads FCIF, validates, generates SEXP logic, and writes FC2. Contains data models, logic generation, and the CLI in a single file.
- `fcif_converter_gui.py` — Graphical User Interface (GUI) for the converter.
- `fc2 file examples/` — Reference `.fc2` campaign files for understanding the output format.

## Notes
- Ship and weapon names in `starting_loadout` must match canonical FSO tokens exactly. Do not invent synonyms or casing/spacing variants.
- The order of missions in the `missions` list determines campaign progression. The first mission is the starting mission; the last mission targets `end-of-campaign`.
- Any ship or weapon used in the campaign must be either listed in `starting_loadout`, or explicitly allowed with the appropriate SEXP (`allow-ship` or `allow-weapon`) during the campaign, otherwise it will not appear in the game even if defined in the mission files.
- For the campaign, the converter verifies the loadout validity across the *entire* campaign and will reject the `.fcif` file if an un-granted ship or weapon is used by the player without being in `starting_loadout` or granted by an `allow-ship`/`allow-weapon` SEXP in a prior mission.
- The converter uses pydantic with `extra='forbid'`, so any unrecognized fields in the FCIF file will cause a validation error. Only fields documented in the [FCIF Specification](../Documentation/fcif/specification.md) are accepted.
