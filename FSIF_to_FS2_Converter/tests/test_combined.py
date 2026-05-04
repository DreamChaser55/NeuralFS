# test_combined.py
# Compatibility shim: re-exports test classes from combined_testing.py so that
# `python -m unittest discover` (which only finds files matching test*.py) can
# locate and run the converter integration tests.
#
# The test logic lives in combined_testing.py; this file exists solely for
# unittest discovery.
from combined_testing import CombinedTesting, VoiceManagerTesting, DemoConversionTesting

__all__ = ["CombinedTesting", "VoiceManagerTesting", "DemoConversionTesting"]
