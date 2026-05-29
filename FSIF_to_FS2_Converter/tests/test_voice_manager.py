"""Tests for VoiceManager filename generation.

Covers:
- Filenames are deterministic across re-runs with the same input.
- Stem is strictly truncated to 25 characters.
- Truncation still applies when a numeric suffix is appended for collision resolution.
- Suffix length grows correctly beyond _9 (e.g. _10, _11).
- All generated filenames remain ≤ 29 characters (25 stem + ".wav").
"""

import tempfile
import unittest
from pathlib import Path

from data_models import Environment, Message, Mission, MissionInfo, PlayerSetup
from voice_manager import VoiceManager
from _fsif_test_helpers import SilencedTestCase


class VoiceManagerTesting(SilencedTestCase):

    def setUp(self):
        self.mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(start_ship="Player Ship", additional_ship_choices=[]),
            environment=Environment(),
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fsif_path = Path(self.temp_dir.name) / "dummy.fsif"
        self.tts_settings = {"mode": "unique"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_determinism(self):
        """Re-running with same input produces same filenames (determinism)."""
        self.mission.messages = [
            Message(name="Alpha", text="Msg 1", voice_name="Voice1"),
            Message(name="Alpha", text="Msg 2", voice_name="Voice1"),
            Message(name="Alpha", text="Msg 3", voice_name="Voice1"),
        ]

        vm1 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm1.process()
        filenames1 = [m.voice_filename for m in self.mission.messages]

        vm2 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm2.process()
        filenames2 = [m.voice_filename for m in self.mission.messages]

        self.assertEqual(filenames1, filenames2, "Filenames should be deterministic across runs")
        self.assertEqual(filenames1, ["alpha.wav", "alpha_1.wav", "alpha_2.wav"])

    def test_length_limit_simple(self):
        """Stem is strictly truncated to 25 characters."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit"
        self.mission.messages = [
            Message(name=long_name, text="Msg", voice_name="Voice1")
        ]

        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        fname = self.mission.messages[0].voice_filename
        self.assertIsNotNone(fname)
        assert fname is not None
        self.assertTrue(len(fname) <= 29, f"Filename '{fname}' exceeds 29 chars")
        self.assertTrue(fname.endswith(".wav"))
        self.assertEqual(fname, "this_is_a_very_long_name_.wav")

    def test_length_limit_collision(self):
        """Truncation still applies when a suffix is added for collision resolution."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit"
        self.mission.messages = [
            Message(name=long_name, text="Msg 1", voice_name="Voice1"),
            Message(name=long_name, text="Msg 2", voice_name="Voice1"),
            Message(name=long_name, text="Msg 3", voice_name="Voice1"),
        ]

        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        fnames = [m.voice_filename for m in self.mission.messages]

        for fn in fnames:
            self.assertIsNotNone(fn)
            assert fn is not None
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")

        self.assertEqual(fnames[0], "this_is_a_very_long_name_.wav")
        self.assertEqual(fnames[1], "this_is_a_very_long_nam_1.wav")
        self.assertEqual(fnames[2], "this_is_a_very_long_nam_2.wav")

    def test_extreme_suffix(self):
        """Suffix length grows correctly for indices ≥ 10."""
        long_name = "test_limit"
        msgs = [
            Message(name=long_name, text=f"Msg {i}", voice_name="Voice1")
            for i in range(12)
        ]

        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        self.assertEqual(msgs[11].voice_filename, "test_limit_11.wav")

        vlong = "aaaaaaaaaaaaaaaaaaaaaaaaa"
        msgs = [
            Message(name=vlong, text=f"Msg {i}", voice_name="Voice1")
            for i in range(12)
        ]

        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()

        self.assertEqual(msgs[0].voice_filename, "a" * 25 + ".wav")
        self.assertEqual(msgs[1].voice_filename, "a" * 23 + "_1.wav")
        self.assertEqual(msgs[10].voice_filename, "a" * 22 + "_10.wav")

        for fn in [m.voice_filename for m in msgs]:
            self.assertIsNotNone(fn)
            assert fn is not None
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")


if __name__ == "__main__":
    unittest.main()
