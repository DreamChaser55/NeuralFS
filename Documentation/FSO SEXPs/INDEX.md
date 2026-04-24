# FSO SEXPs Index

This index was automatically generated from the documentation files in this directory. Each section corresponds to a 'txt' file with detailed specification of the listed SEXPs.

## AI Control
- `add-goal`
- `remove-goal`
- `clear-goals`
- `good-rearm-time`
- `bad-rearm-time`
- `good-primary-time`
- `good-secondary-time`
- `change-ai-class`
- `player-use-ai`
- `player-not-use-ai`
- `set-player-orders`
- `set-order-allowed-for-target`
- `enable-general-orders`
- `validate-general-orders`
- `cap-waypoint-speed`
- `set-wing-formation`

## AI Orders (player-issued)
- `Attack Target`
- `Disable Target`
- `Disarm Target`
- `Destroy Subsystem`
- `Protect Target`
- `Ignore Target`
- `Form on my wing`
- `Cover me`
- `Engage Enemy`
- `Capture Target`
- `Rearm me`
- `Abort rearm`
- `Depart`

## AI goals
- `ai-chase`
- `ai-chase-any`
- `ai-chase-ship-class`
- `ai-chase-ship-type`
- `ai-chase-wing`
- `ai-chase-any`
- `ai-guard`
- `ai-destroy-subsystem`
- `ai-disable-ship`
- `ai-disable-ship-tactical`
- `ai-disarm-ship`
- `ai-disarm-ship-tactical`
- `ai-warp-out`
- `ai-dock`
- `ai-undock`
- `ai-rearm-repair`
- `ai-waypoints`
- `ai-waypoints-once`
- `ai-ignore`
- `ai-ignore-new`
- `ai-form-on-wing`
- `ai-fly-to-ship`
- `ai-stay-near-ship`
- `ai-evade-ship`
- `ai-keep-safe-distance`
- `ai-stay-still`
- `ai-play-dead`
- `ai-play-dead-persistent`

## Arithmetic
- `+`
- `-`
- `*`
- `/`
- `mod`
- `rand`
- `rand-multiple`
- `abs`
- `min`
- `max`
- `avg`
- `pow`
- `signum`
- `is-nan`
- `nan-to-number`
- `set-bit`
- `unset-bit`
- `is-bit-set`
- `bitwise-and`
- `bitwise-or`
- `bitwise-not`
- `bitwise-xor`
- `angle-vectors`

## Armor and Damage Types
- `set-armor-type`
- `weapon-set-damage-type`
- `ship-set-damage-type`
- `ship-set-shockwave-damage-type`
- `field-set-damage-type`
- `set-friendly-damage-caps`

## Backgrounds and Nebulae
- `mission-set-nebula`
- `mission-set-subspace`
- `change-background`
- `add-background-bitmap`
- `add-background-bitmap-new`
- `remove-background-bitmap`
- `add-sun-bitmap`
- `add-sun-bitmap-new`
- `remove-sun-bitmap`
- `nebula-change-storm`
- `nebula-toggle-poof`
- `nebula-fade-poof`
- `nebula-change-pattern`
- `nebula-change-fog-color`
- `volumetrics-toggle`
- `set-skybox-model`
- `set-skybox-orientation`
- `set-skybox-alpha`
- `set-ambient-light`
- `toggle-asteroid-field`
- `set-asteroid-field`
- `set-debris-field`
- `config-asteroid-field`
- `config-debris-field`
- `config-field-targets`
- `set-motion-debris`

