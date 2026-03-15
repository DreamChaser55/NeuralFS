# fs2_writer.py
# Writes the hydrated Mission object to a valid.fs2 file.

import textwrap
from data_models import Mission, DEFAULT_ORIENTATION, DEFAULT_KAMIKAZE_DAMAGE, pack_ambient_light_rgb
import fs_flags_constants
import fs_data
import math


class FS2Writer:
    def __init__(self, mission: Mission, output_path: str, log_func=print):
        self.mission = mission
        self.output_path = output_path
        self.log_func = log_func
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
        
        a, b, c, d, e, f, g, h, i = [float(x) for x in vals[:9]]

        return textwrap.indent(
            f'{a:.6f}, {b:.6f}, {c:.6f},\n'
            f'{d:.6f}, {e:.6f}, {f:.6f},\n'
            f'{g:.6f}, {h:.6f}, {i:.6f}',
            '\t'
        )

    def _format_sexp_inline(self, sexp: str) -> str:
        return ' '.join(str(sexp).split())

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
        self._write(f'$Notes:\n{info.notes}\n$End Notes:')
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
            self.log_func(f'[WARNING] [FSIF->FS2] Unknown mission flags ignored: {", ".join(unknown)}')

        self._write(f'+Flags: {mask}')
        
        env = self.mission.environment
        neb = env.nebula
        
        # Nebula specifics
        if neb.enabled:
            self._write(f'+NebAwacs: {neb.awacs:.6f}')
            self._write(f'+Storm: {neb.storm}')

        self._write('+Fog Near Mult: 1.000000')
        self._write('+Fog Far Mult: 1.000000')
 
        disallow_sup = 1 if info.disallow_support else 0
        self._write(f'+Disallow Support: {disallow_sup}')

        self._write('+Hull Repair Ceiling: 0.000000')
        self._write('+Subsystem Repair Ceiling: 100.000000')

        self._write('+Viewer pos: 0.000000, 150.000000, -200.000000')
        self._write(f'+Viewer orient:\n{self._format_matrix(DEFAULT_ORIENTATION)}')
        
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
            self._write(f'+Wave Filename: {st.voice_filename}')
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
            self._write(f'$voice: {stage.voice_filename}')

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
                self._write(f'$class: {icon.class_}')
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

            self._write(f'$Voice: {stage.voice_filename}')

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
        friendly_starting_wings = {"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}
        
        # Track raw calculated demands
        weapon_demand = {}
        
        # Track max possible capacities to satisfy 'extra_weapons'
        total_primary_banks_demand = 0
        total_secondary_capacity_demand = 0
        
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
                
            # Secondary Banks (count capacity)
            for i, sec in enumerate(ship.weapons.secondary):
                # Default capacity if ship not in tables or bank index out of bounds
                capacity = 50
                if ship.ship_class in fs_data.SHIP_SBANK_CAPACITIES:
                    caps = fs_data.SHIP_SBANK_CAPACITIES[ship.ship_class]
                    if i < len(caps):
                        capacity = caps[i]
                
                total_secondary_capacity_demand += count * capacity
                if not sec: continue
                weapon_demand[sec] = weapon_demand.get(sec, 0) + (count * capacity)
                
        # Process extra weapons
        for ew in setup.extra_weapons:
            if ew in fs_data.ALLOWED_PRIMARY_WEAPONS:
                weapon_demand[ew] = max(weapon_demand.get(ew, 0), total_primary_banks_demand)
            elif ew in fs_data.ALLOWED_SECONDARY_WEAPONS:
                weapon_demand[ew] = max(weapon_demand.get(ew, 0), total_secondary_capacity_demand)
                
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
        
        start_name = self.mission.player_setup.start_ship
        ordered_ships = self.mission.ships[:]
        if start_name:
             for idx, s in enumerate(ordered_ships):
                 if s.name == start_name:
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
                self._write(f'$AI Goals: {self._format_sexp_inline(ship.ai_goals)}')
            
            self._write(f'$Cargo 1:  {self._write_xstr(ship.cargo_1)}')
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

            self._write(f'$Arrival Location: {ship.arrival_location}')
            
            arr_loc_norm = ship.arrival_location.strip().lower()
            if arr_loc_norm != "hyperspace":
                 if ship.arrival_distance is not None:
                     self._write(f'+Arrival Distance: {ship.arrival_distance}')
                 if ship.arrival_anchor:
                     self._write(f'$Arrival Anchor: {ship.arrival_anchor}')
            
            if ship.arrival_delay > 0:
                 self._write(f'+Arrival Delay: {ship.arrival_delay}')

            self._write(f'$Arrival Cue: {ship.arrival_cue}')
            self._write(f'$Departure Location: {ship.departure_location}')
            
            if ship.departure_location.strip().lower() == "docking bay":
                 if ship.departure_anchor:
                     self._write(f'$Departure Anchor: {ship.departure_anchor}')
            
            self._write(f'$Departure Cue: {ship.departure_cue}')
            self._write(f'$Determination: {ship.determination}')

            # Flags (mapped in fs_flags_constants)

            out_flags = []
            out_flags2 = []

            def _route_flag(tok):
                n = fs_flags_constants.normalize_flag(tok)
                bucket = fs_flags_constants.SHIP_FLAGS_BUCKET.get(n)
                if bucket == "flags":
                    out_flags.append(str(tok))
                elif bucket == "flags2":
                    out_flags2.append(str(tok))
                else:
                    self.log_func(f'[WARNING] [FSIF->FS2] Unknown ship flag "{tok}" on {ship.name}; emitting in +Flags.')
                    out_flags.append(str(tok))

            for t in ship.flags:
                _route_flag(t)
            for t in ship.flags2:
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
            dw = ship.docked_with
            if dw and dw in _all_names:
                 self._write(f'+Docked With: {dw}')
                 # FS2 engine expects docking points in a reversed naming convention:
                 #  - `$Docker Point` specifies the point on the DOCKEE (the other ship).
                 #  - `$Dockee Point` specifies the point on the DOCKER (this ship).
                 # FSIF uses intuitive naming (docker_point is on the docker, dockee_point is on the dockee).
                 # Therefore, we swap them here when emitting FS2.
                 # See Documentation/fsif/converter/implementation_details.md for more details.
                 self._write(f'$Docker Point: {ship.dockee_point}')
                 self._write(f'$Dockee Point: {ship.docker_point}')
            
            # Escort
            has_escort_flag = any(fs_flags_constants.normalize_flag(x) == "escort" for x in ship.flags)
            if has_escort_flag or ship.escort_priority > 0:
                 self._write(f'+Escort priority: {ship.escort_priority}')

            # Kamikaze
            has_kamikaze_flag = any(fs_flags_constants.normalize_flag(x) == "kamikaze" for x in ship.flags)
            if has_kamikaze_flag or ship.kamikaze_damage != DEFAULT_KAMIKAZE_DAMAGE:
                 self._write(f'+Kamikaze Damage: {ship.kamikaze_damage}')
            
            # Destroy At
            if ship.destroy_at > 0 and ship.name != start_name:
                 self._write(f'+Destroy At: {ship.destroy_at}')
            
            # Orders
            if ship.orders_accepted_mask is not None:
                 self._write(f'+Orders Accepted: {ship.orders_accepted_mask}')
            if ship.orders_accepted:
                 olist = ' '.join([f'"{str(x)}"' for x in ship.orders_accepted])
                 self._write(f'+Orders Accepted List: ( {olist} )')

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

            self._write(f'$Arrival Location: {wing.arrival_location}')
            
            if wing.arrival_location.strip().lower() != "hyperspace":
                 if wing.arrival_distance is not None:
                     self._write(f'+Arrival Distance: {wing.arrival_distance}')
                 if wing.arrival_anchor:
                     self._write(f'$Arrival Anchor: {wing.arrival_anchor}')
            
            if wing.arrival_delay > 0:
                 self._write(f'+Arrival delay: {wing.arrival_delay}')
            
            self._write(f'$Arrival Cue: {wing.arrival_cue}')
            self._write(f'$Departure Location: {wing.departure_location}')
            
            if wing.departure_location.strip().lower() == "docking bay":
                 if wing.departure_anchor:
                     self._write(f'$Departure Anchor: {wing.departure_anchor}')
            
            self._write(f'$Departure Cue: {wing.departure_cue}')
            
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
            if msg.voice_filename:
                self._write(f'+Wave Name: {msg.voice_filename}')
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
            type_emit = "Attack/Protect"
            if reinf.name in wing_names:
                pass # Default
            elif reinf.name in ship_by_name:
                cls = ship_by_name[reinf.name].ship_class.strip()
                if cls.startswith("GTS ") or cls.startswith("PVS "):
                    type_emit = "Repair/Rearm"
            else:
                 pass # Default/Warn?

            self._write(f'$Type: {type_emit}')
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
        neb = env.nebula
        suppress = False
        if neb.enabled:
            suppress = True
            total = len(env.suns)  # Only suns are emitted for fullneb, starbitmaps are suppressed
        
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

        if suppress:
            return

        for s in env.suns:
            self._write(f'$Sun: {s.texture}')
            p, b, h = s.angles
            self._write(f'+Angles: {p:.6f} {b:.6f} {h:.6f}')
            self._write(f'+Scale: {s.scale:.6f}')
            
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
        self._write(f'+Field Type: {fld.field_type}')
        self._write(f'+Debris Genre: {fld.debris_genre}')

        for t in fld.debris_types:
            self._write(f'+Field Debris Type Name: {t}')

        self._write(f'$Average Speed: {fld.average_speed:.6f}')
        self._write(f'$Minimum: {self._format_vector(fld.min_vec)}')
        self._write(f'$Maximum: {self._format_vector(fld.max_vec)}')

        if fld.field_type == 0 and fld.debris_genre == 0 and fld.targets:
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
