# tts_inworld.py
# Inworld TTS Provider Implementation

import os
import wave
import base64
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

import requests
from tts_provider_base import BaseTTSProvider, TTSConfig

class InworldTTSProvider(BaseTTSProvider):
    """Handles Inworld TTS synthesis via REST API (Non-Streaming)."""

    def __init__(self, config: TTSConfig):
        super().__init__(config)
        self.api_key = None
        self.url = "https://api.inworld.ai/tts/v1/voice"

    def is_available(self) -> bool:
        """Check if requests library is available."""
        return requests is not None

    def read_api_key_from_file(self) -> Optional[str]:
        """
        Attempt to read Inworld API key from API_keys/Inworld_API_key.txt in the project root.
        Returns the key string, or None if file not found/empty.
        """
        candidates = [
            Path(__file__).resolve().parent.parent / "API_keys" / "Inworld_API_key.txt",
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

    def _ensure_api_key(self):
        """Retrieve the API key."""
        if self.api_key is None and not self.config.dry_run:
            # Priority 1: Explicit API Key (from config)
            api_key = self.config.api_key

            # Priority 2: Environment Variable
            if not api_key:
                api_key = os.environ.get("INWORLD_API_KEY")

            # Priority 3: File-based API Key
            if not api_key:
                api_key = self.read_api_key_from_file()

            if not api_key:
                raise ValueError(
                    "No Inworld API key found. Please provide it via argument, "
                    "INWORLD_API_KEY env var, or an API_keys/Inworld_API_key.txt file."
                )
            self.api_key = api_key

    def synthesize_to_wav(self, voice_name: str, style: str, text: str, output_path: Path) -> None:
        """Synthesize text to WAV using Inworld REST API."""
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would synthesize '{output_path}': voice_name={voice_name!r}")
            return

        try:
            self._ensure_api_key()

            headers = {
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }

            model_id = self.config.model_id or "inworld-tts-1.5-max"

            payload = {
                "text": text,
                "voiceId": voice_name,
                "modelId": model_id,
                "audioConfig": {
                    "speakingRate": 1,
                    "audioEncoding": "LINEAR16",
                    "sampleRateHertz": 48000
                }
            }

            response = requests.post(self.url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"[ERROR] Failed to synthesize {output_path}: {response.status_code} - {response.text}")
                return

            result = response.json()
            if 'audioContent' not in result:
                logger.error(f"[ERROR] No audio content returned for {output_path}")
                return

            pcm_data = base64.b64decode(result['audioContent'])

            if not pcm_data:
                 logger.error(f"[ERROR] Decoded audio content is empty for {output_path}")
                 return

            # Save to WAV (LINEAR16, 48000Hz)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(48000)
                wf.writeframes(pcm_data)

            logger.info(f"[TTS] Wrote {output_path}")

        except Exception as exc:
            logger.error(f"[ERROR] Failed to synthesize {output_path}: {exc}")
