# tts_elevenlabs.py
# ElevenLabs TTS Provider Implementation

import os
import wave
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    ElevenLabs = None

from tts_provider_base import BaseTTSProvider, TTSConfig


class ElevenLabsTTSProvider(BaseTTSProvider):
    """Handles ElevenLabs TTS synthesis."""

    # Hardcoded Name -> ID mapping
    # This keeps the FSIF authoring experience clean (using names) while using IDs internally.
    _NAME_TO_ID: Dict[str, str] = {
        # Male voices
        "Adam": "pNInz6obpgDQGcFmaJgB",
        "Arnold": "VR6AewLTigWG4xSOukaG",
        "Brian": "nPczCjzI2devNBz1zQrb",
        "Callum": "N2lVS1w4EtoT3dr4eOWO",
        "Charlie": "IKne3meq5aSn9XLyUdCD",
        "Daniel": "onwK4e9ZLuTAKqWW03F9",
        "George": "JBFqnCBsd6RMkjVDRZzb",
        "Harry": "SOYHLrjzK2X1ezoPC6cr",
        "James": "ZQe5CZNOzWyzPSCn5a3c",
        "Josh": "TxGEqnHWrfWFTfGW9XjX",
        "Ryan": "wViXBPUzp2ZZixB1xQuM",
        "Sam": "yoZ06aMxZJJ28mfd3POQ",
        "Thomas": "GBv7mTt5XYQqbY4UYG9b",
        
        # Female voices
        "Bella": "EXAVITQu4vr4xnSDxMaL",
        "Charlotte": "XB0fDUnXU5powFXDhCwa",
        "Dorothy": "ThT5KcBeYPX3keUQqHPh",
        "Elli": "MF3mGyEYCl7XYWbV9V6O",
        "Emily": "LcfcDJNUP1GQjkzn1xUU",
        "Freya": "jsCqWAovK2LkecY7zXl4",
        "Lily": "pFZP5JQG7iQjIQuC4Bku",
        "Matilda": "XrExE9yKIg1WjnnlVkGX",
        "Nicole": "piTKgcLEGmPE4e6mEKli",
        "Rachel": "21m00Tcm4TlvDq8ikWAM",
        "Sarah": "EXAVITQu4vr4xnSDxMaL", # Note: Bella/Sarah share same ID in some lists, keeping generic
        "Serena": "pMsXgVXv3BLzUgSXRplE",
    }

    def __init__(self, config: TTSConfig):
        super().__init__(config)
        self.client = None

    def is_available(self) -> bool:
        """Check if elevenlabs library is available."""
        return ElevenLabs is not None

    def read_api_key_from_file(self) -> Optional[str]:
        """
        Attempt to read ElevenLabs API key from Elevenlabs_API_key.txt.
        Checks CWD and the module directory.
        """
        candidates = [
            Path.cwd() / "Elevenlabs_API_key.txt",
            Path(__file__).parent / "Elevenlabs_API_key.txt"
        ]

        for key_file in candidates:
            if key_file.exists():
                try:
                    key = key_file.read_text(encoding='utf-8').strip()
                    if key:
                        return key
                except Exception as e:
                    logger.warning(f"[TTS] Warning: Could not read {key_file}: {e}")
        return None

    def _ensure_client(self):
        """Lazy-initialize the ElevenLabs client."""
        if self.client is None and not self.config.dry_run:
            if ElevenLabs is None:
                raise ImportError(
                    "elevenlabs library is not installed. "
                    "Install it with: pip install elevenlabs"
                )
            
            # Priority 1: Explicit API Key (from config)
            api_key = self.config.api_key

            # Priority 2: Environment Variable
            if not api_key:
                api_key = os.environ.get("ELEVENLABS_API_KEY")

            # Priority 3: File-based API Key
            if not api_key:
                api_key = self.read_api_key_from_file()

            if not api_key:
                 raise ValueError(
                     "No ElevenLabs API key found. Please provide it via argument, "
                     "ELEVENLABS_API_KEY env var, or Elevenlabs_API_key.txt file."
                 )

            self.client = ElevenLabs(api_key=api_key)

    def synthesize_to_wav(self, voice_name: str, style: str, text: str, output_path: Path) -> None:
        """Synthesize text to WAV using ElevenLabs."""
        
        # Resolve Voice Name to ID
        # If name is in our well-known list, use the ID.
        # Otherwise, assume the user provided a raw Voice ID (custom voice).
        voice_id = self._NAME_TO_ID.get(voice_name, voice_name)

        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would synthesize '{output_path}': voice_name={voice_name!r} (ID={voice_id!r}), style={style!r}")
            return

        try:
            self._ensure_client()
            
            # Note on style: ElevenLabs API doesn't support a free-text 'style' prompt like Gemini.
            # It uses voice_settings (stability, similarity_boost, etc.).
            # We could parse the 'style' string to adjust settings, but for now we ignore it,
            # as the mapping would be complex/arbitrary.
            # Using default VoiceSettings is usually best unless we expose specific knobs.

            # Determine model
            model_id = self.config.model_id or "eleven_multilingual_v2"

            # Call API
            # Returns a generator of bytes (chunks)
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format="pcm_24000" # 24kHz 16-bit mono PCM (raw bytes, no header)
            )

            # Collect all chunks
            pcm_data = b"".join(chunk for chunk in audio_stream)

            if not pcm_data:
                 logger.error(f"[ERROR] No audio content returned for {output_path}")
                 return

            # Save to WAV
            # ElevenLabs pcm_24000 is raw PCM, so we must wrap it in a WAV container manually.
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(24000)
                wf.writeframes(pcm_data)

            logger.info(f"[TTS] Wrote {output_path}")

        except Exception as exc:
            logger.error(f"[ERROR] Failed to synthesize {output_path}: {exc}")
