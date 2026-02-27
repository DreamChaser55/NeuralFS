# Additional flags

This section lists additional canonical FSO flags supported by the FSIF converter, not mentioned in 'FSO_Tokens_Reference.md'. Many of these flags are used very sparingly or are not useful for mission authors. Standard documentation in 'FSO_Tokens_Reference.md' contains only the generally useful subset.
The converter automatically maps these tokens to the appropriate engine fields (e.g., +Flags, +Flags2, or bitmasks).

## Mission flags (`mission_info.flags`)
These tokens map to the FSO `Mission::Mission_Flags` bitmask.

*   `mission_2d` — Mission is meant to be played top-down style; 2D physics and movement.
*   `player_start_ai` — Player starts mission under AI Control (NOT MULTI COMPATIBLE)
* `use_ap_cinematics` — Use autopilot cinematics
* `deactivate_ap` — Deactivate autopilot
*   `override_hashcommand` — Override #Command with the Command info in Mission Specs
*   `toggle_start_chase_view` — Toggles (versus the default) whether the player starts the mission in chase view
*   `neb2_fog_color_override` — Whether to use explicit fog colors instead of checking the palette

## Ship flags (`entities.ships[*].flags`)
The converter automatically splits these tokens into the `+Flags` and `+Flags2` buckets required by the engine.

### Primary Flags (`+Flags`)
*   `use-unique-orders` — Tells a newly created ship to use the default orders for that ship
*   `dock-leader` — A docked object that is the leader of its group
*   `nav-carry-status` — This ship autopilots with the player
*   `affected-by-gravity` — Ship affected by gravity points
*   `nav-needslink` — This ship requires "linking" for autopilot
*   `set-class-dynamically` — This ship should have its class assigned rather than simply read from the mission file
*   `no-ets` — This ship does not have an ETS
*   `red-alert-deleted` — Used analogously to SEF_PLAYER_DELETED
*   `already-handled` — Used for docking currently, but could be used generically
*   `same-arrival-warp-when-docked` — Same arrival warp when docked
*   `same-departure-warp-when-docked` — Same departure warp when docked
*   `from-player-wing` — Set for ships that are members of any player starting wing
*   `player-start` — Player starts in this ship (Note: This flag is managed automatically by `player_setup.start_ship` in FSIF; do not author it manually. FSIF does not support multiple player starting ships (single player only))

### Secondary Flags (`+Flags2`)
*   `navpoint-carry` — This ship autopilots with the player
*   `force-primary-unlinking` — Turned on when the ship is under good-primary-time
*   `no-insignias` — Do not render insignias, even when one is defined for them

## Wing flags (`entities.wings[*].flags`)
*   `nav-carry` — Wing has nav-carry-status
*   `same-arrival-warp-when-docked` — Same arrival warp when docked
*   `same-departure-warp-when-docked` — Same departure warp when docked
