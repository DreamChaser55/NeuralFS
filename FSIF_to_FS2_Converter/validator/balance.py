# balance.py
# Mixin: advisory mission combat-balance check.

# ---------------------------------------------------------------------------
# Classification constants
# ---------------------------------------------------------------------------

# Primary weapons that cannot penetrate shields.  Fighters and bombers whose
# entire primary loadout consists only of weapons from this set are at a
# significant tactical disadvantage against shielded ships and receive a
# reduced combat weight.
#
# Sources: FSO weapon tables and FS lore references.
SHIELD_INEFFECTIVE_PRIMARIES: frozenset = frozenset({
    'ML-16 Laser',       # Low damage, negligible shield penetration
    'Vasudan Light Laser',  # Vasudan equivalent of ML-16; same deficiency
    'Disruptor',         # Hull/subsystem weapon; zero shield damage by design
    'Training',          # Training weapon; no meaningful combat effect
})

# Weight penalty applied to a fighter/bomber whose entire primary loadout
# consists only of shield-ineffective weapons.
_SHIELD_INEFFECTIVE_PRIMARY_FACTOR = 0.5

# Sentry-gun ship classes.  Sentry guns are combat ships (they carry turrets
# and actively fire on enemies) but they are small, stationary, and easily
# destroyed, so they receive a reduced weight of 0.5 instead of the default
# 1.0.  This weight applies to all four canonical sentry gun classes.
SENTRY_GUN_CLASSES: frozenset = frozenset({
    'GTSG Watchdog',   # Standard Terran defensive turret
    'GTSG Cerberus',   # Heavier Watchdog variant
    'PVSG Ankh',       # Standard Vasudan defensive turret
    'SSG Trident',     # Shivan repair/supply depot turret
})

# Weight factor applied to all sentry gun classes.  Sentry guns are weak and
# easily destroyed in combat, so they contribute only half the combat value of
# a normal warship of equivalent hitpoints.
_SENTRY_GUN_FACTOR = 0.5

# Ship classes that are NOT combat-capable and must be excluded from the
# balance tally.  Everything in the supported spacecraft roster that is NOT
# in this set is treated as a combat ship with base weight 1.0 (before any
# per-class modifiers such as the sentry-gun factor above).
#
# Counted as combat (NOT in this set):
#   fighters, bombers, cruisers, destroyers, juggernauts,
#   installations, and sentry guns (all carry weapons / participate in fights).
#
# Excluded (NOT combat, weight 0):
#   transports, freighters, cargo containers, nav buoys, escape pods,
#   science vessels, support ships, and training drones.
NON_COMBAT_SHIP_CLASSES: frozenset = frozenset({
    # --- Transports ---
    'GTT Elysium',
    'PVT Isis',
    'ST Azrael',
    # --- Freighters ---
    'GTFr Chronos',
    'GTFr Poseidon',
    "PVFr Bast",
    "PVFr Ma'at",
    'PVFr Satis',
    'SFr Mephisto',
    'SFr Asmodeus',
    # --- Cargo containers ---
    'TC 2',
    'TSC 2',
    'TAC 1',
    'TTC 1',
    'VC 3',
    'VAC 4',
    'SC 5',
    'SAC 2',
    # --- Navigation buoys ---
    'Terran NavBuoy',
    # --- Escape pods ---
    'GTEP Hermes',
    'PVEP Ra',
    # --- Science vessels ---
    'GTSC Faustus',
    # --- Support ships ---
    'GTS Centaur',
    'PVS Scarab',
    # --- Training drones ---
    'GTDr Amazon',
    'GTDr Amazon Advanced',
    'PVDr Jackal',
})

# AI class tiers, ordered worst → best.  Captain (index 2) is the reference
# tier: it corresponds to the default $AI Class in the ship tables and does
# not modify weight.
_AI_CLASS_ORDER = ('Coward', 'Lieutenant', 'Captain', 'Major', 'Colonel', 'General')
_AI_CLASS_INDEX = {cls: idx for idx, cls in enumerate(_AI_CLASS_ORDER)}
_AI_CAPTAIN_INDEX = 2       # index of the reference tier
_AI_STEP = 0.2              # multiplicative adjustment per tier vs Captain

