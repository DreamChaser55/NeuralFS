"""Shared test helpers for FSIF converter integration tests.

Provides:
- Path bootstrap (REPO_ROOT, _parent_dir on sys.path).
- make_valid_mission() — standard minimal Alpha-wing player mission.
- make_validator(mission) — convenience wrapper for Validator(mission, REPO_ROOT).
- SilencedTestCase — base TestCase that disables logging during the test class.
"""

import sys
import unittest
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent      # FSIF_to_FS2_Converter/
_repo_root = _parent_dir.parent        # NeuralFS/

for _p in (str(_repo_root), str(_parent_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Exported constants for tests that need them directly.
REPO_ROOT: Path = _repo_root


# ---------------------------------------------------------------------------
# Imports that helpers depend on
# ---------------------------------------------------------------------------
from data_models import (
    Mission,
    MissionInfo,
    PlayerSetup,
    Environment,
    Ship,
    Weapons,
    Wing,
)
from validator import Validator


# ---------------------------------------------------------------------------
# Mission / validator factories
# ---------------------------------------------------------------------------

def make_valid_mission() -> Mission:
    """Return a minimal valid Mission with one Alpha-wing player ship."""
    player_ship = Ship.model_validate(
        {
            "name": "Alpha 1",
            "class": "GTF Ulysses",
            "team": "Friendly",
            "position": [0.0, 0.0, 0.0],
            "arrival_cue": "( true )",
            "weapons": Weapons(
                primary=["Avenger", "Avenger"],
                secondary=["MX-50"],
            ),
        }
    )
    alpha_wing = Wing(
        name="Alpha",
        count=1,
        ships=[player_ship],
        position=[0.0, 0.0, 0.0],
        arrival_cue="( true )",
        initial_orders="( ai-chase-any 89 )",
    )
    return Mission(
        mission_info=MissionInfo(name="Test Mission"),
        player_setup=PlayerSetup(start_ship="Alpha 1", additional_ship_choices=[]),
        environment=Environment(),
        ships=[player_ship],
        wings=[alpha_wing],
    )


def make_validator(mission: Mission) -> Validator:
    """Return Validator(mission, REPO_ROOT)."""
    return Validator(mission, REPO_ROOT)


# ---------------------------------------------------------------------------
# Base test case
# ---------------------------------------------------------------------------

class SilencedTestCase(unittest.TestCase):
    """TestCase that suppresses all logging output for the duration of the class."""

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)
