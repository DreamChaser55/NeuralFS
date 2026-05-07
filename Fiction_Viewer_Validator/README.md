# Fiction Viewer Validator

Validates `.txt` files used by the Fiction Viewer.

## Checks performed
1. **Non-ASCII characters** (error) — FSO does not support non-ASCII characters reliably. Replace em dashes with `-`, curly quotes with `"` or `'`, the ellipsis character with `...`, etc.
2. **"fiction viewer" string** (warning) — "Fiction Viewer" is an internal FSO feature name and must not appear in player-facing narrative text.
3. **Unclosed span-style color tags** (warning) — Every span-style opening tag (e.g. `$c{`, `$y{`, `$f{`, `$h{`) must be closed with `$}` before the next style tag or the end of the text.

## Usage
```bash
# Validate a single file
python Fiction_Viewer_Validator/fiction_viewer_validator.py path/to/story.txt

# Validate multiple files
python Fiction_Viewer_Validator/fiction_viewer_validator.py file1.txt file2.txt
```
