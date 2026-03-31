# Validates fiction viewer text files for FSO compatibility.
# Intended for use by the FSIF+FCIF Writing Agent.

import sys
import re
import argparse
from pathlib import Path
from typing import List, Optional


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

    # Matches a span-opening tag: a '$' followed by a single color letter and '{'
    # e.g. $y{, $R{, $f{, $W{, etc.
    _SPAN_OPEN_TAG_RE = re.compile(r'^\$([WwKkBbGgYyEeVvRrPpOoFfHhNn])\{$')

    # Tokenizes all recognized text styling tags in a string.
    # Matches (in order):
    #   - span color open:    $y{
    #   - single-word color:  $R  (followed by whitespace or end of string)
    #   - color break:        $|
    #   - span color close:   $}
    #   - special placeholders: $quote, $semicolon, $callsign, $rank
    _STYLE_TAG_RE = re.compile(
        r"""
        \$[WwKkBbGgYyEeVvRrPpOoFfHhNn]\{ |          # span color open, e.g. $y{
        \$[WwKkBbGgYyEeVvRrPpOoFfHhNn](?=(?:\s|$)) | # single-word color, e.g. $R text
        \$\| |                                         # color break
        \$\} |                                         # span color close
        \$(?:quote|semicolon|callsign|rank)\b          # special placeholders
        """,
        re.VERBOSE,
    )

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log_error(self, msg: str):
        self.errors.append(msg)

    def log_warning(self, msg: str):
        self.warnings.append(msg)

    def validate(self) -> bool:
        """
        Run all checks on the file. Prints a summary and returns True if
        the file passes (no errors), False otherwise.
        Warnings do not cause a failure (exit code stays 0 if no errors).
        """
        try:
            # Read as UTF-8 so that non-ASCII bytes are decoded into proper
            # Unicode characters, allowing accurate character-level inspection.
            text = self.file_path.read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            self.log_error(f"Could not read file: {e}")
            self._print_results()
            return False

        self._check_non_ascii(text)
        self._check_fiction_viewer_string(text)
        self._validate_span_tags(text)

        self._print_results()
        return len(self.errors) == 0

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_non_ascii(self, text: str):
        """
        Detect non-ASCII characters (code point > 127).
        FSO only supports the 7-bit ASCII range reliably; non-ASCII characters
        will appear garbled or cause parsing issues in the engine.
        """
        offenders = []
        for index, ch in enumerate(text):
            if ord(ch) > 127:
                offenders.append(f"{repr(ch)} (U+{ord(ch):04X}, index {index})")

        if not offenders:
            return

        details = ", ".join(offenders[:5])
        if len(offenders) > 5:
            details += f", ... (+{len(offenders) - 5} more)"

        self.log_error(
            f"Non-ASCII character(s) found — FSO does not support non-ASCII "
            f"characters reliably. Replace them with ASCII equivalents "
            f'(e.g. use \'-\' instead of em-dash, \'"\' instead of curly quotes, '
            f"'...' instead of the ellipsis character). "
            f"Offending character(s): {details}"
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

        Every span-opening tag (e.g. $y{) must be closed with $} before:
          1) A different style tag appears, or
          2) The end of the text is reached.

        Mirrors the logic of Validator._validate_span_style_tags in
        FSIF_to_FS2_Converter/validator.py.
        """
        tokens = list(self._STYLE_TAG_RE.finditer(text))

        for idx, tok in enumerate(tokens):
            opening_tag = tok.group(0)
            if not self._SPAN_OPEN_TAG_RE.match(opening_tag):
                continue  # Not a span-opening tag; skip.

            closed = False
            warned = False

            for next_tok in tokens[idx + 1:]:
                next_tag = next_tok.group(0)

                if next_tag == '$}':
                    closed = True
                    break

                # Placeholders ($callsign, $rank, $quote, $semicolon) are
                # text substitutions, not style tags. They do not open or
                # close a span, so skip them and keep looking for $}.
                if re.match(r'^\$(?:quote|semicolon|callsign|rank)\b', next_tag):
                    continue

                if next_tag != opening_tag:
                    # Encountered a different style tag before the closing $}
                    self.log_warning(
                        f"Span-style color tag '{opening_tag}' is unclosed before "
                        f"'{next_tag}'. "
                        f"Add '$}}' before '{next_tag}' to close the span "
                        f"(or remove the opening '{opening_tag}' if unintentional)."
                    )
                    warned = True
                    break

            if not closed and not warned:
                self.log_warning(
                    f"Span-style color tag '{opening_tag}' is unclosed at end of text. "
                    f"Add '$}}' to close the span."
                )

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
    Resolve a list of file/directory path strings into a flat list of .txt
    file Paths. Returns None if any path does not exist.
    """
    files: List[Path] = []
    for raw in input_paths:
        p = Path(raw)
        if p.is_dir():
            found = sorted(p.rglob('*.txt'))
            if not found:
                print(f"[WARNING] No .txt files found in directory '{p}'.")
            files.extend(found)
        elif p.is_file():
            files.append(p)
        else:
            print(f"[ERROR] Path not found: '{p}'")
            return None
    return files


def main():
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
            "Path(s) to fiction viewer text file(s) or folder(s). "
            "Folders are scanned recursively for .txt files."
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
