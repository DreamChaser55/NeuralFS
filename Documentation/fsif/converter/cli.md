# Converter CLI

## Purpose
- Document how to invoke the FSIF → FS2 converter, expected inputs/outputs and common usage patterns.

## Prerequisites
- Python 3.9+ installed and on PATH
- PyYAML and pydantic installed
  ```bash
  pip install PyYAML pydantic
  ```

## Entry point
- Script: fsif_to_fs2.py

## Basic usage
```bash
python fsif_to_fs2.py <path_to_mission.fsif>
```

## Path quoting
- The input path may be provided with or without surrounding quotes. All of the following work:
  ```bash
  python fsif_to_fs2.py missions/my_ambush_mission.fsif
  python fsif_to_fs2.py "missions/my_ambush_mission.fsif"
  python fsif_to_fs2.py 'missions/my_ambush_mission.fsif'
  ```
- Warning about paths with spaces:
  - Some shells or process runners may split arguments at spaces even when quoted, causing argparse errors.
  - To avoid these errors:
    - Keep the path wrapped in quotes exactly as shown above.
    - Avoid spaces in directory and mission names, use underscores instead (e.g., rename `/My missions/my mission.fsif` → `/My_missions/my_mission.fsif`).
    - You can use the Windows 8.3 short path for the directory (e.g., `missions/DEMO~1/general_demo.fsif`).
    - When batching (cmd.exe example), ensure each `%%F` is quoted.

## TTS Options
The converter supports automatic voice generation using Google GenAI and ElevenLabs TTS. TTS is disabled by default.
- `--enable-tts`: Enable TTS generation.
- `--tts-provider <google|elevenlabs>`: TTS Provider to use (default: `google`).
- `--tts-out-root <path>`: Specify output directory for voice files.
- `--tts-mode <mode>`: Voice filename strategy (default: `unique`).
  - `unique`: Generate unique filenames (e.g. `msg1.wav`) to avoid colliding with existing files. Useful for batch conversions or shared output directories.
  - `overwrite`: Use canonical filenames (e.g. `msg.wav`) and overwrite existing files on disk.
  - `keep`: Use canonical filenames but skip generation if file exists.
- `--tts-overwrite`: [Deprecated] Equivalent to `--tts-mode overwrite`.
- `--tts-skip-existing`: [Deprecated] Equivalent to `--tts-mode keep`.
- `--tts-dry-run`: Simulate generation without calling the API.
- `--tts-default-voice <voice_name>`: Fallback voice for lines without a `voice_name` specified.
- `--google-api-key <key>`: Provide Google API key directly (overrides environment variables).
- `--elevenlabs-api-key <key>`: Provide ElevenLabs API key directly (overrides environment variables).
- `--elevenlabs-model <id>`: ElevenLabs model ID (default: `eleven_multilingual_v2`).
- `--tts-rate-limit-delay <seconds>`: Delay in seconds between consecutive TTS API calls (default: `0.0`).

### API Key Resolution Priority

The converter searches for the API key depending on the selected provider.

#### Google (Gemini TTS)
1. **CLI argument**: `--google-api-key <key>` (or GUI text field)
2. **Environment variables**: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
3. **File**: `Gemini_API_key.txt` in the current working directory
4. **Vertex AI**: Application Default Credentials (for GCP environments)

#### ElevenLabs TTS
1. **CLI argument**: `--elevenlabs-api-key <key>` (or GUI text field)
2. **Environment variable**: `ELEVENLABS_API_KEY`
3. **File**: `Elevenlabs_API_key.txt` in the current working directory

The first source that provides a valid key is used. To use a key file, create a text file named `Gemini_API_key.txt` or `Elevenlabs_API_key.txt` in the directory where you run the converter, containing only your API key.

**Security Note**: Do not commit API key text files to version control. Add them to `.gitignore` if needed.

## Advanced Validation
- The Advanced SEXP Validator runs automatically. It performs a deep semantic check on all SEXP formulas (Events, Goals, Cues, AI Goals) using FSO engine logic (type checking, return types, reference validation).

## Output
- The converter writes a peer .fs2 file next to the input, preserving the base name:
  - Input: missions/my_ambush_mission.fsif
  - Output: missions/my_ambush_mission.fs2

## Version and implementation details
- FSIF version requirements: see `../specification.md`
- Converter emission details: see `implementation_details.md`

## Exit status and logs
- Non-zero exit on fatal errors (e.g., invalid YAML, missing required fields that prevent writing)
- Warnings are printed to stdout/stderr; they should be treated as actionable authoring feedback even when the run succeeds

## Examples

### Demo missions convert
```bash
python fsif_to_fs2.py "missions/Demo_missions/general_demo.fsif"
python fsif_to_fs2.py "missions/Demo_missions/nebula_demo.fsif"
```

### Batch conversion (PowerShell example)
```powershell
Get-ChildItem -Recurse -Filter *.fsif | ForEach-Object {
  python fsif_to_fs2.py $_.FullName
}
```

### Batch conversion (cmd.exe example)
```bat
for /R %%F in (*.fsif) do (
  python fsif_to_fs2.py "%%F"
)
```