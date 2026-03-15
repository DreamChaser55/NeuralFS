# fs_flags_constants.py
# Contains FS2 format constants, flag definitions, and bitmasks.

# Mission flags support (derived from FSO mission/mission_flags.h Mission::Mission_Flags order)
# IMPORTANT: Keep this list in the exact order of the enum in FSO to preserve bit positions.
MISSION_FLAGS_ORDER = [
    "subspace",
    "no_promotion",
    "fullneb",
    "no_builtin_msgs",
    "no_traitor",
    "toggle_ship_trails",
    "support_repairs_hull",
    "beam_free_all_by_default",
    "unused_1",
    "unused_2",
    "no_briefing",
    "toggle_debriefing",
    "unused_3",
    "unused_4",
    "mission_2d",
    "unused_5",
    "red_alert",                    # index 16 -> 1<<16 = 65536
    "scramble",                     # index 17 -> 1<<17 = 131072
    "no_builtin_command",
    "player_start_ai",
    "all_attack",
    "use_ap_cinematics",
    "deactivate_ap",
    "toggle_showing_goals",
    "end_to_mainhall",
    "override_hashcommand",
    "toggle_start_chase_view",
    "neb2_fog_color_override",
    "unused_6",
    "preload_subspace",
]

# Precompute bit values
MISSION_FLAG_BITS = {name: (1 << idx) for idx, name in enumerate(MISSION_FLAGS_ORDER)}

# Ship/Object flags mapping
# Maps flag name to the FS2 section ("flags" or "flags2")
SHIP_FLAGS_BUCKET = {
    # +Flags (primary object flags)
    "cargo_known": "flags",
    "ignore_count": "flags",
    "protect_ship": "flags",
    "reinforcement": "flags",
    "no_shields": "flags",
    "escort": "flags",
    "no_arrival_music": "flags",
    "invulnerable": "flags",
    "hidden_from_sensors": "flags",
    "scannable": "flags",
    "kamikaze": "flags",
    "no_dynamic": "flags",
    "red_alert_carry": "flags",
    "guardian": "flags",
    "special_warp": "flags",
    "stealth": "flags",
    "friendly_stealth_invisible": "flags",
    "player_start": "flags",
    # +Flags (primary object flags - Extended)
    "no_arrival_warp": "flags",
    "no_departure_warp": "flags",
    "beam_protected": "flags",
    "flak_protected": "flags",
    "laser_protected": "flags",
    "missile_protected": "flags",
    "vaporize": "flags",
    "dont_collide_invis": "flags",
    "use_unique_orders": "flags",
    "dock_leader": "flags",
    "cannot_arrive": "flags",
    "warp_broken": "flags",
    "warp_never": "flags",
    "nav_carry_status": "flags",
    "affected_by_gravity": "flags",
    "targetable_as_bomb": "flags",
    "no_builtin_messages": "flags",
    "no_death_scream": "flags",
    "always_death_scream": "flags",
    "nav_needslink": "flags",
    "set_class_dynamically": "flags",
    "lock_all_turrets_initially": "flags",
    "force_shields_on": "flags",
    "immobile": "flags",
    "dont_change_position": "flags",
    "dont_change_orientation": "flags",
    "no_ets": "flags",
    "red_alert_deleted": "flags",
    "already_handled": "flags",
    "no_disabled_self_destruct": "flags",
    "has_display_name": "flags",
    "hide_mission_log": "flags",
    "same_arrival_warp_when_docked": "flags",
    "same_departure_warp_when_docked": "flags",
    "attackable_if_no_collide": "flags",
    "fail_sound_locked_primary": "flags",
    "fail_sound_locked_secondary": "flags",
    "aspect_immune": "flags",
    "cannot_perform_scan": "flags",
    "no_targeting_limits": "flags",
    "from_player_wing": "flags",

    # +Flags2 (secondary object flags)
    "primitive_sensors": "flags2",
    "no_subspace_drive": "flags2",
    "toggle_subsystem_scanning": "flags2",
    "hide_ship_name": "flags2",
    "cloaked": "flags2",
    "scramble_messages": "flags2",
    "no_collide": "flags2",
    "primaries_locked": "flags2",
    "secondaries_locked": "flags2",
    "weapons_locked": "flags2",
    "ship_locked": "flags2",
    "afterburners_locked": "flags2",
    "lock_all_turrets": "flags2",
    # +Flags2 (secondary object flags - Extended)
    "primary_linked": "flags2",
    "secondary_dual_fire": "flags2",
    "navpoint_carry": "flags2",
    "glowmaps_disabled": "flags2",
    "no_secondary_lockon": "flags2",
    "subsystem_movement_locked": "flags2",
    "draw_as_wireframe": "flags2",
    "render_without_diffuse": "flags2",
    "render_without_glowmap": "flags2",
    "render_without_specmap": "flags2",
    "render_without_normalmap": "flags2",
    "render_without_heightmap": "flags2",
    "render_without_ambientmap": "flags2",
    "render_without_miscmap": "flags2",
    "render_without_reflectmap": "flags2",
    "render_full_detail": "flags2",
    "render_without_light": "flags2",
    "render_without_weapons": "flags2",
    "render_with_alpha_mult": "flags2",
    "no_passive_lightning": "flags2",
    "maneuver_despite_engines": "flags2",
    "force_primary_unlinking": "flags2",
    "no_scanned_cargo": "flags2",
    "no_insignias": "flags2",
}

# Wing flags mapping
# Maps flag name to the FS2 section ("flags")
# Wings in FSO generally support +Flags. Some overlap with ships.
WING_FLAGS_BUCKET = {
    "reinforcement": "flags",
    "no_arrival_music": "flags",
    "no_arrival_message": "flags",
    "ignore_count": "flags",
    "no_arrival_warp": "flags",
    "no_departure_warp": "flags",
    "no_dynamic": "flags",
    "departure_ordered": "flags",
    "no_first_wave_message": "flags",
    "waypoints_no_formation": "flags",
}

def normalize_flag(token):
    """
    Normalize a flag string to a canonical key format (lowercase, underscores).
    Used for consistent lookups in flag buckets.
    """
    try:
        import re
        key = str(token).strip().lower()
        key = re.sub(r'[\s\-]+', '_', key)
        key = re.sub(r'[^a-z0-9_]', '', key)
        key = re.sub(r'_+', '_', key).strip('_')
        return key
    except Exception:
        return ""

def resolve_mission_flag(name: str):
    """Resolve a mission flag token to its canonical form."""
    if not isinstance(name, str):
        return None
    token = name.strip()
    if token in MISSION_FLAG_BITS:
        return token
    return None
