import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
# Up one level to Advanced_SEXP_Validator
VALIDATOR_DIR = BASE_DIR.parent
SOURCE_FILE = VALIDATOR_DIR / "FSO code excerpts" / "sexpdotcpp_excerpts.txt"
OUTPUT_FILE = VALIDATOR_DIR / "generated_code" / "sexp_definitions.py"

# Mapping FSO categories to OPR_* types (integer values from sexp_validator)
# Based on SexpReturnType (IntEnum) in advanced_sexp_validator.py:
# NONE = 0
# NUMBER = 4
# BOOL = 3
# NULL = 2
# AI_GOAL = 11
# POSITIVE = 14
# STRING = 12
# AMBIGUOUS = 17
# FLEXIBLE_ARGUMENT = 18

CATEGORY_MAP = {
    "SEXP_ARITHMETIC_OPERATOR": 4,  # NUMBER
    "SEXP_BOOLEAN_OPERATOR": 3,     # BOOL
    "SEXP_ACTION_OPERATOR": 2,      # NULL
    "SEXP_CONDITIONAL_OPERATOR": 2, # NULL
    "SEXP_INTEGER_OPERATOR": 4,     # NUMBER
    "SEXP_GOAL_OPERATOR": 11,       # AI_GOAL
    "SEXP_ARGUMENT_OPERATOR": 17,   # AMBIGUOUS
    "SEXP_STRING_OPERATOR": 12,     # STRING
}

def generate():
    print(f"Reading from {SOURCE_FILE}...")
    try:
        content = SOURCE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Source file not found at {SOURCE_FILE}")
        return

    # Regex to find the vector content
    # Matches: { "text", OP_ID, min, max, CATEGORY, }
    # We must be careful with whitespace and comments.
    # The pattern looks for the curly braces and the string literal.
    pattern = re.compile(r'\{\s*"([^"]+)"\s*,\s*([A-Z0-9_]+)\s*,\s*(-?\d+|INT_MAX)\s*,\s*(-?\d+|INT_MAX|MAX_COMPLETE_ESCORT_LIST|MAX_SQUADRON_WINGS|\d+\s*\+\s*[A-Z_]+)\s*,\s*([A-Z0-9_]+)\s*,')
    
    definitions = {}
    
    for match in pattern.finditer(content):
        text, op_id, min_args_str, max_args_str, category = match.groups()
        
        # Parse Min Args
        if min_args_str == "INT_MAX": min_args = 9999
        else: min_args = int(min_args_str)
        
        # Parse Max Args
        if max_args_str == "INT_MAX": 
            max_args = 9999
        elif "MAX_" in max_args_str:
            # Handle constants like MAX_COMPLETE_ESCORT_LIST
            # We'll just default them to a large number for validation leniency, or 9999
            max_args = 9999
        elif "+" in max_args_str:
             # Handle "1+ NUM_TURRET_ORDER_TYPES"
             max_args = 9999 
        else: 
            max_args = int(max_args_str)
        
        # Map Category
        return_type = CATEGORY_MAP.get(category, 17) # Default to AMBIGUOUS if unknown
        
        # Specific overrides for FSO operators that behave differently than their basic category
        if text in ["functional-if-then-else", "functional-when", "functional-switch"]:
            return_type = 17  # AMBIGUOUS (or FLEXIBLE_ARGUMENT) to allow in any context
        elif text == "num-valid-arguments":
            return_type = 4   # NUMBER

        definitions[text] = {
            "id": op_id,
            "min_args": min_args,
            "max_args": max_args,
            "return_type": return_type
        }
        
    # Write output
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# sexp_definitions.py\n")
        f.write("# Auto-generated from FSO source code. Do not edit manually.\n\n")
        f.write("INT_MAX = 9999\n\n")
        f.write("SEXP_DEFINITIONS = {\n")
        for text, data in sorted(definitions.items()):
            # Format nicely
            f.write(f'    "{text}": {{"id": "{data["id"]}", "min_args": {data["min_args"]}, "max_args": {data["max_args"]}, "return_type": {data["return_type"]}}},\n')
        f.write("}\n")
        
    print(f"Successfully generated {len(definitions)} operator definitions.")

if __name__ == "__main__":
    generate()
