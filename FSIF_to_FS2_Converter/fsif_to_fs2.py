# fsif_to_fs2.py
# Main executable script for the converter.

import argparse
import os
import sys
import logging
import yaml
from pathlib import Path

# Inject root directory to sys.path to allow imports from common
_root_dir = Path(__file__).resolve().parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from mission_loader import load_mission_with_yaml_root
from fs2_writer import FS2Writer
from validator import Validator
from voice_manager import VoiceManager
from common.utils import sanitize_path

# Setup basic module logger
logger = logging.getLogger(__name__)


# Valid explicit TTS provider names accepted by the CLI and the tts_settings dict.
# The special sentinel value None means "defer to the FSIF file setting".
_KNOWN_PROVIDERS = frozenset({'google', 'elevenlabs', 'inworld', 'none'})


def resolve_tts_provider(
    tts_enabled: bool,
    cli_provider,   # str | None
    fsif_provider,  # str | None
):
    """Resolve the effective TTS provider name and generation-enabled flag.

    This is the single source of truth for TTS provider precedence.  It
    encodes the following priority order:

    1. If *tts_enabled* is False the result is always ('none', False, 'google').
       TTS generation is disabled regardless of any provider setting, and
       'google' is returned as the *validation_provider* fallback so that the
       validator and voice manager can still name-check voice fields.
    2. If *cli_provider* is one of the known provider names (``'google'``,
       ``'elevenlabs'``, ``'inworld'``, ``'none'``) it overrides the FSIF
       setting completely.
    3. If *cli_provider* is ``None`` (i.e. omitted from the CLI / GUI) the
       FSIF file's ``audio.tts_provider`` value is used when present.
    4. When neither source specifies a provider the built-in default is
       ``'google'``.

    The GUI maps its "From FSIF File" radio button to ``None`` before calling
    ``process_mission()``, so it follows the same path as an omitted CLI flag.
    The old tolerance for a literal ``'fsif'`` string has been removed; callers
    must pass ``None`` to indicate "defer to FSIF file".

    Parameters
    ----------
    tts_enabled:
        Whether the caller has explicitly enabled TTS generation (e.g. via
        ``--enable-tts`` on the CLI or the GUI checkbox).
    cli_provider:
        Provider string supplied by the caller, or ``None`` when omitted.
        Must be one of ``_KNOWN_PROVIDERS`` or ``None``.
    fsif_provider:
        The ``audio.tts_provider`` value read from the loaded FSIF file, or
        ``None`` when the field is absent/empty.

    Returns
    -------
    tuple[str, bool, str]
        ``(final_provider, generation_enabled, validation_provider)``

        * *final_provider* — the canonical provider name string
          (``'google'`` / ``'elevenlabs'`` / ``'inworld'`` / ``'none'``).
        * *generation_enabled* — ``True`` when voice files should be
          generated (i.e. *final_provider* != ``'none'``).
        * *validation_provider* — the provider to pass to the Validator and
          VoiceManager even when generation is disabled; always a real
          provider name (never ``'none'``).
    """
    if not tts_enabled:
        return ('none', False, 'google')

    # Normalise cli_provider to lowercase if supplied
    if cli_provider is not None:
        cli_provider = str(cli_provider).lower().strip()
    if fsif_provider is not None:
        fsif_provider = str(fsif_provider).lower().strip()

    # Priority 1: explicit CLI/caller override
    if cli_provider in _KNOWN_PROVIDERS:
        final_provider = cli_provider
    # Priority 2: FSIF file setting
    elif fsif_provider in _KNOWN_PROVIDERS:
        final_provider = fsif_provider
    # Priority 3: built-in default
    else:
        final_provider = 'google'

    generation_enabled = (final_provider != 'none')
    # validation_provider is always a real provider so the validator can
    # check voice-name tokens even when TTS generation is off.
    validation_provider = final_provider if generation_enabled else 'google'
    return (final_provider, generation_enabled, validation_provider)

