"""
Tests for the advisory mission balance validator warning.

The balance check tallies allied (Friendly) and enemy (Hostile) combat weights,
factors in fighter/bomber shield status (``no-shields`` flag) and AI class, plus
wing ``wave_count``, then emits a non-fatal advisory warning when:

    |allied - enemy| / max(allied, enemy) >= 0.5  (50 %)

Reference scoring rules:
  * base weight = 1.0 per combat ship
  * fighters/bombers only: ×0.5 if the ``no-shields`` flag is set (and
    ``force-shields-on`` is absent)
  * fighters/bombers only: AI factor = 1 + 0.2*(tier_index - 2) where
    Coward=0, Lieutenant=1, Captain=2 (default), Major=3, Colonel=4, General=5
  * wings: sum of per-member weights × wave_count
  * pre-placed wreckage (destroyed_before_mission_seconds > 0) excluded
  * Unknown-team ships excluded entirely

Cases tested:
  - Equal allied/enemy fighters                → no warning
  - Diff below threshold (33 %)               → no warning
  - No enemy combat ships (edge case)          → no warning
  - Non-combat ships (transports) excluded     → no warning
  - Unknown-team ships excluded                → no warning
  - Unshielded enemies have reduced weight     → no warning when totals equal
  - Coward AI reduces enemy weight             → no warning when gap < 50 %
  - Pre-placed wreckage excluded               → no warning
  - Larger-ship AI class is NOT modified       → no warning for equal cruisers
  - Installation (GTI Arcadia) counts as combat weight 1.0  → balances score
  - Sentry gun (GTSG Watchdog) counts as combat weight 1.0  → balances score
  - Heavy enemy imbalance (67 %)              → warning
  - Exactly at 50 % threshold                 → warning
  - wave_count multiplies enemy (75 %)        → warning
  - Multiple waves (1 ally vs 6 effective)    → warning
  - General AI inflates enemy weight          → warning
  - None ai_class defaults to Captain         → same as Captain, warning at 50 %
  - Allied side is the stronger side          → warning (message names Allied)
  - Warning is advisory: validate() returns True
  - Warning message reports both scores and stronger side
"""

import unittest
import sys
from pathlib import Path

_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
_repo_root = _parent_dir.parent
for _p in (str(_repo_root), str(_parent_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Weapons, Wing
from validator import Validator

_REPO_ROOT = _repo_root

# Unique fragment present in every balance warning message.
_WARNING_FRAGMENT = "Mission balance may be lopsided"

# GTF Ulysses hardpoints: 2 primary, 1 secondary.
# Used for ALL fighter-type ships in these tests so hardpoint counts are known.
_ULYSSES_WEAPONS = Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


def _fighter_ship(name: str, team: str = "Hostile", ai_class: str = None,
                  flags=None, destroyed_before: int = 0) -> Ship:
    """Standalone GTF Ulysses fighter."""
    d = {
        "name": name,
        "class": "GTF Ulysses",
        "team": team,
        "position": [0.0, 0.0, float(abs(hash(name)) % 5000 + 100)],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known"],
        "weapons": _ULYSSES_WEAPONS,
        "destroyed_before_mission_seconds": destroyed_before,
    }
    if ai_class:
        d["ai_class"] = ai_class
    return Ship.model_validate(d)


def _fighter_wing(name: str, team: str, count: int, wave_count: int = 1,
                  ai_class: str = None, flags=None, pos_z: float = 1000.0) -> Wing:
    """Wing of ``count`` GTF Ulysses fighters."""
    ships = []
    for i in range(count):
        d = {
            "name": f"{name} {i + 1}",
            "class": "GTF Ulysses",
            "team": team,
            "position": [float(i * 60), 0.0, pos_z],
            "arrival_cue": "( true )",
            "flags": flags if flags is not None else ["cargo-known"],
            "weapons": _ULYSSES_WEAPONS,
        }
        if ai_class:
            d["ai_class"] = ai_class
        ships.append(Ship.model_validate(d))
    return Wing(
        name=name,
        count=count,
        ships=ships,
        position=[0.0, 0.0, pos_z],
        arrival_cue="( true )",
        wave_count=wave_count,
        initial_orders="( ai-chase-any 89 )",
    )


def _transport(name: str, team: str = "Hostile") -> Ship:
    """GTT Elysium transport — non-combat (excluded from balance tally)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTT Elysium",
        "team": team,
        "position": [300.0, 0.0, float(abs(hash(name)) % 3000 + 100)],
        "arrival_cue": "( true )",
        "flags": ["cargo-known"],
        "cargo": "personnel",
    })


def _installation(name: str, team: str = "Friendly") -> Ship:
    """GTI Arcadia installation — combat, weight 1.0 (not in NON_COMBAT_SHIP_CLASSES).
    Given the 'escort' flag to avoid triggering the unrelated escort-list warning.
    """
    return Ship.model_validate({
        "name": name,
        "class": "GTI Arcadia",
        "team": team,
        "position": [1500.0, 0.0, 500.0],
        "arrival_cue": "( true )",
        "flags": ["cargo-known", "escort"],
    })


def _sentry_gun(name: str, team: str = "Hostile") -> Ship:
    """GTSG Watchdog sentry gun — combat, weight 1.0 (not in NON_COMBAT_SHIP_CLASSES)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTSG Watchdog",
        "team": team,
        "position": [500.0, 0.0, 200.0],
        "arrival_cue": "( true )",
        "flags": ["cargo-known"],
    })


