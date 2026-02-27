import unittest
import sys
from pathlib import Path

# Add parent directory to path to allow importing modules
# FSIF_to_FS2_Converter/tests/ -> FSIF_to_FS2_Converter/
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from data_models import Mission, Message, MissionInfo, PlayerSetup, Environment
from voice_manager import VoiceManager

class TestVoiceManager(unittest.TestCase):
    def setUp(self):
        # Create a minimal valid mission
        self.mission = Mission(
            mission_info=MissionInfo(name="Test Mission"),
            player_setup=PlayerSetup(ship_choices=[], weapon_pool=[]),
            environment=Environment()
        )
        self.fsif_path = Path("dummy.fsif")
        self.tts_settings = {'mode': 'unique'}

    def test_determinism(self):
        """Test that re-running with same input produces same filenames (determinism)."""
        # Create messages with generic names that would collide if not handled
        self.mission.messages = [
            Message(name="Alpha", message="Msg 1", voice_name="Voice1"),
            Message(name="Alpha", message="Msg 2", voice_name="Voice1"),
            Message(name="Alpha", message="Msg 3", voice_name="Voice1"),
        ]

        # Run 1
        vm1 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm1.process()
        filenames1 = [m.voice_filename for m in self.mission.messages]

        # Reset filenames
        for m in self.mission.messages:
            m.voice_filename = None

        # Run 2
        vm2 = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm2.process()
        filenames2 = [m.voice_filename for m in self.mission.messages]

        self.assertEqual(filenames1, filenames2, "Filenames should be deterministic across runs")
        
        # Verify specific filenames (should use counter)
        # alpha.wav is used for the first one? Or alpha.wav then alpha_1.wav?
        # Logic says: check "alpha.wav". If free, use it.
        # Next "Alpha": check "alpha.wav" (taken). Check "alpha_1.wav" (free).
        expected = ['alpha.wav', 'alpha_1.wav', 'alpha_2.wav']
        self.assertEqual(filenames1, expected)

    def test_length_limit_simple(self):
        """Test strict truncation to 25 chars for stem."""
        # 30 chars
        long_name = "this_is_a_very_long_name_that_exceeds_limit" 
        self.mission.messages = [
            Message(name=long_name, message="Msg", voice_name="Voice1")
        ]
        
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()
        
        fname = self.mission.messages[0].voice_filename
        self.assertTrue(len(fname) <= 29, f"Filename '{fname}' exceeds 29 chars")
        self.assertTrue(fname.endswith(".wav"))
        
        # Stem should be truncated to 25 chars
        # "this_is_a_very_long_name_" (25) + ".wav" (4) = 29
        expected_stem = "this_is_a_very_long_name_"
        self.assertEqual(fname, expected_stem + ".wav")

    def test_length_limit_collision(self):
        """Test truncation when suffix is added."""
        long_name = "this_is_a_very_long_name_that_exceeds_limit" 
        # Collision scenario
        self.mission.messages = [
            Message(name=long_name, message="Msg 1", voice_name="Voice1"),
            Message(name=long_name, message="Msg 2", voice_name="Voice1"),
            Message(name=long_name, message="Msg 3", voice_name="Voice1"),
        ]
        
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()
        
        fnames = [m.voice_filename for m in self.mission.messages]
        
        for fn in fnames:
            self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")
            
        # 1. "this_is_a_very_long_name_.wav" (25 stem)
        # 2. "this_is_a_very_long_nam_1.wav" (23 stem + "_1" = 25 stem equiv) -> wait, logic check
        # Logic: 
        #   MAX_STEM = 25.
        #   Try "stem". If len > 25 -> truncate to 25. Check avail.
        #   If collision, append "_1".
        #   New check: if len(stem + suffix) > 25, truncate stem further!
        #   
        #   Stem: "this_is_a_very_long_name_" (25)
        #   Suffix: "_1" (2)
        #   Total Stem needed: 27 > 25.
        #   Truncate stem to (25 - 2) = 23 chars.
        #   Stem: "this_is_a_very_long_nam" (23)
        #   Result: "this_is_a_very_long_nam_1.wav" (23+2+4 = 29)
        
        self.assertEqual(fnames[0], "this_is_a_very_long_name_.wav")
        self.assertEqual(fnames[1], "this_is_a_very_long_nam_1.wav")
        self.assertEqual(fnames[2], "this_is_a_very_long_nam_2.wav")

    def test_extreme_suffix(self):
        """Test logic with longer suffixes (e.g. _10)."""
        long_name = "test_limit"
        msgs = []
        # Create 12 collisions
        for i in range(12):
            msgs.append(Message(name=long_name, message=f"Msg {i}", voice_name="Voice1"))
            
        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()
        
        last_fname = msgs[11].voice_filename # Should be test_limit_11.wav
        self.assertEqual(last_fname, "test_limit_11.wav")
        
        # Test extreme truncation with suffix
        # Stem 25 chars. Suffix "_10" (3 chars).
        # Stem must truncate to 22 chars.
        vlong = "aaaaaaaaaaaaaaaaaaaaaaaaa" # 25 'a's
        msgs = []
        for i in range(12):
            msgs.append(Message(name=vlong, message=f"Msg {i}", voice_name="Voice1"))
            
        self.mission.messages = msgs
        vm = VoiceManager(self.mission, self.fsif_path, self.tts_settings)
        vm.process()
        
        # Index 0: aaaaaaaaaaaaaaaaaaaaaaaaa.wav (25 'a')
        self.assertEqual(msgs[0].voice_filename, "a"*25 + ".wav")
        
        # Index 1: aaaaaaaaaaaaaaaaaaaaaaa_1.wav (23 'a', _1)
        self.assertEqual(msgs[1].voice_filename, "a"*23 + "_1.wav")
        
        # Index 10: aaaaaaaaaaaaaaaaaaaaaa_10.wav (22 'a', _10) -> 22+3=25
        self.assertEqual(msgs[10].voice_filename, "a"*22 + "_10.wav")
        
        for fn in [m.voice_filename for m in msgs]:
             self.assertTrue(len(fn) <= 29, f"Filename '{fn}' exceeds 29 chars")

if __name__ == '__main__':
    unittest.main()
