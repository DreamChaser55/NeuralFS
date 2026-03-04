import re
from pathlib import Path

# Extracts fighter/bomber hardpoint info from FSIF_to_FS2_Converter/ship_tables.txt
# and writes it to:
# Documentation/FSO and fs2 format/fighter_bomber_hardpoints.md


def extract_hardpoints():
    tools_dir = Path(__file__).resolve().parent
    converter_dir = tools_dir.parent
    root_dir = converter_dir.parent

    input_file = converter_dir / "ship_tables.txt"
    output_file = root_dir / "Documentation" / "FSO and fs2 format" / "fighter_bomber_hardpoints.md"

    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return

    with input_file.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Split into blocks based on $Name:
    # Prepend a newline so the first block matches if it starts at file beginning.
    content = "\n" + content
    ship_blocks = re.split(r"\n\$Name:\s*", content)

    ships_data = []

    # Skip leading split segment (before first $Name) if empty.
    if ship_blocks and not ship_blocks[0].strip():
        ship_blocks.pop(0)

    print(f"Found {len(ship_blocks)} ship blocks.")

    for block in ship_blocks:
        # Extract Name (first line)
        lines = block.split("\n")
        name = lines[0].strip()

        # Check flags for fighter/bomber.
        # Flags typically look like: $Flags: ( "fighter" "player_ship" )
        flags_match = re.search(r"\$Flags:\s*\((.*?)\)", block, re.DOTALL)
        if not flags_match:
            continue

        flags_str = flags_match.group(1).lower()
        if "fighter" not in flags_str and "bomber" not in flags_str:
            continue

        # Extract Secondary Banks (+Missile Banks)
        missile_banks = 0
        mb_match = re.search(r"\+Missile Banks:\s*(\d+)", block)
        if mb_match:
            missile_banks = int(mb_match.group(1))
        else:
            # Fallback: check $Default SBanks count if +Missile Banks is missing.
            sb_match = re.search(r"\$Default SBanks:\s*\((.*?)\)", block, re.DOTALL)
            if sb_match:
                sb_content = sb_match.group(1)
                # Count quoted strings.
                missile_banks = len(re.findall(r'"[^"]*"', sb_content))

        # Extract Primary Banks ($Default PBanks count)
        primary_banks = 0
        pb_match = re.search(r"\$Default PBanks:\s*\((.*?)\)", block, re.DOTALL)
        if pb_match:
            pb_content = pb_match.group(1)
            # Count quoted strings.
            primary_banks = len(re.findall(r'"[^"]*"', pb_content))

        ships_data.append(
            {
                "name": name,
                "primary": primary_banks,
                "secondary": missile_banks,
            }
        )

    # Sort by name.
    ships_data.sort(key=lambda x: x["name"])

    # Write Markdown output.
    with output_file.open("w", encoding="utf-8") as f:
        f.write("# Fighter and Bomber Hardpoint Configuration\n")
        for ship in ships_data:
            f.write(f"\n## {ship['name']}\n")
            f.write(f"- Primary: {ship['primary']}\n")
            f.write(f"- Secondary: {ship['secondary']}\n")

    print(f"Extracted {len(ships_data)} fighters/bombers. Saved to {output_file}.")


if __name__ == "__main__":
    extract_hardpoints()