import re
from pathlib import Path
import pprint

def parse_ship_tables(input_path: Path):
    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        return None

    content = input_path.read_text(encoding="utf-8")
    
    # Split into sections by $Name:
    # We use a lookahead to split by $Name but keep $Name in the parts
    parts = re.split(r'(?=\$Name:)', content)
    
    compatibility = {}
    
    # Regexes for fields
    name_re = re.compile(r'\$Name:\s*(.+)')
    flags_re = re.compile(r'\$Flags:\s*\(\s*(.*?)\s*\)', re.DOTALL)
    pbanks_re = re.compile(r'\$Allowed PBanks:\s*\(\s*(.*?)\s*\)', re.DOTALL)
    sbanks_re = re.compile(r'\$Allowed SBanks:\s*\(\s*(.*?)\s*\)', re.DOTALL)
    
    def extract_list(text):
        if not text:
            return set()
        # Items are double quoted
        return set(re.findall(r'"(.*?)"', text))

    for part in parts:
        name_match = name_re.search(part)
        if not name_match:
            continue
            
        ship_name = name_match.group(1).strip()
        
        flags_match = flags_re.search(part)
        flags = extract_list(flags_match.group(1)) if flags_match else set()
        
        # Check if it's a fighter or bomber
        is_fighter = "fighter" in [f.lower() for f in flags]
        is_bomber = "bomber" in [f.lower() for f in flags]
        
        if is_fighter or is_bomber:
            pbanks_match = pbanks_re.search(part)
            sbanks_match = sbanks_re.search(part)
            
            pbanks = extract_list(pbanks_match.group(1)) if pbanks_match else set()
            sbanks = extract_list(sbanks_match.group(1)) if sbanks_match else set()
            
            # Only include if at least one bank list is provided
            if pbanks or sbanks:
                compatibility[ship_name] = {
                    "primary": pbanks,
                    "secondary": sbanks
                }
            
    return compatibility

def main():
    # This script is in FSIF_to_FS2_Converter/tools/
    tools_dir = Path(__file__).resolve().parent
    converter_dir = tools_dir.parent
    
    input_file = converter_dir / "ship_tables.txt"
    output_file = converter_dir / "weapons_compatibility_data.py"
    
    print(f"Parsing {input_file}...")
    compatibility = parse_ship_tables(input_file)
    
    if compatibility is not None:
        print(f"Found {len(compatibility)} fighters/bombers.")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# weapons_compatibility_data.py\n")
            f.write("# AUTO-GENERATED. DO NOT EDIT MANUALLY.\n\n")
            f.write("WEAPON_COMPATIBILITY = ")
            # Use pprint for a nice readable dictionary
            f.write(pprint.pformat(compatibility, indent=4))
            f.write("\n")
        
        print(f"Successfully generated {output_file}")

if __name__ == "__main__":
    main()
