# mission_loader.py
# Parses YAML, hydrates with defaults, and expands abstractions.

import yaml
import copy
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from data_models import (
    Mission, Ship, Wing, Environment, MissionInfo, PlayerSetup,
    Event, Goal, Message, Reinforcement, JumpNode,
    Briefing, Debriefing, CommandBriefing, BriefingIcon,
    AudioSettings
)
import briefing_icon_types as brief_types
from utils import calculate_briefing_camera_height

logger = logging.getLogger(__name__)


class MissionLoader:
    def __init__(self, fsif_path: str):
        self.fsif_path = Path(fsif_path)
        self.data: Dict[str, Any] = {}
        self.fsif_version: Optional[str] = None
        
        # Intermediate state
        self.templates: Dict[str, Any] = {}
        self.all_ships: List[Ship] = []
        self.all_wings: List[Wing] = []

    _FORBIDDEN_TEMPLATE_FIELDS = (
        'arrival_location',
        'arrival_anchor',
        'arrival_distance',
        'arrival_delay',
        'arrival_cue',
        'departure_location',
        'departure_anchor',
        'departure_cue',
        'ai_goals',
        'dock',
        'docked_with',
        'docker_point',
        'dockee_point',
    )
        
    def load(self) -> Mission:
        """Main execution method."""
        self._read_yaml()
        self._validate_version()
        self._check_required_sections()
        
        # Load sections
        mission_info = self._load_mission_info()
        environment = self._load_environment(mission_info) # updates flags in mission_info
        player_setup = self._load_player_setup()
        
        self._load_entities(player_setup)
        
        flow_data = self._load_mission_flow()
        
        # Other top-level
        jump_nodes = [JumpNode(**jn) for jn in self.data.get('jump_nodes', [])]
        reinforcements = self._process_reinforcements()
        audio = self._load_audio()
        
        # Construct Mission
        return Mission(
            mission_info=mission_info,
            environment=environment,
            player_setup=player_setup,
            ships=self.all_ships,
            wings=self.all_wings,
            waypoints=self.data.get('entities', {}).get('waypoints', {}),
            events=flow_data['events'],
            goals=flow_data['goals'],
            messages=flow_data['messages'],
            briefing=flow_data['briefing'],
            debriefing=flow_data['debriefing'],
            command_briefing=flow_data['command_briefing'],
            fiction_viewer=flow_data['fiction_viewer'],
            reinforcements=reinforcements,
            jump_nodes=jump_nodes,
            audio=audio
        )

    def _read_yaml(self):
        with open(self.fsif_path, 'r') as f:
            self.data = yaml.safe_load(f) or {}

    def _validate_version(self):
        """
        Validate the 'fsif_version' field.
        
        Currently accepted FSIF version: '2.8'.
        
        Raises:
            ValueError: If 'fsif_version' is missing, malformed, or unsupported.
        """
        version_str = self.data.get('fsif_version')
        if not isinstance(version_str, str) or not version_str.strip():
            raise ValueError("fsif_version is required and must be the exact string '2.8'.")
        version_str = version_str.strip()
        if version_str != '2.8':
            raise ValueError(
                f"Unsupported fsif_version '{version_str}'. The current converter accepts FSIF version '2.8' only. "
                f"Please update your mission file (see Migration Guide)."
            )
        self.fsif_version = version_str

    def _check_required_sections(self):
        required = ['mission_info', 'player_setup', 'entities', 'mission_flow']
        for sec in required:
            if sec not in self.data:
                raise ValueError(f"Missing required top-level section: '{sec}'.")

    def _load_mission_info(self) -> MissionInfo:
        """
        Parse and validate the 'mission_info' section.
        
        Injects creation and modification timestamps.
        
        Returns:
            MissionInfo: Populated mission info object.
            
        Raises:
            ValueError: If 'name' is missing.
        """
        mission_info_data = self.data.get('mission_info', {})
        if 'name' not in mission_info_data:
            raise ValueError("mission_info.name is required.")
        
        # Add generated timestamps
        now = datetime.now().strftime('%m/%d/%y at %H:%M:%S')
        mission_info_data['created'] = now
        mission_info_data['modified'] = now
        
        return MissionInfo(**mission_info_data)

    def _load_environment(self, mission_info: MissionInfo) -> Environment:
        """
        Parse and validate the 'environment' section.
        
        Handles injection of implied mission flags (e.g. for nebula).
        
        Args:
            mission_info: MissionInfo object to update with implied flags.
            
        Returns:
            Environment: Populated environment object.
        """
        env_data = self.data.get('environment', {})

        ambient_light_level = env_data.get('ambient_light_level')
        if not isinstance(ambient_light_level, list):
            raise ValueError(
                "FSIF requires environment.ambient_light_level to be authored as [red, green, blue]."
            )
        
        # Nebula Normalization
        neb_src = env_data.get('nebula')
        if neb_src and isinstance(neb_src, dict):

            if neb_src.get('enabled'):
                 if not neb_src.get('pattern'):
                     raise ValueError("environment.nebula.pattern is required when environment.nebula.enabled is true.")
                 
                 # Flags injection
                 flags = mission_info.flags
                 if not any(str(x).strip().lower() == 'fullneb' for x in flags):
                     flags.append('fullneb')
                 
                 mission_info.flags = flags # Update model
            
            env_data['nebula'] = neb_src
        
        # Asteroid Field Normalization
        af_src = env_data.get('asteroid_field')
        if af_src and isinstance(af_src, dict):
            # Normalise the two human-readable string keys.
            # 'genre' -> 'asteroid' | 'debris'  (kept as-is in the model)
            # 'type'  -> 'active'   | 'passive'  (renamed to 'field_type' for the model)
            genre = str(af_src.get('genre', 'asteroid')).lower()
            ftype = str(af_src.get('type', 'passive')).lower()

            # Enforce constraint: a debris field cannot be active.
            if genre != 'asteroid' and ftype == 'active':
                logger.warning(f"[WARNING] Debris field cannot be active; coercing to passive.")
                ftype = 'passive'

            # Map bounds to min_vec/max_vec
            if 'bounds' in af_src and isinstance(af_src['bounds'], dict):
                b = af_src['bounds']
                if 'min' in b: af_src['min_vec'] = b['min']
                if 'max' in b: af_src['max_vec'] = b['max']

            # Write normalised strings back; rename 'type' -> 'field_type' to match model field.
            af_src['genre'] = genre
            af_src['field_type'] = ftype

            # Cleanup source for strict model
            af_src.pop('type', None)
            af_src.pop('bounds', None)

            env_data['asteroid_field'] = af_src

        return Environment(**env_data)

    def _load_player_setup(self) -> PlayerSetup:
        ps_data = self.data.get('player_setup', {})
        return PlayerSetup(**ps_data)

    def _load_entities(self, player_setup: PlayerSetup):
        """
        Load all mission entities (ships, wings, templates).
        
        Orchestrates the loading process by processing templates first,
        then expanding wings into individual ships, and finally processing
        standalone ships.
        
        Args:
            player_setup: Player setup for identifying start ship.
        """
        entities = self.data.get('entities', {})
        self.templates = entities.get('ship_templates', {})
        
        # Validate templates
        for name, template in self.templates.items():
            self._validate_ship_template_authoring_rules(name, template)
            self._validate_no_player_start(template.get('flags'), f"template '{name}'")

        # Expand Wings
        for wing_data in entities.get('wings', []):
            self._process_wing(wing_data, player_setup)

        # Expand Standalone Ships
        for ship_data in entities.get('ships', []):
            self._process_ship(ship_data)

    def _validate_ship_template_authoring_rules(self, template_name: str, template_data: Dict[str, Any]):
        """
        Reject ship-template fields that must be authored on the concrete ship/wing.

        Arrival/departure locations, anchors, distances and cues do not work when
        inherited by ships that are part of a wing, so FSIF forbids authoring these
        fields in ship_templates entirely. Standalone ships must author them directly
        on the ship, while wing members must author them on the wing.
        """
        if not isinstance(template_data, dict):
            raise ValueError(f"Ship template '{template_name}' must be a mapping.")

        forbidden_fields = [field for field in self._FORBIDDEN_TEMPLATE_FIELDS if field in template_data]
        if not forbidden_fields:
            return

        if len(forbidden_fields) == 1:
            fields_phrase = f"field '{forbidden_fields[0]}'"
        else:
            fields_phrase = "fields " + ", ".join(f"'{field}'" for field in forbidden_fields)

        raise ValueError(
            f"Validation error in ship template '{template_name}': {fields_phrase} must not be authored in ship_templates. "
            f"Author these values directly on a standalone ship, or on the corresponding wing if the ship is part of a wing."
        )

    def _process_wing(self, wing_data: Dict[str, Any], player_setup: PlayerSetup):
        """
        Expand a wing definition into individual ship objects.
        
        Processes wing template references, calculates ship positions based on
        centroid and spacing, and adds ships to the mission ship list.
        
        Args:
            wing_data: Raw wing definition from FSIF containing template, count, position.
            player_setup: Player setup for identifying start ship.
        
        Raises:
            ValueError: If wing is missing required fields or references invalid template.
        """
        if 'count' not in wing_data:
            raise ValueError(f"Wing '{wing_data.get('name')}' missing required 'count'.")
        
        tmpl_name = wing_data.get('template')
        if tmpl_name is not None and not isinstance(tmpl_name, str):
            raise ValueError(f"Validation Error: Wing '{wing_data.get('name', 'unknown')}' must use a string reference for 'template', found {type(tmpl_name).__name__} instead.")
            
        if not tmpl_name or tmpl_name not in self.templates:
            raise ValueError(f"Wing '{wing_data.get('name')}' must reference a valid template.")
        
        template_base = self.templates[tmpl_name]
        
        if wing_data.get('formation_pos') is not None:
             raise ValueError(f"Wing '{wing_data.get('name')}' uses deprecated 'formation_pos'. Use 'position'.")
        if 'position' not in wing_data:
             raise ValueError(f"Wing '{wing_data.get('name')}' must define 'position: [x, y, z]'.")

        try:
            raw_pos = wing_data['position']
            if len(raw_pos) < 3: raise ValueError
            cx, cy, cz = float(raw_pos[0]), float(raw_pos[1]), float(raw_pos[2])
        except (ValueError, IndexError, TypeError):
             raise ValueError(f"Wing '{wing_data.get('name')}' has invalid position format. Expected [x, y, z].")

        # Validate and wrap ai_goals
        if 'ai_goals' in wing_data:
            goals_raw = str(wing_data['ai_goals']).strip()
            # FSIF 2.2: Reject explicit ( goals ... ) wrapper
            cleaned = '\n'.join([line.split(';')[0] for line in goals_raw.splitlines()]).strip()
            if cleaned:
                if cleaned.startswith('( goals') or cleaned.startswith('(goals'):
                    raise ValueError(f"Wing '{wing_data.get('name')}' ai_goals must NOT be wrapped in '( goals ... )'.")
                wing_data['ai_goals'] = f"( goals\n{goals_raw}\n)"

        spacing = float(wing_data.get('spacing', 50.0))
        wing_ships_objs = []
        count = int(wing_data.get('count', 0))
        center_index = (count - 1) / 2.0
        
        for i in range(count):
             ship_name = f"{wing_data['name']} {i + 1}"
             ship_props = copy.deepcopy(template_base)
             
             offset = (i - center_index) * spacing
             ship_props['location'] = [cx + offset, cy, cz]
             ship_props['name'] = ship_name
             
             if ship_name == player_setup.start_ship:
                 ship_props.setdefault('flags', []).append('player-start')
             
             ship_obj = Ship(**ship_props)
             wing_ships_objs.append(ship_obj)
             self.all_ships.append(ship_obj)
        
        self.all_wings.append(Wing(ships=wing_ships_objs, **wing_data))

    def _process_ship(self, ship_data: Dict[str, Any]):
        """
        Process a standalone ship definition.
        
        Applies template inheritance if specified, normalizes subsystems and
        docking fields, and validates constraints.
        
        Args:
            ship_data: Raw ship definition dictionary.
            
        Raises:
            ValueError: If required fields are missing or logic constraints violated.
        """
        self._validate_no_player_start(ship_data.get('flags'), f"ship '{ship_data.get('name')}'")
        
        props = {}
        if 'template' in ship_data:
            if ship_data['template'] is not None and not isinstance(ship_data['template'], str):
                raise ValueError(f"Validation Error: Ship '{ship_data.get('name', 'unknown')}' must use a string reference for 'template', found {type(ship_data['template']).__name__} instead.")
            t_props = copy.deepcopy(self.templates.get(ship_data['template'], {}))
            props.update(t_props)
        props.update(ship_data)
        
        if 'location' not in props:
             raise ValueError(f"Ship '{props.get('name')}' missing required 'location'.")
        
        # Normalize custom subsystems
        subs = props.get('subsystems', {})
        if isinstance(subs, dict) and subs.get('status') == 'custom':
             raw_list = subs.get('list', [])
             valid_list = [item for item in raw_list if isinstance(item, dict) and item.get('name')]
             subs['list'] = valid_list
        
        # Normalize Docking
        alias_keys = [k for k in ('docked_with', 'docker_point', 'dockee_point') if k in ship_data]
        if alias_keys and 'dock' in ship_data:
             raise ValueError(f"Ship '{props.get('name')}' mixes 'dock' block with alias keys {alias_keys}.")
        
        dock_src = props.get('dock')
        if isinstance(dock_src, dict):
            props['docked_with'] = dock_src.get('with')
            props['docker_point'] = dock_src.get('docker_point')
            props['dockee_point'] = dock_src.get('dockee_point')

        # Validate and wrap ai_goals
        if 'ai_goals' in props:
            goals_raw = str(props['ai_goals']).strip()
            # FSIF 2.2: Reject explicit ( goals ... ) wrapper
            cleaned = '\n'.join([line.split(';')[0] for line in goals_raw.splitlines()]).strip()
            if cleaned:
                if cleaned.startswith('( goals') or cleaned.startswith('(goals'):
                    raise ValueError(f"Ship '{props.get('name')}' ai_goals must NOT be wrapped in '( goals ... )'.")
                props['ai_goals'] = f"( goals\n{goals_raw}\n)"

        props.pop('template', None)
        props.pop('dock', None)
            
        self.all_ships.append(Ship(**props))

    def _load_mission_flow(self) -> Dict[str, Any]:
        """
        Load mission flow components (fiction_viewer, events, goals, messages, briefings).

        Also extracts the optional fiction_viewer filename from mission_flow.

        Calculates briefing cameras for each stage.
        
        Returns:
            Dict containing parsed lists of events, goals, messages, briefing objects,
            and the optional fiction_viewer filename.
        """
        flow = self.data.get('mission_flow', {})

        fiction_viewer = flow.get('fiction_viewer')

        events = [Event(**e) for e in flow.get('events', [])]
        
        goals = []
        for g in flow.get('goals', []):
             if 'message' not in g:
                 raise ValueError(f"Goal '{g.get('name')}' missing required 'message'.")
             goals.append(Goal(**g))
        
        messages = [Message(**m) for m in flow.get('messages', [])]
        
        # Briefing
        briefing_raw = flow.get('briefing', {})
        for st in briefing_raw.get('stages', []):
             new_icons = []
             for ic in st.get('icons', []):
                 typ_str = ic.get('type')
                 if not typ_str: raise ValueError("Briefing icon missing type.")
                 rid = brief_types.parse_icon_type(typ_str)
                 ic_data = dict(ic)
                 ic_data['type_id'] = rid
                 ic_data['type'] = brief_types.canonical_name_for_id(rid)
                 new_icons.append(BriefingIcon(**ic_data))
             st['icons'] = new_icons 
             
             self._calculate_briefing_camera(st, new_icons)
        
        briefing = Briefing(**briefing_raw)
        debriefing = Debriefing(**flow.get('debriefing', {}))
        command_briefing = CommandBriefing(**flow.get('command_briefing', {}))
        
        return {
            'fiction_viewer': fiction_viewer,
            'events': events,
            'goals': goals,
            'messages': messages,
            'briefing': briefing,
            'debriefing': debriefing,
            'command_briefing': command_briefing
        }

    def _calculate_briefing_camera(self, stage_data: Dict, icons: List[BriefingIcon]):
         """
         Calculate the optimal camera position and orientation to view a set of icons.
         
         The calculation uses a tight bounding box around all icons, constrained by the FSO briefing camera aspect ratio (2.5) and FOV (45 degrees).
         
         Args:
             stage_data: The briefing stage dictionary to update with 'camera_pos' and 'camera_orient'.
             icons: List of BriefingIcon objects in this stage.
         """
         if icons:
             # 1. Find the extent of the points (Tight Bounding Box)
             x_values = [ic.pos[0] for ic in icons]
             z_values = [ic.pos[2] for ic in icons]
             
             x_min = min(x_values)
             x_max = max(x_values)
             z_min = min(z_values)
             z_max = max(z_values)
             
             delta_x = x_max - x_min
             delta_z = z_max - z_min
             
             center_x = (x_min + x_max) / 2.0
             center_z = (z_min + z_max) / 2.0
             
             cam_h = calculate_briefing_camera_height(delta_x, delta_z)
             
             stage_data['camera_pos'] = [center_x, cam_h, center_z]
             stage_data['camera_orient'] = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0]
         else:
             stage_data['camera_pos'] = [0.0, 2000.0, 0.0]
             stage_data['camera_orient'] = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0]

    def _process_reinforcements(self) -> List[Reinforcement]:
        """
        Validate and link reinforcement definitions to mission entities.
        
        Injects the 'reinforcement' flag into the referenced ships and wings.
        
        Returns:
            List of Reinforcement objects.
            
        Raises:
            ValueError: If a reinforcement references a non-existent ship/wing.
        """
        reinforcements = []
        name_to_wing = {w.name: w for w in self.all_wings}
        name_to_ship = {s.name: s for s in self.all_ships}
        entities = self.data.get('entities', {})
        seen = set()
        
        # Wings
        for item in entities.get('reinforcement_wings', []):
            n = str(item.get('name', '')).strip()
            if not n or n in seen: continue
            
            wing_obj = name_to_wing.get(n)
            if not wing_obj: raise ValueError(f"Unknown reinforcement wing '{n}'")
            
            if 'reinforcement' not in [x.lower() for x in wing_obj.flags]:
                wing_obj.flags.append('reinforcement')
                
            reinforcements.append(Reinforcement(**item))
            seen.add(n)
            
        # Ships
        for item in entities.get('reinforcement_ships', []):
            n = str(item.get('name', '')).strip()
            if not n or n in seen: continue
            
            s_obj = name_to_ship.get(n)
            if not s_obj: raise ValueError(f"Unknown reinforcement ship '{n}'")
            
            in_wing = any(s_obj in w.ships for w in self.all_wings)
            if in_wing: raise ValueError(f"Reinforcement ship '{n}' is part of a wing.")

            if 'reinforcement' not in [x.lower() for x in s_obj.flags]:
                s_obj.flags.append('reinforcement')
                
            reinforcements.append(Reinforcement(**item))
            seen.add(n)
            
        return reinforcements

    def _load_audio(self) -> AudioSettings:
        audio_src = self.data.get('audio', {})
        if isinstance(audio_src, dict):
            return AudioSettings(**audio_src)
        return AudioSettings()

    def _validate_no_player_start(self, flags_list, context):
        """
        Ensure 'player-start' flag is not manually specified.
        
        This flag is managed automatically by the player_setup section.
        
        Args:
            flags_list: List of flags to check.
            context: Context description for error message.
            
        Raises:
            ValueError: If 'player-start' is found in the list.
        """
        if not flags_list or not isinstance(flags_list, list): return
        for f in flags_list:
            if str(f).strip().lower() == 'player-start':
                raise ValueError(f"Manual usage of 'player-start' flag is forbidden on {context}.")


def load_mission_from_fsif(fsif_path: str) -> Mission:
    """Wrapper for backward compatibility."""
    loader = MissionLoader(fsif_path)
    return loader.load()
