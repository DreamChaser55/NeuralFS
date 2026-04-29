# fs2_writer.py
# Writes the hydrated Mission object to a valid.fs2 file.

import textwrap
import logging
from data_models import Mission, DEFAULT_ORIENTATION, pack_ambient_light_rgb
from utils import calculate_briefing_camera_height
import fs_flags_constants
import fs_data
import math

logger = logging.getLogger(__name__)


from typing import Optional

class FS2Writer:
    def __init__(self, mission: Mission, output_path: str):
        self.mission = mission
        self.output_path = output_path
        self.file = None
        self._brief_icon_id = 1

    def _write(self, text: str):
        if self.file is None:
            raise RuntimeError("FS2 output file is not open for writing.")
        self.file.write(text + '\n')

    def _sanitize_xstr_text(self, text: str) -> str:
        s = str(text) if text is not None else ""
        s = s.replace('\r\n', '\n').replace('\r', '\n').replace('\n', ' ')
        # Escape backslashes first, then quotes
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        return s.strip()

    def _write_xstr(self, text: str):
        return f'XSTR("{self._sanitize_xstr_text(text)}", -1)'

    def _format_vector(self, vec):
        if vec is None:
            x, y, z = 0.0, 0.0, 0.0
        else:
            x, y, z = float(vec[0]), float(vec[1]), float(vec[2])
        return f'{x:.6f}, {y:.6f}, {z:.6f}'

    def _format_matrix(self, mat):
        def _flatten(m):
            if m is None:
                return None
            # Nested 3x3
            if len(m) == 3 and isinstance(m[0], (list, tuple)):
                return [m[0][0], m[0][1], m[0][2],
                        m[1][0], m[1][1], m[1][2],
                        m[2][0], m[2][1], m[2][2]]
            # Flat
            return list(m)

        vals = _flatten(mat)
        if not vals or len(vals) < 9:
            vals = [
                1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, 1.0
            ]
        
        m00, m01, m02, m10, m11, m12, m20, m21, m22 = [float(x) for x in vals[:9]]

        return textwrap.indent(
            f'{m00:.6f}, {m01:.6f}, {m02:.6f},\n'
            f'{m10:.6f}, {m11:.6f}, {m12:.6f},\n'
            f'{m20:.6f}, {m21:.6f}, {m22:.6f}',
            '\t'
        )

    def _write_arrival_block(self, entity, is_wing=False):
        self._write(f'$Arrival Location: {entity.arrival_location}')
        
        arr_loc_norm = entity.arrival_location.strip().lower()
        if arr_loc_norm != "hyperspace":
            if arr_loc_norm == "docking bay":
                self._write(f'+Arrival Distance: 0')
            elif entity.arrival_distance is not None:
                self._write(f'+Arrival Distance: {entity.arrival_distance}')
            if entity.arrival_anchor:
                self._write(f'$Arrival Anchor: {entity.arrival_anchor}')
        
        if entity.arrival_delay > 0:
            # FRED uses lowercase 'd' for wings and uppercase 'D' for ships
            # This is intentional to ensure exact compatibility with FSO.
            if is_wing:
                self._write(f'+Arrival delay: {entity.arrival_delay}')
            else:
                self._write(f'+Arrival Delay: {entity.arrival_delay}')

        self._write(f'$Arrival Cue: {entity.arrival_cue}')

    def _write_departure_block(self, entity):
        self._write(f'$Departure Location: {entity.departure_location}')
        
        if entity.departure_location.strip().lower() == "docking bay":
             if entity.departure_anchor:
                 self._write(f'$Departure Anchor: {entity.departure_anchor}')
        
        self._write(f'$Departure Cue: {entity.departure_cue}')

    def write_mission(self):
        """
        Orchestrate the writing of the entire FS2 mission file.
        
        Opens the output file and calls sub-methods to write each section
        in the order expected by the FSO engine.
        """
        with open(self.output_path, 'w') as f:
            self.file = f
            self.write_mission_info()
            self.write_fiction_viewer()
            self.write_command_briefing()
            self.write_briefing()
            self.write_debriefing()
            self.write_player_setup()
            self.write_objects()
            self.write_wings()
            self.write_events()
            self.write_goals()
            self.write_waypoints()
            self.write_messages()
            self.write_reinforcements()
            self.write_environment()
            self.write_asteroid_field()
            self.write_music()
            self._write('#End')

    def write_mission_info(self):
        """
        Write the '#Mission Info' section.
        
        Includes version, metadata, flags, and global environment settings
        (fog, nebula storm, etc.).
        """
        self._write('#Mission Info\n')
        info = self.mission.mission_info
        
        self._write(f'$Version: 23.1')
        self._write(f'$Name:  {self._write_xstr(info.name)}')
        self._write(f'$Author: {info.author}')
        self._write(f'$Created: {info.created}')
        self._write(f'$Modified: {info.modified}')
        self._write(f'$Notes:\n nothing \n$End Notes:')
        self._write(f'$Mission Desc:\n {self._write_xstr(info.description)}\n$end_multi_text')

        game_type_map = {'single': 1, 'multiplayer': 2, 'training': 4}
        self._write(f'+Game Type Flags: {game_type_map.get(info.game_type, 1)}')

        # Mission flags
        flags_in = info.flags or []
        mask = 0
        unknown = []
        for f in flags_in:
            canon = fs_flags_constants.resolve_mission_flag(f)
            if canon and canon in fs_flags_constants.MISSION_FLAG_BITS:
                mask |= fs_flags_constants.MISSION_FLAG_BITS[canon]
            else:
                unknown.append(str(f))

        if unknown:
            logger.warning(f'[WARNING] [FSIF->FS2] Unknown mission flags ignored: {", ".join(unknown)}')

        self._write(f'+Flags: {mask}')
        
        env = self.mission.environment
        neb = env.nebula
        
        # Nebula specifics
        if neb.enabled:
            self._write(f'+NebAwacs: {neb.awacs:.6f}')
            self._write(f'+Storm: {neb.storm}')

        self._write('+Fog Near Mult: 1.000000')
        self._write('+Fog Far Mult: 1.000000')
 
        # Support ships
        disallow_sup = 1 if info.disallow_support_ships else 0
        self._write(f'+Disallow Support: {disallow_sup}')

        self._write('+Hull Repair Ceiling: 0.000000')
        self._write('+Subsystem Repair Ceiling: 100.000000')

        # Calculate FRED camera position
        # Find the center of the mission based on all ships, waypoints, jump nodes, and asteroid field bounds. Then calculate a suitable camera height by reusing the calculate_briefing_camera_height function.
        
        x_values = []
        y_values = []
        z_values = []
        
        # Add ships
        for ship in self.mission.ships:
            x_values.append(ship.location[0])
            y_values.append(ship.location[1])
            z_values.append(ship.location[2])
            
        # Add waypoints
        for path in self.mission.waypoints.values():
            for point in path:
                x_values.append(point[0])
                y_values.append(point[1])
                z_values.append(point[2])
                
        # Add jump nodes
        for jn in self.mission.jump_nodes:
            x_values.append(jn.position[0])
            y_values.append(jn.position[1])
            z_values.append(jn.position[2])
            
        # Add asteroid field bounds
        ast = self.mission.environment.asteroid_field
        if ast:
            x_values.extend([ast.min_vec[0], ast.max_vec[0]])
            y_values.extend([ast.min_vec[1], ast.max_vec[1]])
            z_values.extend([ast.min_vec[2], ast.max_vec[2]])

        if not x_values:
            center_x, cam_y, center_z = 0.0, 2000.0, 0.0
        else:
            x_min = min(x_values)
            x_max = max(x_values)
            y_max = max(y_values)
            z_min = min(z_values)
            z_max = max(z_values)
            
            center_x = (x_min + x_max) / 2.0
            center_z = (z_min + z_max) / 2.0
            
            delta_x = x_max - x_min
            delta_z = z_max - z_min
            
            cam_y = calculate_briefing_camera_height(delta_x, delta_z) + y_max

        self._write(f'+Viewer pos: {center_x:.6f}, {cam_y:.6f}, {center_z:.6f}')
        top_down_orient = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0]
        self._write(f'+Viewer orient:\n{self._format_matrix(top_down_orient)}')
        
        self._write(f'\n$AI Profile: {info.ai_profile}')

    def write_fiction_viewer(self):
        if not self.mission.fiction_viewer:
            return
        self._write('\n#Fiction Viewer\n')
        self._write(f'$File: {self.mission.fiction_viewer}')

    def write_command_briefing(self):
        """
        Write the '#Command Briefing' section.
        
        Emits stages with text, animation filename, and voice filename.
        """
        self._write('\n#Command Briefing\n')
        cb = self.mission.command_briefing
        stages = cb.stages
        for st in stages:
            self._write('$Stage Text:')
            self._write(f' {self._write_xstr(st.text)}')
            self._write('$end_multi_text')
            self._write(f'$Ani Filename: {st.ani}')
            self._write(f'+Wave Filename: {getattr(st, "voice_filename", None) or "none"}')
            self._write('')

    def write_briefing(self):
        """
        Write the '#Briefing' section.
        
        Emits briefing stages, including camera positioning (calculated by loader)
        and icon definitions (mapping canonical types to numeric IDs).
        """
        self._write('\n#Briefing')
        briefing = self.mission.briefing
        self._write('$start_briefing')

        stages = briefing.stages
        self._write(f'$num_stages: {len(stages)}')
        self._brief_icon_id = 1

        for stage in stages:
            self._write('$start_stage')

            self._write(f'$multi_text\n {self._write_xstr(stage.text)}\n$end_multi_text')
            self._write(f'$voice: {getattr(stage, "voice_filename", None) or "none.wav"}')

            # Determine camera and icons
            icons = stage.icons
            cam_pos = stage.camera_pos
            cam_orient = stage.camera_orient

            # FSIF 2.1: Camera orientation is calculated by the loader.
            # We simply write what is provided.
            cam_orient_use = cam_orient if cam_orient else DEFAULT_ORIENTATION

            self._write(f'$camera_pos: {self._format_vector(cam_pos)}')
            self._write(f'$camera_orient:\n{self._format_matrix(cam_orient_use)}')
            self._write(f'$camera_time: {stage.camera_time}')

            self._write(f'$num_lines: 0')
            self._write(f'$num_icons: {len(icons)}')
            self._write(f'$Flags: 0')
            self._write(f'$Formula: ( true )')

            for icon in icons:
                self._write('$start_icon')
                self._write(f'$type: {icon.type_id}')
                self._write(f'$team: {icon.team}')
                self._write(f'$class: {icon.ship_class}')
                self._write(f'$pos: {self._format_vector(icon.pos)}')
                self._write(f'$label: {self._write_xstr(icon.label)}')
                self._write(f'+id: {self._brief_icon_id}')
                self._write(f'$hlight: {1 if icon.highlighted else 0}')
                self._write(f'$mirror: 0')
                self._brief_icon_id += 1
                self._write('$multi_text\n$end_multi_text')
                self._write('$end_icon')

            self._write('$end_stage')

        self._write('$end_briefing')

    def write_debriefing(self):
        """
        Write the '#Debriefing_info' section.
        
        Emits stages with condition formulas, text, voice, and recommendations.
        """
        self._write('\n#Debriefing_info\n')
        stages = self.mission.debriefing.stages

        self._write(f'$Num stages: {len(stages)}')
        self._write('')

        for stage in stages:
            self._write(f'$Formula: {stage.condition}')

            self._write('$Multi text')
            self._write(f'    {self._write_xstr(stage.text)}')
            self._write('$end_multi_text')

            self._write(f'$Voice: {getattr(stage, "voice_filename", None) or "none.wav"}')

            self._write('$Recommendation text:')
            self._write(f'    {self._write_xstr(stage.recommendation)}')
            self._write('$end_multi_text')
            self._write('')

    def write_player_setup(self):
        """
        Write the '#Players' section.
        
        Defines the starting ship, allowed ship choices, and automatically calculates
        and emits the weapon pool based on the demands of Friendly player starting wings.
        Also calculates quantities for explicitly authored extra weapons based on maximum
        possible demands across all player wings.
        """
        self._write('\n#Players\t\t;! 1 total\n')
        setup = self.mission.player_setup
        self._write(f'$Starting Shipname: {setup.start_ship}')
        
        choices = '\n\t'.join([f'"{c.ship_class}"\t{c.count}' for c in setup.extra_ships])
        self._write(f'$Ship Choices: (\n\t{choices}\n)')
        
        # Calculate Weapon Pool automatically
        friendly_starting_wings = fs_data.PLAYER_WING_NAMES
        
        # Track raw calculated demands
        weapon_demand = {}
        
        # Track max possible capacities to satisfy 'extra_weapons'
        total_primary_banks_demand = 0
        all_secondary_bank_capacities = []
        
        for w in self.mission.wings:
            if w.name not in friendly_starting_wings:
                continue
            if not w.ships:
                continue
            if w.ships[0].team != 'Friendly':
                continue
                
            count = len(w.ships)
            ship = w.ships[0]
            
            # Primary Banks (count banks)
            total_primary_banks_demand += count * len(ship.weapons.primary)
            for p in ship.weapons.primary:
                if not p: continue
                weapon_demand[p] = weapon_demand.get(p, 0) + count
                
            # Secondary Banks (calculate missile counts from capacity and size)
            for i, sec in enumerate(ship.weapons.secondary):
                # Default capacity if ship not in tables or bank index out of bounds
                capacity = 50
                if ship.ship_class in fs_data.SHIP_SBANK_CAPACITIES:
                    caps = fs_data.SHIP_SBANK_CAPACITIES[ship.ship_class]
                    if i < len(caps):
                        capacity = caps[i]
                
                for _ in range(count):
                    all_secondary_bank_capacities.append(capacity)
                    
                if not sec: continue
                cargo_size = fs_data.WEAPON_CARGO_SIZES.get(sec, 1.0)
                missile_count = int(capacity / cargo_size)
                weapon_demand[sec] = weapon_demand.get(sec, 0) + (count * missile_count)
                
        # Process extra weapons
        for ew in setup.extra_weapons:
            if ew in fs_data.ALLOWED_PRIMARY_WEAPONS:
                weapon_demand[ew] = max(weapon_demand.get(ew, 0), total_primary_banks_demand)
            elif ew in fs_data.ALLOWED_SECONDARY_WEAPONS:
                cargo_size = fs_data.WEAPON_CARGO_SIZES.get(ew, 1.0)
                max_demand = sum(int(cap / cargo_size) for cap in all_secondary_bank_capacities)
                weapon_demand[ew] = max(weapon_demand.get(ew, 0), max_demand)
                
        # Apply 25% safety factor and cast to int
        pool_lines = []
        for w_name, w_count in sorted(weapon_demand.items()):
            safe_count = int(math.ceil(w_count * 1.25))
            pool_lines.append(f'"{w_name}"\t{safe_count}')
            
        if pool_lines:
            weapons = '\n\t'.join(pool_lines)
            self._write(f'+Weaponry Pool: (\n\t{weapons}\n)')
        else:
            self._write(f'+Weaponry Pool: (\n)')

    def write_objects(self):
        """
        Write the '#Objects' section.
        
        Emits all ships (including those expanded from wings). Ensures the
        player start ship is emitted first. Handles complex properties like
        subsystems, weapons, flags (split into +Flags/+Flags2), and pre-spawn docking.
        """
        self._write(f'\n#Objects\t\t;! {len(self.mission.ships)} total\n')
        
        player_start_ship = self.mission.player_setup.start_ship
        ordered_ships = self.mission.ships[:]
        if player_start_ship:
             for idx, s in enumerate(ordered_ships):
                 if s.name == player_start_ship:
                     if idx != 0:
                         ordered_ships.insert(0, ordered_ships.pop(idx))
                     break

        _all_names = {s.name for s in ordered_ships}

        for i, ship in enumerate(ordered_ships):
            # No manual validation needed (Pydantic handled it)
            
            self._write(f'$Name: {ship.name}\t\t;! Object #{i}')
            self._write(f'$Class: {ship.ship_class}')
            self._write(f'$Team: {ship.team}')
            self._write(f'$Location: {self._format_vector(ship.location)}')
            self._write(f'$Orientation:\n{self._format_matrix(ship.orientation)}')
            
            if ship.ai_class:
                self._write(f'+AI Class: {ship.ai_class}')

            if ship.ai_goals:
                self._write(f'$AI Goals: {ship.ai_goals}')
            
            self._write(f'$Cargo 1:  {self._write_xstr(ship.cargo)}')
            self._write(f'+Initial Velocity: {ship.initial_velocity}')
            self._write(f'+Initial Hull: {ship.initial_hull}')
            
            # Subsystems
            self._write(f'+Subsystem: Pilot')
            if ship.subsystems.status == 'custom':
                 for it in ship.subsystems.list:
                     if it.name.lower() == 'pilot': continue
                     self._write(f'+Subsystem: {it.name}')
                     damage = 100 - it.health
                     if damage > 0:
                         self._write(f'$Damage: {damage}')

            # Weapons
            weapons = ship.weapons
            def _fmt_bank_names(names):
                return " ".join([f'"{str(n).strip()}"' for n in names if str(n).strip()])

            if weapons.primary:
                self._write(f'+Primary Banks: ( {_fmt_bank_names(weapons.primary)} )')
            if weapons.secondary:
                self._write(f'+Secondary Banks: ( {_fmt_bank_names(weapons.secondary)} )')
                
                # Ammo logic
                ammo = weapons.secondary_ammo
                if ammo:
                     sanitized = []
                     for k in range(len(weapons.secondary)):
                         v = ammo[k] if k < len(ammo) else 0
                         sanitized.append(max(0, v))
                     ammo_str = " ".join(str(x) for x in sanitized)
                     self._write(f'+Sbank Ammo: ( {ammo_str} )')

            self._write_arrival_block(ship)
            self._write_departure_block(ship)
            self._write(f'$Determination: 10')

            # Flags (mapped in fs_flags_constants)

            out_flags = []
            out_flags2 = []

            def _route_flag(tok):
                bucket = fs_flags_constants.SHIP_FLAGS_BUCKET.get(tok)
                if bucket == "flags":
                    out_flags.append(str(tok))
                elif bucket == "flags2":
                    out_flags2.append(str(tok))
                else:
                    logger.warning(f'[WARNING] [FSIF->FS2] Unknown ship flag "{tok}" on {ship.name}; emitting in +Flags.')
                    out_flags.append(str(tok))

            for t in ship.flags:
                _route_flag(t)

            if out_flags:
                flags_str = " ".join([f'"{f}"' for f in out_flags])
                self._write(f'+Flags: ( {flags_str} )')
            if out_flags2:
                flags2_str = " ".join([f'"{f}"' for f in out_flags2])
                self._write(f'+Flags2: ( {flags2_str} )')

            # Ancillary
            if ship.respawn_priority > 0:
                 self._write(f'+Respawn priority: {ship.respawn_priority}')

            # Pre-spawn docking
            docked_with = ship.docked_with
            if docked_with and docked_with in _all_names:
                 self._write(f'+Docked With: {docked_with}')
                 # FS2 engine expects docking points in a reversed naming convention:
                 #  - `$Docker Point` specifies the point on the DOCKEE (the other ship).
                 #  - `$Dockee Point` specifies the point on the DOCKER (this ship).
                 # FSIF uses intuitive naming (docker_point is on the docker, dockee_point is on the dockee).
                 # Therefore, we swap them here when emitting FS2.
                 # See Documentation/fsif/converter/implementation_details.md for more details.
                 self._write(f'$Docker Point: {ship.dockee_point}')
                 self._write(f'$Dockee Point: {ship.docker_point}')
            
            # Escort
            has_escort_flag = "escort" in ship.flags
            if has_escort_flag or ship.escort_priority > 0:
                 self._write(f'+Escort priority: {ship.escort_priority}')
            
            # Destroy Before Mission
            if ship.destroy_before_mission > 0 and ship.name != player_start_ship:
                 self._write(f'+Destroy At: {ship.destroy_before_mission}')
            

            self._write("\n")

    def write_wings(self):
        """
        Write the '#Wings' section.
        
        Emits wing definitions including wave configurations, arrival/departure logic,
        and member ship references.
        """
        self._write(f'#Wings\t\t;! {len(self.mission.wings)} total\n')
        for wing in self.mission.wings:
            self._write(f'$Name: {wing.name}')
            self._write(f'$Waves: {wing.waves}')
            self._write(f'$Wave Threshold: {wing.wave_threshold}')
            self._write(f'$Special Ship: 0\t\t;! Wing Leader')

            self._write_arrival_block(wing, is_wing=True)
            self._write_departure_block(wing)
            
            ship_names = '\n'.join([f'\t"{ship.name}"' for ship in wing.ships])
            self._write(f'$Ships: (\n{ship_names}\n)')
            
            if wing.ai_goals:
                self._write(f'$AI Goals: {wing.ai_goals}')
            
            if wing.flags:
                flags_formatted = [f'"{flag}"' for flag in wing.flags]
                flags_str = " ".join(flags_formatted)
                self._write(f'+Flags: ( {flags_str} )')

            if wing.wave_delay_min is not None:
                 self._write(f'+Wave Delay Min: {wing.wave_delay_min}')
            if wing.wave_delay_max is not None:
                 self._write(f'+Wave Delay Max: {wing.wave_delay_max}')

            self._write('')

    def write_events(self):
        self._write(f'#Events\t\t;! {len(self.mission.events)} total\n')
        for event in self.mission.events:
            self._write(f'$Formula: {event.formula}')
            if event.name:
                self._write(f'+Name: {event.name}')
            if event.directive_text:
                self._write(f'+Objective:  {self._write_xstr(event.directive_text)}')
            self._write('')

    def write_goals(self):
        self._write(f'#Goals\t\t;! {len(self.mission.goals)} total\n')
        for goal in self.mission.goals:
            self._write(f'$Type: {goal.type}')
            self._write(f'+Name: {goal.name}')
            self._write(f'$MessageNew:  {self._write_xstr(goal.message)}\n$end_multi_text')
            self._write(f'$Formula: {goal.formula}\n')

    def write_waypoints(self):
        """
        Write the '#Waypoints' section.
        
        Includes both Jump Nodes (as $Jump Node) and Waypoint paths.
        """
        self._write(f'#Waypoints\t\t;! {len(self.mission.waypoints)} lists total\n')
        for node in self.mission.jump_nodes:
            self._write(f'$Jump Node: {self._format_vector(node.position)}')
            self._write(f'$Jump Node Name: {node.name}')
        
        for name, path in self.mission.waypoints.items():
            self._write(f'$Name: {name}')
            points = '\n'.join([f'\t( {self._format_vector(p)} )' for p in path])
            self._write(f'$List: (\n{points}\n)\n')

    def write_messages(self):
        self._write(f'#Messages\t\t;! {len(self.mission.messages)} total\n')
        for msg in self.mission.messages:
            self._write(f'$Name: {msg.name}')
            self._write(f'$Team: -1')
            self._write(f'$MessageNew:  {self._write_xstr(msg.message)}\n$end_multi_text')
            self._write(f'+AVI Name: <None>')
            vf = getattr(msg, "voice_filename", None)
            if vf:
                self._write(f'+Wave Name: {vf}')
            self._write('')

    def write_reinforcements(self):
        """
        Write the '#Reinforcements' section.
        
        Automatically determines reinforcement type ($Type) based on the unit
        (Support Ship vs other).
        """
        self._write(f'#Reinforcements\t\t;! {len(self.mission.reinforcements)} total\n')
        
        ship_by_name = {s.name: s for s in self.mission.ships}
        wing_names = {w.name for w in self.mission.wings}

        for reinf in self.mission.reinforcements:
            self._write(f'$Name: {reinf.name}')
            reinf_type = "Attack/Protect"
            if reinf.name in wing_names:
                pass # Default
            elif reinf.name in ship_by_name:
                cls = ship_by_name[reinf.name].ship_class.strip()
                if cls.startswith("GTS ") or cls.startswith("PVS "):
                    reinf_type = "Repair/Rearm"
            else:
                 pass # Default/Warn?

            self._write(f'$Type: {reinf_type}')
            self._write(f'$Num times: {reinf.num_times}')
            
            if reinf.arrival_delay > 0:
                self._write(f'+Arrival Delay: {reinf.arrival_delay}')
            if reinf.no_messages:
                msg_list = ' '.join([f'"{msg}"' for msg in reinf.no_messages])
                self._write(f'+No Messages: ( {msg_list} )')
            if reinf.yes_messages:
                msg_list = ' '.join([f'"{msg}"' for msg in reinf.yes_messages])
                self._write(f'+Yes Messages: ( {msg_list} )')
            self._write('')

    def write_environment(self):
        """
        Write the '#Background bitmaps' section.
        
        Handles suns, starbitmaps (planets/nebulae), and full nebula background
        configurations. Manages background suppression if full nebula is enabled.
        """
        env = self.mission.environment
        total = len(env.suns) + len(env.starbitmaps)
        
        # Nebula Background Logic
        # When full nebula is active, starbitmaps are suppressed (the volumetric nebula
        # fills the background), but suns are still emitted and visible.
        neb = env.nebula
        suppress_starbitmaps = neb.enabled
        if suppress_starbitmaps:
            total = len(env.suns)  # Only suns are emitted for fullneb; starbitmaps are suppressed
        
        self._write(f'#Background bitmaps\t\t;! {total} total')
        self._write(f'')
        self._write(f'$Num stars: 2000')
        packed_ambient_light = pack_ambient_light_rgb(env.ambient_light_level)
        self._write(f'$Ambient light level: {packed_ambient_light}')

        if neb.enabled and neb.pattern:
            self._write('')
            self._write(f'+Neb2: {neb.pattern}')
            if neb.poofs:
                poofs_joined = " ".join([f'"{str(p)}"' for p in neb.poofs])
                self._write(f'+Neb2 Poofs List: ( {poofs_joined} )')

        self._write('')
        self._write('$Bitmap List:')
        self._write('+Flags: ( "corrected angles" )')

        for s in env.suns:
            self._write(f'$Sun: {s.texture}')
            p, b, h = s.angles
            self._write(f'+Angles: {p:.6f} {b:.6f} {h:.6f}')
            self._write(f'+Scale: {s.scale:.6f}')

        if suppress_starbitmaps:
            return

        for s in env.starbitmaps:
            self._write(f'$Starbitmap: {s.texture}')
            p, b, h = s.angles
            self._write(f'+Angles: {p:.6f} {b:.6f} {h:.6f}')
            
            # Handle scale dict/float
            sx, sy = 1.0, 1.0
            if isinstance(s.scale, (int, float)):
                 sx = sy = float(s.scale)
            else:
                 sx = s.scale.get('x', 1.0)
                 sy = s.scale.get('y', sx)
            self._write(f'+ScaleX: {sx:.6f}')
            self._write(f'+ScaleY: {sy:.6f}')
            
            # Handle div dict/int
            dx, dy = 1, 1
            if isinstance(s.div, int):
                dx = dy = s.div
            else:
                dx = s.div.get('x', 1)
                dy = s.div.get('y', 1)
            self._write(f'+DivX: {dx}')
            self._write(f'+DivY: {dy}')

    def write_asteroid_field(self):
        fld = self.mission.environment.asteroid_field
        if not fld:
            return

        self._write('\n#Asteroid Fields\n')
        self._write(f'$Density: {fld.density}')
        field_type_int   = 0 if fld.type == 'active'   else 1
        debris_genre_int = 0 if fld.genre      == 'asteroid' else 1
        self._write(f'+Field Type: {field_type_int}')
        self._write(f'+Debris Genre: {debris_genre_int}')

        for t in fld.debris_types:
            self._write(f'+Field Debris Type Name: {t}')

        self._write(f'$Average Speed: {fld.average_speed:.6f}')
        self._write(f'$Minimum: {self._format_vector(fld.min_vec)}')
        self._write(f'$Maximum: {self._format_vector(fld.max_vec)}')

        if fld.type == 'active' and fld.genre == 'asteroid' and fld.targets:
            targets_joined = ' '.join([f'"{name}"' for name in fld.targets])
            self._write(f'$Asteroid Targets: ( {targets_joined} )')

        self._write('')

    def write_music(self):
        audio = self.mission.audio
        
        em = audio.mission_music # in-mission music is emitted as '$Event Music' in fs2
        bm = audio.briefing_music
        
        if not em and not bm: return
        
        self._write('\n#Music\n')
        if em: self._write(f'$Event Music: {em}')
        if bm: self._write(f'$Briefing Music: {bm}')
