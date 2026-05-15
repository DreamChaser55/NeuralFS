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

# Matches only color-applying tags: span-opening ($y{) and single-word ($R).
# Does NOT match $}, $|, or placeholder tags.
COLOR_STYLE_TAG_RE = re.compile(
    r"""
    \$[WwKkBbGgYyEeVvRrPpOoFfHhNn]\{ |           # span color open, e.g. $f{
    \$[WwKkBbGgYyEeVvRrPpOoFfHhNn](?=(?:\s|$))   # single-word color, e.g. $h
    """,
    re.VERBOSE,
)

def has_color_styling_tag(text: Optional[str]) -> bool:
    """
    Return True if text contains at least one color-applying styling tag:
    either a span-opening tag (e.g. '$f{') or a single-word color tag (e.g. '$h').

    Close tags ($}), color breaks ($|), and placeholder substitutions
    ($callsign, $rank, $quote, $semicolon) are intentionally excluded.
    """
    if not text:
        return False
    return bool(COLOR_STYLE_TAG_RE.search(text))


def strip_text_styling_tags(text: Optional[str]) -> str:
    """
    Strips FSO text styling tags from a string and replaces 
    placeholders with TTS-friendly equivalents.
    Useful for cleaning text before sending it to a TTS provider.
    """
    if not text:
        return ""
        
    def replacer(match):
        tag = match.group(0)
        if tag.startswith('$quote'):
            return '"'
        elif tag.startswith('$semicolon'):
            return ';'
        elif tag.startswith('$callsign'):
            return 'Pilot'
        elif tag.startswith('$rank'):
            return 'Lieutenant'
        else:
            return ''
            
    clean_text = STYLE_TAG_RE.sub(replacer, text)
    # Clean up double spaces that might result from tag stripping
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text


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
