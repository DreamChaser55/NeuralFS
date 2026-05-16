# FCIF Converter CLI

## Purpose
Document how to invoke the FCIF → FC2 converter, expected inputs/outputs, and common usage patterns.

## Prerequisites
- Python 3.9+ installed and on PATH
- PyYAML and pydantic installed:
  ```bash
  pip install PyYAML pydantic
  ```

## Entry Point
- Script: `FCIF_to_FC2_Converter/fcif_to_fc2.py`

## Basic Usage
```bash
python FCIF_to_FC2_Converter/fcif_to_fc2.py <input.fcif> [-o output.fc2]
```

## Arguments

### Positional Arguments
| Argument | Description |
|---|---|
| `input` | Path to the input `.fcif` file. |

### Optional Arguments
| Flag | Description |
|---|---|
| `-o`, `--output` | Path to the output `.fc2` file. If omitted, defaults to the input path with the extension changed to `.fc2`. |

## Path Quoting
- The input and output paths may be provided with or without surrounding quotes. All of the following work:
  ```bash
  python FCIF_to_FC2_Converter/fcif_to_fc2.py campaigns/my_campaign.fcif -o campaigns/my_campaign.fc2
  python FCIF_to_FC2_Converter/fcif_to_fc2.py "campaigns/my_campaign.fcif" -o "campaigns/my_campaign.fc2"
  ```
- Warning about paths with spaces:
  - Some shells or process runners may split arguments at spaces even when quoted, causing argparse errors.
  - To avoid these errors:
    - Keep the path wrapped in quotes exactly as shown above.
    - Avoid spaces in directory and file names; use underscores instead.
    - When batching in `cmd.exe`, ensure each `%%F` is quoted.

## Advance Condition Reference Check

For every mission that has a `success_goal`, `failure_goal`, `success_event`, or `failure_event` field set, the converter verifies that the referenced name actually exists in the corresponding `.fsif` file. The `.fsif` path is inferred from the `.fcif` location: `campaign_folder/fsif/<mission_stem>.fsif`.

- **Goal fields** (`success_goal`, `failure_goal`): the referenced name must match `mission_flow.goals[*].name` in the FSIF.
- **Event fields** (`success_event`, `failure_event`): the referenced name must match `mission_flow.events[*].name` in the FSIF.

If the FSIF file is missing or unparseable for a mission that has an advance condition, or if the referenced name is not found, an `[ERROR]` is printed and the conversion is aborted. Missions without an advance condition are silently skipped. The error message lists all available goal/event names to help identify the mismatch.

## Campaign-Wide Player Loadout Check

The first mission of a campaign is special: no `allow-ship` or `allow-weapon` SEXP has run before it, so every player ship class and weapon it uses must be in `starting_loadout` — otherwise it will not appear in the game. In subsequent missions, the player can only use ships and weapons that are either in `starting_loadout` or explicitly granted by an `allow-ship` or `allow-weapon` SEXP in a previous mission.

The converter automatically verifies this campaign progression by tracking allowed items from `starting_loadout`, scanning each mission's `.fsif` file for new `allow-ship`/`allow-weapon` SEXPs, and validating the player's loadout for the current mission (Alpha–Epsilon wings, `start_ship`, `additional_ship_choices`, `additional_weapons`).

For each item that is used by the player but not previously granted, an `[ERROR]` is printed and the conversion is aborted.

## Output
The converter writes the `.fc2` file to the specified (or derived) output path.

## Version and Implementation Details
- FCIF specification and field details: see `../specification.md`
- Converter emission details and SEXP logic generation: see `implementation_details.md`

## Exit Status and Logs
- Non-zero exit (`sys.exit(1)`) on fatal errors:
  - Invalid YAML syntax
  - Pydantic validation errors (missing required fields, unrecognized fields, wrong types)
  - Input file not found
  - Error writing the output file
- All progress messages (successes, warnings, and errors) are printed to stderr (`logging.basicConfig` default output):
  - `Loading FCIF: <path>`
  - `Converting '<campaign_name>' (<N> missions)...`
  - `Successfully wrote: <output_path>`

## Examples

### Single conversion (deriving output name)
```bash
python FCIF_to_FC2_Converter/fcif_to_fc2.py campaigns/test_campaign.fcif
# Creates campaigns/test_campaign.fc2
```

### Single conversion (explicit output name)
```bash
python FCIF_to_FC2_Converter/fcif_to_fc2.py campaigns/test_campaign.fcif -o campaigns/custom_name.fc2
```

## Troubleshooting
- **"Validation Error" with "path separators"** (e.g. `it must not contain path separators`):
  - A `missions[*].filename` entry contains a `/` or `\` character. The field must be a bare mission filename such as `missionname.fs2`, with no directory components.
- **"Validation Error" with "missing '.fs2' extension"** (e.g. `must end with the '.fs2' extension`):
  - A `missions[*].filename` entry is missing the `.fs2` extension or has the wrong extension (e.g. `.fc2`, `.fsif`). The field must look like `missionname.fs2`.
- **"Validation Error" with "extra inputs are not permitted"**:
  - The FCIF file contains an unrecognized field. The converter uses strict validation (`extra='forbid'`). Only fields documented in the [FCIF Specification](../specification.md) are accepted. Remove any extra or misspelled fields.
- **"Validation Error" with "field required"**:
  - A required field is missing. Check the [FCIF Specification](../specification.md) for required fields (`campaign`, `starting_loadout`, `missions`, etc.).
- **"Error: Input file '...' not found."**:
  - Check the input path for typos. Ensure the `.fcif` file exists at the specified location.
- **"Error parsing YAML"**:
  - The FCIF file contains invalid YAML syntax. Check for indentation errors, missing colons, or unquoted special characters.
