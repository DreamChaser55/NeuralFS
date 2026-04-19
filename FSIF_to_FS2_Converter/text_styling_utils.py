import re
from typing import List, Optional

# Matches a span-opening tag: a '$' followed by a single color letter and '{'
# e.g. $y{, $R{, $f{, $W{, etc.
SPAN_OPEN_TAG_RE = re.compile(r'^\$([WwKkBbGgYyEeVvRrPpOoFfHhNn])\{$')

# Tokenizes all recognized text styling tags in a string.
# Matches (in order):
#   - span color open:    $y{
#   - single-word color:  $R  (followed by whitespace or end of string)
#   - color break:        $|
#   - span color close:   $}
#   - special placeholders: $quote, $semicolon, $callsign, $rank
STYLE_TAG_RE = re.compile(
    r"""
    \$[WwKkBbGgYyEeVvRrPpOoFfHhNn]\{ |          # span color open, e.g. $y{
    \$[WwKkBbGgYyEeVvRrPpOoFfHhNn](?=(?:\s|$)) | # single-word color, e.g. $R text
    \$\| |                                         # color break
    \$\} |                                         # span color close
    \$(?:quote|semicolon|callsign|rank)\b          # special placeholders
    """,
    re.VERBOSE,
)

def extract_briefing_style_tags(text: Optional[str]) -> List[str]:
    """
    Extract all recognized text styling tags from a string.
    """
    if not text:
        return []
    matches = {m.group(0) for m in STYLE_TAG_RE.finditer(text)}
    return sorted(matches)

def validate_span_style_tags(text: Optional[str]) -> List[str]:
    """
    Validate span-style color tags ($c{ ... $}) in text.
    Returns a list of warning message strings if tags are unclosed.

    Single-pass O(N) stack-based approach:
    - Push each span-opening tag onto a stack.
    - $} pops the stack (span properly closed).
    - Any other style tag while the stack is non-empty means the open span
      was not closed — pop and warn. FSO does not support nested span tags.
    - Placeholder tags ($callsign, $rank, $quote, $semicolon) are skipped.
    - Tags remaining on the stack at the end are unclosed at end-of-text.
    """
    warnings = []
    if not text:
        return warnings

    tokens = list(STYLE_TAG_RE.finditer(text))
    stack: list = []  # unclosed span-opening tags

    for tok in tokens:
        tag = tok.group(0)

        # Placeholders ($callsign, $rank, $quote, $semicolon) are text
        # substitutions, not style tags. They do not open or close a span.
        if re.match(r'^\$(?:quote|semicolon|callsign|rank)\b', tag):
            continue

        if SPAN_OPEN_TAG_RE.match(tag):
            # A new span-open tag: if one is already open it was never closed.
            if stack:
                open_tag = stack.pop()
                warnings.append(
                    f"span-style color tag '{open_tag}' is unclosed before "
                    f"'{tag}'. Add '$}}' before '{tag}' (or remove '{open_tag}')."
                )
            stack.append(tag)

        elif tag == '$}':
            if stack:
                stack.pop()  # Span properly closed.
            else:
                warnings.append(
                    f"found '$}}' with no matching opening span tag. "
                    f"Remove the extra '$}}'."
                )

        else:
            # $| (color break) or single-word color tag (e.g. $R).
            # FSO does not support nested span tags of any kind; if a span
            # is currently open, this tag interrupts it.
            if stack:
                open_tag = stack.pop()
                warnings.append(
                    f"span-style color tag '{open_tag}' is unclosed before "
                    f"'{tag}'. Add '$}}' before '{tag}' (or remove '{open_tag}')."
                )

    # Any spans still on the stack were never closed.
    for open_tag in stack:
        warnings.append(
            f"span-style color tag '{open_tag}' is unclosed before end of text. "
            f"Add '$}}' to close the span."
        )

    return warnings
