"""
Unit tests for TTS provider resolution in fsif_to_fs2.py.

These tests exercise the provider precedence logic independently of file I/O,
TTS libraries, or FSIF schema validation.

Provider precedence (highest to lowest):
  1. Explicit CLI/caller provider string ('google', 'elevenlabs', 'inworld',
     or 'none') overrides the FSIF setting.
  2. FSIF file's audio.tts_provider value is used when caller omits provider.
  3. No provider defaults to 'none'.  There is no implicit Google fallback.

Voice-name validation runs only when a real provider is specified by CLI/caller
or FSIF, even if generation itself is disabled.  If no real provider is known,
validation_provider is None.
"""

import sys
import unittest
from pathlib import Path

_converter_dir = Path(__file__).resolve().parent.parent
_root_dir = _converter_dir.parent
for p in (_converter_dir, _root_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fsif_to_fs2 import (  # noqa: E402
    _KNOWN_PROVIDERS,
    _compute_intended_provider,
    _should_warn_tts_requested_without_provider,
    resolve_tts_provider,
)


REAL_PROVIDERS = ('google', 'elevenlabs', 'inworld')


class TestTtsProviderBehaviorMatrix(unittest.TestCase):
    """All core behavior-matrix scenarios for provider resolution."""

    def assertResolved(
        self,
        *,
        tts_enabled,
        cli_provider,
        fsif_provider,
        expected_final,
        expected_generation,
        expected_validation,
        expected_warning,
    ):
        final, generation, validation = resolve_tts_provider(
            tts_enabled=tts_enabled,
            cli_provider=cli_provider,
            fsif_provider=fsif_provider,
        )
        self.assertEqual(final, expected_final)
        self.assertEqual(generation, expected_generation)
        self.assertEqual(validation, expected_validation)
        self.assertEqual(
            _should_warn_tts_requested_without_provider(tts_enabled, final),
            expected_warning,
        )

    def test_tts_disabled_no_provider_anywhere(self):
        self.assertResolved(
            tts_enabled=False,
            cli_provider=None,
            fsif_provider=None,
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=False,
        )

    def test_tts_disabled_cli_real_provider_still_validates_against_cli_provider(self):
        for provider in REAL_PROVIDERS:
            with self.subTest(provider=provider):
                self.assertResolved(
                    tts_enabled=False,
                    cli_provider=provider,
                    fsif_provider=None,
                    expected_final='none',
                    expected_generation=False,
                    expected_validation=provider,
                    expected_warning=False,
                )

    def test_tts_disabled_fsif_real_provider_still_validates_against_fsif_provider(self):
        for provider in REAL_PROVIDERS:
            with self.subTest(provider=provider):
                self.assertResolved(
                    tts_enabled=False,
                    cli_provider=None,
                    fsif_provider=provider,
                    expected_final='none',
                    expected_generation=False,
                    expected_validation=provider,
                    expected_warning=False,
                )

    def test_tts_enabled_cli_real_provider_generates_with_cli_provider(self):
        for provider in REAL_PROVIDERS:
            with self.subTest(provider=provider):
                self.assertResolved(
                    tts_enabled=True,
                    cli_provider=provider,
                    fsif_provider='elevenlabs' if provider != 'elevenlabs' else 'google',
                    expected_final=provider,
                    expected_generation=True,
                    expected_validation=provider,
                    expected_warning=False,
                )

    def test_tts_enabled_fsif_real_provider_generates_with_fsif_provider(self):
        for provider in REAL_PROVIDERS:
            with self.subTest(provider=provider):
                self.assertResolved(
                    tts_enabled=True,
                    cli_provider=None,
                    fsif_provider=provider,
                    expected_final=provider,
                    expected_generation=True,
                    expected_validation=provider,
                    expected_warning=False,
                )

    def test_tts_enabled_no_provider_warns_and_skips_generation(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider=None,
            fsif_provider=None,
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=True,
        )

    def test_tts_enabled_cli_none_warns_and_skips_generation(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider='none',
            fsif_provider='google',
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=True,
        )

    def test_tts_enabled_fsif_none_warns_and_skips_generation(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider=None,
            fsif_provider='none',
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=True,
        )

    def test_invalid_cli_falls_through_to_fsif_real_provider(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider='bogus_provider',
            fsif_provider='inworld',
            expected_final='inworld',
            expected_generation=True,
            expected_validation='inworld',
            expected_warning=False,
        )

    def test_empty_cli_falls_through_to_fsif_real_provider(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider='',
            fsif_provider='elevenlabs',
            expected_final='elevenlabs',
            expected_generation=True,
            expected_validation='elevenlabs',
            expected_warning=False,
        )

    def test_invalid_cli_and_invalid_fsif_do_not_fall_back_to_google(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider='bogus',
            fsif_provider='also_bogus',
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=True,
        )

    def test_empty_cli_and_empty_fsif_do_not_fall_back_to_google(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider='',
            fsif_provider='',
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=True,
        )

    def test_case_insensitive_provider_inputs(self):
        self.assertResolved(
            tts_enabled=True,
            cli_provider='Google',
            fsif_provider='elevenlabs',
            expected_final='google',
            expected_generation=True,
            expected_validation='google',
            expected_warning=False,
        )
        self.assertResolved(
            tts_enabled=True,
            cli_provider=None,
            fsif_provider='ElevenLabs',
            expected_final='elevenlabs',
            expected_generation=True,
            expected_validation='elevenlabs',
            expected_warning=False,
        )
        self.assertResolved(
            tts_enabled=True,
            cli_provider='NONE',
            fsif_provider='google',
            expected_final='none',
            expected_generation=False,
            expected_validation=None,
            expected_warning=True,
        )


class TestComputeIntendedProvider(unittest.TestCase):
    """Unit tests for _compute_intended_provider()."""

    def test_no_provider_returns_none_not_google(self):
        self.assertEqual(_compute_intended_provider(None, None), 'none')
        self.assertEqual(_compute_intended_provider('bogus', 'also_bogus'), 'none')
        self.assertEqual(_compute_intended_provider('', ''), 'none')

    def test_fsif_real_provider_returned_when_cli_absent_or_invalid(self):
        self.assertEqual(_compute_intended_provider(None, 'google'), 'google')
        self.assertEqual(_compute_intended_provider(None, 'elevenlabs'), 'elevenlabs')
        self.assertEqual(_compute_intended_provider(None, 'inworld'), 'inworld')
        self.assertEqual(_compute_intended_provider('bogus', 'inworld'), 'inworld')

    def test_explicit_none_returned_as_none(self):
        self.assertEqual(_compute_intended_provider(None, 'none'), 'none')
        self.assertEqual(_compute_intended_provider('none', None), 'none')
        self.assertEqual(_compute_intended_provider('none', 'elevenlabs'), 'none')

    def test_cli_real_provider_overrides_fsif(self):
        self.assertEqual(_compute_intended_provider('google', 'elevenlabs'), 'google')
        self.assertEqual(_compute_intended_provider('elevenlabs', 'google'), 'elevenlabs')
        self.assertEqual(_compute_intended_provider('inworld', 'none'), 'inworld')

    def test_case_insensitive_inputs(self):
        self.assertEqual(_compute_intended_provider('Google', None), 'google')
        self.assertEqual(_compute_intended_provider(None, 'ElevenLabs'), 'elevenlabs')
        self.assertEqual(_compute_intended_provider('NONE', None), 'none')

    def test_return_always_in_known_providers(self):
        combos = [
            (None, None),
            ('google', None),
            ('elevenlabs', 'google'),
            ('none', 'elevenlabs'),
            (None, 'none'),
            (None, 'inworld'),
            ('bogus', 'bogus'),
        ]
        for cli, fsif in combos:
            result = _compute_intended_provider(cli, fsif)
            self.assertIn(result, _KNOWN_PROVIDERS)


class TestResolveTtsProviderStructuralInvariants(unittest.TestCase):
    def test_return_is_always_3_tuple(self):
        result = resolve_tts_provider(True, None, None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_final_provider_always_in_known_set(self):
        combos = [
            (True, None, None),
            (True, 'google', None),
            (True, 'none', 'elevenlabs'),
            (True, None, 'inworld'),
            (False, 'elevenlabs', 'google'),
            (False, None, None),
        ]
        for args in combos:
            final, _, _ = resolve_tts_provider(*args)
            self.assertIn(final, _KNOWN_PROVIDERS)

    def test_generation_enabled_is_bool(self):
        for provider in list(_KNOWN_PROVIDERS) + [None]:
            _, enabled, _ = resolve_tts_provider(True, provider, None)
            self.assertIsInstance(enabled, bool)

    def test_generation_enabled_is_true_only_for_real_final_provider(self):
        combos = [
            (True, 'google', None),
            (True, 'elevenlabs', None),
            (True, 'inworld', None),
            (True, 'none', None),
            (True, None, None),
            (False, 'google', 'inworld'),
        ]
        for args in combos:
            final, enabled, _ = resolve_tts_provider(*args)
            self.assertEqual(enabled, final in REAL_PROVIDERS)

    def test_validation_provider_is_real_provider_or_none(self):
        combos = [
            (True, 'google', None),
            (True, 'none', None),
            (True, None, 'none'),
            (True, None, None),
            (False, 'elevenlabs', None),
            (False, None, 'inworld'),
        ]
        for args in combos:
            _, _, validation = resolve_tts_provider(*args)
            self.assertTrue(validation is None or validation in REAL_PROVIDERS)


class TestKnownProvidersConstant(unittest.TestCase):
    def test_all_cli_choices_present(self):
        self.assertEqual(_KNOWN_PROVIDERS, {'google', 'elevenlabs', 'inworld', 'none'})


if __name__ == '__main__':
    unittest.main()
