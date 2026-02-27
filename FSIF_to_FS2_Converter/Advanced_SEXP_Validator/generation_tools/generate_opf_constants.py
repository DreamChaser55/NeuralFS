import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
VALIDATOR_DIR = BASE_DIR.parent
SEXP_H_FILE = VALIDATOR_DIR / "FSO code excerpts" / "sexp.h"
OUTPUT_FILE = VALIDATOR_DIR / "generated_code" / "opf_definitions.py"

def generate():
    print(f"Reading from {SEXP_H_FILE}...")
    try:
        content = SEXP_H_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Source file not found at {SEXP_H_FILE}")
        return

    # Regex to find the enum block
    # Matches: enum sexp_opf_t : int { ... }
    enum_pattern = re.compile(r'enum\s+sexp_opf_t\s*:\s*int\s*\{(.*?)\};', re.DOTALL)
    
    match = enum_pattern.search(content)
    if not match:
        print("Error: Could not find sexp_opf_t enum definition.")
        return

    enum_body = match.group(1)
    
    # Parse individual entries
    # Entries look like: OPF_UNUSED, or OPF_UNUSED
    # We need to assign integer values starting from 0 (though OPF_UNUSED is 0)
    
    definitions = {}
    current_value = 0
    
    # Split by lines and process
    for line in enum_body.splitlines():
        line = line.strip()
        # Remove comments
        if "//" in line:
            line = line.split("//")[0].strip()
        
        # Split by comma
        parts = [p.strip() for p in line.split(',') if p.strip()]
        
        for part in parts:
            if part:
                # Check if there is an assignment (rare in this enum but possible in C++)
                if '=' in part:
                    name, val_str = part.split('=')
                    name = name.strip()
                    try:
                        val = int(val_str.strip())
                        current_value = val
                    except ValueError:
                        print(f"Warning: Could not parse value for {name}: {val_str}")
                        continue
                else:
                    name = part
                
                definitions[name] = current_value
                current_value += 1

    # Write output
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# opf_definitions.py\n")
        f.write("# Auto-generated from FSO sexp.h. Do not edit manually.\n\n")
        
        for name, value in definitions.items():
            f.write(f"{name} = {value}\n")
            
        f.write(f"\n# Total definitions: {len(definitions)}\n")
        
    print(f"Successfully generated {len(definitions)} OPF constants.")

if __name__ == "__main__":
    generate()