# Relative-difference threshold above which a mission is considered lopsided.
_IMBALANCE_THRESHOLD = 0.5  # 50 %


class BalanceChecksMixin:
    """Advisory check: warn when allied and enemy combat scores diverge by >= 50%.

    Scoring rules
    -------------
    * Every *combat* ship (any class **not** in ``NON_COMBAT_SHIP_CLASSES``)
      starts with a base weight of **1.0**.
    * **Sentry-gun modifier** — weight *= 0.5 for all classes in
      ``SENTRY_GUN_CLASSES``.  Sentry guns are small, stationary, and easily
      destroyed, so they count for half the weight of a normal warship.
    * For fighters and bombers only:
      - **Shield modifier** — weight *= 0.5 when the ship carries the
        ``no-shields`` flag **and** does not carry ``force-shields-on``.
        Larger ships cannot carry shields in FreeSpace, so their weight is
        never modified for shields.
      - **Primary-weapon shield-penetration modifier** — weight *= 0.5 when
        the ship's entire primary loadout consists only of weapons in
        ``SHIELD_INEFFECTIVE_PRIMARIES`` (ML-16 Laser, Vasudan Light Laser,
        Disruptor, Training).  A fighter/bomber that cannot penetrate shields
        with any of its guns is at a significant disadvantage against shielded
        opponents.  A mixed loadout containing at least one shield-penetrating
        primary is not penalised.  An empty primary list is not penalised.
        This modifier stacks with the shield modifier above.
      - **AI-class modifier** — weight *= ``1 + 0.2 * (ai_index - 2)``,
        where ``ai_index`` is the ship's position in the ordered ladder
        Coward / Lieutenant / **Captain** / Major / Colonel / General.
        A missing ``ai_class`` defaults to Captain (index 2, factor 1.0).
    * Wing totals = sum of per-member weights * ``wave_count`` (all waves).
    * Pre-placed wreckage (``destroyed_before_mission_seconds > 0``) is
      excluded from the tally.
    * ``Friendly`` ships contribute to the **allied** score;
      ``Hostile`` ships contribute to the **enemy** score;
      ``Unknown`` ships are excluded entirely from the tally.

    Threshold
    ---------
    ``relative_difference = |allied - enemy| / max(allied, enemy)``

    The warning fires when ``relative_difference >= 0.5`` **and** both sides
    have a non-zero combat score.  A mission where one side has no combat ships
    at all (e.g. a pure ferry mission with no enemies) is a different scenario
    and is not flagged as a balance issue.

    The warning is advisory and does not abort conversion.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _combat_weight(self, ship) -> float:
        """Return the combat weight of *ship*, or 0.0 if non-combat / excluded.

        ``ship`` is a runtime ``data_models.Ship`` instance.
        """
        # Unknown ship class → skip (already flagged elsewhere in validate_ships)
        if ship.ship_class not in self.ship_classes:
            return 0.0
        # Explicitly non-combat class → excluded from tally
        if ship.ship_class in NON_COMBAT_SHIP_CLASSES:
            return 0.0

        weight = 1.0

        # Sentry-gun modifier: sentry guns are small, stationary, and easily
        # destroyed — they are worth only half a standard combat ship.
        if ship.ship_class in SENTRY_GUN_CLASSES:
            weight *= _SENTRY_GUN_FACTOR

        is_fighter_bomber = ship.ship_class in self.fighter_bomber_classes

        if is_fighter_bomber:
            # Shield modifier: only meaningful for fighters/bombers.
            # Larger ships cannot have shields in FreeSpace; their weight
            # is not modified by this factor.
            flags = set(ship.flags)
            if 'no-shields' in flags and 'force-shields-on' not in flags:
                weight *= 0.5

            # Primary-weapon shield-penetration modifier.
            # If the ship has a non-empty primary list and every weapon in it
            # cannot penetrate shields, the ship is at a significant
            # disadvantage against shielded opponents.
            primaries = ship.weapons.primary
            if primaries and all(w in SHIELD_INEFFECTIVE_PRIMARIES for w in primaries):
                weight *= _SHIELD_INEFFECTIVE_PRIMARY_FACTOR

            # AI-class modifier.
            ai_name = ship.ai_class if ship.ai_class else 'Captain'
            ai_idx = _AI_CLASS_INDEX.get(ai_name, _AI_CAPTAIN_INDEX)
            ai_factor = 1.0 + _AI_STEP * (ai_idx - _AI_CAPTAIN_INDEX)
            weight *= ai_factor

        return weight

    # ------------------------------------------------------------------
    # Main validation method
    # ------------------------------------------------------------------

    def validate_mission_balance(self):
        """Check whether allied and enemy combat scores are reasonably balanced.

        Tallies all combat ships (including all wing waves) and emits a
        non-fatal advisory warning when the relative difference between the
        allied and enemy scores is >= 50% of the stronger side's score.
        """
        allied: float = 0.0
        enemy: float = 0.0

        # ── Determine which ships belong to a wing ──────────────────────────
        wing_member_names: set = set()
        for wing in self.mission.wings:
            for s in wing.ships:
                wing_member_names.add(s.name)

        # ── Standalone ships (not part of any wing) ─────────────────────────
        for ship in self.mission.ships:
            if ship.name in wing_member_names:
                continue  # handled via the wing loop below (with wave_count)
            if ship.destroyed_before_mission_seconds > 0:
                continue  # pre-placed wreckage — not a live combatant
            w = self._combat_weight(ship)
            if ship.team == 'Friendly':
                allied += w
            elif ship.team == 'Hostile':
                enemy += w
            # Unknown: excluded per design decision

        # ── Wings: sum per-member weights, multiply by wave_count ───────────
        for wing in self.mission.wings:
            if not wing.ships:
                continue

            # Sum one full wave (mission.ships holds the expanded first-wave
            # members; additional waves are identical, captured by wave_count).
            wave_weight: float = 0.0
            for ship in wing.ships:
                if ship.destroyed_before_mission_seconds > 0:
                    continue
                wave_weight += self._combat_weight(ship)

            total_wing_weight = wave_weight * wing.wave_count

            # All members of a valid FSIF wing share the same team (from the
            # single ship template).  Use the first member's team.
            team = wing.ships[0].team
            if team == 'Friendly':
                allied += total_wing_weight
            elif team == 'Hostile':
                enemy += total_wing_weight
            # Unknown: excluded

        # ── No-opposition edge case ─────────────────────────────────────────
        # When one side has zero combat weight the scenario is intentional
        # (e.g. a pure escort / ferry mission with no enemy combat ships),
        # not an imbalance; skip the warning.
        if allied <= 0.0 or enemy <= 0.0:
            return

        # ── Balance test ────────────────────────────────────────────────────
        max_score = max(allied, enemy)
        relative_diff = abs(allied - enemy) / max_score

        if relative_diff < _IMBALANCE_THRESHOLD:
            return

        stronger_side = 'Allied' if allied > enemy else 'Enemy'
        diff_pct = relative_diff * 100.0

        self.log_warning(
            f"Mission balance may be lopsided: "
            f"Allied combat score {allied:.2f}, Enemy combat score {enemy:.2f} "
            f"(relative difference {diff_pct:.0f}%, "
            f"threshold {int(_IMBALANCE_THRESHOLD * 100)}%). "
            f"The {stronger_side} side is significantly stronger. "
            f"Scores account for relative weakness of sentry guns (x{_SENTRY_GUN_FACTOR}), "
            f"fighter/bomber shield status (unshielded = x0.5), "
            f"primary weapons unable to penetrate shields (all-ineffective loadout = x0.5), "
            f"AI class relative to Captain (x{_AI_STEP} per tier above/below), "
            f"and wing wave counts. "
            f"Consider adjusting ship counts, AI classes, shield settings, "
            f"or primary weapon loadouts for a more balanced encounter."
        )
