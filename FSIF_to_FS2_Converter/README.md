# FSIF to FS2 Converter (part of NeuralFS)

## Overview
This tool converts mission files from the concise FreeSpace Intermediate Format (.fsif) into the standard, engine-readable FreeSpace Open mission format (.fs2).
FSIF is a YAML-based, human-readable, and LLM-friendly representation that abstracts .fs2 boilerplate for rapid mission prototyping and AI-driven content creation.

## Features (high level)
- Concise YAML syntax
- High-level abstractions (ship templates, unified wings)
- Automatic boilerplate generation
- S-Expression (SEXP) preservation for mission logic
- Localization of selected player-facing strings via XSTR
- Environment support (backgrounds, ambient light)
- Full nebula (volumetric) support
- Asteroid/debris fields
- Jump nodes
- Reinforcements
- Automatic TTS voice generation during conversion
  - **Google Gemini 2.5 TTS** (Default)
  - **ElevenLabs TTS**
- Basic validation of FSIF files with actionable error reports
- Advanced SEXP Validation (semantic checks)

## Versions
- **Current FSIF version**: 2.7
- **FSIF version support**: converter accepts FSIF **2.7** only.

## Requirements
- Python 3.9+
- PyYAML
- pydantic>=2.0

Optional (for Google TTS):
- `google-genai` (for Gemini 2.5 TTS)
- A configured Google Cloud project (API Key or Vertex AI)

Optional (for ElevenLabs TTS):
- `elevenlabs` (for ElevenLabs API)
- An ElevenLabs account and API Key

## Installation
Install the required libraries:
```bash
# Core requirements
pip install PyYAML pydantic

# For Google TTS
pip install google-genai

# For ElevenLabs TTS
pip install elevenlabs
```

## Documentation
- [CLI Usage](../Documentation/fsif/converter/cli.md)
- [Converter Implementation Details](../Documentation/fsif/converter/implementation_details.md)

## Usage (GUI)
A graphical user interface (`fsif_converter_gui.py`) is available for users who prefer not to use the command line.

Run the GUI script:
```bash
python fsif_converter_gui.py
```
This tool allows you to:
- Select a single file or a folder for batch conversion.
- Configure output paths.
- Toggle TTS generation and configure TTS options (overwrite, dry run, etc.).
- View real-time conversion logs.

## Data Generation Tools

The `tools/` folder contains four scripts that generate or update data files used by the converter. Three of them (`extract_hardpoints.py`, `parse_tables.py`, and `generate_weapons_compatibility.py`) must be run **before** `generate_fs_data.py` whenever the raw FSO table files (`ship_tables.txt`, `weapon_tables.txt`) are updated, because they produce the intermediate Markdown/Python files that `generate_fs_data.py` reads.

### `tools/extract_hardpoints.py`
Reads `ship_tables.txt` and extracts the number of primary and secondary weapon banks (hardpoints) for every ship flagged as a fighter or bomber. Writes the results to `Documentation/FSO and fs2 format/fighter_bomber_hardpoints.md`, which is used by `generate_fs_data.py` and by the converter's empty-hardpoint validator.

```bash
python tools/extract_hardpoints.py
```

### `tools/parse_tables.py`
Reads `ship_tables.txt` and `weapon_tables.txt` and extracts two data sets needed by the weapon supply validation logic:
- **Secondary bank capacities** per fighter/bomber ship → written to `secondary_bank_capacities.md`
- **Cargo sizes** of all secondary weapons → written to `secondary_weapon_sizes.md`

Both output files are read by `generate_fs_data.py` and directly by the converter's weapon pool calculator.

```bash
python tools/parse_tables.py
```

### `tools/generate_weapons_compatibility.py`
Reads `ship_tables.txt` and extracts the allowed primary and secondary weapon lists for every fighter/bomber (from the `$Allowed PBanks` / `$Allowed SBanks` table fields). Writes the result to `weapons_compatibility_data.py` in the converter directory.

```bash
python tools/generate_weapons_compatibility.py
```

### `tools/generate_fs_data.py`
The converter relies on valid FSO data (ship classes, weapons, SEXPs, voices, etc.) defined in `fs_data.py`. This file is generated from the official project documentation located in `Documentation/`.

To update the validation data (e.g., after adding a new ship class or SEXP to the documentation):
```bash
python tools/generate_fs_data.py
```
This will re-parse the Markdown files and overwrite `fs_data.py` with the latest definitions.

## Project Structure
- `fsif_to_fs2.py` — CLI entry: reads FSIF, generates TTS, and writes FS2.
- `fsif_converter_gui.py` — Graphical User Interface (GUI) for the converter.
- `mission_loader.py` — Loads FSIF, applies templates, expands wings.
- `fs2_writer.py` — Emits FS2 sections.
- `validator.py` — Performs strict validation of logic, references, and constraints.
- `data_models.py` — Pydantic models for in-memory mission structures and schema validation.
- `fs_flags_constants.py` — FS2 format flag definitions and bitmask constants.
- `fs_data.py` — Auto-generated static reference data and token lists (teams, weapons, backgrounds, etc.) for validation. Do not edit manually.
- `briefing_icon_types.py` — Canonical mappings for briefing icon types.
- `tts_provider_base.py` — Abstract base class and common orchestration logic for TTS providers.
- `tts_google.py` — Google GenAI TTS Provider Implementation.
- `tts_elevenlabs.py` — ElevenLabs TTS Provider Implementation.
- `voice_manager.py` — Manages voice filename generation and normalization. It assigns unique filenames to voiced lines, handling collision resolution based on the selected TTS strategy.
- `utils.py` — Shared utility functions.
- `tools/` — This folder is documented above, in the "Data Generation Tools" section.
- `Advanced SEXP Validator/` — A Python implementation of the SEXP parser and validator used in the FSO engine.