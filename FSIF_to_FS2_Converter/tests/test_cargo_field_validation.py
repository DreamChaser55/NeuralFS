"""
Tests for the four cargo-field validation checks added to ``validate_cargo_field()``.

Rule summary:
1. ERROR   — cargo defined on a ship whose class is not a transport or cargo container.
2. WARNING — a Friendly transport or cargo container has no cargo defined.
3. WARNING — a Friendly ship has cargo defined but is missing the 'cargo-known' flag.
4. ERROR   — a ship has both the 'scannable' flag and cargo defined.

All four checks are exercised here.  Each test is named after the specific rule
and expected outcome (error / no-error / warning / no-warning).
"""

import sys
import unittest
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap (mirrors other test files in the same package)
# ---------------------------------------------------------------------------
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent      # FSIF_to_FS2_Converter/
_repo_root = _parent_dir.parent        # NeuralFS/

for _p in (str(_repo_root), str(_parent_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_models import Mission, MissionInfo, PlayerSetup, Environment, Ship, Weapons, Wing
from validator import Validator

_REPO_ROOT = _repo_root


# ---------------------------------------------------------------------------
# Unique string fragments in each check's messages
# ---------------------------------------------------------------------------
_ERR_FRAG_NON_CAPABLE   = "support the cargo string in FSO"      # check 1 error
_ERR_FRAG_SCANNABLE     = "completely overrides the cargo"        # check 4 error
_WARN_FRAG_NO_CARGO     = "has no cargo defined"                  # check 2 warning
_WARN_FRAG_NO_KNOWN     = "missing the 'cargo-known' flag"        # check 3 warning


# ---------------------------------------------------------------------------
# Ship factory helpers
# ---------------------------------------------------------------------------

def _fighter(name: str, *, cargo: str = "Nothing", flags=None) -> Ship:
    """Minimal GTF Ulysses.  Default cargo and cargo-known (to avoid unrelated warnings)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTF Ulysses",
        "team": "Friendly",
        "position": [0.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known"],
        "cargo": cargo,
        "weapons": Weapons(primary=["Avenger", "Avenger"], secondary=["MX-50"]),
    })


def _transport(name: str, *, team: str = "Friendly", cargo: str = "Nothing", flags=None) -> Ship:
    """Minimal GTT Elysium transport."""
    return Ship.model_validate({
        "name": name,
        "class": "GTT Elysium",
        "team": team,
        "position": [800.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known", "escort"],
        "cargo": cargo,
    })


def _vasudan_transport(name: str, *, team: str = "Friendly", cargo: str = "Nothing",
                       flags=None) -> Ship:
    """Minimal PVT Isis (Vasudan transport)."""
    return Ship.model_validate({
        "name": name,
        "class": "PVT Isis",
        "team": team,
        "position": [900.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known", "escort"],
        "cargo": cargo,
    })


def _shivan_transport(name: str, *, team: str = "Hostile", cargo: str = "Nothing",
                      flags=None) -> Ship:
    """Minimal ST Azrael (Shivan transport)."""
    return Ship.model_validate({
        "name": name,
        "class": "ST Azrael",
        "team": team,
        "position": [1000.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known"],
        "cargo": cargo,
    })


def _cargo_container(name: str, *, team: str = "Friendly", cargo: str = "Nothing",
                     flags=None) -> Ship:
    """Minimal TC 2 (Terran cargo container)."""
    return Ship.model_validate({
        "name": name,
        "class": "TC 2",
        "team": team,
        "position": [300.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known"],
        "cargo": cargo,
    })


def _tsc2_container(name: str, *, team: str = "Friendly", cargo: str = "Nothing",
                    flags=None) -> Ship:
    """Minimal TSC 2 (hardened military cargo container)."""
    return Ship.model_validate({
        "name": name,
        "class": "TSC 2",
        "team": team,
        "position": [350.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known"],
        "cargo": cargo,
    })


def _freighter(name: str, *, team: str = "Friendly", cargo: str = "Nothing",
               flags=None) -> Ship:
    """Minimal GTFr Poseidon (armed freighter — NOT cargo-capable)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTFr Poseidon",
        "team": team,
        "position": [600.0, 0.0, 0.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known", "escort"],
        "cargo": cargo,
    })


def _cruiser(name: str, *, team: str = "Friendly", cargo: str = "Nothing",
             flags=None) -> Ship:
    """Minimal GTC Fenris (cruiser — NOT cargo-capable)."""
    return Ship.model_validate({
        "name": name,
        "class": "GTC Fenris",
        "team": team,
        "position": [500.0, 0.0, 500.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else ["cargo-known", "escort"],
        "cargo": cargo,
    })


def _hostile_fighter(name: str, *, cargo: str = "Nothing", flags=None) -> Ship:
    """Minimal hostile SF Scorpion (fighter — NOT cargo-capable)."""
    return Ship.model_validate({
        "name": name,
        "class": "SF Scorpion",
        "team": "Hostile",
        "position": [2000.0, 0.0, 2000.0],
        "arrival_cue": "( true )",
        "flags": flags if flags is not None else [],
        "cargo": cargo,
        "weapons": Weapons(primary=["Shivan Light Laser", "Shivan Light Laser"],
                           secondary=["MX-50#Shivan"]),
    })


def _alpha_wing(ships) -> Wing:
    """Minimal Alpha wing for player start."""
    return Wing(
        name="Alpha",
        count=len(ships),
        ships=ships,
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )


def _make_mission(*ships) -> Mission:
    """Build a minimal Mission.  The first GTF Ulysses-class ship becomes the player start."""
    all_ships = list(ships)
    start_name = all_ships[0].name
    for s in all_ships:
        if s.ship_class == "GTF Ulysses":
            start_name = s.name
            break
    start_ship = next(s for s in all_ships if s.name == start_name)
    player_wing = _alpha_wing([start_ship])
    return Mission(
        mission_info=MissionInfo(name="CargoTest"),
        player_setup=PlayerSetup(start_ship=start_name),
        environment=Environment(),
        ships=all_ships,
        wings=[player_wing],
    )


def _make_validator(mission: Mission) -> Validator:
    return Validator(mission, _REPO_ROOT)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestCargoFieldValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    # ===================================================================
    # CHECK 1: cargo on non-cargo-capable ship → ERROR
    # ===================================================================

    def test_check1_cargo_on_cruiser_is_error(self):
        """Cruiser (GTC Fenris) with cargo → validation error."""
        player = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1", cargo="secret documents")
        mission = _make_mission(player, cruiser)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Expected non-capable error, got: {v.errors}",
        )

    def test_check1_cargo_on_freighter_is_error(self):
        """Freighter (GTFr Poseidon) with cargo → validation error."""
        player = _fighter("Alpha 1")
        fr = _freighter("GTFr Trent", cargo="supplies")
        mission = _make_mission(player, fr)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Expected non-capable error, got: {v.errors}",
        )

    def test_check1_cargo_on_hostile_fighter_is_error(self):
        """Hostile fighter (SF Scorpion) with cargo → validation error."""
        player = _fighter("Alpha 1")
        enemy = _hostile_fighter("SF Dragon 1", cargo="contraband")
        mission = _make_mission(player, enemy)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Expected non-capable error, got: {v.errors}",
        )

    def test_check1_cargo_nothing_on_cruiser_is_fine(self):
        """Cruiser with default cargo='Nothing' is NOT an error."""
        player = _fighter("Alpha 1")
        cruiser = _cruiser("GTC Fenris 1")  # cargo defaults to "Nothing"
        mission = _make_mission(player, cruiser)
        v = _make_validator(mission)
        # Validate may warn (orientation etc.) but must not error on cargo
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error on cargo='Nothing': {v.errors}",
        )

    def test_check1_cargo_on_transport_is_ok(self):
        """Transport (GTT Elysium) with cargo defined → no cargo error."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1", cargo="civilians")
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error for transport: {v.errors}",
        )

    def test_check1_cargo_on_vasudan_transport_is_ok(self):
        """Vasudan transport (PVT Isis) with cargo → no cargo class error."""
        player = _fighter("Alpha 1")
        t = _vasudan_transport("PVT Nile 1", team="Friendly", cargo="refugees",
                               flags=["cargo-known", "escort"])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error for PVT Isis: {v.errors}",
        )

    def test_check1_cargo_on_shivan_transport_is_ok(self):
        """Shivan transport (ST Azrael) with cargo → no cargo class error."""
        player = _fighter("Alpha 1")
        t = _shivan_transport("ST Azrael 1", cargo="Shivan intel")
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error for ST Azrael: {v.errors}",
        )

    def test_check1_cargo_on_tc2_container_is_ok(self):
        """TC 2 cargo container with cargo → no cargo class error."""
        player = _fighter("Alpha 1")
        c = _cargo_container("TC 2 Crate", cargo="weapon parts")
        mission = _make_mission(player, c)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error for TC 2: {v.errors}",
        )

    def test_check1_cargo_on_tsc2_container_is_ok(self):
        """TSC 2 container with cargo → no cargo class error."""
        player = _fighter("Alpha 1")
        c = _tsc2_container("TSC 2 Box", cargo="civilians")
        mission = _make_mission(player, c)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error for TSC 2: {v.errors}",
        )

    # ===================================================================
    # CHECK 2: Friendly transport/cargo container with no cargo → WARNING
    # ===================================================================

    def test_check2_friendly_transport_no_cargo_warns(self):
        """Friendly GTT Elysium with no cargo defined → warning emitted,
        validation still passes."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1")  # cargo='Nothing' (default)
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Expected no-cargo warning for friendly transport, got: {v.warnings}",
        )

    def test_check2_friendly_cargo_container_no_cargo_warns(self):
        """Friendly TC 2 with no cargo → warning."""
        player = _fighter("Alpha 1")
        c = _cargo_container("TC 2 Crate")  # cargo='Nothing'
        mission = _make_mission(player, c)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Expected no-cargo warning for friendly cargo container, got: {v.warnings}",
        )

    def test_check2_hostile_transport_no_cargo_no_warn(self):
        """Hostile transport without cargo → no check-2 warning (check is Friendly-only)."""
        player = _fighter("Alpha 1")
        t = _shivan_transport("ST Azrael 1", team="Hostile")  # no cargo, hostile
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Unexpected no-cargo warning for hostile transport: {v.warnings}",
        )

    def test_check2_friendly_transport_with_cargo_no_warn(self):
        """Friendly transport WITH cargo → no check-2 warning."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1", cargo="evacuees")
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Unexpected no-cargo warning when cargo is set: {v.warnings}",
        )

    def test_check2_cargo_nothing_explicit_warns(self):
        """Explicit cargo='Nothing' is treated same as default (not defined) → warning."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1", cargo="Nothing")
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Expected no-cargo warning for cargo='Nothing', got: {v.warnings}",
        )

    def test_check2_cargo_nothing_case_insensitive_warns(self):
        """Cargo 'nothing' (lowercase) is also treated as not defined → warning."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1", cargo="nothing")
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Expected no-cargo warning for cargo='nothing', got: {v.warnings}",
        )

    # ===================================================================
    # CHECK 3: Friendly ship with cargo but no cargo-known flag → WARNING
    # ===================================================================

    def test_check3_friendly_transport_cargo_no_cargokown_warns(self):
        """Friendly transport with cargo defined but no cargo-known flag → warning,
        validation still passes."""
        player = _fighter("Alpha 1")
        # Explicitly omit cargo-known (use only 'escort')
        t = _transport("GTT Evac 1", cargo="evacuees", flags=["escort"])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertTrue(v.validate(), v.errors)
        self.assertTrue(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Expected no-cargo-known warning, got: {v.warnings}",
        )

    def test_check3_friendly_transport_cargo_with_cargokown_no_warn(self):
        """Friendly transport with cargo AND cargo-known → no check-3 warning."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1", cargo="evacuees", flags=["cargo-known", "escort"])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Unexpected no-cargo-known warning when flag is present: {v.warnings}",
        )

    def test_check3_hostile_transport_cargo_no_cargokown_no_warn(self):
        """Hostile transport with cargo but no cargo-known → no check-3 warning
        (check is Friendly-only; hostile scanning is intentional)."""
        player = _fighter("Alpha 1")
        # ST Azrael hostile, no cargo-known — this is the correct pattern for hostile
        # cargo ships where the player should scan to reveal the cargo.
        t = _shivan_transport("ST Azrael 1", team="Hostile", cargo="Shivan intel", flags=[])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Unexpected no-cargo-known warning for hostile ship: {v.warnings}",
        )

    def test_check3_friendly_container_cargo_with_cargokown_no_warn(self):
        """Friendly TSC 2 with cargo and cargo-known → no warning (demo mission pattern)."""
        player = _fighter("Alpha 1")
        c = _tsc2_container("TSC 2 Crate", cargo="civilians",
                            flags=["cargo-known"])
        mission = _make_mission(player, c)
        v = _make_validator(mission)
        self.assertFalse(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Unexpected warning for TSC 2 with cargo and cargo-known: {v.warnings}",
        )

    def test_check3_does_not_fire_when_no_cargo_defined(self):
        """Friendly transport without cargo defined should not trigger check-3
        (check-3 only fires when cargo IS defined)."""
        player = _fighter("Alpha 1")
        # cargo defaults to 'Nothing'; flags include cargo-known
        t = _transport("GTT Evac 1")
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Unexpected no-cargo-known warning when cargo not defined: {v.warnings}",
        )

    # ===================================================================
    # CHECK 4: scannable flag + cargo defined → ERROR
    # ===================================================================

    def test_check4_scannable_and_cargo_is_error(self):
        """Ship with both 'scannable' flag and cargo defined → validation error."""
        player = _fighter("Alpha 1")
        # Use a transport (cargo-capable), but also set scannable — still an error.
        t = _transport("GTT Evac 1", cargo="evacuees",
                       flags=["scannable", "escort", "cargo-known"])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERR_FRAG_SCANNABLE in e for e in v.errors),
            f"Expected scannable+cargo error, got: {v.errors}",
        )

    def test_check4_scannable_without_cargo_no_error(self):
        """Ship with 'scannable' flag but no cargo → no check-4 error."""
        player = _fighter("Alpha 1")
        # A standalone cruiser as a scannable target (no cargo)
        cruiser = _cruiser("GTC Scanner 1", flags=["scannable", "escort"])
        mission = _make_mission(player, cruiser)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_SCANNABLE in e for e in v.errors),
            f"Unexpected scannable+cargo error when no cargo defined: {v.errors}",
        )

    def test_check4_cargo_without_scannable_no_error(self):
        """Cargo-capable ship with cargo but NO 'scannable' flag → no check-4 error."""
        player = _fighter("Alpha 1")
        t = _transport("GTT Evac 1", cargo="evacuees",
                       flags=["cargo-known", "escort"])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(
            any(_ERR_FRAG_SCANNABLE in e for e in v.errors),
            f"Unexpected scannable+cargo error when no scannable flag: {v.errors}",
        )

    def test_check4_hostile_ship_scannable_and_cargo_is_error(self):
        """Hostile transport with both 'scannable' and cargo → check-4 error regardless of team."""
        player = _fighter("Alpha 1")
        t = _shivan_transport("ST Mahishi 1", team="Hostile",
                              cargo="Shivan intel",
                              flags=["scannable", "escort"])
        mission = _make_mission(player, t)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERR_FRAG_SCANNABLE in e for e in v.errors),
            f"Expected scannable+cargo error for hostile ship, got: {v.errors}",
        )

    # ===================================================================
    # Combined / integration scenarios
    # ===================================================================

    def test_clean_transport_mission_no_cargo_errors_or_warnings(self):
        """Demo-style clean mission: friendly transport with cargo and cargo-known,
        hostile transport with cargo and no cargo-known (intended for scanning).
        Should produce no cargo-related errors or warnings."""
        player = _fighter("Alpha 1")
        # Friendly cargo container carrying civilians — properly defined
        crate = _tsc2_container("TSC 2 Cargo", cargo="civilians", flags=["cargo-known"])
        # Hostile transport without cargo-known — player must scan it
        hostile_t = _shivan_transport("ST Mahishi 1", team="Hostile",
                                      cargo="Shivan intel",
                                      flags=["escort"])
        mission = _make_mission(player, crate, hostile_t)
        v = _make_validator(mission)
        # No cargo-related errors
        self.assertFalse(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Unexpected non-capable error: {v.errors}",
        )
        self.assertFalse(
            any(_ERR_FRAG_SCANNABLE in e for e in v.errors),
            f"Unexpected scannable error: {v.errors}",
        )
        # No cargo-related warnings
        self.assertFalse(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Unexpected no-cargo warning: {v.warnings}",
        )
        self.assertFalse(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Unexpected no-cargo-known warning: {v.warnings}",
        )

    def test_check1_and_check4_both_fire_independently(self):
        """A freighter (non-capable) with BOTH scannable and cargo triggers
        check-1 AND check-4 independently."""
        player = _fighter("Alpha 1")
        fr = _freighter("GTFr Poseidon 1", cargo="supplies",
                        flags=["scannable", "escort"])
        mission = _make_mission(player, fr)
        v = _make_validator(mission)
        self.assertFalse(v.validate())
        self.assertTrue(
            any(_ERR_FRAG_NON_CAPABLE in e for e in v.errors),
            f"Expected non-capable error, got: {v.errors}",
        )
        self.assertTrue(
            any(_ERR_FRAG_SCANNABLE in e for e in v.errors),
            f"Expected scannable+cargo error, got: {v.errors}",
        )

    def test_check2_and_check3_independent(self):
        """Check 2 fires for 'no cargo defined' and check 3 fires for
        'cargo defined but no cargo-known'.  They are mutually exclusive:
        when cargo is defined, check 2 is silent; when cargo is absent,
        check 3 is silent."""
        player = _fighter("Alpha 1")

        # Transport A: no cargo → check 2 warning only
        ta = _transport("GTT Evac 1")  # cargo='Nothing', flags include cargo-known
        # Transport B: cargo but no cargo-known → check 3 warning only
        tb = _transport("GTT Evac 2", cargo="refugees", flags=["escort"])
        mission = _make_mission(player, ta, tb)
        v = _make_validator(mission)

        v.validate()
        # Check 2 fires for GTT Evac 1
        self.assertTrue(
            any(_WARN_FRAG_NO_CARGO in w for w in v.warnings),
            f"Expected no-cargo warning for GTT Evac 1, got: {v.warnings}",
        )
        # Check 3 fires for GTT Evac 2
        self.assertTrue(
            any(_WARN_FRAG_NO_KNOWN in w for w in v.warnings),
            f"Expected no-cargo-known warning for GTT Evac 2, got: {v.warnings}",
        )


if __name__ == "__main__":
    unittest.main()
