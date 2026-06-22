# balance.py
# Mixin: advisory mission combat-balance check.

# ---------------------------------------------------------------------------
# Classification constants
# ---------------------------------------------------------------------------

# Ship classes that are NOT combat-capable and must be excluded from the
# balance tally.  Everything in the supported spacecraft roster that is NOT
# in this set is treated as a combat ship with base weight 1.0.
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
    * For fighters and bombers only:
      - **Shield modifier** — weight *= 0.5 when the ship carries the
        ``no-shields`` flag **and** does not carry ``force-shields-on``.
        Larger ships cannot carry shields in FreeSpace, so their weight is
        never modified for shields.
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
        is_fighter_bomber = ship.ship_class in self.fighter_bomber_classes

        if is_fighter_bomber:
            # Shield modifier: only meaningful for fighters/bombers.
            # Larger ships cannot have shields in FreeSpace; their weight
            # is not modified by this factor.
            flags = set(ship.flags)
            if 'no-shields' in flags and 'force-shields-on' not in flags:
                weight *= 0.5

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
            f"Scores account for fighter/bomber shield status (unshielded = x0.5), "
            f"AI class relative to Captain (x{_AI_STEP} per tier above/below), "
            f"and wing wave counts. "
            f"Consider adjusting ship counts, AI classes, or shield settings "
            f"for a more balanced encounter."
        )
