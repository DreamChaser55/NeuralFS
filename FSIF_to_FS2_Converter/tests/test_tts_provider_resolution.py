"""
Unit tests for resolve_tts_provider() in fsif_to_fs2.py.

These tests exercise the TTS provider precedence logic independently of any
file I/O, TTS libraries, or FSIF schema validation.  They run without
pydantic, PyYAML, or any external library being installed.

Precedence (highest to lowest):
  1. TTS disabled entirely → always resolves to 'none' / generation off.
  2. Explicit CLI/caller provider string (one of 'google', 'elevenlabs',
     'inworld', 'none') → overrides FSIF setting.
  3. FSIF file's audio.tts_provider value → used when caller omits provider.
  4. Built-in default 'google' → when neither CLI nor FSIF specifies a
     provider but TTS is enabled.
"""

import sys
import os
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — make FSIF_to_FS2_Converter importable without a venv or
# installed package.  We import only resolve_tts_provider and _KNOWN_PROVIDERS;
# the rest of fsif_to_fs2 (yaml, pydantic, mission_loader …) is NOT imported
# so we avoid any hard dependency on optional libraries.
# ---------------------------------------------------------------------------
_converter_dir = Path(__file__).resolve().parent.parent
_root_dir = _converter_dir.parent
for p in (_converter_dir, _root_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# We import only the pure helper; the module-level side-effects (Advanced SEXP
# Validator import, logger setup) are harmless but isolated because we import
# by name rather than running main().
from fsif_to_fs2 import resolve_tts_provider, _KNOWN_PROVIDERS, _compute_intended_provider  # noqa: E402


class TestResolveTtsProviderDisabled(unittest.TestCase):
    """When TTS is disabled, generation is always off but validation_provider
    still reflects the declared provider so voice-name checks use the correct
    voice list.  A declared provider of 'none' falls back to 'google'."""

    def _assert_disabled(self, final, enabled, validation, expected_validation='google'):
        self.assertEqual(final, 'none', "final_provider must be 'none' when TTS is disabled")
        self.assertFalse(enabled, "generation_enabled must be False when TTS is disabled")
        self.assertEqual(
            validation, expected_validation,
            f"validation_provider should be '{expected_validation}' when TTS is disabled "
            f"(got '{validation}')"
        )

    def test_disabled_no_cli_no_fsif(self):
        """No provider specified anywhere — validation falls back to 'google'."""
        result = resolve_tts_provider(tts_enabled=False, cli_provider=None, fsif_provider=None)
        self._assert_disabled(*result, expected_validation='google')

    def test_disabled_with_cli_provider(self):
        """CLI provider propagates to validation_provider even when generation is off."""
        result = resolve_tts_provider(tts_enabled=False, cli_provider='elevenlabs', fsif_provider=None)
        self._assert_disabled(*result, expected_validation='elevenlabs')

    def test_disabled_with_fsif_provider(self):
        """FSIF provider propagates to validation_provider even when generation is off."""
        result = resolve_tts_provider(tts_enabled=False, cli_provider=None, fsif_provider='inworld')
        self._assert_disabled(*result, expected_validation='inworld')

    def test_disabled_with_both_sources(self):
        """CLI wins over FSIF; validation_provider = CLI provider."""
        result = resolve_tts_provider(tts_enabled=False, cli_provider='google', fsif_provider='elevenlabs')
        self._assert_disabled(*result, expected_validation='google')

    def test_disabled_provider_none_falls_back_to_google(self):
        """A declared provider of 'none' maps to 'google' for validation."""
        result = resolve_tts_provider(tts_enabled=False, cli_provider=None, fsif_provider='none')
        self._assert_disabled(*result, expected_validation='google')

    def test_disabled_cli_none_provider_falls_back_to_google(self):
        """CLI 'none' also maps to 'google' for validation."""
        result = resolve_tts_provider(tts_enabled=False, cli_provider='none', fsif_provider=None)
        self._assert_disabled(*result, expected_validation='google')


class TestResolveTtsProviderCliOverride(unittest.TestCase):
    """An explicit CLI provider overrides the FSIF file setting."""

    def test_cli_google_beats_fsif_elevenlabs(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider='google', fsif_provider='elevenlabs')
        self.assertEqual(final, 'google')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'google')

    def test_cli_elevenlabs_beats_fsif_google(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider='elevenlabs', fsif_provider='google')
        self.assertEqual(final, 'elevenlabs')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'elevenlabs')

    def test_cli_inworld_beats_fsif_google(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider='inworld', fsif_provider='google')
        self.assertEqual(final, 'inworld')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'inworld')

    def test_cli_none_disables_generation_even_when_fsif_is_google(self):
        """--tts-provider none must disable TTS even though --enable-tts is set."""
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider='none', fsif_provider='google')
        self.assertEqual(final, 'none')
        self.assertFalse(enabled)
        self.assertEqual(validation, 'google',
                         "validation_provider must be a real provider name even when generation is off")

    def test_cli_none_disables_without_fsif(self):
        final, enabled, _ = resolve_tts_provider(
            tts_enabled=True, cli_provider='none', fsif_provider=None)
        self.assertEqual(final, 'none')
        self.assertFalse(enabled)

    def test_cli_overrides_regardless_of_fsif_being_none(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider='inworld', fsif_provider=None)
        self.assertEqual(final, 'inworld')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'inworld')

    def test_cli_provider_is_case_insensitive(self):
        """Callers may pass uppercase or mixed-case provider strings."""
        final, enabled, _ = resolve_tts_provider(
            tts_enabled=True, cli_provider='Google', fsif_provider='elevenlabs')
        self.assertEqual(final, 'google')
        self.assertTrue(enabled)


