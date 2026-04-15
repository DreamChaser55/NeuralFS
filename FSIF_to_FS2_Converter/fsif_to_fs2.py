# fsif_to_fs2.py
# Main executable script for the converter.

import argparse
import os
import sys
import traceback
import logging
from pathlib import Path
from mission_loader import load_mission_from_fsif
from fs2_writer import FS2Writer
from validator import Validator
from voice_manager import VoiceManager

# Setup basic module logger
logger = logging.getLogger(__name__)

# Import Advanced SEXP Validator
try:
    # Try relative import (Package Mode)
    from .Advanced_SEXP_Validator import advanced_sexp_validator
except (ImportError, ValueError):
    try:
        # Fallback: Absolute/Local import (Script Mode)
        # Assuming Advanced_SEXP_Validator is in the same directory or PYTHONPATH
        from Advanced_SEXP_Validator import advanced_sexp_validator
    except ImportError:
        # Last resort: Try adding path if not found (legacy behavior)
        _adv_val_dir = Path(__file__).parent / "Advanced_SEXP_Validator"
        if _adv_val_dir.exists() and str(_adv_val_dir) not in sys.path:
            sys.path.append(str(_adv_val_dir))
            try:
                import advanced_sexp_validator
            except ImportError:
                advanced_sexp_validator = None
        else:
            advanced_sexp_validator = None


def sanitize_path(arg: str) -> str:
    """
    Conservative path normalization:
    - Remove one symmetric outer quote layer if present.
    - Expand ~ and environment variables.
    - Preserve embedded spaces and valid characters.
    - Return a normalized path string appropriate for the current OS.
    """
    if not arg:
        return ""

    p = str(arg).strip()
    if len(p) >= 2 and ((p[0] == '"' and p[-1] == '"') or (p[0] == "'" and p[-1] == "'")):
        p = p[1:-1]

    p = os.path.expandvars(os.path.expanduser(p))
    return str(Path(p))


def process_mission(input_file, output_file=None, tts_settings=None):
    """
    Core conversion logic.
    
    :param input_file: Path to the .fsif file.
    :param output_file: Optional path for the output .fs2 file.
    :param tts_settings: Dictionary containing TTS options:
                         - enabled: bool (default False)
                         - provider: str (default 'google')
                         - out_root: str (optional)
                         - mode: str (default 'unique', can be 'unique', 'overwrite', or 'keep')
                         - dry_run: bool (default False)
                         - default_voice: str (optional)
                         - api_key: str (optional)
                         - model_id: str (optional)
    :return: True if successful, False otherwise.
    """
    # Default TTS settings
    tts_opts = {
        'enabled': False,
        'provider': 'google',
        'out_root': None,
        'mode': 'unique', # unique | overwrite | keep
        'dry_run': False,
        'default_voice': None,
        'api_key': None,
        'model_id': None,
        'rate_limit_delay': 0.0
    }
    
    if tts_settings:
        tts_opts.update(tts_settings)

    # Resolve mode to flags
    mode = str(tts_opts.get('mode', 'unique')).lower().strip()
    provider = str(tts_opts.get('provider', 'google')).lower().strip()
    
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
        mission = load_mission_from_fsif(str(ip))
    except ValueError as e:
        logger.error(f"[ERROR] Validation failed during loading: {e}")
        return False

    # Extended Validation
    logger.info(f"[INFO] TTS Provider: {provider}")
    logger.info(f"[INFO] Validating mission structure...")
    # Determine root directory (where script/Documentation are)
    # We assume fsif_to_fs2.py is in the FSIF_to_FS2_Converter subdirectory, so root is parent.
    root_dir = Path(__file__).parent.parent.resolve()
    validator = Validator(mission, root_dir, ip, tts_provider=provider)
    is_valid = validator.validate()

    # Advanced SEXP Validation (Core Feature)
    logger.info("[INFO] Running Advanced SEXP Validation...")
    if advanced_sexp_validator:
        try:
            if not advanced_sexp_validator.validate_mission(mission):
                is_valid = False
        except Exception as e:
            logger.error(f"[ERROR] Advanced SEXP validation crashed: {e}")
            traceback.print_exc()
            is_valid = False
    else:
         logger.warning("[WARNING] Advanced SEXP Validator module not available. Validation skipped.")

    if not is_valid:
        logger.error("[ERROR] Validation failed. See logs above for details.")
        return False

    # Voice Filename Normalization (if TTS enabled)
    voice_map = {}
    if tts_opts['enabled']:
        logger.info(f"[INFO] Normalizing voice filenames (Mode: {mode})...")
        vm = VoiceManager(mission, ip, tts_opts)
        voice_map = vm.process()
    else:
        logger.info("[INFO] TTS disabled: Skipping voice filename generation (voice lines will be silent in FS2).")

    # Generate TTS voice files (if enabled and library available)
    if tts_opts['enabled']:
        try:
            from tts_provider_base import TTSConfig, get_provider
            
            raw_root = tts_opts['out_root']
            path_root = Path(raw_root) if raw_root and isinstance(raw_root, str) else None
            
            tts_config = TTSConfig(
                provider=provider,
                out_root=path_root,
                skip_existing=skip_existing,
                dry_run=tts_opts['dry_run'],
                default_voice=tts_opts['default_voice'],
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
                    items = generator.collect_items_from_mission(mission, ip.parent, voice_map)
                    
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
        except Exception:
            logger.warning(f"[WARNING] TTS generation failed:")
            traceback.print_exc()
            logger.warning("         Continuing with FS2 conversion...")

    if output_file:
        op = Path(sanitize_path(output_file))
    else:
        op = ip.with_suffix('.fs2')

    logger.info(f"[INFO] Writing to '{op}'...")
    
    # Allow logic errors to propagate with stack trace
    try:
        writer = FS2Writer(mission, str(op), voice_map)
        writer.write_mission()
        logger.info("[SUCCESS] Conversion successful.")
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
    parser.add_argument("--tts-out-root", dest="tts_out_root",
                        help="Base directory for generated voice files (default: same as .fsif)")
    
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
    parser.add_argument("--tts-provider", dest="tts_provider", choices=['google', 'elevenlabs'],
                        default='google', help="TTS Provider to use (default: google)")

    parser.add_argument("--tts-dry-run", dest="tts_dry_run", action="store_true",
                        help="Show what TTS would generate without calling API")
    parser.add_argument("--tts-default-voice", dest="tts_default_voice",
                        help="Fallback voice for lines without voice_name")
    
    # API Keys
    parser.add_argument("--google-api-key", dest="google_api_key",
                        help="Google API Key for TTS generation")
    parser.add_argument("--elevenlabs-api-key", dest="elevenlabs_api_key",
                        help="ElevenLabs API Key for TTS generation")
    
    # ElevenLabs specific
    parser.add_argument("--elevenlabs-model", dest="elevenlabs_model",
                        help="ElevenLabs model ID (default: eleven_multilingual_v2)")
    
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
    if args.tts_provider == 'google':
        api_key = args.google_api_key
    elif args.tts_provider == 'elevenlabs':
        api_key = args.elevenlabs_api_key

    # Map args to tts_settings dict
    tts_settings = {
        'enabled': args.tts,
        'provider': args.tts_provider,
        'out_root': args.tts_out_root,
        'mode': mode,
        'dry_run': args.tts_dry_run,
        'default_voice': args.tts_default_voice,
        'api_key': api_key,
        'model_id': args.elevenlabs_model,
        'rate_limit_delay': args.tts_rate_limit_delay
    }

    logger.info(f"Input file: {args.input_file}")
    success = process_mission(args.input_file, args.output, tts_settings)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