## Beams and Turrets
- `fire-beam`
- `fire-beam-at-coordinates`
- `beam-create`
- `beam-free`
- `beam-free-all`
- `beam-lock`
- `beam-lock-all`
- `turret-free`
- `turret-free-all`
- `turret-lock`
- `turret-lock-all`
- `turret-tagged-only`
- `turret-tagged-clear`
- `turret-tagged-specific`
- `turret-tagged-clear-specific`
- `turret-change-weapon`
- `turret-set-direction-preference`
- `turret-set-rate-of-fire`
- `turret-set-optimum-range`
- `turret-set-target-priorities`
- `turret-set-inaccuracy`
- `turret-set-target-order`
- `ship-turret-target-order`
- `turret-subsys-target-disable`
- `turret-subsys-target-enable`
- `turret-set-forced-target`
- `turret-set-forced-subsys-target`
- `turret-clear-forced-target`
- `turret-set-primary-ammo`
- `turret-set-secondary-ammo`

## Cargo
- `transfer-cargo`
- `exchange-cargo`
- `set-cargo`
- `jettison-cargo-delay`
- `jettison-cargo`
- `set-docked`
- `cargo-no-deplete`
- `set-scanned`
- `set-unscanned`

## Cargo Status
- `is-cargo-known-delay`
- `cap-subsys-cargo-known-delay`
- `is-cargo`

## Conditionals
- `when`
- `when-argument`
- `every-time`
- `every-time-argument`
- `on-mission-skip`
- `functional-when`
- `if-then-else`
- `functional-if-then-else`
- `switch`
- `functional-switch`
- `any-of`
- `every-of`
- `random-of`
- `random-multiple-of`
- `number-of`
- `first-of`
- `in-sequence`
- `for-counter`
- `for-ship-class`
- `for-ship-type`
- `for-ship-team`
- `for-ship-species`
- `for-players`
- `for-subsystems`
- `for-container-data`
- `for-map-container-keys`
- `invalidate-argument`
- `invalidate-all-arguments`
- `validate-argument`
- `validate-all-arguments`
- `do-for-valid-arguments`
- `num-valid-arguments`

## Container Status
- `is-container-empty`
- `get-container-size`
- `list-has-data`
- `list-data-index`
- `map-has-key`
- `map-has-data-item`

## Containers
- `add-to-list`
- `remove-from-list`
- `add-to-map`
- `remove-from-map`
- `get-map-keys`
- `clear-container`
- `copy-container`
- `apply-container-filter`

## Coordinate Manipulation
- `set-object-position`
- `set-object-orientation`
- `set-object-facing`
- `set-object-facing-object`
- `set-object-speed-x`
- `set-object-speed-y`
- `set-object-speed-z`
- `ship-maneuver`
- `ship-rot-maneuver`
- `ship-lat-maneuver`
- `set-immobile`
- `set-mobile`

## Cutscenes
- `set-cutscene-bars`
- `unset-cutscene-bars`
- `fade-in`
- `fade-out`
- `set-camera`
- `set-camera-position`
- `set-camera-facing`
- `set-camera-facing-object`
- `set-camera-rotation`
- `set-camera-host`
- `set-camera-target`
- `set-camera-fov`
- `set-fov`
- `get-fov`
- `reset-fov`
- `reset-camera`
- `show-subtitle`
- `show-subtitle-text`
- `show-subtitle-image`
- `clear-subtitles`
- `lock-perspective`
- `set-camera-shudder`
- `supernova-start`
- `supernova-stop`
- `set-motion-debris-override`

## Damage
- `shields-left`
- `hits-left`
- `hits-left-subsystem`
- `hits-left-subsystem-generic`
- `hits-left-subsystem-specific`
- `sim-hits-left`
- `get-damage-caused`

## Damaged Escorts and Support Ships
- `damaged-escort-priority`
- `damaged-escort-priority-all`
- `set-support-ship`

## Distance and Coordinates
- `distance`
- `distance-to-center`
- `distance-to-bbox`
- `distance-center-to-subsystem`
- `distance-bbox-to-subsystem`
- `distance-to-nav`
- `num-within-box`
- `is-in-box`
- `special-warp-dist`
- `get-object-x`
- `get-object-y`
- `get-object-z`
- `get-object-pitch`
- `get-object-bank`
- `get-object-heading`
- `get-object-speed-x`
- `get-object-speed-y`
- `get-object-speed-z`
- `angle-facing-object`