def _cruiser(name: str, team: str = "Hostile", ai_class: str = None) -> Ship:
    """SC Cain cruiser — combat, NOT a fighter/bomber (AI class does not modify weight)."""
    d = {
        "name": name,
        "class": "SC Cain",
        "team": team,
        "position": [800.0, 0.0, 1500.0],
        "arrival_cue": "( true )",
        "flags": ["cargo-known"],
    }
    if ai_class:
        d["ai_class"] = ai_class
    return Ship.model_validate(d)


def _make_mission(allied_count: int = 1, *extra_entities) -> Mission:
    """Build a mission with an Alpha wing of *allied_count* GTF Ulysses fighters
    plus any extra ships/wings passed as additional positional arguments.

    The player starts as Alpha 1.
    """
    alpha_wing = _fighter_wing("Alpha", "Friendly", allied_count, pos_z=0.0)
    all_ships = list(alpha_wing.ships)
    all_wings = [alpha_wing]

    for item in extra_entities:
        if isinstance(item, Wing):
            all_wings.append(item)
            all_ships.extend(item.ships)
        elif isinstance(item, Ship):
            all_ships.append(item)

    return Mission(
        mission_info=MissionInfo(name="Balance Test"),
        player_setup=PlayerSetup(start_ship="Alpha 1"),
        environment=Environment(),
        ships=all_ships,
        wings=all_wings,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMissionBalanceWarning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import logging
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        import logging
        logging.disable(logging.NOTSET)

    def _has_balance_warning(self, v: Validator) -> bool:
        return any(_WARNING_FRAGMENT in w for w in v.warnings)

    # ------------------------------------------------------------------
    # Cases that must NOT trigger the balance warning
    # ------------------------------------------------------------------

    def test_equal_counts_no_warning(self):
        """1 allied fighter vs 1 enemy fighter: 0 % diff → no warning."""
        enemy = _fighter_wing("Rama", "Hostile", 1)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"No warning for 1v1; warnings: {v.warnings}")

    def test_below_threshold_no_warning(self):
        """2 allied vs 3 enemy: |2-3|/3 = 33 % < 50 % → no warning."""
        enemy = _fighter_wing("Rama", "Hostile", 3)
        m = _make_mission(2, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"No warning for 2v3 (33%); warnings: {v.warnings}")

    def test_no_enemy_combat_ships_skips_warning(self):
        """No enemy combat ships (enemy_score = 0): edge case, warning is suppressed.

        A mission with zero enemy combat presence is a 'no opposition'
        scenario, not a balance imbalance.
        """
        m = _make_mission(1)   # only Alpha wing, no enemies
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"No warning when enemy_score=0; warnings: {v.warnings}")

    def test_non_combat_ships_excluded(self):
        """Transports are non-combat and must not affect the tally.

        1 allied vs 1 enemy fighter (balanced), plus 4 hostile transports
        that contribute zero weight → still no warning.
        """
        enemy_wing = _fighter_wing("Rama", "Hostile", 1)
        transports = [_transport(f"GTT Elysium {i}", team="Hostile")
                      for i in range(1, 5)]
        m = _make_mission(1, enemy_wing, *transports)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"Transports must not affect balance; warnings: {v.warnings}")

    def test_unknown_team_excluded(self):
        """Unknown-team ships are excluded; a swarm of Unknown fighters must
        not trigger the warning.

        6 Unknown fighters would cause a 6:1 imbalance if counted, but they
        must be ignored entirely.
        """
        unknown_wing = _fighter_wing("Krishna", "Unknown", 6, pos_z=3000.0)
        m = _make_mission(1, unknown_wing)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"Unknown-team ships must be excluded; warnings: {v.warnings}")

    def test_unshielded_enemies_halve_effective_weight(self):
        """4 unshielded enemy fighters (weight 0.5 each = 2.0 total) vs
        2 allied fighters (weight 1.0 each = 2.0 total) → balanced, no warning.

        Shield modifier: GTF Ulysses with 'no-shields' flag → × 0.5.
        """
        enemy = _fighter_wing("Rama", "Hostile", 4,
                               flags=["cargo-known", "no-shields"])
        m = _make_mission(2, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"4 unshielded enemies = 2 allied (2.0 each); warnings: {v.warnings}")

    def test_coward_ai_reduces_enemy_weight(self):
        """Coward fighters: weight = 1 + 0.2*(0-2) = 0.6 each.
        3 Coward enemies = 1.8 total vs 2 allied (2.0).
        |2.0-1.8|/2.0 = 10 % < 50 % → no warning.
        """
        enemy = _fighter_wing("Rama", "Hostile", 3, ai_class="Coward")
        m = _make_mission(2, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"Coward AI reduces enemy weight; warnings: {v.warnings}")

    def test_pre_placed_wreckage_excluded(self):
        """Ships with destroyed_before_mission_seconds > 0 are wreckage and
        must not be tallied. A wing of 6 pre-destroyed enemies contributes 0.
        """
        wreck_ships = [
            _fighter_ship(f"Rama {i + 1}", team="Hostile", destroyed_before=30)
            for i in range(6)
        ]
        wreck_wing = Wing(
            name="Rama",
            count=6,
            ships=wreck_ships,
            position=[0.0, 0.0, 2000.0],
            arrival_cue="( true )",
            initial_orders="( ai-chase-any 89 )",
        )
        m = _make_mission(1, wreck_wing)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"Wreckage must be excluded; warnings: {v.warnings}")

    def test_larger_ship_ai_class_not_modified(self):
        """AI class does NOT modify weight for non-fighter/bomber ships.

        1 allied fighter (1.0) vs 1 General-AI SC Cain cruiser (weight 1.0
        unchanged — AI factor applies to fighters/bombers only).
        |1.0-1.0|/1.0 = 0 → no warning.
        """
        enemy_cruiser = _cruiser("SC Cain 1", ai_class="General")
        m = _make_mission(1, enemy_cruiser)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"General AI on cruiser must not boost its weight; warnings: {v.warnings}")

    def test_installation_counts_as_combat_weight(self):
        """GTI Arcadia installation is a combat ship (weight 1.0).

        1 allied fighter + 1 friendly installation (allied = 2.0) vs
        3 enemy fighters (enemy = 3.0).
        |2.0-3.0|/3.0 = 33 % < 50 % → no warning (installation contributes).
        """
        install = _installation("GTI Arcadia 1", team="Friendly")
        enemy = _fighter_wing("Rama", "Hostile", 3)
        m = _make_mission(1, install, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"Installation should add allied combat weight; warnings: {v.warnings}")

    def test_sentry_gun_counts_as_combat_weight(self):
        """GTSG Watchdog sentry gun is a combat ship (weight 1.0).

        1 allied fighter (1.0) vs 1 enemy sentry gun (1.0) → 0 % diff → no warning.
        """
        sentry = _sentry_gun("GTSG Watchdog 1", team="Hostile")
        m = _make_mission(1, sentry)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertFalse(self._has_balance_warning(v),
                         f"Sentry gun must count as enemy combat weight 1.0; warnings: {v.warnings}")

    # ------------------------------------------------------------------
    # Cases that MUST trigger the balance warning
    # ------------------------------------------------------------------

    def test_heavy_enemy_imbalance_warns(self):
        """1 allied vs 3 enemy fighters: |1-3|/3 = 67 % >= 50 % → warning."""
        enemy = _fighter_wing("Rama", "Hostile", 3)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"Expected warning for 1v3 (67%); warnings: {v.warnings}")

    def test_exactly_at_threshold_warns(self):
        """1 allied vs 2 enemy fighters: |1-2|/2 = 50 % (>= threshold) → warning."""
        enemy = _fighter_wing("Rama", "Hostile", 2)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"Expected warning at exactly 50%; warnings: {v.warnings}")

    def test_wave_count_multiplies_enemy_strength(self):
        """1 member × 4 waves = effective weight 4.
        1 allied (1.0) vs 4 effective enemy (4.0): |1-4|/4 = 75 % → warning.
        """
        enemy = _fighter_wing("Rama", "Hostile", 1, wave_count=4)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"Expected warning when wave_count=4; warnings: {v.warnings}")

    def test_multiple_wave_members_warns(self):
        """2 members × 3 waves = effective weight 6.
        1 allied (1.0) vs 6 effective enemies: |1-6|/6 = 83 % → warning.
        """
        enemy = _fighter_wing("Rama", "Hostile", 2, wave_count=3)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"Expected warning for 1 ally vs 6 effective enemies; warnings: {v.warnings}")

    def test_general_ai_inflates_enemy_weight(self):
        """General fighters: weight = 1 + 0.2*(5-2) = 1.6 each.
        3 General enemies = 4.8 total vs 1 allied (1.0).
        |1.0-4.8|/4.8 = 79 % → warning.
        """
        enemy = _fighter_wing("Rama", "Hostile", 3, ai_class="General")
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"Expected warning for General AI enemies; warnings: {v.warnings}")

    def test_none_ai_class_defaults_to_captain(self):
        """ai_class=None must default to Captain (factor 1.0), same as Captain.

        1 allied vs 2 None-ai_class enemies → |1-2|/2 = 50 % → warning.
        """
        enemy = _fighter_wing("Rama", "Hostile", 2)   # ai_class omitted → None
        for s in enemy.ships:
            self.assertIsNone(s.ai_class, "ai_class must be None")
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"None ai_class should default to Captain; warnings: {v.warnings}")

    def test_allied_side_can_be_stronger(self):
        """The allied side can also be the dominant side.

        4 allied fighters (4.0) vs 1 enemy fighter (1.0): |4-1|/4 = 75 % → warning.
        The warning message must name 'Allied' as the stronger side.
        """
        enemy = _fighter_wing("Rama", "Hostile", 1)
        m = _make_mission(4, enemy)
        v = _make_validator(m)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(self._has_balance_warning(v),
                        f"Expected warning when allied is stronger; warnings: {v.warnings}")
        balance_msg = next(w for w in v.warnings if _WARNING_FRAGMENT in w)
        self.assertIn("Allied", balance_msg,
                      "Warning must name 'Allied' as the stronger side.")

    # ------------------------------------------------------------------
    # Warning quality and advisory behaviour
    # ------------------------------------------------------------------

    def test_warning_is_advisory_validate_returns_true(self):
        """Even when the balance warning fires, validate() must return True
        because balance warnings are advisory (non-fatal).
        """
        enemy = _fighter_wing("Rama", "Hostile", 4)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        result = v.validate()
        self.assertTrue(result,
                        f"validate() must return True for advisory warning; errors: {v.errors}")
        self.assertTrue(self._has_balance_warning(v),
                        f"A balance warning should have been emitted; warnings: {v.warnings}")
        self.assertEqual([], v.errors,
                         f"No errors expected; errors: {v.errors}")

    def test_warning_message_reports_both_scores(self):
        """The warning message must report both the allied and enemy scores."""
        enemy = _fighter_wing("Rama", "Hostile", 4)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        v.validate()
        msgs = [w for w in v.warnings if _WARNING_FRAGMENT in w]
        self.assertTrue(msgs, "At least one balance warning expected.")
        msg = msgs[0]
        self.assertIn("Allied combat score", msg,
                      "Warning should report Allied combat score.")
        self.assertIn("Enemy combat score", msg,
                      "Warning should report Enemy combat score.")

    def test_warning_message_reports_stronger_side(self):
        """The warning message explicitly names the dominant side."""
        enemy = _fighter_wing("Rama", "Hostile", 4)
        m = _make_mission(1, enemy)
        v = _make_validator(m)
        v.validate()
        msgs = [w for w in v.warnings if _WARNING_FRAGMENT in w]
        msg = msgs[0]
        # Enemy is the dominant side when 4 enemies face 1 ally.
        self.assertIn("Enemy", msg,
                      "Warning must name 'Enemy' as the dominant side.")


if __name__ == "__main__":
    unittest.main()
