from typing import Union, List, Optional
from pydantic import AfterValidator
from typing_extensions import Annotated

def find_non_ascii_characters(value: Union[str, bytes]) -> Optional[str]:
    """
    Checks a string or byte array for non-ASCII characters (> 127).
    Returns a formatted string describing the offenders if any are found, or None if the value is purely ASCII.
    """
    if isinstance(value, str) and value.isascii():
        return None
        
    offenders: List[str] = []
    
    if isinstance(value, bytes):
        for index, byte_val in enumerate(value):
            if byte_val > 127:
                offenders.append(f"0x{byte_val:02X} (byte offset {index})")
    else:
        # value is narrowed to str here, but cast to satisfy type checkers
        for index, ch in enumerate(str(value)):
            if ord(ch) > 127:
                offenders.append(f"{repr(ch)} (U+{ord(ch):04X}, index {index})")
                
    if not offenders:
        return None
        
    details = ", ".join(offenders[:5])
    if len(offenders) > 5:
        details += f", ... (+{len(offenders) - 5} more)"
        
    return details

def _ascii_check(v: str) -> str:
    """AfterValidator: raises ValueError if *v* contains any non-ASCII character."""
    offenders_details = find_non_ascii_characters(v)
    if offenders_details:
        raise ValueError(f"contains non-ASCII character(s): {offenders_details}")
    return v

# AsciiStr: a Pydantic Annotated type that enforces ASCII-only strings.
# Applied to FSO-facing string fields so validity is guaranteed at construction time.
AsciiStr = Annotated[str, AfterValidator(_ascii_check)]
