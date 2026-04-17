# tts_google.py
# Google GenAI TTS Provider Implementation

import os
import wave
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from tts_provider_base import BaseTTSProvider, TTSConfig


class GoogleTTSProvider(BaseTTSProvider):
    """Handles Google GenAI TTS synthesis."""

    def __init__(self, config: TTSConfig):
        super().__init__(config)
        self.client = None

    def is_available(self) -> bool:
        """Check if google-genai library is available."""
        return genai is not None

    def read_api_key_from_file(self) -> Optional[str]:
        """
        Attempt to read Gemini API key from Gemini_API_key.txt.
        Checks CWD and the module directory.
        Returns the key string, or None if file not found/empty.
        """
        candidates = [
            Path.cwd() / "Gemini_API_key.txt",
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
        """Lazy-initialize the Google GenAI client."""
        if self.client is None and not self.config.dry_run:
            if genai is None:
                raise ImportError(
                    "google-genai is not installed. "
                    "Install it with: pip install google-genai"
                )
            
            # Priority 1: Explicit API Key (from config)
            if self.config.api_key:
                self.client = genai.Client(api_key=self.config.api_key)
                return

            # Priority 2: Environment Variable API Key (AI Studio)
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                return

            # Priority 3: File-based API Key
            file_api_key = self.read_api_key_from_file()
            if file_api_key:
                logger.info("[TTS] Using API key from Gemini_API_key.txt")
                self.client = genai.Client(api_key=file_api_key)
                return

            # Priority 4: Vertex AI (ADC)
            try:
                import google.auth
                _, project = google.auth.default()
                if project:
                    self.client = genai.Client(vertexai=True, project=project, location="us-central1")
                    logger.info(f"[TTS] Authenticated via Vertex AI (project: {project}, location: us-central1)")
                    return
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"[TTS] Warning: Failed to auto-detect Vertex AI credentials: {e}")

            raise ValueError(
                "No Google API key found. Provide it via --google-api-key, "
                "the GEMINI_API_KEY or GOOGLE_API_KEY environment variable, "
                "a Gemini_API_key.txt file in the current working directory, "
                "or configure Vertex AI Application Default Credentials."
            )

    def synthesize_to_wav(self, voice_name: str, style: str, text: str, output_path: Path) -> None:
        """Synthesize text to WAV using Google GenAI."""
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would synthesize '{output_path}': voice={voice_name!r}, style={style!r}")
            return

        try:
            self._ensure_client()

            # Construct prompt: If style is provided, use structured format.
            if style:
                prompt_text = (
                    f"# Style:\n{style}\n\n"
                    f"# Transcript:\n{text}"
                )
            else:
                prompt_text = text

            # Configure request
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )

            # Call API
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-tts-preview",
                contents=prompt_text,
                config=config
            )

            # Extract PCM data
            if (not response.candidates or 
                not response.candidates[0].content or 
                not response.candidates[0].content.parts or
                not response.candidates[0].content.parts[0].inline_data):
                logger.error(f"[ERROR] No audio content returned for {output_path}")
                return

            pcm_data = response.candidates[0].content.parts[0].inline_data.data

            # Save to WAV
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(24000) # Gemini TTS output is 24kHz
                wf.writeframes(pcm_data)

            logger.info(f"[TTS] Wrote {output_path}")

        except Exception as exc:
            logger.error(f"[ERROR] Failed to synthesize {output_path}: {exc}")
