# mission_loader.py
# Parses YAML, hydrates with defaults, and expands abstractions.

import yaml
import copy
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from data_models import (
    Mission, Ship, Wing, Environment, MissionInfo, PlayerSetup,
    Event, Goal, Message, Reinforcement, JumpNode,
    Briefing, Debriefing, CommandBriefing, BriefingIcon,
    AudioSettings
)
import briefing_icon_types as brief_types
from common.utils import calculate_briefing_camera_height

logger = logging.getLogger(__name__)


class MissionLoader:
    def __init__(self, fsif_path: str):
        self.fsif_path = Path(fsif_path)
        self.data: Dict[str, Any] = {}
        self.fsif_version: Optional[str] = None
        self.root_node: Optional[yaml.Node] = None
        
        # Intermediate state
        self.templates: Dict[str, Any] = {}
        self.all_ships: List[Ship] = []
        self.all_wings: List[Wing] = []

    def load(self) -> Mission:
        """Main execution method."""
        self._read_yaml()
        self._validate_version()
        self._validate_fsif_schema()
        self._check_required_sections()
        
        # Load sections
        mission_info = self._load_mission_info()
        environment = self._load_environment(mission_info) # updates flags in mission_info
        player_setup = self._load_player_setup()
        
        self._load_entities(player_setup)
        
        flow_data = self._load_mission_flow()
        
        # Other top-level
        entities_data = self.data.get('entities', {})
        jump_nodes = [
            JumpNode(**jn)
            for jn in self._as_list(entities_data.get('jump_nodes'), 'entities.jump_nodes')
        ]

        # Resolve string orientation targets to facing matrices now that all
        # entity positions (ships, wings, jump nodes, waypoints) are known.
        self._resolve_orientation_targets(jump_nodes)

        reinforcements = self._process_reinforcements()
        audio = self._load_audio()

        # Generate conversion timestamps (internal metadata, never authored in FSIF)
        now = datetime.now().strftime('%m/%d/%y at %H:%M:%S')

        # Construct Mission
        return Mission(
            mission_info=mission_info,
            environment=environment,
            player_setup=player_setup,
            ships=self.all_ships,
            wings=self.all_wings,
            waypoints=self._as_mapping(
                self.data.get('entities', {}).get('waypoints'), 'entities.waypoints'
            ),
            events=flow_data['events'],
            goals=flow_data['goals'],
            messages=flow_data['messages'],
            briefing=flow_data['briefing'],
            debriefing=flow_data['debriefing'],
            command_briefing=flow_data['command_briefing'],
            fiction_viewer=flow_data['fiction_viewer'],
            reinforcements=reinforcements,
            jump_nodes=jump_nodes,
            audio=audio,
            created=now,
            modified=now,
        )

    def _read_yaml(self):
        with open(self.fsif_path, 'r', encoding='utf-8') as f:
            raw_yaml = f.read()

        try:
            loaded = yaml.safe_load(raw_yaml)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML in FSIF file '{self.fsif_path}': {e}"
            ) from e

        if loaded is None:
            loaded = {}

        if not isinstance(loaded, dict):
            raise ValueError(
                f"FSIF root document must be a YAML mapping/object, "
                f"got {type(loaded).__name__!r}. "
                f"Check that the file starts with top-level key/value pairs "
                f"(e.g. 'fsif_version: \"1.0\"') rather than a list or scalar."
            )

        self.data = loaded

        # Compose once from the same in-memory YAML text so downstream
        # validators can inspect scalar styles without re-opening the file.
        try:
            self.root_node = yaml.compose(raw_yaml)
        except yaml.YAMLError as e:
            logger.warning(
                "Could not compose YAML root node for scalar-style validation "
                "(safe_load succeeded, so the file is valid): %s", e
            )
            self.root_node = None

    def _validate_version(self):
        """
        Validate the 'fsif_version' field.
        
        Currently accepted FSIF version: '1.0'.
        
        Raises:
            ValueError: If 'fsif_version' is missing, malformed, or unsupported.
        """
        version_str = self.data.get('fsif_version')
        if not isinstance(version_str, str) or not version_str.strip():
            raise ValueError("fsif_version is required and must be the exact string '1.0'.")
        version_str = version_str.strip()
        if version_str != '1.0':
            raise ValueError(
                f"Unsupported fsif_version '{version_str}'. The current converter accepts FSIF version '1.0' only."
            )
        self.fsif_version = version_str

    def _validate_fsif_schema(self):
        """
        Deep strict validation of the raw FSIF document against the current
        supported schema (FSIFDocument Pydantic model).

        All nested input models use extra='forbid', so any unknown or renamed
        keys are caught here and reported as schema errors.

        Must be called AFTER _validate_version() so that unsupported FSIF
        versions fail fast with a simple version error rather than a wall of
        Pydantic field errors caused by incompatible field names.

        Raises:
            ValueError: If any field in the document violates the schema.
        """
        from data_models import FSIFDocument
        from pydantic import ValidationError
        try:
            FSIFDocument(**self.data)
        except ValidationError as e:
            raise ValueError(f"FSIF document validation error:\n{e}")

    def _check_required_sections(self):
        required = ['mission_info', 'environment', 'player_setup', 'entities', 'mission_flow']
        for sec in required:
            if sec not in self.data:
                raise ValueError(f"Missing required top-level section: '{sec}'.")

    def _load_mission_info(self) -> MissionInfo:
        """
        Parse and validate the 'mission_info' section.

        Returns:
            MissionInfo: Populated mission info object.
            
        Raises:
            ValueError: If 'name' is missing.
        """
        mission_info_data = self.data.get('mission_info', {})
        if 'name' not in mission_info_data:
            raise ValueError("mission_info.name is required.")
        
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
        # Work on a deep copy so that loader normalization (asteroid field
        # bounds -> min_vec/max_vec, default variants injection, etc.) does not
        # mutate the raw YAML document held in self.data.
        env_data = copy.deepcopy(self.data.get('environment', {}))

        ambient_light_level = env_data.get('ambient_light_level')
        if not isinstance(ambient_light_level, list):
            raise ValueError(
                "FSIF requires environment.ambient_light_level to be authored as [red, green, blue]."
            )
        
        # Nebula Normalization
        neb_src = env_data.get('nebula')
        if neb_src and isinstance(neb_src, dict):

            if neb_src.get('enabled'):
                 # Flags injection
                 flags = mission_info.flags
                 if not any(str(x).strip().lower() == 'fullneb' for x in flags):
                     flags.append('fullneb')
                 
                 mission_info.flags = flags # Update model
        
        # Asteroid Field Normalization
        #   Authored FSIF key  -> internal AsteroidField field
        #   object_type        -> object_type  ('asteroid' | 'debris')
        #   behavior           -> behavior     ('active'   | 'passive')
        af_src = env_data.get('asteroid_field')
        if af_src and isinstance(af_src, dict):
            object_type = str(af_src.get('object_type', 'asteroid')).lower()
            behavior = str(af_src.get('behavior', 'passive')).lower()

            # Enforce constraint: a debris field cannot be active.
            if object_type != 'asteroid' and behavior == 'active':
                logger.warning(f"[WARNING] Debris field cannot be active; coercing to passive.")
                behavior = 'passive'

            # Map bounds to min_vec/max_vec
            if 'bounds' in af_src and isinstance(af_src['bounds'], dict):
                b = af_src['bounds']
                if 'min' in b: af_src['min_vec'] = b['min']
                if 'max' in b: af_src['max_vec'] = b['max']

            # Write normalised strings back.
            af_src['object_type'] = object_type
            af_src['behavior'] = behavior

            # Apply object_type-specific defaults for object_variants when the author
            # omitted the field (None) or did not provide it at all (key absent).
            # An explicitly authored empty list is preserved so the validator can
            # produce an actionable error message for it.
            authored_variants = af_src.get('object_variants')
            if authored_variants is None:
                from common import fs_data as _fs_data
                if object_type == 'debris':
                    af_src['object_variants'] = list(_fs_data.DEBRIS_FIELD_VARIANTS)
                else:
                    af_src['object_variants'] = list(_fs_data.ASTEROID_FIELD_VARIANTS)

            # Cleanup source for strict model
            af_src.pop('bounds', None)

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
        # Normalize optional mapping/list sub-sections so that explicit YAML
        # `null` values are treated identically to omitted keys.
        # Deep-copy so that template dicts are independent of self.data —
        # wing expansion mutates ship_props derived from these dicts, and we
        # want self.data['entities']['ship_templates'] to stay authored-clean.
        self.templates = copy.deepcopy(
            self._as_mapping(entities.get('ship_templates'), 'entities.ship_templates')
        )

        # Forbidden template fields (arrival/departure/dock/orientation/etc.) are
        # already rejected by ShipTemplateInput(extra='forbid') during
        # _validate_fsif_schema(), so only the player-start flag needs checking here.
        for name, template in self.templates.items():
            self._validate_no_player_start(template.get('flags'), f"template '{name}'")

        # Expand Wings
        for wing_data in self._as_list(entities.get('wings'), 'entities.wings'):
            self._process_wing(wing_data, player_setup)

        # Expand Standalone Ships
        for ship_data in self._as_list(entities.get('ships'), 'entities.ships'):
            self._process_ship(ship_data)

    def _normalize_initial_orders(self, entity_name: str, raw_orders_str: str) -> str:
        """
        Validates and wraps AI goals (initial_orders).
        """
        goals_raw = str(raw_orders_str).strip()
        # Reject explicit ( goals ... ) wrapper; FSIF expects bare SEXP operators
        cleaned = '\n'.join([line.split(';')[0] for line in goals_raw.splitlines()]).strip()
        if cleaned:
            if cleaned.startswith('( goals') or cleaned.startswith('(goals'):
                raise ValueError(f"{entity_name} initial_orders must NOT be wrapped in '( goals ... )'.")
            return f"( goals\n{goals_raw}\n)"
        return raw_orders_str

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
        # Work on a local deep copy so that normalization (e.g. wrapping
        # initial_orders) does not mutate the raw YAML dict in self.data.
        wing_data = copy.deepcopy(wing_data)

        if 'count' not in wing_data:
            raise ValueError(f"Wing '{wing_data.get('name')}' missing required 'count'.")
        
        tmpl_name = wing_data.get('template')
        if tmpl_name is not None and not isinstance(tmpl_name, str):
            raise ValueError(f"Validation Error: Wing '{wing_data.get('name', 'unknown')}' must use a string reference for 'template', found {type(tmpl_name).__name__} instead.")
            
        if not tmpl_name or tmpl_name not in self.templates:
            raise ValueError(f"Wing '{wing_data.get('name')}' must reference a valid template.")
        
        template_base = self.templates[tmpl_name]
        
        if 'position' not in wing_data:
             raise ValueError(f"Wing '{wing_data.get('name')}' must define 'position: [x, y, z]'.")

        try:
            raw_pos = wing_data['position']
            if len(raw_pos) < 3: raise ValueError
            cx, cy, cz = float(raw_pos[0]), float(raw_pos[1]), float(raw_pos[2])
        except (ValueError, IndexError, TypeError):
             raise ValueError(f"Wing '{wing_data.get('name')}' has invalid position format. Expected [x, y, z].")

        # Validate and wrap initial_orders
        orders_key = 'initial_orders' if 'initial_orders' in wing_data else None
        if orders_key:
            wing_data[orders_key] = self._normalize_initial_orders(
                f"Wing '{wing_data.get('name')}'",
                wing_data[orders_key]
            )

        spacing = float(wing_data.get('member_spacing', 50.0))
        wing_ships_objs = []
        count = int(wing_data.get('count', 0))
        center_index = (count - 1) / 2.0

        # Wing-level orientation: if authored, it is applied to every member.
        # Templates are now forbidden from carrying orientation, so the only
        # way a wing member can have a non-identity orientation at spawn time
        # is through this wing-level field.
        # The value may be a 9-float matrix OR a string naming an object to face.
        wing_orientation = wing_data.get('orientation')
        wing_orient_is_target = isinstance(wing_orientation, str)

        for i in range(count):
             ship_name = f"{wing_data['name']} {i + 1}"
             ship_props = copy.deepcopy(template_base)
             
             offset = (i - center_index) * spacing
             ship_props['position'] = [cx + offset, cy, cz]
             ship_props['name'] = ship_name

             # Apply wing orientation to every member when authored.
             if wing_orientation is not None:
                 if wing_orient_is_target:
                     # String target: store for post-expansion resolution;
                     # identity orientation placeholder is used until resolved.
                     ship_props['orientation_target'] = wing_orientation
                 else:
                     ship_props['orientation'] = wing_orientation

             # Wing members must have arrival_cue '( false )' in #Objects so
             # that the individual ship entries do not trigger independent
             # arrivals.  The wing-level arrival_cue in #Wings is authoritative
             # and controls when the wing (and therefore its members) spawns.
             # Templates are forbidden from authoring arrival_cue, so no
             # authored value is ever overridden here.
             ship_props['arrival_cue'] = '( false )'
             
             if ship_name == player_setup.start_ship:
                 ship_props.setdefault('flags', []).append('player-start')
             
             ship_obj = Ship(**ship_props)
             wing_ships_objs.append(ship_obj)
             self.all_ships.append(ship_obj)

        # When wing orientation is a string target, move it to orientation_target
        # on the Wing so the validator advisory can detect deliberate facing,
        # and remove the raw string from the orientation key (Wing.orientation
        # expects a 9-float list or None).
        if wing_orient_is_target:
            wing_data['orientation_target'] = wing_orientation
            del wing_data['orientation']

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
        # Work on a local deep copy so that normalization (subsystem list
        # filtering, dock expansion) does not mutate the raw YAML dict in
        # self.data.
        ship_data = copy.deepcopy(ship_data)

        self._validate_no_player_start(ship_data.get('flags'), f"ship '{ship_data.get('name')}'")
        
        ship_props = {}
        if 'template' in ship_data:
            if ship_data['template'] is not None and not isinstance(ship_data['template'], str):
                raise ValueError(f"Validation Error: Ship '{ship_data.get('name', 'unknown')}' must use a string reference for 'template', found {type(ship_data['template']).__name__} instead.")
            if isinstance(ship_data['template'], str) and ship_data['template'] not in self.templates:
                raise ValueError(
                    f"Ship '{ship_data.get('name', 'unknown')}' references unknown template "
                    f"'{ship_data['template']}'. "
                    f"Check that the template name is defined in entities.ship_templates."
                )
            template_props = copy.deepcopy(self.templates.get(ship_data['template'], {}))
            ship_props.update(template_props)
        ship_props.update(ship_data)
        
        if 'position' not in ship_props:
             raise ValueError(f"Ship '{ship_props.get('name')}' missing required 'position'.")
        
        # Normalize custom subsystems
        subs = ship_props.get('subsystems', {})
        if isinstance(subs, dict) and subs.get('status') == 'custom':
             raw_list = subs.get('list', [])
             valid_list = [item for item in raw_list if isinstance(item, dict) and item.get('name')]
             subs['list'] = valid_list
        
        # Normalize Docking
        dock_src = ship_props.get('dock')
        if isinstance(dock_src, dict):
            ship_props['docked_with'] = dock_src.get('dockee')
            ship_props['docker_point'] = dock_src.get('docker_point')
            ship_props['dockee_point'] = dock_src.get('dockee_point')

        # Validate and wrap initial_orders
        orders_key = 'initial_orders' if 'initial_orders' in ship_props else None
        if orders_key:
            ship_props[orders_key] = self._normalize_initial_orders(
                f"Ship '{ship_props.get('name')}'",
                ship_props[orders_key]
            )

        ship_props.pop('template', None)
        ship_props.pop('dock', None)

        # If orientation was authored as a string (target name to face), move it
        # to orientation_target so the runtime Ship keeps identity orientation as
        # a placeholder; the post-expansion _resolve_orientation_targets pass will
        # compute and assign the real matrix once all positions are known.
        orient_val = ship_props.get('orientation')
        if isinstance(orient_val, str):
            ship_props['orientation_target'] = orient_val
            del ship_props['orientation']

        self.all_ships.append(Ship(**ship_props))

    def _load_mission_flow(self) -> Dict[str, Any]:
        """
        Load mission flow components (fiction_viewer, events, goals, messages, briefings).

        Also extracts the optional fiction_viewer filename from mission_flow.

        Calculates briefing cameras for each stage.
        
        Returns:
            Dict containing parsed lists of events, goals, messages, briefing objects,
            and the optional fiction_viewer filename.
        """
        mission_flow_raw = self.data.get('mission_flow', {})

        fiction_viewer = mission_flow_raw.get('fiction_viewer')

        # Normalize optional collections: explicit YAML `null` is treated the
        # same as an omitted key (empty list/mapping) rather than crashing.
        events = [
            Event(**e)
            for e in self._as_list(mission_flow_raw.get('events'), 'mission_flow.events')
        ]

        goals = []
        for g in self._as_list(mission_flow_raw.get('goals'), 'mission_flow.goals'):
             if 'objective_text' not in g:
                 raise ValueError(f"Goal '{g.get('name')}' missing required 'objective_text'.")
             goals.append(Goal(**g))

        messages = [
            Message(**m)
            for m in self._as_list(mission_flow_raw.get('messages'), 'mission_flow.messages')
        ]

        # Briefing — normalize both the top-level mapping and the stages list
        # so that `briefing: null` or `briefing: {stages: null}` both yield an
        # empty Briefing rather than an AttributeError.
        # Deep-copy so that we can safely replace icon dicts with BriefingIcon
        # objects and inject camera fields into stage dicts without mutating
        # the raw YAML document held in self.data.
        briefing_raw = copy.deepcopy(self._as_mapping(mission_flow_raw.get('briefing'), 'mission_flow.briefing'))
        briefing_stages = self._as_list(
            briefing_raw.get('stages'), 'mission_flow.briefing.stages'
        )
        for st in briefing_stages:
             new_icons = []
             for ic in self._as_list(st.get('icons'), 'mission_flow.briefing.stages[*].icons'):
                 typ_str = ic.get('icon_type')
                 if not typ_str: raise ValueError("Briefing icon missing icon_type.")
                 rid = brief_types.parse_icon_type(typ_str)
                 ic_data = dict(ic)
                 ic_data['type_id'] = rid
                 ic_data['icon_type'] = brief_types.canonical_name_for_id(rid)
                 # Preserve whether the author explicitly wrote display_class.
                 ic_data['display_class_authored'] = 'display_class' in ic
                 new_icons.append(BriefingIcon(**ic_data))
             st['icons'] = new_icons

             self._calculate_briefing_camera(st, new_icons)

        briefing_raw['stages'] = briefing_stages
        briefing = Briefing(**briefing_raw)

        debriefing = Debriefing(
            **self._as_mapping(mission_flow_raw.get('debriefing'), 'mission_flow.debriefing')
        )
        command_briefing = CommandBriefing(
            **self._as_mapping(mission_flow_raw.get('command_briefing'), 'mission_flow.command_briefing')
        )
        
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
             x_values = [ic.map_position[0] for ic in icons]
             z_values = [ic.map_position[2] for ic in icons]
             
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
        for item in self._as_list(
            entities.get('reinforcement_wings'), 'entities.reinforcement_wings'
        ):
            n = str(item.get('name', '')).strip()
            if not n: continue
            if n in seen:
                raise ValueError(f"Duplicate reinforcement entry found for '{n}'. Each ship or wing can only be listed as a reinforcement once.")
            
            wing_obj = name_to_wing.get(n)
            if not wing_obj: raise ValueError(f"Unknown reinforcement wing '{n}'")
            
            if 'reinforcement' not in [x.lower() for x in wing_obj.flags]:
                wing_obj.flags.append('reinforcement')
                
            reinforcements.append(Reinforcement(**item))
            seen.add(n)
            
        # Ships
        for item in self._as_list(
            entities.get('reinforcement_ships'), 'entities.reinforcement_ships'
        ):
            n = str(item.get('name', '')).strip()
            if not n: continue
            if n in seen:
                raise ValueError(f"Duplicate reinforcement entry found for '{n}'. Each ship or wing can only be listed as a reinforcement once.")
            
            s_obj = name_to_ship.get(n)
            if not s_obj: raise ValueError(f"Unknown reinforcement ship '{n}'")
            
            in_wing = any(s_obj in w.ships for w in self.all_wings)
            if in_wing: raise ValueError(f"Reinforcement ship '{n}' is part of a wing.")

            if 'reinforcement' not in [x.lower() for x in s_obj.flags]:
                s_obj.flags.append('reinforcement')
                
            reinforcements.append(Reinforcement(**item))
            seen.add(n)
            
        return reinforcements

    def _resolve_orientation_targets(self, jump_nodes: List[JumpNode]):
        """Resolve string ``orientation_target`` values to computed facing matrices.

        Called after all entities (ships, wings) are expanded and jump nodes are
        built, so every position in the mission is known.

        Builds a name → position lookup from:
        - All ships (standalone + wing members, identified by name).
        - Wings (by wing name → centroid position).
        - Jump nodes (by jump node name).
        - Waypoint points (by ``"PathName:N"`` 1-based index notation).

        For each ship or wing member with ``orientation_target`` set, computes a
        facing matrix via :func:`common.utils.compute_facing_orientation` and
        assigns it to ``ship.orientation``.  The ``orientation_target`` field is
        left intact so the validator can detect deliberate facing intent.

        Raises:
            ValueError: If a target name is not found, or if source and target
                positions are coincident (zero-length forward vector).
        """
        from common.utils import compute_facing_orientation

        # ── Build target-name → position lookup ──────────────────────────────
        target_positions: Dict[str, Any] = {}

        # Ships (standalone + wing members)
        for s in self.all_ships:
            target_positions[s.name] = s.position

        # Wings by wing name → centroid
        for w in self.all_wings:
            if w.position is not None:
                centroid = w.position
            elif w.ships:
                centroid = w.ships[0].position
            else:
                continue
            target_positions[w.name] = centroid

        # Jump nodes
        for jn in jump_nodes:
            target_positions[jn.name] = jn.position

        # Waypoints: "PathName:N" (1-based index)
        waypoints_raw = self._as_mapping(
            self.data.get('entities', {}).get('waypoints'), 'entities.waypoints'
        )
        for path_name, points in waypoints_raw.items():
            if not isinstance(points, list):
                continue
            for idx, pt in enumerate(points, start=1):
                target_positions[f"{path_name}:{idx}"] = pt

        # Sorted for stable error messages
        all_target_names_sorted = sorted(target_positions.keys())

        def resolve_one(entity_name: str, entity_pos, target_name: str) -> List[float]:
            if target_name not in target_positions:
                raise ValueError(
                    f"orientation_target '{target_name}' referenced by '{entity_name}' "
                    f"was not found. Valid target names: "
                    f"{', '.join(all_target_names_sorted)}"
                )
            target_pos = target_positions[target_name]
            try:
                return compute_facing_orientation(entity_pos, target_pos)
            except ValueError as e:
                raise ValueError(
                    f"Cannot compute facing orientation for '{entity_name}' "
                    f"toward target '{target_name}': {e}"
                ) from e

        # ── Resolve ships (standalone + wing members) ─────────────────────────
        for s in self.all_ships:
            if s.orientation_target is None:
                continue
            matrix = resolve_one(s.name, s.position, s.orientation_target)
            s.orientation = matrix

        # ── Validate wing-level orientation_target (members already resolved) ─
        # The per-member matrices are computed above.  Here we just confirm the
        # wing's own orientation_target also resolves, so any typo in the target
        # name is caught at load time with a wing-level error message.
        for w in self.all_wings:
            if w.orientation_target is None:
                continue
            if w.orientation_target not in target_positions:
                raise ValueError(
                    f"orientation_target '{w.orientation_target}' referenced by "
                    f"wing '{w.name}' was not found. Valid target names: "
                    f"{', '.join(all_target_names_sorted)}"
                )

    def _load_audio(self) -> AudioSettings:
        audio_src = self.data.get('audio', {})
        if isinstance(audio_src, dict):
            return AudioSettings(**audio_src)
        return AudioSettings()

    @staticmethod
    def _as_list(value: Any, field_path: str) -> list:
        """Normalize an optional FSIF list field.

        - ``None`` (explicit YAML ``null`` or omitted key) → empty list.
        - A proper ``list`` → returned as-is.
        - Any other type → ``ValueError`` with a clear field-path message.

        Using this helper instead of bare ``or []`` ensures that an author who
        accidentally writes a scalar or mapping where a list is expected gets a
        clear error rather than a generic ``TypeError`` deep inside the loader.
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        raise ValueError(
            f"FSIF field '{field_path}' must be a list (or null/omitted), "
            f"got {type(value).__name__!r}: {value!r}"
        )

    @staticmethod
    def _as_mapping(value: Any, field_path: str) -> dict:
        """Normalize an optional FSIF mapping field.

        - ``None`` (explicit YAML ``null`` or omitted key) → empty dict.
        - A proper ``dict`` → returned as-is.
        - Any other type → ``ValueError`` with a clear field-path message.
        """
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        raise ValueError(
            f"FSIF field '{field_path}' must be a mapping (or null/omitted), "
            f"got {type(value).__name__!r}: {value!r}"
        )

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


def load_mission_with_yaml_root(fsif_path: str) -> Tuple[Mission, Optional[yaml.Node]]:
    """
    Load a mission and return both the hydrated Mission object and the composed
    YAML root node (if available).
    """
    loader = MissionLoader(fsif_path)
    mission = loader.load()
    return mission, loader.root_node
