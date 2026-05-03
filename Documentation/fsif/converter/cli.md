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
- Script: FSIF_to_FS2_Converter/fsif_to_fs2.py

## Basic usage
```bash
python FSIF_to_FS2_Converter/fsif_to_fs2.py <path_to_mission.fsif>
```

## Path quoting
- The input path may be provided with or without surrounding quotes. All of the following work:
  ```bash
  python FSIF_to_FS2_Converter/fsif_to_fs2.py missions/my_ambush_mission.fsif
  python FSIF_to_FS2_Converter/fsif_to_fs2.py "missions/my_ambush_mission.fsif"
  python FSIF_to_FS2_Converter/fsif_to_fs2.py 'missions/my_ambush_mission.fsif'
  ```
- Warning about paths with spaces:
  - Some shells or process runners may split arguments at spaces even when quoted, causing argparse errors.
  - To avoid these errors:
    - Keep the path wrapped in quotes exactly as shown above.
    - Avoid spaces in directory and mission names, use underscores instead (e.g., rename `/My missions/my mission.fsif` → `/My_missions/my_mission.fsif`).
    - You can use the Windows 8.3 short path for the directory (e.g., `missions/DEMO~1/general_demo.fsif`).
    - When batching (cmd.exe example), ensure each `%%F` is quoted.

## TTS Options
The converter supports automatic voice generation using Google GenAI, ElevenLabs or Inworld TTS. The TTS provider should ideally be specified in the `.fsif` file itself under the `audio.tts_provider` field. The CLI arguments act as optional overrides.

- `--enable-tts`: Force enable TTS generation, using Google if no provider is specified in the `.fsif` file or CLI.
- `--tts-provider <google|elevenlabs|inworld|none>`: Force the TTS Provider to use, overriding the `.fsif` file setting. Use `none` to forcefully disable TTS generation.
- `--tts-mode <mode>`: Voice filename strategy (default: `unique`).
  - `unique`: Generate unique filenames (e.g. `msg1.wav`) to avoid colliding with existing files. Useful for batch conversions or shared output directories.
  - `overwrite`: Use canonical filenames (e.g. `msg.wav`) and overwrite existing files on disk.
  - `keep`: Use canonical filenames but skip generation if file exists.
- `--tts-overwrite`: [Deprecated] Equivalent to `--tts-mode overwrite`.
- `--tts-skip-existing`: [Deprecated] Equivalent to `--tts-mode keep`.
- `--tts-dry-run`: Simulate generation without calling the API.
- `--google-api-key <key>`: Provide Google API key directly (overrides other key sources).
- `--elevenlabs-api-key <key>`: Provide ElevenLabs API key directly (overrides other key sources).
- `--inworld-api-key <key>`: Provide Inworld API key directly (overrides other key sources).
- `--elevenlabs-model <id>`: ElevenLabs model ID (default: `eleven_v3`).
- `--inworld-model <id>`: Inworld model ID (default: `inworld-tts-1.5-max`).
- `--tts-rate-limit-delay <seconds>`: Delay in seconds between consecutive TTS API calls (default: `0.0`).

### API Key Resolution Priority

The converter searches for the API key depending on the selected provider.

#### Google (Gemini TTS)
1. **CLI argument**: `--google-api-key <key>` (or GUI text field)
2. **Environment variables**: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
3. **File**: `Gemini_API_key.txt` in the `API_keys` directory
4. **Vertex AI**: Application Default Credentials (for GCP environments)

#### ElevenLabs TTS
1. **CLI argument**: `--elevenlabs-api-key <key>` (or GUI text field)
2. **Environment variable**: `ELEVENLABS_API_KEY`
3. **File**: `Elevenlabs_API_key.txt` in the `API_keys` directory

#### Inworld TTS
1. **CLI argument**: `--inworld-api-key <key>` (or GUI text field)
2. **Environment variable**: `INWORLD_API_KEY`
3. **File**: `Inworld_API_key.txt` in the `API_keys` directory

The first source that provides a valid key is used.

### Using API Key Files

To use a key file, create a text file named `Gemini_API_key.txt`, `Elevenlabs_API_key.txt`, or `Inworld_API_key.txt` in the `API_keys` directory located in the NeuralFS root folder, containing only your API key.

**Security Note**: Make sure your API key text files are not committed to version control. The `API_keys` directory is in `.gitignore`, so this should not happen with Git.

## Advanced Validation
- The Advanced SEXP Validator runs automatically. It performs a deep semantic check on all SEXP formulas (Events, Goals, Arrival/Departure Conditions, AI Goals) using FSO engine logic (type checking, return types, reference validation).

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
python FSIF_to_FS2_Converter/fsif_to_fs2.py "missions/Demo_missions/general_demo.fsif"
python FSIF_to_FS2_Converter/fsif_to_fs2.py "missions/Demo_missions/nebula_demo.fsif"
```

### Batch conversion (PowerShell example)
```powershell
Get-ChildItem -Recurse -Filter *.fsif | ForEach-Object {
  python FSIF_to_FS2_Converter/fsif_to_fs2.py $_.FullName
}
```

### Batch conversion (cmd.exe example)
```bat
for /R %%F in (*.fsif) do (
  python FSIF_to_FS2_Converter/fsif_to_fs2.py "%%F"
)
```
