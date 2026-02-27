from pathlib import Path
from typing import Dict, Set, Optional, Union, List

from data_models import Mission, Message, BriefingStage, DebriefingStage, CommandBriefingStage
from utils import slugify_filename, ensure_wav_extension

class VoiceManager:
    def __init__(self, mission: Mission, fsif_path: Path, tts_settings: dict):
        self.mission = mission
        self.fsif_path = fsif_path
        self.tts_settings = tts_settings
        self.mode = str(tts_settings.get('mode', 'unique')).lower().strip()
        
        # Helper state
        self.fsif_dir = fsif_path.parent.resolve()
        self.existing_voice_files: Set[str] = set()
        self.reserved_filenames: Dict[str, str] = {} # canonical_filename -> text_content
        
        self._initialize_existing_files()

    def _initialize_existing_files(self):
        """Scans for existing voice files if using 'unique' mode."""
        if self.mode == 'unique':
            voice_dir = self.fsif_dir / 'voice'
            if voice_dir.exists():
                for f in voice_dir.rglob('*.wav'):
                    self.existing_voice_files.add(f.name.lower())

    def process(self):
        """Iterates through the mission and normalizes voice filenames."""
        # Messages
        for idx, msg in enumerate(self.mission.messages):
            self._process_node(msg, text_attr='message', name_attr='name', section='messages')

        # Briefing Stages
        for idx, stage in enumerate(self.mission.briefing.stages):
            self._process_node(stage, text_attr='text', section='briefing')

        # Debriefing Stages
        for idx, stage in enumerate(self.mission.debriefing.stages):
            self._process_node(stage, text_attr='text', section='debriefing')
            
        # Command Briefing Stages
        for idx, stage in enumerate(self.mission.command_briefing.stages):
            self._process_node(stage, text_attr='text', section='command_briefing')

    def _process_node(self, voiced_item: Union[Message, BriefingStage, DebriefingStage, CommandBriefingStage],
                      text_attr: str, section: str, name_attr: Optional[str] = None):
        
        text = getattr(voiced_item, text_attr, '')
        text_str = str(text) if text is not None else ''
        
        # If no text, it's effectively silent/skipped, but we leave defaults.
        if not text_str.strip():
            return

        voice_name = getattr(voiced_item, 'voice_name', None)
        voice_name = str(voice_name).strip() if voice_name else None

        # If not voiced (no voice_name), enforce "none" values and return
        if not voice_name:
            if 'command_briefing' in section:
                voiced_item.voice_filename = 'none'
            elif 'briefing' in section or 'debriefing' in section:
                voiced_item.voice_filename = 'none.wav'
            # For Message, it's Optional[str] = None, so we leave it or set to None
            if isinstance(voiced_item, Message):
                voiced_item.voice_filename = None
            return

        # Voiced line: Generate filename
        base = ''
        if name_attr and hasattr(voiced_item, name_attr):
            base = str(getattr(voiced_item, name_attr, '')).strip()
        
        if not base:
            base = text_str
            
        slug = slugify_filename(base)
        
        # Note: We pass the full slug to _resolve_collision, which handles truncation/suffixing.
        # However, to be safe, we can cap it here reasonably (e.g. 50 chars) so we don't pass massive strings.
        if len(slug) > 50:
            slug = slug[:50]

        # Collision Handling
        canonical = self._resolve_collision(slug, text_str)
        canonical = ensure_wav_extension(canonical)

        # Update Voiced Item
        voiced_item.voice_filename = canonical
        # Ensure voice_name is clean
        voiced_item.voice_name = voice_name
        
        # Reserve it
        self.reserved_filenames[canonical] = text_str

    def _resolve_collision(self, original_slug: str, text_content: str) -> str:
        """
        Determines the final filename based on mode and collisions.
        Uses deterministic numbering (e.g., _1, _2) for unique names.
        Ensures the final stem length does not exceed 25 characters.
        """
        
        # Max stem length to leave room for .wav (4 chars) -> 29 total
        MAX_STEM_LEN = 25
        
        # 1. Try the original slug first (truncated to max length)
        current_stem = original_slug[:MAX_STEM_LEN]
        
        if self._is_available(current_stem, text_content):
            return current_stem
            
        # 2. Try with suffixes
        counter = 1
        while True:
            suffix = f"_{counter}"
            
            # Safety check to prevent infinite loops or absurd filenames
            if len(suffix) >= MAX_STEM_LEN:
                 # This should technically never happen given reasonably small counters,
                 # but as a fallback for huge counters, we return a truncated randomized fallback
                 # or just the truncated stem (collision inevitable but safe length).
                 # For now, let's just break and return current_stem to respect length.
                 return current_stem
            
            # Truncate base to make room for suffix
            base_len = MAX_STEM_LEN - len(suffix)
            base = original_slug[:base_len]
            candidate_stem = base + suffix
            
            if self._is_available(candidate_stem, text_content):
                return candidate_stem
                
            counter += 1

    def _is_available(self, stem: str, text_content: str) -> bool:
        """Checks if a filename stem is available for use."""
        filename = stem + ".wav"
        
        # Check in-memory reservation first (always applies)
        if filename in self.reserved_filenames:
            # If text content matches, we reuse this file
            if self.reserved_filenames[filename] == text_content:
                return True # Re-use same slug
            else:
                return False # Collision with different content
        
        # Check mode-specific availability
        if self.mode == 'unique':
            # In unique mode, we must not collide with existing files on disk
            if filename.lower() in self.existing_voice_files:
                return False
        
        # In 'overwrite' or 'keep' mode, disk collisions are allowed (we overwrite or skip later).
        # We only care about in-memory collisions (handled above).
        return True