class TestResolveTtsProviderFsifFallback(unittest.TestCase):
    """When CLI provider is omitted (None), the FSIF setting is used."""

    def test_fsif_google_used_when_cli_is_none(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider=None, fsif_provider='google')
        self.assertEqual(final, 'google')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'google')

    def test_fsif_elevenlabs_used_when_cli_is_none(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider=None, fsif_provider='elevenlabs')
        self.assertEqual(final, 'elevenlabs')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'elevenlabs')

    def test_fsif_inworld_used_when_cli_is_none(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider=None, fsif_provider='inworld')
        self.assertEqual(final, 'inworld')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'inworld')

    def test_fsif_none_disables_generation(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider=None, fsif_provider='none')
        self.assertEqual(final, 'none')
        self.assertFalse(enabled)
        self.assertEqual(validation, 'google')

    def test_fsif_provider_is_case_insensitive(self):
        final, enabled, _ = resolve_tts_provider(
            tts_enabled=True, cli_provider=None, fsif_provider='ElevenLabs')
        self.assertEqual(final, 'elevenlabs')
        self.assertTrue(enabled)


class TestResolveTtsProviderDefault(unittest.TestCase):
    """When both CLI and FSIF are absent, 'google' is the built-in default."""

    def test_both_absent_defaults_to_google(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider=None, fsif_provider=None)
        self.assertEqual(final, 'google')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'google')

    def test_invalid_cli_falls_through_to_fsif(self):
        """An unrecognised cli_provider is treated like None (falls through)."""
        final, enabled, _ = resolve_tts_provider(
            tts_enabled=True, cli_provider='bogus_provider', fsif_provider='inworld')
        self.assertEqual(final, 'inworld')
        self.assertTrue(enabled)

    def test_invalid_cli_and_invalid_fsif_defaults_to_google(self):
        final, enabled, validation = resolve_tts_provider(
            tts_enabled=True, cli_provider='bogus', fsif_provider='also_bogus')
        self.assertEqual(final, 'google')
        self.assertTrue(enabled)
        self.assertEqual(validation, 'google')

    def test_empty_string_cli_treated_as_unknown(self):
        """An empty string is not a known provider and falls through to FSIF."""
        final, enabled, _ = resolve_tts_provider(
            tts_enabled=True, cli_provider='', fsif_provider='elevenlabs')
        self.assertEqual(final, 'elevenlabs')

    def test_empty_string_both_falls_to_google(self):
        final, enabled, _ = resolve_tts_provider(
            tts_enabled=True, cli_provider='', fsif_provider='')
        self.assertEqual(final, 'google')
        self.assertTrue(enabled)