## Event-Goals
- `is-goal-true-delay`
- `is-goal-false-delay`
- `is-goal-incomplete`
- `is-event-true-delay`
- `is-event-true-msecs-delay`
- `is-event-false-delay`
- `is-event-false-msecs-delay`
- `is-event-incomplete`
- `is-previous-goal-true`
- `is-previous-goal-false`
- `is-previous-event-true`
- `is-previous-event-false`
- `reset-event`
- `reset-goal`

## HUD
- `hud-disable`
- `hud-disable-except-messages`
- `hud-set-custom-gauge-active`
- `hud-set-builtin-gauge-active`
- `hud-set-text`
- `hud-set-text-num`
- `hud-set-message`
- `hud-set-directive`
- `hud-set-frame`
- `hud-set-coords`
- `hud-set-color`
- `hud-display-gauge`
- `hud-gauge-set-active`
- `hud-activate-gauge-type`
- `hud-clear-messages`
- `hud-set-max-targeting-range`
- `hud-force-sensor-static`
- `hud-force-emp-effect`

## Jump Nodes
- `set-jumpnode-name`
- `set-jumpnode-display-name`
- `set-jumpnode-color`
- `set-jumpnode-model`
- `show-jumpnode`
- `hide-jumpnode`

## Logical
- `true`
- `false`
- `and`
- `and-in-sequence`
- `or`
- `not`
- `xor`
- `=`
- `!=`
- `>`
- `>=`
- `<`
- `<=`
- `string-equals`
- `string-greater-than`
- `string-less-than`
- `perform-actions-bool-first`
- `perform-actions-bool-last`
- `has-time-elapsed`
- `has-time-elapsed-msecs`

## Messages and Personas
- `send-message`
- `send-builtin-message`
- `send-message-list`
- `send-message-chain`
- `send-random-message`
- `scramble-messages`
- `unscramble-messages`
- `disable-builtin-messages`
- `enable-builtin-messages`
- `set-persona`
- `set-death-message`
- `set-mission-mood`

## Mission
- `num-ships-in-battle`
- `num-ships-in-wing`
- `directive-value`
- `get-hotkey`

## Mission and Campaign
- `invalidate-goal`
- `validate-goal`
- `red-alert`
- `end-mission`
- `force-jump`
- `end-campaign`
- `set-debriefing-toggled`
- `set-debriefing-persona`
- `set-traitor-override`
- `allow-treason`
- `grant-promotion`
- `grant-medal`
- `allow-ship`
- `allow-weapon`
- `tech-add-ships`
- `tech-add-weapons`
- `tech-add-intel`
- `tech-remove-intel`
- `tech-add-intel-xstr`
- `tech-remove-intel-xstr`
- `tech-reset-to-default`
- `change-player-score`
- `change-team-score`
- `set-respawns`
- `add-remove-hotkey`

## Models and Textures
- `change-ship-class`
- `deactivate-glow-maps`
- `activate-glow-maps`
- `deactivate-glow-points`
- `activate-glow-points`
- `deactivate-glow-point-bank`
- `activate-glow-point-bank`
- `set-thrusters-status`
- `don't-collide-invisible`
- `collide-invisible`
- `add-to-collision-group`
- `remove-from-collision-group`
- `add-to-collision-group-new`
- `remove-from-collision-group-new`
- `get-collision-group`
- `change-team-color`
- `replace-texture`
- `replace-skybox-texture`
- `set-alpha-multiplier`
- `trigger-ship-animation`
- `stop-looping-animation`
- `update-moveable-animation`

## Multiplayer
- `num-players`
- `team-score`
- `ship-deaths`
- `respawns-left`
- `is-player`

## Music and Sound
- `change-soundtrack`
- `play-sound-from-table`
- `play-sound-from-file`
- `close-sound-from-file`
- `pause-sound-from-file`
- `set-sound-environment`
- `update-sound-environment`
- `adjust-audio-volume`

