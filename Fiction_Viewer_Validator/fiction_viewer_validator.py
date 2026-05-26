# Validates fiction viewer text files for FSO compatibility.
# Intended for use by the FSIF+FCIF Writing Agent.

import sys
import re
import argparse
from pathlib import Path
from typing import List, Optional


# Add root to path to import common utils
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from common.text_styling_utils import validate_span_style_tags
from common.utils import sanitize_path


class FictionViewerValidator:
    """
    Validates a single fiction viewer text file for FSO compatibility.

    Checks performed:
    1. Non-ASCII characters (error) — FSO does not support non-ASCII reliably.
    2. "fiction viewer" string (warning) — internal feature name, should not
       appear in player-facing text.
    3. Span-style color tag closure (warning) — unclosed $c{ ... $} spans
       will produce incorrect colors in-game.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log_error(self, msg: str):
        """Append a fatal validation error. Files with any error fail validation."""
        self.errors.append(msg)

    def log_warning(self, msg: str):
        """Append a non-fatal warning. Warnings are reported but do not fail validation."""
        self.warnings.append(msg)

    def validate(self) -> bool:
        """
        Run all checks on the file. Prints a summary and returns True if
        the file passes (no errors), False otherwise.
        Warnings do not cause a failure (exit code stays 0 if no errors).
        """
        try:
            # Read raw bytes so _check_non_ascii can report the actual byte
            # values and byte offsets. Using read_text with errors='replace'
            # would silently substitute every invalid byte with U+FFFD,
            # making the reported character unlocatable in an editor.
            raw = self.file_path.read_bytes()
        except OSError as e:
            self.log_error(f"Could not read file: {e}")
            self._print_results()
            return False

        self._check_non_ascii(raw)

        # Decode for the remaining text-based checks.
        # errors='replace' is acceptable here because non-ASCII bytes have
        # already been caught and reported by _check_non_ascii above.
        text = raw.decode('utf-8', errors='replace')
        self._check_fiction_viewer_string(text)
        self._validate_span_tags(text)

        self._print_results()
        return len(self.errors) == 0

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_non_ascii(self, data: bytes):
        """
        Detect non-ASCII bytes (byte value > 127).
        Operates on the raw byte content so that the exact byte values and byte
        offsets are reported — never the Unicode replacement character U+FFFD
        that would appear if the file were decoded with errors='replace'.
        FSO only supports the 7-bit ASCII range reliably; non-ASCII bytes will
        appear garbled or cause parsing issues in the engine.
        """
        from common.validation_utils import find_non_ascii_characters
        offenders_details = find_non_ascii_characters(data)
        
        if offenders_details:
            self.log_error(
                f"Non-ASCII byte(s) found — FSO does not support non-ASCII "
                f"characters reliably. Replace them with ASCII equivalents "
                f'(e.g. use \'-\' instead of em-dash, \'"\' instead of curly quotes, '
                f"'...' instead of the ellipsis character). "
                f"Offending byte(s): {offenders_details}"
            )

    def _check_fiction_viewer_string(self, text: str):
        """
        Warn if the literal phrase 'fiction viewer' appears in the text.
        'Fiction viewer' is an internal FSO/NeuralFS feature name and should
        never appear in player-facing narrative content.
        """
        if re.search(r'fiction\s+viewer', text, re.IGNORECASE):
            self.log_warning(
                "'fiction viewer' detected in player-facing text. "
                "'Fiction Viewer' is an internal FSO feature name and should not "
                "appear in text shown to players. "
                "Remove or replace any development notes that reference this feature name."
            )

    def _validate_span_tags(self, text: str):
        """
        Validate span-style color tag closure.
        """
        for w in validate_span_style_tags(text):
            # Capitalize the first letter for consistency with original messages
            self.log_warning(w[0].upper() + w[1:])

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _print_results(self):
        if self.warnings:
            print(f"[WARNING] ({len(self.warnings)} warning(s)):")
            for w in self.warnings:
                print(f"  - {w}")

        if self.errors:
            print(f"[ERROR] ({len(self.errors)} error(s)):")
            for e in self.errors:
                print(f"  - {e}")
            print("[FAILED] Validation FAILED.")
        else:
            if self.warnings:
                print("[SUCCESS] Validation passed with warnings.")
            else:
                print("[SUCCESS] Validation PASSED.")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

def collect_files(input_paths: List[str]) -> Optional[List[Path]]:
    """
    Resolve a list of file path strings into a flat list of .txt
    file Paths. Returns None if any path does not exist or if a directory
    is passed.
    """
    files: List[Path] = []
    for raw in input_paths:
        p = Path(sanitize_path(raw))
        if p.is_dir():
            print(f"[ERROR] Directory parsing is not supported. Please pass specific .txt files (e.g., *_story.txt) instead of directories: '{p}'")
            return None
        elif p.is_file():
            files.append(p)
        else:
            print(f"[ERROR] Path not found: '{p}'")
            return None
    return files


def main():
    """
    CLI entry point for the Fiction Viewer Validator.

    Parses one or more `.txt` file paths from the command line, runs all
    validation checks on each file, and exits with status 1 if any file
    fails (contains errors). Directories are rejected — only explicit `.txt`
    file paths are accepted. Warnings are printed to stdout but do not affect
    the exit code.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate fiction viewer text files for FSO compatibility. "
            "Checks for non-ASCII characters, accidental internal feature names, "
            "and unclosed span-style color tags."
        )
    )
    parser.add_argument(
        "input",
        nargs='+',
        help=(
            "Path(s) to fiction viewer text file(s)."
        ),
    )
    args = parser.parse_args()

    files = collect_files(args.input)
    if files is None:
        # A path was not found; error already printed.
        sys.exit(1)

    if not files:
        print("[WARNING] No files to validate.")
        sys.exit(0)

    all_passed = True
    for file_path in files:
        print(f"\n--- Validating: {file_path} ---")
        validator = FictionViewerValidator(file_path)
        if not validator.validate():
            all_passed = False

    print()  # Blank line before final summary
    if len(files) > 1:
        if all_passed:
            print(f"[SUCCESS] All {len(files)} file(s) passed validation.")
        else:
            print(f"[FAILED] One or more of {len(files)} file(s) failed validation.")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
