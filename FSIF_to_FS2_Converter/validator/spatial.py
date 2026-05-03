import math
from typing import List, Optional, Set

class SpatialChecksMixin:
    _MISSION_SCALE_RECOMMENDATION_METERS = 20_000.0

    def validate_mission_scale_recommendations(self):
        """
        Warn when authored mission geometry exceeds the recommended 20 km scale.

        This is an advisory mission-design check only. It does not fail validation.
        It covers:
        - distances between positioned mission objects (standalone ships, wing centroids, jump nodes, waypoint points)
        - authored arrival_distance values on ships and wings that reference an arrival_anchor

        Arrival location awareness:
        - "Hyperspace" (default): the authored location/position field is used directly.
        - "Docking Bay": the object's effective position is inherited from its arrival_anchor ship
          (resolved recursively, with cycle detection).
        - Any directional arrival (e.g. "Near Ship", "In front of ship"): the object is excluded
          from distance checks because it has no definite initial position.
        """
        limit_m = self._MISSION_SCALE_RECOMMENDATION_METERS
        limit_km = limit_m / 1000.0

        # Build a ship-name → Ship lookup for arrival_anchor resolution.
        ship_map = {s.name: s for s in self.mission.ships}

        def resolve_effective_position(arrival_method, arrival_anchor, own_position, visited=None):
            """
            Return the effective starting position of a ship or wing, taking arrival_method
            into account.  Returns None when the object has no definite initial position and
            should therefore be excluded from distance checks.
            """
            arr_loc = (arrival_method or "Hyperspace").strip().lower()

            if arr_loc == "hyperspace":
                return own_position

            if arr_loc == "docking bay":
                if not arrival_anchor:
                    return None  # Malformed; skip
                if visited is None:
                    visited = set()
                if arrival_anchor in visited:
                    return None  # Cycle guard
                visited.add(arrival_anchor)
                anchor_ship = ship_map.get(arrival_anchor)
                if anchor_ship is None:
                    return None  # Anchor not found; skip
                return resolve_effective_position(
                    anchor_ship.arrival_method,
                    anchor_ship.arrival_anchor,
                    anchor_ship.position,
                    visited,
                )

            # Any other directional arrival_method (e.g. "Near Ship", "In front of ship"):
            # the object spawns relative to a moving anchor — no definite initial position.
            return None

        positioned_objects = []
        distance_violations = []

        wing_member_names: Set[str] = set()
        for wing in self.mission.wings:
            for ship in wing.ships:
                wing_member_names.add(ship.name)

        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue
            eff_pos = resolve_effective_position(ship.arrival_method, ship.arrival_anchor, ship.position)
            if eff_pos is not None:
                positioned_objects.append(("Ship", ship.name, eff_pos))

        for wing in self.mission.wings:
            wing_own_position = wing.position
            if wing_own_position is None and wing.ships:
                # Defensive fallback: use the leader position if the authored wing centroid is unexpectedly unavailable.
                wing_own_position = wing.ships[0].position

            eff_pos = resolve_effective_position(wing.arrival_method, wing.arrival_anchor, wing_own_position)
            if eff_pos is not None:
                positioned_objects.append(("Wing", wing.name, eff_pos))

        for jump_node in self.mission.jump_nodes:
            positioned_objects.append(("Jump Node", jump_node.name, jump_node.position))

        for path_name, points in self.mission.waypoints.items():
            for index, point in enumerate(points, start=1):
                positioned_objects.append(("Waypoint", f"{path_name}:{index}", point))

        for i in range(len(positioned_objects)):
            kind_a, name_a, pos_a = positioned_objects[i]
            for j in range(i + 1, len(positioned_objects)):
                kind_b, name_b, pos_b = positioned_objects[j]

                dx = float(pos_a[0]) - float(pos_b[0])
                dy = float(pos_a[1]) - float(pos_b[1])
                dz = float(pos_a[2]) - float(pos_b[2])
                distance_m = math.sqrt(dx * dx + dy * dy + dz * dz)

                if distance_m > limit_m:
                    distance_violations.append((kind_a, name_a, kind_b, name_b, distance_m))

        if distance_violations:
            distance_violations.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
            violation_lines = [
                f"    - {kind_a} '{name_a}' <-> {kind_b} '{name_b}': "
                f"{distance_m / 1000.0:.1f} km"
                for kind_a, name_a, kind_b, name_b, distance_m in distance_violations
            ]
            self.log_warning(
                f"Mission scale recommendation: {len(distance_violations)} object pair(s) exceed the "
                f"recommended maximum distance of {limit_km:.1f} km. Keep points of interest within 20 km "
                f"to avoid long travel times.\n"
                + "\n".join(violation_lines)
            )

        def check_arrival_distance(context: str, arrival_anchor: Optional[str], arrival_distance: Optional[int]):
            if not arrival_anchor or arrival_distance is None:
                return

            if arrival_distance > limit_m:
                self.log_warning(
                    f"Mission scale recommendation: {context} arrival_distance {arrival_distance} m "
                    f"from arrival_anchor '{arrival_anchor}' exceeds the recommended maximum of "
                    f"{limit_km:.1f} km. Keep anchor-based arrivals within 20 km to avoid long travel times."
                )

        for ship in self.mission.ships:
            check_arrival_distance(f"Ship '{ship.name}'", ship.arrival_anchor, ship.arrival_distance)

        for wing in self.mission.wings:
            check_arrival_distance(f"Wing '{wing.name}'", wing.arrival_anchor, wing.arrival_distance)

    def validate_3d_mission_design(self):
        """
        Warn if all objects in a mission are placed strictly on the XZ plane (Y-coordinate = 0).
        This encourages using the 3D space to make missions more interesting and prevent unintended collisions.
        """
        positioned_objects = []

        for ship in self.mission.ships:
            positioned_objects.append(("Ship", ship.name, ship.position))

        for wing in self.mission.wings:
            wing_position = wing.position
            if wing_position is None and wing.ships:
                wing_position = wing.ships[0].position
            if wing_position is not None:
                positioned_objects.append(("Wing", wing.name, wing_position))

        for jump_node in self.mission.jump_nodes:
            positioned_objects.append(("Jump Node", jump_node.name, jump_node.position))

        for path_name, points in self.mission.waypoints.items():
            for index, point in enumerate(points, start=1):
                positioned_objects.append(("Waypoint", f"{path_name}:{index}", point))

        if not positioned_objects:
            return

        all_y_zero = True
        for kind, name, pos in positioned_objects:
            if abs(float(pos[1])) >= 0.001:
                all_y_zero = False
                break

        if all_y_zero:
            self.log_warning(
                "Mission design recommendation: All objects are currently placed on the 2D XZ plane (Y=0). "
                "Spreading objects in the third dimension (Y-axis) creates more interesting 3D missions "
                "and prevents unintended collisions."
            )

    def validate_spawn_collisions(self):
        """
        Warn if ships or wings that arrive via Hyperspace spawn too close to each other.
        """
        positioned_objects = []
        wing_members = set()

        # Collect wing members
        for w in self.mission.wings:
            for s in w.ships:
                wing_members.add(s.name)

        # 1. Collect all standalone ships arriving via Hyperspace
        for s in self.mission.ships:
            if s.name in wing_members:
                continue
            
            arr_loc = s.arrival_method.strip().lower()
            if arr_loc != "hyperspace":
                continue
                
            obb = self._get_world_obb(s.ship_class, s.orientation, s.position, padding=0.0)
            positioned_objects.append({
                'type': 'Ship',
                'name': s.name,
                'pos': s.position,
                'obb': obb,
                'docked_with': s.docked_with
            })

        # 2. Collect all wings arriving via Hyperspace
        for w in self.mission.wings:
            arr_loc = w.arrival_method.strip().lower()
            if arr_loc != "hyperspace":
                continue
                
            # Use wing position, fallback to leader's position
            pos = w.position
            if pos is None and w.ships:
                pos = w.ships[0].position
                
            if pos is None:
                continue

            # Estimate wing bounding box using the first ship's class
            if w.ships:
                obb = self._get_world_obb(w.ships[0].ship_class, w.ships[0].orientation, pos, padding=100.0)
            else:
                ident_orientation = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
                obb = self._get_world_obb("Unknown", ident_orientation, pos, padding=100.0)

            positioned_objects.append({
                'type': 'Wing',
                'name': w.name,
                'pos': pos,
                'obb': obb,
                'docked_with': None # Wings can't be pre-spawn docked
            })

        collisions = []

        # 3. Pairwise check
        for i in range(len(positioned_objects)):
            obj_a = positioned_objects[i]
            for j in range(i + 1, len(positioned_objects)):
                obj_b = positioned_objects[j]

                # Skip if a is explicitly docked to b or vice versa
                if obj_a['docked_with'] == obj_b['name'] or obj_b['docked_with'] == obj_a['name']:
                    continue

                # OBB overlap test
                if self._obb_intersects(obj_a['obb'], obj_b['obb']):
                    dx = float(obj_a['pos'][0]) - float(obj_b['pos'][0])
                    dy = float(obj_a['pos'][1]) - float(obj_b['pos'][1])
                    dz = float(obj_a['pos'][2]) - float(obj_b['pos'][2])
                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                    collisions.append((obj_a, obj_b, dist))

        if collisions:
            # Sort by distance for cleaner logging
            collisions.sort(key=lambda x: x[2])
            for obj_a, obj_b, dist in collisions:
                self.log_warning(
                    f"Mission design recommendation: {obj_a['type']} '{obj_a['name']}' spawns very close to "
                    f"{obj_b['type']} '{obj_b['name']}'. Their bounding boxes intersect (center distance {dist:.1f}m). "
                    f"Both objects arrive via Hyperspace at static locations. This may cause an immediate collision upon mission start or arrival."
                )

    def _dot(self, v1: List[float], v2: List[float]) -> float:
        return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

    def _cross(self, v1: List[float], v2: List[float]) -> List[float]:
        return [
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        ]

    def _normalize(self, v: List[float]) -> List[float]:
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if mag == 0:
            return [0.0, 0.0, 0.0]
        return [v[0]/mag, v[1]/mag, v[2]/mag]

    def _obb_intersects(self, obb_a: dict, obb_b: dict) -> bool:
        T = [obb_b['center'][i] - obb_a['center'][i] for i in range(3)]
        
        axes_a = obb_a['axes']
        axes_b = obb_b['axes']
        
        axes_to_test = []
        axes_to_test.extend(axes_a)
        axes_to_test.extend(axes_b)
        
        for i in range(3):
            for j in range(3):
                cross_axis = self._cross(axes_a[i], axes_b[j])
                if sum(c*c for c in cross_axis) > 1e-6:
                    axes_to_test.append(self._normalize(cross_axis))
                    
        for L in axes_to_test:
            t_proj = abs(self._dot(T, L))
            r_a = sum(obb_a['extents'][i] * abs(self._dot(axes_a[i], L)) for i in range(3))
            r_b = sum(obb_b['extents'][i] * abs(self._dot(axes_b[i], L)) for i in range(3))
            
            if t_proj > r_a + r_b:
                return False
                
        return True

    def _get_ship_radius(self, ship_class: str) -> float:
        """Estimate the collision radius of a ship.
        First tries to use accurate bounding box data, then falls back to prefix heuristic.
        """
        if ship_class in self.ship_bounding_boxes:
            box = self.ship_bounding_boxes[ship_class]
            min_x, min_y, min_z = box['min']
            max_x, max_y, max_z = box['max']
            # Max distance from center to any corner
            return math.sqrt(max(abs(min_x), abs(max_x))**2 + 
                             max(abs(min_y), abs(max_y))**2 + 
                             max(abs(min_z), abs(max_z))**2)
            
        cls = ship_class.upper()
        if any(p in cls for p in ['GTI', 'PVI', 'BASE', 'INSTALLATION']):
            return 1000.0
        if any(cls.startswith(p) for p in ['GTD', 'PVD', 'SD']):
            return 600.0
        if any(cls.startswith(p) for p in ['GTC', 'PVC', 'SC', 'GTSC', 'PVSC']):
            return 150.0
        if any(cls.startswith(p) for p in ['GTFR', 'PVFR', 'SFR', 'GTT', 'PVT', 'ST']):
            return 150.0
        return 50.0

    def _get_world_obb(self, ship_class: str, orientation: List[float], location: List[float], padding: float = 0.0) -> dict:
        """
        Get the world-space Oriented Bounding Box (OBB) for a ship given its class, orientation, location, and optional padding.
        """
        # 1. Get local bounding box
        if ship_class in self.ship_bounding_boxes:
            box = self.ship_bounding_boxes[ship_class]
            min_x, min_y, min_z = box['min']
            max_x, max_y, max_z = box['max']
        else:
            r = self._get_ship_radius(ship_class)
            min_x, min_y, min_z = -r, -r, -r
            max_x, max_y, max_z = r, r, r

        # 2. Local center and extents
        cx = (max_x + min_x) / 2.0
        cy = (max_y + min_y) / 2.0
        cz = (max_z + min_z) / 2.0

        ex = (max_x - min_x) / 2.0 + padding
        ey = (max_y - min_y) / 2.0 + padding
        ez = (max_z - min_z) / 2.0 + padding

        # 3. Local axes in world space
        axis_x = self._normalize([orientation[0], orientation[3], orientation[6]])
        axis_y = self._normalize([orientation[1], orientation[4], orientation[7]])
        axis_z = self._normalize([orientation[2], orientation[5], orientation[8]])

        # 4. Transform local center to world space
        world_cx = orientation[0] * cx + orientation[1] * cy + orientation[2] * cz + location[0]
        world_cy = orientation[3] * cx + orientation[4] * cy + orientation[5] * cz + location[1]
        world_cz = orientation[6] * cx + orientation[7] * cy + orientation[8] * cz + location[2]

        return {
            'center': [world_cx, world_cy, world_cz],
            'axes': [axis_x, axis_y, axis_z],
            'extents': [ex, ey, ez]
        }

    def validate_waypoint_collisions(self):
        """
        Check if standalone ship waypoint move orders are likely to cause a collision 
        with another ship or station in the mission.
        
        Note: Wing-level waypoint orders are intentionally not checked for path collisions. 
        Wings typically consist of fighters or bombers which have their own AI routines for collision avoidance.
        """
        import re
        import math

        # Regex to find ai-waypoints and ai-waypoints-once
        # Extracts the path name, stripping quotes if present
        wp_regex = re.compile(r'\(\s*ai-waypoints(?:-once)?\s+(?:"([^"]+)"|([^"\s)]+))', re.IGNORECASE)

        ships_with_waypoints = set()
        for w in self.mission.wings:
            if w.initial_orders and wp_regex.search(w.initial_orders):
                for s in w.ships:
                    ships_with_waypoints.add(s.name)
                    
        for s in self.mission.ships:
            if s.initial_orders and wp_regex.search(s.initial_orders):
                ships_with_waypoints.add(s.name)

        ship_map = {s.name: s for s in self.mission.ships}

        def get_effective_initial_location(ship_name, visited=None):
            if visited is None:
                visited = set()
            if ship_name in visited:
                return None
            visited.add(ship_name)
            
            s = ship_map.get(ship_name)
            if not s:
                return None
                
            arr_loc = s.arrival_method.strip().lower()
            if arr_loc == "hyperspace":
                return s.position
            elif arr_loc == "docking bay":
                if s.arrival_anchor:
                    anchor_loc = get_effective_initial_location(s.arrival_anchor, visited)
                    if anchor_loc is not None:
                        return anchor_loc
                return s.position
            else:
                return None

        # 1. Collect all stationary or existing objects to check against
        obstacles = []
        wing_members = set()
        for w in self.mission.wings:
            for s in w.ships:
                wing_members.add(s.name)
                
        for s in self.mission.ships:
            radius = self._get_ship_radius(s.ship_class)
            if radius <= 50.0:
                continue
            if s.name in ships_with_waypoints:
                continue
            eff_loc = get_effective_initial_location(s.name)
            if eff_loc is None:
                continue
            
            obb = self._get_world_obb(s.ship_class, s.orientation, eff_loc, padding=0.0)
            
            obstacles.append({
                'name': s.name,
                'pos': eff_loc,
                'radius': radius,
                'obb': obb,
                'is_wing_member': s.name in wing_members
            })

        def point_segment_distance(p, a, b):
            """Calculate the shortest distance from point p to line segment a-b."""
            ab = [b[0]-a[0], b[1]-a[1], b[2]-a[2]]
            ap = [p[0]-a[0], p[1]-a[1], p[2]-a[2]]
            
            ab_len_sq = ab[0]**2 + ab[1]**2 + ab[2]**2
            if ab_len_sq == 0:
                # a and b are the same point
                return math.sqrt(ap[0]**2 + ap[1]**2 + ap[2]**2)
                
            t = (ap[0]*ab[0] + ap[1]*ab[1] + ap[2]*ab[2]) / ab_len_sq
            t = max(0.0, min(1.0, t))
            
            closest = [a[0] + t*ab[0], a[1] + t*ab[1], a[2] + t*ab[2]]
            dist = math.sqrt((p[0]-closest[0])**2 + (p[1]-closest[1])**2 + (p[2]-closest[2])**2)
            return dist

        def get_segment_obb(p1, p2, ship_class):
            if ship_class in self.ship_bounding_boxes:
                box = self.ship_bounding_boxes[ship_class]
                min_x, min_y, min_z = box['min']
                max_x, max_y, max_z = box['max']
            else:
                r = self._get_ship_radius(ship_class)
                min_x, min_y, min_z = -r, -r, -r
                max_x, max_y, max_z = r, r, r
                
            ex = (max_x - min_x) / 2.0
            ey = (max_y - min_y) / 2.0
            ez = (max_z - min_z) / 2.0
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            axis_z = self._normalize([dx, dy, dz])
            if sum(abs(c) for c in axis_z) < 1e-6:
                axis_z = [0.0, 0.0, 1.0]
                
            up = [0.0, 1.0, 0.0]
            if abs(self._dot(axis_z, up)) > 0.999:
                up = [1.0, 0.0, 0.0]
                
            axis_x = self._normalize(self._cross(up, axis_z))
            axis_y = self._normalize(self._cross(axis_z, axis_x))
            
            cx = (p1[0] + p2[0]) / 2.0
            cy = (p1[1] + p2[1]) / 2.0
            cz = (p1[2] + p2[2]) / 2.0
            
            return {
                'center': [cx, cy, cz],
                'axes': [axis_x, axis_y, axis_z],
                'extents': [ex, ey, ez + (dist / 2.0)]
            }

        def check_path_for_collisions(entity_type, entity_name, start_pos, entity_class, path_name):
            if path_name not in self.mission.waypoints:
                return
                
            points = [start_pos] + self.mission.waypoints[path_name]
            collisions = {}
            
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                
                segment_obb = get_segment_obb(p1, p2, entity_class)
                
                for obs in obstacles:
                    # Don't collide with yourself
                    if obs['name'] == entity_name:
                        continue
                        
                    # Exclude collision checks between a ship and its arrival anchor
                    # if the ship starts in the anchor's docking bay
                    entity_ship = ship_map.get(entity_name)
                    obs_ship = ship_map.get(obs['name'])
                    
                    if entity_ship and entity_ship.arrival_method.strip().lower() == "docking bay" and entity_ship.arrival_anchor == obs['name']:
                        continue
                        
                    if obs_ship and obs_ship.arrival_method.strip().lower() == "docking bay" and obs_ship.arrival_anchor == entity_name:
                        continue

                    if self._obb_intersects(segment_obb, obs['obb']):
                        dist = point_segment_distance(obs['pos'], p1, p2)
                        if obs['name'] not in collisions or dist < collisions[obs['name']]:
                            collisions[obs['name']] = dist

            if collisions:
                details = ", ".join(f"ship '{name}' (distance {d:.1f}m, bounding boxes intersect)" for name, d in collisions.items())
                self.log_warning(
                    f"{entity_type} '{entity_name}' waypoint path '{path_name}' passes very close "
                    f"to the initial location of {details}. "
                    f"This could cause a collision during waypoint movement."
                )

        # 2. Check standalone ships
        for s in self.mission.ships:
            if s.name in wing_members:
                continue
            if s.initial_orders:
                match = wp_regex.search(s.initial_orders)
                if match:
                    path_name = match.group(1) or match.group(2)
                    my_radius = self._get_ship_radius(s.ship_class)
                    if my_radius <= 50.0:
                        continue
                    eff_loc = get_effective_initial_location(s.name)
                    if eff_loc is None:
                        continue
                    check_path_for_collisions("Ship", s.name, eff_loc, s.ship_class, path_name)