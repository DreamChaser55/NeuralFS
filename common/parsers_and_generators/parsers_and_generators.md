# Data Generation Tools

This folder contains four scripts that generate or update data files used by the converter. Three of them (`extract_hardpoints.py`, `parse_tables.py`, and `generate_weapons_compatibility.py`) must be run **before** `generate_fs_data.py` whenever the raw FSO table files (`ship_tables.txt`, `weapon_tables.txt`) are updated, because they produce the intermediate Markdown/Python files that `generate_fs_data.py` reads.

## `common/parsers_and_generators/extract_hardpoints.py`
Reads `ship_tables.txt` and extracts the number of primary and secondary weapon banks (hardpoints) for every ship flagged as a fighter or bomber. Writes the results to `Documentation/FSO and fs2 format/fighter_bomber_hardpoints.md`, which is used by `generate_fs_data.py` and by the converter's empty-hardpoint validator.

```bash
python common/parsers_and_generators/extract_hardpoints.py
```

## `common/parsers_and_generators/parse_tables.py`
Reads `ship_tables.txt` and `weapon_tables.txt` and extracts two data sets needed by the weapon supply validation logic:
- **Secondary bank capacities** per fighter/bomber ship → written to `secondary_bank_capacities.md`
- **Cargo sizes** of all secondary weapons → written to `secondary_weapon_sizes.md`

Both output files are read by `generate_fs_data.py` and directly by the converter's weapon pool calculator.

```bash
python common/parsers_and_generators/parse_tables.py
```

## `common/parsers_and_generators/generate_weapons_compatibility.py`
Reads `ship_tables.txt` and extracts the allowed primary and secondary weapon lists for every fighter/bomber (from the `$Allowed PBanks` / `$Allowed SBanks` table fields). Writes the result to `weapons_compatibility_data.py` in the converter directory.

```bash
python common/parsers_and_generators/generate_weapons_compatibility.py
```

## `common/parsers_and_generators/generate_fs_data.py`
The converter relies on valid FSO data (ship classes, weapons, SEXPs, voices, etc.) defined in `fs_data.py`. This file is generated from the official project documentation located in `Documentation/`.

To update the validation data (e.g., after adding a new ship class or SEXP to the documentation):
```bash
python common/parsers_and_generators/generate_fs_data.py
```
This will re-parse the Markdown files and overwrite `fs_data.py` with the latest definitions.