class TestResolveTtsProviderReturnShape(unittest.TestCase):
    """Structural invariants that must always hold."""

    _all_providers = ['google', 'elevenlabs', 'inworld', 'none']

    def test_return_is_always_3_tuple(self):
        result = resolve_tts_provider(True, None, None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_final_provider_always_in_known_set(self):
        combos = [
            (True,  None,          None),
            (True,  'google',      None),
            (True,  'none',        'elevenlabs'),
            (True,  None,          'inworld'),
            (False, 'elevenlabs',  'google'),
        ]
        for args in combos:
            final, _, _ = resolve_tts_provider(*args)
            self.assertIn(final, _KNOWN_PROVIDERS,
                          f"final_provider={final!r} not in _KNOWN_PROVIDERS for args={args}")

    def test_generation_enabled_is_bool(self):
        for p in self._all_providers + [None]:
            _, enabled, _ = resolve_tts_provider(True, p, None)
            self.assertIsInstance(enabled, bool,
                                  f"generation_enabled must be bool for cli_provider={p!r}")

    def test_validation_provider_never_none_string(self):
        """validation_provider must never be 'none'."""
        combos = [
            (True,  'none',  None),
            (True,  None,    'none'),
            (False, 'none',  None),
            (False, None,    'none'),
        ]
        for args in combos:
            _, _, validation = resolve_tts_provider(*args)
            self.assertNotEqual(validation, 'none',
                                f"validation_provider was 'none' for args={args}")

    def test_enabled_consistent_with_final_provider(self):
        """generation_enabled must be True iff final_provider != 'none'."""
        combos = [
            (True,  'google',      None),
            (True,  'none',        None),
            (True,  None,          'elevenlabs'),
            (True,  None,          'none'),
            (True,  None,          None),
            (False, 'google',      'inworld'),
        ]
        for args in combos:
            final, enabled, _ = resolve_tts_provider(*args)
            expected_enabled = (final != 'none')
            self.assertEqual(enabled, expected_enabled,
                             f"Mismatch for args={args}: final={final!r}, enabled={enabled}")


class TestKnownProvidersConstant(unittest.TestCase):
    """The _KNOWN_PROVIDERS constant should include all valid provider names."""

    def test_all_cli_choices_present(self):
        expected = {'google', 'elevenlabs', 'inworld', 'none'}
        self.assertEqual(_KNOWN_PROVIDERS, expected,
                         "_KNOWN_PROVIDERS must exactly match the CLI --tts-provider choices")


class TestComputeIntendedProvider(unittest.TestCase):
    """Unit tests for _compute_intended_provider().

    This helper returns the raw declared/intended provider (which may be 'none')
    using the same CLI > FSIF > default precedence as resolve_tts_provider(),
    without the 'none'→'google' mapping applied by validation_provider.

    This is what the disabled-branch log line in process_mission() uses to
    report the accurate mission-declared provider, avoiding the earlier bug
    where 'none' was reported as 'google'.
    """

    # ------------------------------------------------------------------
    # Default fallback
    # ------------------------------------------------------------------

    def test_both_absent_returns_google(self):
        self.assertEqual(_compute_intended_provider(None, None), 'google')

    def test_unrecognised_cli_and_fsif_returns_google(self):
        self.assertEqual(_compute_intended_provider('bogus', 'also_bogus'), 'google')

    def test_empty_string_both_returns_google(self):
        self.assertEqual(_compute_intended_provider('', ''), 'google')

    # ------------------------------------------------------------------
    # FSIF fallback (CLI absent or unrecognised)
    # ------------------------------------------------------------------

    def test_fsif_google_returned_when_cli_none(self):
        self.assertEqual(_compute_intended_provider(None, 'google'), 'google')

    def test_fsif_elevenlabs_returned_when_cli_none(self):
        self.assertEqual(_compute_intended_provider(None, 'elevenlabs'), 'elevenlabs')

    def test_fsif_inworld_returned_when_cli_none(self):
        self.assertEqual(_compute_intended_provider(None, 'inworld'), 'inworld')

    def test_fsif_none_returned_as_none_not_remapped(self):
        """'none' declared in the FSIF must come back as 'none', not 'google'.

        This is the core regression test for the bug: _compute_intended_provider
        must NOT apply the validation-provider mapping ('none'→'google') that
        resolve_tts_provider uses internally for voice-name checks.
        """
        self.assertEqual(_compute_intended_provider(None, 'none'), 'none')

    def test_fsif_used_when_cli_is_unrecognised(self):
        self.assertEqual(_compute_intended_provider('bogus', 'inworld'), 'inworld')

    # ------------------------------------------------------------------
    # CLI override
    # ------------------------------------------------------------------

    def test_cli_google_overrides_fsif_elevenlabs(self):
        self.assertEqual(_compute_intended_provider('google', 'elevenlabs'), 'google')

    def test_cli_elevenlabs_overrides_fsif_google(self):
        self.assertEqual(_compute_intended_provider('elevenlabs', 'google'), 'elevenlabs')

    def test_cli_inworld_overrides_fsif_none(self):
        self.assertEqual(_compute_intended_provider('inworld', 'none'), 'inworld')

    def test_cli_none_returned_as_none(self):
        """CLI 'none' must also come back as 'none' (no remapping)."""
        self.assertEqual(_compute_intended_provider('none', None), 'none')

    def test_cli_none_beats_fsif_elevenlabs(self):
        self.assertEqual(_compute_intended_provider('none', 'elevenlabs'), 'none')

    # ------------------------------------------------------------------
    # Case-insensitivity
    # ------------------------------------------------------------------

    def test_cli_mixed_case_normalised(self):
        self.assertEqual(_compute_intended_provider('Google', None), 'google')

    def test_fsif_mixed_case_normalised(self):
        self.assertEqual(_compute_intended_provider(None, 'ElevenLabs'), 'elevenlabs')

    def test_cli_uppercase_none_normalised(self):
        self.assertEqual(_compute_intended_provider('NONE', None), 'none')

    # ------------------------------------------------------------------
    # Return value always in _KNOWN_PROVIDERS
    # ------------------------------------------------------------------

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
            self.assertIn(result, _KNOWN_PROVIDERS,
                          f"_compute_intended_provider({cli!r}, {fsif!r}) = {result!r} "
                          f"not in _KNOWN_PROVIDERS")


if __name__ == '__main__':
    unittest.main()
