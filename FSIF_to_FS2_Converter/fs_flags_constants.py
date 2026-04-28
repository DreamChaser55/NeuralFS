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
# These are the exact canonical string formats expected by FSO.
SHIP_FLAGS_BUCKET = {
    # +Flags (primary object flags)
    "cargo-known": "flags",
    "ignore-count": "flags",
    "protect-ship": "flags",
    "reinforcement": "flags",
    "no-shields": "flags",
    "escort": "flags",
    "no-arrival-music": "flags",
    "invulnerable": "flags",
    "hidden-from-sensors": "flags",
    "scannable": "flags",
    "kamikaze": "flags",
    "no-dynamic": "flags",
    "red-alert-carry": "flags",
    "guardian": "flags",
    "special-warp": "flags",
    "stealth": "flags",
    "friendly-stealth-invisible": "flags",
    "player-start": "flags",
    # +Flags (primary object flags - Extended)
    "no-arrival-warp": "flags",
    "no-departure-warp": "flags",
    "beam-protected": "flags",
    "flak-protected": "flags",
    "laser-protected": "flags",
    "missile-protected": "flags",
    "vaporize": "flags",
    "dont-collide-invis": "flags",
    "use-unique-orders": "flags",
    "dock-leader": "flags",
    "cannot-arrive": "flags",
    "warp-broken": "flags",
    "warp-never": "flags",
    "nav-carry-status": "flags",
    "affected-by-gravity": "flags",
    "targetable-as-bomb": "flags",
    "no-builtin-messages": "flags",
    "no-death-scream": "flags",
    "always-death-scream": "flags",
    "nav-needslink": "flags",
    "set-class-dynamically": "flags",
    "lock-all-turrets-initially": "flags",
    "force-shields-on": "flags",
    "immobile": "flags",
    "dont-change-position": "flags",
    "dont-change-orientation": "flags",
    "no-ets": "flags",
    "red-alert-deleted": "flags",
    "already-handled": "flags",
    "no-disabled-self-destruct": "flags",
    "has-display-name": "flags",
    "hide-mission-log": "flags",
    "same-arrival-warp-when-docked": "flags",
    "same-departure-warp-when-docked": "flags",
    "attackable-if-no-collide": "flags",
    "fail-sound-locked-primary": "flags",
    "fail-sound-locked-secondary": "flags",
    "aspect-immune": "flags",
    "cannot-perform-scan": "flags",
    "no-targeting-limits": "flags",
    "from-player-wing": "flags",

    # +Flags2 (secondary object flags)
    "primitive-sensors": "flags2",
    "no-subspace-drive": "flags2",
    "toggle-subsystem-scanning": "flags2",
    "hide-ship-name": "flags2",
    "cloaked": "flags2",
    "scramble-messages": "flags2",
    "no_collide": "flags2", # Documented with underscore
    "primaries-locked": "flags2",
    "secondaries-locked": "flags2",
    "weapons-locked": "flags2",
    "ship-locked": "flags2",
    "afterburners-locked": "flags2",
    "lock-all-turrets": "flags2",
    # +Flags2 (secondary object flags - Extended)
    "primary-linked": "flags2",
    "secondary-dual-fire": "flags2",
    "navpoint-carry": "flags2",
    "glowmaps-disabled": "flags2",
    "no-secondary-lockon": "flags2",
    "subsystem-movement-locked": "flags2",
    "draw-as-wireframe": "flags2",
    "render-without-diffuse": "flags2",
    "render-without-glowmap": "flags2",
    "render-without-specmap": "flags2",
    "render-without-normalmap": "flags2",
    "render-without-heightmap": "flags2",
    "render-without-ambientmap": "flags2",
    "render-without-miscmap": "flags2",
    "render-without-reflectmap": "flags2",
    "render-full-detail": "flags2",
    "render-without-light": "flags2",
    "render-without-weapons": "flags2",
    "render-with-alpha-mult": "flags2",
    "no-passive-lightning": "flags2",
    "maneuver-despite-engines": "flags2",
    "force-primary-unlinking": "flags2",
    "no-scanned-cargo": "flags2",
    "no-insignias": "flags2",
}

# Wing flags mapping
# Maps flag name to the FS2 section ("flags")
# Wings in FSO generally support +Flags. Some overlap with ships.
WING_FLAGS_BUCKET = {
    "reinforcement": "flags",
    "no-arrival-music": "flags",
    "no-arrival-message": "flags",
    "ignore-count": "flags",
    "no-arrival-warp": "flags",
    "no-departure-warp": "flags",
    "no-dynamic": "flags",
    "departure-ordered": "flags",
    "no-first-wave-message": "flags",
    "waypoints-no-formation": "flags",
}

def resolve_mission_flag(name: str):
    """Resolve a mission flag token to its canonical form."""
    if not isinstance(name, str):
        return None
    token = name.strip()
    if token in MISSION_FLAG_BITS:
        return token
    return None
