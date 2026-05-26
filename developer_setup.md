# Developer setup and tests

A `pyproject.toml` at the repository root declares all runtime and optional dependencies.

## 1. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

Install the core runtime dependencies plus the dev extras (`pytest`):
```bash
pip install -e ".[dev]"
```

To also install optional TTS dependencies (all three providers):
```bash
pip install -e ".[dev,google-tts,elevenlabs-tts,inworld-tts]"
```

## 3. Run the test suite

```bash
python -m pytest
```

This automatically discovers tests under `FSIF_to_FS2_Converter/tests/`, `FCIF_to_FC2_Converter/tests/`, and `Fiction_Viewer_Validator/tests/`.

## 4. Run a Python syntax check

```bash
python -m compileall -q common FCIF_to_FC2_Converter Fiction_Viewer_Validator FSIF_to_FS2_Converter
```