## Nav Points
- `add-nav-waypoint`
- `add-nav-ship`
- `del-nav`
- `hide-nav`
- `restrict-nav`
- `unhide-nav`
- `unrestrict-nav`
- `set-nav-visited`
- `unset-nav-visited`
- `set-nav-carry`
- `unset-nav-carry`
- `set-nav-needslink`
- `unset-nav-needslink`
- `use-nav-cinematics`
- `use-autopilot`
- `select-nav`
- `unselect-nav`
- `set-nav-color`
- `set-nav-visited-color`

## Objectives
- `is-destroyed-delay`
- `was-destroyed-by-delay`
- `is-subsystem-destroyed-delay`
- `is-disabled-delay`
- `is-disarmed-delay`
- `has-docked-delay`
- `has-undocked-delay`
- `has-arrived-delay`
- `has-departed-delay`
- `are-waypoints-done-delay`
- `is-nav-visited`
- `ship-type-destroyed`
- `percent-ships-destroyed`
- `percent-ships-disabled`
- `percent-ships-disarmed`
- `percent-ships-departed`
- `percent-ships-arrived`
- `percent-ships-scanned`
- `depart-node-delay`
- `destroyed-or-departed-delay`

## Player
- `was-promotion-granted`
- `was-medal-granted`
- `skill-level-at-least`
- `num_kills`
- `num_assists`
- `num_type_kills`
- `num_class_kills`
- `ship_score`
- `time-elapsed-last-order`
- `player-is-cheating`
- `is-language`
- `used-cheat`

## Script Evals and Debug
- `script-eval-bool`
- `script-eval-num`
- `script-eval`
- `script-eval-block`
- `multi-eval`
- `script-eval-string`
- `debug`
- `do-nothing`

## Ship Status
- `protect-ship`
- `unprotect-ship`
- `beam-protect-ship`
- `beam-unprotect-ship`
- `turret-protect-ship`
- `turret-unprotect-ship`
- `ship-invisible`
- `ship-visible`
- `ship-stealthy`
- `ship-unstealthy`
- `friendly-stealth-invisible`
- `friendly-stealth-visible`
- `primitive-sensors-set-range`
- `ship-targetable-as-bomb`
- `ship-untargetable-as-bomb`
- `kamikaze`
- `change-iff`
- `change-iff-color`
- `add-remove-escort`
- `ship-change-alt-name`
- `ship-change-callsign`
- `ship-tag`
- `ship-untag`
- `set-arrival-info`
- `set-departure-info`
- `alter-ship-flag`
- `alter-wing-flag`
- `cancel-future-waves`

## Ship Status 2
- `is-in-mission`
- `is-docked`
- `is-ship-visible`
- `is-ship-stealthy`
- `is-friendly-stealth-visible`
- `is-iff`
- `is-species`
- `is-ai-class`
- `is-ship-type`
- `is-ship-class`
- `is-facing`
- `is_tagged`
- `has-been-tagged-delay`
- `are-ship-flags-set`
- `are-wing-flags-set`
- `has-armor-type`
- `is-ship-emp-active`
- `get-throttle-speed`
- `current-speed`
- `is-nav-linked`

## Special Effects
- `set-post-effect`
- `reset-post-effects`
- `ship-effect`
- `ship-create`
- `weapon-create`
- `ship-vanish`
- `ship-vaporize`
- `ship-no-vaporize`
- `set-explosion-option`
- `create-bolt`
- `explosion-effect`
- `warp-effect`
- `clear-weapons`
- `clear-debris`
- `set-time-compression`
- `reset-time-compression`
- `call-ssm-strike`
- `set-gravity-accel`
- `force-rearm`
- `abort-rearm`

