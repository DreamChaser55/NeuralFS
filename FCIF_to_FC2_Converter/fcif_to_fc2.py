import argparse
import sys
import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator, model_validator

# --- FCIF Data Models ---

class CampaignInfo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: str

    @field_validator('description')
    @classmethod
    def no_double_quotes_in_description(cls, v: str) -> str:
        if '"' in v:
            raise ValueError(
                'campaign.description must not contain double quotes ("), '
                'because it would cause syntax issues in the generated .fc2 file. '
                'Remove all double quotes from the description string.'
            )
        return v

class StartingLoadout(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ships: List[str] = Field(default_factory=list)
    weapons: List[str] = Field(default_factory=list)

class CampaignMission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: str
    success_goal: Optional[str] = None
    success_event: Optional[str] = None
    failure_goal: Optional[str] = None
    failure_event: Optional[str] = None

    @model_validator(mode='after')
    def check_mutual_exclusivity(self) -> 'CampaignMission':
        """Ensure at most one advance condition field is set per mission."""
        condition_fields = {
            'success_goal': self.success_goal,
            'success_event': self.success_event,
            'failure_goal': self.failure_goal,
            'failure_event': self.failure_event,
        }
        set_fields = [name for name, value in condition_fields.items() if value is not None]
        if len(set_fields) > 1:
            raise ValueError(
                f"Mission '{self.filename}': only one advance condition field may be set per mission, "
                f"but found: {', '.join(set_fields)}. "
                f"Use exactly one of: success_goal, success_event, failure_goal, failure_event."
            )
        return self

SUPPORTED_FCIF_VERSIONS = {"1.0", "1.1"}

class FCIF(BaseModel):
    model_config = ConfigDict(extra='forbid')
    fcif_version: str = "1.1"
    
    @field_validator('fcif_version', mode='before')
    @classmethod
    def cast_version_to_str(cls, v) -> str:
        return str(v)

    campaign: CampaignInfo
    starting_loadout: StartingLoadout
    missions: List[CampaignMission]

    @model_validator(mode='after')
    def check_version(self) -> 'FCIF':
        """Reject unsupported FCIF versions."""
        if self.fcif_version not in SUPPORTED_FCIF_VERSIONS:
            raise ValueError(
                f"Unsupported fcif_version: {self.fcif_version}. "
                f"Supported versions: {sorted(SUPPORTED_FCIF_VERSIONS)}"
            )
        return self

# --- Logic ---

def load_fcif(path: Path) -> FCIF:
    """Loads and validates the FCIF YAML file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return FCIF(**data)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Validation Error:\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        sys.exit(1)

def format_sexp_string(s: str) -> str:
    """Formats a string for SEXP (quoted)."""
    return f'"{s}"'

def _build_condition_sexp(mission: CampaignMission) -> Optional[str]:
    """
    Determines the advance condition SEXP for a mission based on its condition field.

    Returns the condition SEXP string, or None if the mission advances unconditionally.

    Mapping:
        success_goal  -> ( is-previous-goal-true  "mission" "name" )
        success_event -> ( is-previous-event-true  "mission" "name" )
        failure_goal  -> ( is-previous-goal-false  "mission" "name" )
        failure_event -> ( is-previous-event-false "mission" "name" )
    """
    mission_quoted = format_sexp_string(mission.filename)

    if mission.success_goal:
        return f'( is-previous-goal-true {mission_quoted} {format_sexp_string(mission.success_goal)} )'
    if mission.success_event:
        return f'( is-previous-event-true {mission_quoted} {format_sexp_string(mission.success_event)} )'
    if mission.failure_goal:
        return f'( is-previous-goal-false {mission_quoted} {format_sexp_string(mission.failure_goal)} )'
    if mission.failure_event:
        return f'( is-previous-event-false {mission_quoted} {format_sexp_string(mission.failure_event)} )'

    return None  # Unconditional

def generate_formula(mission: CampaignMission, next_mission_filename: Optional[str]) -> str:
    """
    Generates the mission progression logic (formula).

    Logic:
    - If an advance condition field is present (success_goal, success_event,
      failure_goal, or failure_event):
        ( cond
           ( ( <condition-sexp> ) ( next-mission "next" ) )
           ( ( true ) ( next-mission "current" ) )
        )
    - If no condition field is set (unconditional):
        ( cond
           ( ( true ) ( next-mission "next" ) )
           ( ( true ) ( next-mission "current" ) )
        )
    - If it's the last mission (next_mission_filename is None):
        Target is ( end-of-campaign ) instead of ( next-mission ... )
    """

    current_mission_quoted = format_sexp_string(mission.filename)

    # Determine the "success" action
    if next_mission_filename:
        next_action = f'( next-mission {format_sexp_string(next_mission_filename)} )'
    else:
        next_action = '( end-of-campaign )'

    # Repeat action (fallback)
    repeat_action = f'( next-mission {current_mission_quoted} )'

    # Build branches
    branches = []

    # Branch 1: Advance condition check
    condition = _build_condition_sexp(mission)
    if condition:
        branches.append(f'( {condition} {next_action} )')
    else:
        # Unconditional advancement
        branches.append(f'( ( true ) {next_action} )')

    # Branch 2: Fallback (Repeat)
    # Always added for robustness and to match standard format
    branches.append(f'( ( true ) {repeat_action} )')

    # Wrap in cond
    formula_body = "\n   ".join(branches)
    return f"( cond\n   {formula_body}\n)"

def write_fc2(fcif: FCIF, output_path: Path):
    """Generates the .fc2 file."""
    
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        # Header
        f.write(f"$Name: {fcif.campaign.name}\n")
        f.write("$Type: single\n")
        
        # Description with XSTR
        # Using -1 for ID as per standard for non-localized text, or allow tool to handle IDs later
        f.write("+Description:\n")
        f.write(f' XSTR("{fcif.campaign.description}", -1)\n')
        f.write("$end_multi_text\n\n")
        
        # Starting Loadout
        ships_str = ' '.join([f'"{s}"' for s in fcif.starting_loadout.ships])
        f.write(f'+Starting Ships: ( {ships_str} )\n\n')
        
        weapons_str = ' '.join([f'"{w}"' for w in fcif.starting_loadout.weapons])
        f.write(f'+Starting Weapons: ( {weapons_str} )\n\n')
        
        # Missions
        for i, mission in enumerate(fcif.missions):
            f.write(f"$Mission: {mission.filename}\n")
            
            f.write("+Flags: 0\n")
            f.write("+Main Hall: \n")
            
            # Logic
            next_mission = None
            if i < len(fcif.missions) - 1:
                next_mission = fcif.missions[i+1].filename
            
            formula = generate_formula(mission, next_mission)
            f.write(f"+Formula: {formula}\n")
            
            # Level and Position
            # Level increments, Position is usually 1 in linear campaigns
            f.write(f"\n+Level: {i}\n")
            f.write("+Position: 1\n\n")
            
        f.write("#End\n")

def main():
    parser = argparse.ArgumentParser(description="Convert FCIF (Freespace Campaign Intermediate File) to FC2 format.")
    parser.add_argument("input", type=Path, help="Input .fcif file")
    parser.add_argument("-o", "--output", type=Path, help="Output .fc2 file (optional, defaults to input filename with .fc2 extension)")
    
    args = parser.parse_args()

    # Determine output path if not provided
    if args.output is None:
        args.output = args.input.with_suffix('.fc2')
    
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Loading FCIF: {args.input}")
    fcif_data = load_fcif(args.input)
    
    print(f"Converting '{fcif_data.campaign.name}' ({len(fcif_data.missions)} missions)...")
    
    try:
        write_fc2(fcif_data, args.output)
        print(f"Successfully wrote: {args.output}")
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
