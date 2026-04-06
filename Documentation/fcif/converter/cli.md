# FCIF Converter CLI

## Purpose
- Document how to invoke the FCIF → FC2 converter, expected inputs/outputs, and common usage patterns.

## Prerequisites
- Python 3.9+ installed and on PATH
- PyYAML and pydantic installed
  ```bash
  pip install PyYAML pydantic
  ```

## Entry point
- Script: fcif_to_fc2.py

## Basic usage
```bash
python fcif_to_fc2.py <input.fcif> [-o output.fc2]
```

## Arguments

### Positional arguments
| Argument | Description |
|---|---|
| `input` | Path to the input `.fcif` file. |

### Optional arguments
| Flag | Description |
|---|---|
| `-o`, `--output` | Path to the output `.fc2` file. If omitted, defaults to the input path with the extension changed to `.fc2`. |

## Path quoting
- The input and output paths may be provided with or without surrounding quotes. All of the following work:
  ```bash
  python fcif_to_fc2.py campaigns/my_campaign.fcif -o campaigns/my_campaign.fc2
  python fcif_to_fc2.py "campaigns/my_campaign.fcif" -o "campaigns/my_campaign.fc2"
  ```
- Warning about paths with spaces:
  - Some shells or process runners may split arguments at spaces even when quoted, causing argparse errors.
  - To avoid these errors:
    - Keep the path wrapped in quotes exactly as shown above.
    - Avoid spaces in directory and file names; use underscores instead.
    - When batching (cmd.exe example), ensure each `%%F` is quoted.

## Campaign-Wide Player Loadout Check

The first mission of a campaign is special: no `allow-ship` or `allow-weapon` SEXP has run before it, so every player ship class and weapon it uses must be in `starting_loadout` — otherwise it will not appear in the game. In subsequent missions, the player can only use ships and weapons that are either in the `starting_loadout` or explicitly granted by an `allow-ship` or `allow-weapon` SEXP in a previous mission.

The converter will automatically verify this campaign progression by tracking allowed items from `starting_loadout`, scanning each mission's `.fsif` file for new `allow-ship`/`allow-weapon` SEXPs, and validating the player's loadout for the current mission (Alpha-Epsilon wings, `start_ship`, `extra_ships`, `extra_weapons`).

For each item that is used by the player but not previously granted, a `[ERROR]` is printed and the conversion process is aborted.

## Output
- The converter writes the `.fc2` file to the specified (or derived) output path.

## Version and implementation details
- FCIF specification and field details: see `../specification.md`
- Converter emission details and SEXP logic generation: see `implementation_details.md`

## Exit status and logs
- Non-zero exit (`sys.exit(1)`) on fatal errors:
  - Invalid YAML syntax
  - Pydantic validation errors (missing required fields, unrecognized fields, wrong types)
  - Input file not found
  - Error writing the output file
- Errors are printed to stderr.
- On success, progress messages are printed to stdout:
  - `Loading FCIF: <path>`
  - `Converting '<campaign_name>' (<N> missions)...`
  - `Successfully wrote: <output_path>`

## Examples

### Single conversion (deriving output name)
```bash
python fcif_to_fc2.py campaigns/test_campaign.fcif
# Creates campaigns/test_campaign.fc2
```

### Single conversion (explicit output name)
```bash
python fcif_to_fc2.py campaigns/test_campaign.fcif -o campaigns/custom_name.fc2
```

## Troubleshooting
- **"Validation Error" with "extra inputs are not permitted"**:
  - The FCIF file contains an unrecognized field. The converter uses strict validation (`extra='forbid'`). Only fields documented in the [FCIF Specification](../specification.md) are accepted. Remove any extra or misspelled fields.
- **"Validation Error" with "field required"**:
  - A required field is missing. Check the [FCIF Specification](../specification.md) for required fields (`campaign`, `starting_loadout`, `missions`, etc.).
- **"Error: Input file '...' not found."**:
  - Check the input path for typos. Ensure the `.fcif` file exists at the specified location.
- **"Error parsing YAML"**:
  - The FCIF file contains invalid YAML syntax. Check for indentation errors, missing colons, or unquoted special characters.