## Subsystems and Health
- `ship-invulnerable`
- `ship-vulnerable`
- `ship-guardian`
- `ship-no-guardian`
- `ship-guardian-threshold`
- `ship-subsys-guardian-threshold`
- `self-destruct`
- `destroy-instantly`
- `destroy-instantly-with-debris`
- `destroy-subsys-instantly`
- `sabotage-subsystem`
- `repair-subsystem`
- `ship-copy-damage`
- `set-subsystem-strength`
- `subsys-set-random`
- `lock-rotating-subsystem`
- `free-rotating-subsystem`
- `reverse-rotating-subsystem`
- `rotating-subsys-set-turn-time`
- `lock-translating-subsystem`
- `free-translating-subsystem`
- `reverse-translating-subsystem`
- `translating-subsys-set-speed`
- `trigger-submodel-animation`
- `change-subsystem-name`
- `ship-subsys-targetable`
- `ship-subsys-untargetable`
- `ship-subsys-no-replace`
- `ship-subsys-no-live-debris`
- `ship-subsys-vanish`
- `ship-subsys-ignore_if_dead`
- `awacs-set-radius`

## Time
- `time-ship-destroyed`
- `time-ship-arrived`
- `time-ship-departed`
- `time-wing-destroyed`
- `time-wing-arrived`
- `time-wing-departed`
- `mission-time`
- `mission-time-msecs`
- `time-docked`
- `time-undocked`
- `time-to-goal`
- `set-hud-timer-padding`

## Training
- `key-pressed`
- `key-reset`
- `key-reset-multiple`
- `ignore-key`
- `targeted`
- `node-targeted`
- `missile-locked`
- `speed`
- `facing`
- `facing-waypoint`
- `order`
- `query-orders`
- `reset-orders`
- `waypoint-missed`
- `waypoint-twice`
- `path-flown`
- `training-msg`
- `flash-hud-gauge`
- `primaries-depleted`
- `secondaries-depleted`
- `special-check`
- `set-training-context-fly-path`
- `set-training-context-speed`

## Variable Status
- `string-to-int`
- `string-get-length`

## Variables
- `modify-variable`
- `get-variable-by-index`
- `set-variable-by-index`
- `copy-variable-from-index`
- `copy-variable-between-indexes`
- `int-to-string`
- `string-concatenate`
- `string-concatenate-block`
- `string-get-substring`
- `string-set-substring`
- `modify-variable-xstr`

## Weapons, Shields and Engines
- `set-weapon-energy`
- `set-shield-energy`
- `set-player-throttle-speed`
- `set-afterburner-energy`
- `set-subspace-drive`
- `set-primary-weapon`
- `set-secondary-weapon`
- `set-primary-ammo`
- `set-secondary-ammo`
- `set-num-countermeasures`
- `lock-primary-weapon`
- `unlock-primary-weapon`
- `lock-secondary-weapon`
- `unlock-secondary-weapon`
- `lock-afterburner`
- `unlock-afterburner`
- `shields-on`
- `shields-off`
- `force-glide`
- `disable-ets`
- `enable-ets`
- `break-warp`
- `fix-warp`
- `never-warp`
- `allow-warp`
- `special-warpout-name`
- `set-ets-values`
- `get-power-output`

## Weapons, Shields and Engines Status
- `has-primary-weapon`
- `has-secondary-weapon`
- `is-primary-selected`
- `is-secondary-selected`
- `primary-fired-since`
- `turret-fired-since`
- `secondary-fired-since`
- `primary-ammo-pct`
- `secondary-ammo-pct`
- `get-primary-ammo`
- `get-secondary-ammo`
- `turret-get-primary-ammo`
- `turret-get-secondary-ammo`
- `turret-has-primary-weapon`
- `turret-has-secondary-weapon`
- `get-num-countermeasures`
- `weapon-energy-pct`
- `afterburner-energy-pct`
- `shield-recharge-pct`
- `weapon-recharge-pct`
- `engine-recharge-pct`
- `shield-quad-low`
- `get-ets-value`
- `is-in-turret-fov`

