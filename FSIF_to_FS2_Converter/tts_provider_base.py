# tts_provider_base.py
# Abstract base class and common orchestration logic for TTS providers.

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils import slugify_filename, ensure_wav_extension

@dataclass
class TTSConfig:
    """Configuration for TTS generation."""
    provider: str = 'google' # 'google' | 'elevenlabs'
    out_root: Optional[Path] = None  # Base directory for .wav files
    skip_existing: bool = True  # Don't overwrite existing files
    dry_run: bool = False  # Print what would be done without calling API
    default_voice: Optional[str] = None  # Fallback voice for lines without voice_name
    api_key: Optional[str] = None  # Provider-specific API Key
    model_id: Optional[str] = None # Provider-specific model ID (e.g. for ElevenLabs)


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    def __init__(self, config: TTSConfig):
        self.config = config

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider's dependencies are installed."""
        pass

    @abstractmethod
    def synthesize_to_wav(self, voice_name: str, style: str, text: str, output_path: Path) -> None:
        """Synthesize text to a WAV file using the provider's API."""
        pass
    
    @abstractmethod
    def read_api_key_from_file(self) -> Optional[str]:
        """Attempt to read API key from a provider-specific file."""
        pass

    def collect_items_from_mission(self, mission, fsif_dir: Path) -> List[Dict[str, Any]]:
        """Extract all TTS work items from a Mission object (Provider-agnostic logic)."""
        items: List[Dict[str, Any]] = []
        
        # Determine voice root directory
        if self.config.out_root:
            voice_root = self.config.out_root
        else:
            voice_root = fsif_dir / 'voice'

        # Collect from messages
        items.extend(self._collect_from_messages(mission, voice_root))

        # Collect from briefing stages
        items.extend(self._collect_from_stages(
            mission.briefing, voice_root, "briefing", "text"
        ))

        # Collect from debriefing stages
        items.extend(self._collect_from_stages(
            mission.debriefing, voice_root, "debriefing", "text"
        ))

        # Collect from command briefing stages
        items.extend(self._collect_from_stages(
            mission.command_briefing, voice_root, "command_briefing", "text"
        ))

        return items

    def _collect_from_messages(self, mission, base_out_dir: Path) -> List[Dict[str, Any]]:
        """Collect TTS items from mission.messages."""
        items: List[Dict[str, Any]] = []
        msgs = mission.messages or []

        for idx, msg in enumerate(msgs):
            # Check if this message should be voiced (has voice_name and text)
            text_str = str(msg.message).strip() if msg.message else ""
            if not text_str:
                continue

            # Get voice_filename (mission_loader has already normalized this)
            vf_str = str(msg.voice_filename).strip() if msg.voice_filename else ""

            # Skip if explicitly unvoiced
            if not vf_str or vf_str.lower() in ("none", "none.wav"):
                continue

            if not vf_str:
                # Fallback: derive from message name
                name_str = str(msg.name) if msg.name else f"message_{idx+1}"
                vf_str = slugify_filename(name_str) + ".wav"

            vf_str = ensure_wav_extension(vf_str)
            out_path = base_out_dir / 'special' / vf_str

            items.append({
                "section": "messages",
                "index": idx,
                "node": msg,
                "text": text_str,
                "style": str(msg.voice_style_instructions or ""),
                "voice_filename": vf_str,
                "out_path": out_path,
            })

        return items

    def _collect_from_stages(
        self,
        section_data: Any,
        base_out_dir: Path,
        section_key: str,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Collect TTS items from briefing/debriefing/command_briefing stages."""
        items: List[Dict[str, Any]] = []
        
        # Determine subfolder
        if section_key == 'command_briefing':
            subfolder = 'command_briefings'
        elif section_key == 'briefing':
            subfolder = 'briefing'
        elif section_key == 'debriefing':
            subfolder = 'debriefing'
        else:
            subfolder = section_key # Fallback

        # section_data is now an object (Briefing, Debriefing, etc.) with a .stages list
        if not section_data:
            return items
        
        stages = getattr(section_data, 'stages', []) or []

        for idx, stage in enumerate(stages):
            # Get text
            text_val = getattr(stage, text_key, None)
            text_str = str(text_val).strip() if text_val else ""
            
            if not text_str:
                continue

            # Get voice_filename
            vf_val = getattr(stage, 'voice_filename', None)
            vf_str = str(vf_val).strip() if vf_val else ""

            # Check if voiced (skip if none/empty)
            if not vf_str or vf_str.lower() in ("none", "none.wav"):
                continue

            if not vf_str:
                # Fallback: use section_name_index.wav
                vf_str = f"{section_key}_{idx+1}.wav"

            vf_str = ensure_wav_extension(vf_str)
            out_path = base_out_dir / subfolder / vf_str

            items.append({
                "section": section_key,
                "index": idx,
                "node": stage,
                "text": text_str,
                "style": str(getattr(stage, 'voice_style_instructions', "") or ""),
                "voice_filename": vf_str,
                "out_path": out_path,
            })

        return items

    def generate_all(self, items: List[Dict[str, Any]]) -> int:
        """Generate all voice files from collected items."""
        if not items:
            return 0

        # Generate each item
        generated_count = 0
        for item in items:
            if self._generate_one(item):
                generated_count += 1

        return generated_count

    def _generate_one(self, item: Dict[str, Any]) -> bool:
        """Generate a single voice file."""
        node = item["node"]
        text_str = item["text"]
        style = item["style"]
        out_path: Path = item["out_path"]

        # Resolve voice_name
        voice_name = self._resolve_voice_name(node)
        if not voice_name:
            print(
                f"[WARNING] Skipping line (section={item['section']}, index={item['index']}): "
                f"no voice_name set and no default voice provided."
            )
            return False

        # Check if file exists and should skip
        if out_path.exists() and self.config.skip_existing:
            if not self.config.dry_run:
                print(f"[INFO] Skipping existing file {out_path}")
            return False

        # Generate the file
        self.synthesize_to_wav(voice_name, style, text_str, out_path)
        return True

    def _resolve_voice_name(self, node: Any) -> Optional[str]:
        """Resolve voice_name from node or default."""
        voice_name = getattr(node, 'voice_name', None)
        if voice_name:
            try:
                vs = str(voice_name).strip()
            except Exception:
                vs = ""
            if vs:
                return vs

        # Fall back to default voice
        if self.config.default_voice:
            return self.config.default_voice

        return None


def get_provider(config: TTSConfig) -> BaseTTSProvider:
    """Factory function to return the correct TTS provider."""
    provider_name = config.provider.lower()
    
    if provider_name == 'google':
        try:
            from tts_google import GoogleTTSProvider
            return GoogleTTSProvider(config)
        except ImportError:
            # Fallback for circular imports or missing files
            # In a clean structure, this should just work
            raise ImportError("Could not import GoogleTTSProvider. Ensure tts_google.py exists.")
            
    elif provider_name == 'elevenlabs':
        try:
            from tts_elevenlabs import ElevenLabsTTSProvider
            return ElevenLabsTTSProvider(config)
        except ImportError:
            raise ImportError("Could not import ElevenLabsTTSProvider. Ensure tts_elevenlabs.py exists.")
    
    else:
        raise ValueError(f"Unknown TTS provider: {provider_name}")
