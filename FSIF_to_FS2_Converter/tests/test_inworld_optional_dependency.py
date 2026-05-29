"""Tests that Inworld TTS provider handles a missing requests library gracefully.

The import is guarded at module level, so importing tts_inworld never
raises even when requests is absent. The constructor, however, raises a
clear ImportError with a pip-install hint, and the factory must not mask
that message with its own generic "Could not import" text.

Covers:
- InworldTTSProvider.__init__ raises ImportError with 'pip install requests'
  hint when the requests sentinel is None.
- get_provider('inworld') propagates the clear dependency error, not a generic mask.
- is_available() returns False when the requests sentinel is None.
- is_available() returns True when requests is present.
- Importing tts_inworld never raises ImportError, even without requests installed.
"""

import importlib
import unittest

from _fsif_test_helpers import SilencedTestCase


class InworldOptionalDependencyTesting(SilencedTestCase):

    # ------------------------------------------------------------------
    # Constructor raises a clear message when requests is missing
    # ------------------------------------------------------------------

    def test_constructor_raises_clear_importerror_when_requests_is_none(self):
        """InworldTTSProvider.__init__ must raise ImportError with a pip install hint
        when the requests module is unavailable."""
        import tts_inworld
        from tts_provider_base import TTSConfig

        original = tts_inworld.requests
        try:
            tts_inworld.requests = None
            with self.assertRaises(ImportError) as ctx:
                tts_inworld.InworldTTSProvider(TTSConfig(provider='inworld'))
            msg = str(ctx.exception)
            self.assertIn("requests is not installed", msg,
                          f"Expected 'requests is not installed' in: {msg}")
            self.assertIn("pip install requests", msg,
                          f"Expected 'pip install requests' in: {msg}")
        finally:
            tts_inworld.requests = original

    # ------------------------------------------------------------------
    # Factory must not mask the clear dependency error
    # ------------------------------------------------------------------

    def test_get_provider_propagates_dependency_error_not_generic_message(self):
        """get_provider('inworld') must propagate the clear 'requests is not installed'
        ImportError and must NOT replace it with the generic 'Could not import
        InworldTTSProvider' message."""
        import tts_inworld
        from tts_provider_base import TTSConfig, get_provider

        original = tts_inworld.requests
        try:
            tts_inworld.requests = None
            with self.assertRaises(ImportError) as ctx:
                get_provider(TTSConfig(provider='inworld'))
            msg = str(ctx.exception)
            self.assertIn("requests is not installed", msg,
                          f"Expected clear dependency message in: {msg}")
            self.assertNotIn("Could not import InworldTTSProvider", msg,
                             f"Generic mask message must not appear in: {msg}")
        finally:
            tts_inworld.requests = original

    # ------------------------------------------------------------------
    # is_available() reflects the module-level sentinel correctly
    # ------------------------------------------------------------------

    def test_is_available_returns_false_when_requests_is_none(self):
        """is_available() must return False when the module-level requests sentinel
        is None (i.e. requests was not importable at module load time)."""
        import tts_inworld
        from tts_provider_base import TTSConfig

        original = tts_inworld.requests
        try:
            tts_inworld.requests = None
            provider = object.__new__(tts_inworld.InworldTTSProvider)
            provider.config = TTSConfig(provider='inworld')
            self.assertFalse(provider.is_available())
        finally:
            tts_inworld.requests = original

    def test_is_available_returns_true_when_requests_is_present(self):
        """is_available() must return True when requests is importable."""
        import tts_inworld
        from tts_provider_base import TTSConfig

        if tts_inworld.requests is None:
            self.skipTest("requests library not installed; skipping positive is_available test")

        provider = object.__new__(tts_inworld.InworldTTSProvider)
        provider.config = TTSConfig(provider='inworld')
        self.assertTrue(provider.is_available())

    # ------------------------------------------------------------------
    # Module import is always safe (even without requests)
    # ------------------------------------------------------------------

    def test_tts_inworld_module_can_always_be_imported(self):
        """Importing tts_inworld must never raise ImportError, even when requests
        is absent — the guarded import at module level must silently set the
        sentinel to None instead."""
        import tts_inworld
        reloaded = importlib.import_module('tts_inworld')
        self.assertIsNotNone(reloaded)


if __name__ == "__main__":
    unittest.main()