# Import Advanced SEXP Validator
try:
    # Try relative import (Package Mode)
    from .Advanced_SEXP_Validator import advanced_sexp_validator
except (ImportError, ValueError):
    try:
        # Fallback: Absolute/Local import (Script Mode)
        from Advanced_SEXP_Validator import advanced_sexp_validator
    except ImportError:
        advanced_sexp_validator = None


def process_mission(input_file, output_file=None, tts_settings=None):
    """
    Core conversion logic.
    
    :param input_file: Path to the .fsif file.
    :param output_file: Optional path for the output .fs2 file.
    :param tts_settings: Dictionary containing TTS options:
                         - enabled: bool (default False)
                         - provider: str (default 'google')
                         - mode: str (default 'unique', can be 'unique', 'overwrite', or 'keep')
                         - dry_run: bool (default False)
                         - api_key: str (optional)
                         - model_id: str (optional)
    :return: True if successful, False otherwise.
    """
    # Default TTS settings
    tts_opts = {
        'enabled': False,
        'provider': None,
        'mode': 'unique', # unique | overwrite | keep
        'dry_run': False,
        'api_key': None,
        'model_id': None,
        'rate_limit_delay': 0.0
    }
    
    if tts_settings:
        tts_opts.update(tts_settings)

    # Resolve mode to flags
    mode = str(tts_opts.get('mode', 'unique')).lower().strip()
    
    # Mode logic for TTS Generator (file writing)
    # unique: skip_existing=True (TTS respects file)
    # overwrite: skip_existing=False (TTS overwrites)
    # keep: skip_existing=True (TTS skips if exists)
    
    skip_existing = True
    
    if mode == 'overwrite':
        skip_existing = False
    elif mode == 'keep':
        skip_existing = True
    elif mode == 'unique':
        skip_existing = True
    else:
        logger.warning(f"[WARNING] Unknown TTS mode '{mode}', defaulting to 'unique'.")

    ip = Path(sanitize_path(input_file))
    if not ip.exists() or not ip.is_file():
        logger.error(f"[ERROR] Input file not found at '{ip}'")
        return False

    if ip.suffix.lower() != '.fsif':
        logger.error("[ERROR] Input file must have a .fsif extension.")
        return False

    logger.info(f"[INFO] Loading and processing '{ip}'...")
    try:
        # Load mission (without voice generation)
        mission, fsif_root_node = load_mission_with_yaml_root(str(ip))
    except ValueError as e:
        # Covers FSIF schema errors, YAML parse errors re-raised by the loader,
        # version mismatches, and all other load-time validation failures.
        logger.error(f"[ERROR] Validation failed during loading: {e}")
        return False
    except yaml.YAMLError as e:
        # Defensive: yaml.YAMLError should normally be caught and re-raised
        # as ValueError inside mission_loader, but catch it here too so that
        # any future code path that omits that conversion still fails cleanly.
        logger.error(f"[ERROR] YAML parse error in '{ip}': {e}")
        return False
    except OSError as e:
        logger.error(f"[ERROR] Could not read FSIF file '{ip}': {e}")
        return False
    except Exception as e:
        # Pydantic ValidationError or any other unexpected exception during
        # loading — log with a stack trace so bugs remain visible, then abort.
        logger.exception(f"[ERROR] Unexpected error while loading '{ip}': {e}")
        return False

    # Determine final TTS provider and enable state via the canonical helper.
    # resolve_tts_provider() encodes the full precedence in one tested place:
    #   CLI/caller > FSIF file > built-in default ('google').
    fsif_tts_provider = mission.audio.tts_provider if mission.audio and mission.audio.tts_provider else None
    final_provider, tts_enabled, provider = resolve_tts_provider(
        tts_enabled=bool(tts_opts.get('enabled')),
        cli_provider=tts_opts.get('provider'),
        fsif_provider=fsif_tts_provider,
    )

    # Extended Validation
    logger.info(f"[INFO] TTS Provider: {final_provider}")
    logger.info(f"[INFO] Validating mission structure...")
    # Determine root directory (where script/Documentation are)
    # We assume fsif_to_fs2.py is in the FSIF_to_FS2_Converter subdirectory, so root is parent.
    root_dir = Path(__file__).parent.parent.resolve()
    validator = Validator(mission, root_dir, ip, tts_provider=provider, fsif_root_node=fsif_root_node)
    is_valid = validator.validate()

    # Advanced SEXP Validation (Core Feature)
    logger.info("[INFO] Running Advanced SEXP Validation...")
    if advanced_sexp_validator:
        try:
            if not advanced_sexp_validator.validate_mission(mission):
                is_valid = False
        except Exception as e:
            logger.exception(f"[ERROR] Advanced SEXP validation crashed: {e}")
            is_valid = False
    else:
         logger.warning("[WARNING] Advanced SEXP Validator module not available. Validation skipped.")

    if not is_valid:
        logger.error("[ERROR] Validation failed. See logs above for details.")
        return False

    # Voice Filename Normalization (if TTS enabled)
    if tts_enabled:
        logger.info(f"[INFO] Normalizing voice filenames (Mode: {mode})...")
        # Update tts_opts so VoiceManager uses the resolved provider
        tts_opts['provider'] = provider
        vm = VoiceManager(mission, ip, tts_opts)
        vm.process()
    else:
        logger.info("[INFO] TTS disabled: Skipping voice filename generation (voice lines will be silent in FS2).")

    # Generate TTS voice files (if enabled and library available)
    if tts_enabled:
        try:
            from tts_provider_base import TTSConfig, get_provider
            
            tts_config = TTSConfig(
                provider=provider,
                skip_existing=skip_existing,
                dry_run=tts_opts['dry_run'],
                api_key=tts_opts.get('api_key'),
                model_id=tts_opts.get('model_id'),
                rate_limit_delay=tts_opts.get('rate_limit_delay', 0.0)
            )
            
            try:
                generator = get_provider(tts_config)
            except Exception as e:
                logger.error(f"[ERROR] Failed to initialize TTS provider '{provider}': {e}")
                logger.error("Check if required libraries are installed (e.g., 'pip install elevenlabs' or 'pip install google-genai')")
                generator = None

            if generator:
                if generator.is_available():
                    logger.info(f"[INFO] Generating voice files (Provider: {provider}, Mode: {mode})...")
                    items = generator.collect_items_from_mission(mission, ip.parent)
                    
                    if items:
                        generated_count = generator.generate_all(items)
                        if tts_opts['dry_run']:
                            logger.info(f"[INFO] [DRY RUN] Would generate {len(items)} voice file(s)")
                        else:
                            skipped = len(items) - generated_count
                            if generated_count > 0:
                                msg = f"[INFO] Generated {generated_count} voice file(s)"
                                if skipped > 0:
                                    msg += f" (skipped {skipped} existing)"
                                logger.info(msg)
                            elif skipped > 0:
                                logger.info(f"[INFO] All {skipped} voice file(s) already exist (skipped)")
                    else:
                        logger.info("[INFO] No voiced lines found - skipping TTS")
                else:
                    logger.info(f"[INFO] TTS provider '{provider}' libraries not available - skipping TTS generation")
                    logger.info("       Install 'google-genai' for Google TTS or 'elevenlabs' for ElevenLabs TTS.")
        except Exception as e:
            logger.exception(f"[ERROR] TTS generation failed: {e}")
            return False

    if output_file:
        op = Path(sanitize_path(output_file))
    else:
        op = ip.with_suffix('.fs2')

    logger.info(f"[INFO] Writing to '{op}'...")
    
    # Allow logic errors to propagate with stack trace
    try:
        writer = FS2Writer(mission, str(op))
        writer.write_mission()
        suffix = " (with warnings)" if validator.warnings else ""
        logger.info(f"[SUCCESS] Conversion successful{suffix}.")
        return True
    except OSError as e:
        logger.error(f"[ERROR] IO failure while writing FS2 file: {e}")
        return False


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    parser = argparse.ArgumentParser(
        description="Convert a .fsif (FreeSpace Intermediate Format) file to a .fs2 mission file.")
    parser.add_argument("input_file", help="Path to the input .fsif file.")
    parser.add_argument("-o", "--output", help="Path to write the output .fs2 file")
    
    # TTS options
    parser.add_argument("--enable-tts", dest="tts", action="store_true", default=False,
                        help="Enable automatic TTS generation (default: disabled; requires Google GenAI)")
    
    # Mode selection
    parser.add_argument("--tts-mode", dest="tts_mode", choices=['unique', 'overwrite', 'keep'],
                        default='unique',
                        help="Voice filename strategy: 'unique' (default, rename new files), 'overwrite' (replace existing), 'keep' (reuse name, skip TTS)")

    # Legacy flags mapped to mode
    parser.add_argument("--tts-skip-existing", dest="tts_skip_legacy", action="store_true",
                        help="[Deprecated] Alias for --tts-mode keep")
    parser.add_argument("--tts-overwrite", dest="tts_overwrite_legacy", action="store_true",
                        help="[Deprecated] Alias for --tts-mode overwrite")
    
    # Provider selection
    parser.add_argument("--tts-provider", dest="tts_provider", choices=['google', 'elevenlabs', 'inworld', 'none'],
                        default=None, help="TTS Provider to use (overrides FSIF setting)")

    parser.add_argument("--tts-dry-run", dest="tts_dry_run", action="store_true",
                        help="Show what TTS would generate without calling API")
    
    # API Keys
    parser.add_argument("--google-api-key", dest="google_api_key",
                        help="Google API Key for TTS generation")
    parser.add_argument("--elevenlabs-api-key", dest="elevenlabs_api_key",
                        help="ElevenLabs API Key for TTS generation")
    parser.add_argument("--inworld-api-key", dest="inworld_api_key",
                        help="Inworld API Key for TTS generation")
    
    # ElevenLabs / Inworld specific
    parser.add_argument("--elevenlabs-model", dest="elevenlabs_model",
                        help="ElevenLabs model ID (default: eleven_v3)")
    parser.add_argument("--inworld-model", dest="inworld_model",
                        help="Inworld model ID (default: inworld-tts-1.5-max)")
    
    parser.add_argument("--tts-rate-limit-delay", dest="tts_rate_limit_delay", type=float, default=0.0,
                        help="Delay in seconds between consecutive TTS API calls (default: 0.0)")
    
    args = parser.parse_args()

    # Determine mode priority: explicit mode > overwrite flag > skip flag > default
    mode = args.tts_mode
    if args.tts_overwrite_legacy:
        mode = 'overwrite'
    elif args.tts_skip_legacy:
        mode = 'keep'

    # Determine API key based on provider
    api_key = None
    model_id = None
    if args.tts_provider == 'google':
        api_key = args.google_api_key
    elif args.tts_provider == 'elevenlabs':
        api_key = args.elevenlabs_api_key
        model_id = args.elevenlabs_model
    elif args.tts_provider == 'inworld':
        api_key = args.inworld_api_key
        model_id = args.inworld_model

    # Map args to tts_settings dict
    tts_settings = {
        'enabled': args.tts,
        'provider': args.tts_provider,
        'mode': mode,
        'dry_run': args.tts_dry_run,
        'api_key': api_key,
        'model_id': model_id,
        'rate_limit_delay': args.tts_rate_limit_delay
    }

    logger.info(f"Input file: {args.input_file}")
    success = process_mission(args.input_file, args.output, tts_settings)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
