# FSIF to FS2 Converter (part of NeuralFS)

## Overview
This tool converts mission files from the concise FreeSpace Intermediate Format (.fsif) into the standard, engine-readable FreeSpace Open mission format (.fs2).
FSIF is a YAML-based, human-readable, and LLM-friendly representation that abstracts `.fs2` boilerplate, enabling rapid mission prototyping and AI-driven content creation.

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
  - **Google Gemini Flash TTS** (default)
  - **ElevenLabs TTS**
  - **Inworld TTS**
- Validation of FSIF files with actionable warning/error reports
  - Reported errors must be fixed for the conversion to succeed
  - Reported warnings are non-fatal, but should be addressed for best results
- Advanced SEXP validation

## Versions
- **Current FSIF version**: 4.0
- **FSIF version support**: the converter accepts FSIF **4.0** only.

## Requirements
- Python 3.9+
- PyYAML
- pydantic>=2.0

Optional (for Google TTS):
- `google-genai`
- A configured Google Cloud project (API key or Vertex AI credentials)

Optional (for ElevenLabs TTS):
- `elevenlabs`
- An ElevenLabs account and API key

Optional (for Inworld TTS):
- `requests` (for REST API)
- An Inworld account and API key

## Installation
Install the required libraries:
```bash
# Core requirements
pip install PyYAML pydantic

# For Google TTS
pip install google-genai

# For ElevenLabs TTS
pip install elevenlabs

# For Inworld TTS
pip install requests
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

## Project Structure
- `fsif_to_fs2.py` — CLI entry point: imports the other components and orchestrates the conversion process.
- `fsif_converter_gui.py` — Graphical user interface (GUI) for the converter.
- `mission_loader.py` — Loads FSIF, applies templates, and expands wings.
- `fs2_writer.py` — Emits FS2 sections.
- `validator/` — This package performs strict validation of logic, references, and constraints.
- `data_models.py` — Pydantic models for in-memory mission structures and schema validation.
- `fs_flags_constants.py` — FS2 format flag definitions and bitmask constants.
- `fs_data.py` — Auto-generated static reference data and token lists (teams, weapons, backgrounds, etc.) for validation. Do not edit manually.
- `briefing_icon_types.py` — Canonical mappings for briefing icon types.
- `tts_provider_base.py` — Abstract base class and common orchestration logic for TTS providers.
- `tts_google.py` — Google GenAI TTS provider implementation.
- `tts_elevenlabs.py` — ElevenLabs TTS provider implementation.
- `voice_manager.py` — Manages voice filename generation and normalization. Assigns unique filenames to voiced lines and handles collision resolution based on the selected TTS strategy.
- `utils.py` — Shared utility functions.
- `Advanced_SEXP_Validator/` — A Python implementation of the SEXP parser and validator used in the FSO engine.
