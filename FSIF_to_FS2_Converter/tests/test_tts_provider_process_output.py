"""Process-level tests for FSIF converter TTS provider behavior and log output."""

import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_tests_dir = Path(__file__).resolve().parent
_converter_dir = _tests_dir.parent
_repo_root = _converter_dir.parent

for _p in (str(_repo_root), str(_converter_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fsif_to_fs2 import process_mission  # noqa: E402


_BASE_FSIF = """\
fsif_version: "1.0"
mission_info:
  name: "TTS Provider Process Test"
environment:
  ambient_light_level: [0, 0, 0]
player_setup:
  start_ship: "Alpha 1"
entities:
  ship_templates:
    alpha_t:
      class: "GTF Ulysses"
      team: "Friendly"
      weapons:
        primary: ["ML-16 Laser", "ML-16 Laser"]
        secondary: ["MX-50"]
  wings:
    - name: "Alpha"
      template: "alpha_t"
      count: 1
      position: [0, 0, 0]
mission_flow:
  messages:
    - name: "TTSMsg"
      text: "Test voice line."
      voice_name: "VOICE_NAME_PLACEHOLDER"
"""


def _fsif_with_voice_and_audio(voice_name: str, audio_block: str = "") -> str:
    content = _BASE_FSIF.replace("VOICE_NAME_PLACEHOLDER", voice_name)
    if audio_block:
        content += f"\n{audio_block.rstrip()}\n"
    return content


def _write_temp_fsif(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".fsif", delete=False, encoding="utf-8")
    tmp.write(content)
    tmp.close()
    return tmp.name


class _FakeTTSProvider:
    def __init__(self):
        self.generated = False

    def is_available(self):
        return True

    def collect_items_from_mission(self, mission, fsif_dir):
        return []

    def generate_all(self, items):
        self.generated = True
        return 0


class TestTtsProviderProcessOutput(unittest.TestCase):
    def _run_process(self, fsif_content, tts_settings=None):
        path = _write_temp_fsif(fsif_content)
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))

        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "out.fs2")
            with self.assertLogs(level='INFO') as logs:
                result = process_mission(path, output_file=output, tts_settings=tts_settings or {})
        return result, "\n".join(logs.output)

    def test_tts_disabled_no_provider_no_warning_and_voice_validation_skipped(self):
        result, logs = self._run_process(_fsif_with_voice_and_audio("NotARealVoice"))

        self.assertTrue(result)
        self.assertIn("TTS generation disabled (no TTS provider specified; voice-name validation skipped)", logs)
        self.assertNotIn("TTS generation requested", logs)
        self.assertNotIn("unknown voice_name", logs)

    def test_tts_disabled_cli_real_provider_validates_voice_names(self):
        result, logs = self._run_process(
            _fsif_with_voice_and_audio("NotARealVoice"),
            tts_settings={"enabled": False, "provider": "elevenlabs"},
        )

        self.assertFalse(result)
        self.assertIn("provider specified for voice-name validation: elevenlabs", logs)
        self.assertIn("unknown voice_name 'NotARealVoice'", logs)
        self.assertNotIn("TTS generation requested", logs)

    def test_tts_disabled_fsif_real_provider_validates_voice_names(self):
        result, logs = self._run_process(
            _fsif_with_voice_and_audio("NotARealVoice", "audio:\n  tts_provider: inworld"),
            tts_settings={"enabled": False},
        )

        self.assertFalse(result)
        self.assertIn("provider specified for voice-name validation: inworld", logs)
        self.assertIn("unknown voice_name 'NotARealVoice'", logs)

    def test_tts_enabled_cli_real_provider_logs_generation_enabled(self):
        fake_provider = _FakeTTSProvider()
        with patch('tts_provider_base.get_provider', return_value=fake_provider):
            result, logs = self._run_process(
                _fsif_with_voice_and_audio("Adam"),
                tts_settings={"enabled": True, "provider": "elevenlabs", "dry_run": True},
            )

        self.assertTrue(result)
        self.assertIn("TTS Generation enabled. TTS provider: elevenlabs", logs)
        self.assertIn("Generating voice files (Provider: elevenlabs", logs)
        self.assertNotIn("TTS generation requested", logs)

    def test_tts_enabled_fsif_real_provider_logs_generation_enabled(self):
        fake_provider = _FakeTTSProvider()
        with patch('tts_provider_base.get_provider', return_value=fake_provider):
            result, logs = self._run_process(
                _fsif_with_voice_and_audio("Adam", "audio:\n  tts_provider: elevenlabs"),
                tts_settings={"enabled": True, "provider": None, "dry_run": True},
            )

        self.assertTrue(result)
        self.assertIn("TTS Generation enabled. TTS provider: elevenlabs", logs)
        self.assertIn("Generating voice files (Provider: elevenlabs", logs)
        self.assertNotIn("TTS generation requested", logs)

    def test_tts_enabled_no_provider_warns_skips_generation_and_voice_validation(self):
        with patch('tts_provider_base.get_provider') as mock_get_provider:
            result, logs = self._run_process(
                _fsif_with_voice_and_audio("NotARealVoice"),
                tts_settings={"enabled": True, "provider": None, "dry_run": True},
            )

        self.assertTrue(result)
        self.assertIn("TTS generation requested, but no active TTS provider was specified", logs)
        self.assertIn("skipping TTS generation", logs)
        self.assertNotIn("unknown voice_name", logs)
        mock_get_provider.assert_not_called()

    def test_tts_enabled_cli_none_warns_and_skips_generation(self):
        with patch('tts_provider_base.get_provider') as mock_get_provider:
            result, logs = self._run_process(
                _fsif_with_voice_and_audio("NotARealVoice", "audio:\n  tts_provider: google"),
                tts_settings={"enabled": True, "provider": "none", "dry_run": True},
            )

        self.assertTrue(result)
        self.assertIn("TTS generation requested, but no active TTS provider was specified", logs)
        self.assertNotIn("unknown voice_name", logs)
        mock_get_provider.assert_not_called()

    def test_tts_enabled_fsif_none_warns_and_skips_generation(self):
        with patch('tts_provider_base.get_provider') as mock_get_provider:
            result, logs = self._run_process(
                _fsif_with_voice_and_audio("NotARealVoice", "audio:\n  tts_provider: none"),
                tts_settings={"enabled": True, "provider": None, "dry_run": True},
            )

        self.assertTrue(result)
        self.assertIn("TTS generation requested, but no active TTS provider was specified", logs)
        self.assertNotIn("unknown voice_name", logs)
        mock_get_provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
