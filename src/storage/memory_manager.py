"""
MIA_JETSON - Memory Manager
Manages Short-Term Memory (60-minute rolling conversational history)
and Long-Term Memory (permanent profile fact store) for multi-speaker layout.
Uses atomic JSON writes to prevent file corruption.
"""
import os
import json
import time
import re
import tempfile

class MemoryManager:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Locate the data/memories folder relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data", "memories")
        
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 60 minutes sliding window in seconds
        self.stm_window = 3600
        
        # Cache for short-term history: {speaker: [interaction_dicts]}
        self.short_term_history = {}

    def _get_ltm_path(self, speaker: str) -> str:
        return os.path.join(self.data_dir, f"{speaker.lower()}.json")

    def _get_stm_path(self, speaker: str) -> str:
        return os.path.join(self.data_dir, f"{speaker.lower()}_short_term.json")

    def _safe_write_json(self, filepath: str, data):
        """Write JSON atomically to prevent corruption during power cuts."""
        temp_dir = os.path.dirname(filepath)
        with tempfile.NamedTemporaryFile('w', dir=temp_dir, delete=False, encoding='utf-8') as tf:
            json.dump(data, tf, indent=2, ensure_ascii=False)
            temp_name = tf.name
        os.replace(temp_name, filepath)

    def _load_json(self, filepath: str, default):
        if not os.path.exists(filepath):
            return default
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Memory Warning] Failed to load JSON {filepath}: {e}")
            return default

    # ------------------------------------------------------------------
    # Short-Term Memory (60-minute window)
    # ------------------------------------------------------------------
    def load_short_term_history(self, speaker: str) -> list:
        filepath = self._get_stm_path(speaker)
        history = self._load_json(filepath, [])
        # Filter stale items immediately upon loading
        now = time.time()
        filtered = [turn for turn in history if now - turn.get("timestamp", 0) < self.stm_window]
        self.short_term_history[speaker.lower()] = filtered
        return filtered

    def save_short_term_history(self, speaker: str):
        filepath = self._get_stm_path(speaker)
        history = self.short_term_history.get(speaker.lower(), [])
        self._safe_write_json(filepath, history)

    def add_interaction(self, speaker: str, role: str, text: str):
        """Add a turn and prune elements older than 60 minutes."""
        speaker_key = speaker.lower()
        if speaker_key not in self.short_term_history:
            self.load_short_term_history(speaker)
            
        now = time.time()
        self.short_term_history[speaker_key].append({
            "role": role,
            "text": text,
            "timestamp": now
        })
        
        # Purge elements older than 60 minutes
        self.short_term_history[speaker_key] = [
            turn for turn in self.short_term_history[speaker_key]
            if now - turn.get("timestamp", 0) < self.stm_window
        ]
        
        # Persist to disk
        self.save_short_term_history(speaker)

    def get_short_term_context(self, speaker: str) -> list:
        speaker_key = speaker.lower()
        if speaker_key not in self.short_term_history:
            self.load_short_term_history(speaker)
        return self.short_term_history[speaker_key]

    # ------------------------------------------------------------------
    # Long-Term Memory (Permanent profiles)
    # ------------------------------------------------------------------
    def load_profile(self, speaker: str) -> dict:
        filepath = self._get_ltm_path(speaker)
        profile = self._load_json(filepath, None)
        if not profile:
            profile = {
                "name": speaker,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "facts": []
            }
        return profile

    def save_profile(self, speaker: str, profile: dict):
        filepath = self._get_ltm_path(speaker)
        self._safe_write_json(filepath, profile)

    def save_fact(self, speaker: str, category: str, fact_text: str) -> bool:
        """Save a new permanent fact, avoiding duplicate content."""
        profile = self.load_profile(speaker)
        facts = profile.get("facts", [])
        
        # Check if identical fact exists
        cleaned_new = re.sub(r'\s+', '', fact_text.lower())
        for f in facts:
            if re.sub(r'\s+', '', f.get("text", "").lower()) == cleaned_new:
                # Already exists
                return False
                
        fact_id = f"fact_{int(time.time())}"
        facts.append({
            "id": fact_id,
            "category": category.strip().lower(),
            "text": fact_text.strip(),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        profile["facts"] = facts
        self.save_profile(speaker, profile)
        print(f"[Memory] Fact saved for {speaker} [{category}]: {fact_text}")
        return True

    def delete_fact(self, speaker: str, fact_id: str) -> bool:
        profile = self.load_profile(speaker)
        facts = profile.get("facts", [])
        original_len = len(facts)
        
        filtered = [f for f in facts if f.get("id") != fact_id]
        if len(filtered) < original_len:
            profile["facts"] = filtered
            self.save_profile(speaker, profile)
            return True
        return False

    def get_long_term_facts(self, speaker: str) -> list:
        profile = self.load_profile(speaker)
        return profile.get("facts", [])

    # ------------------------------------------------------------------
    # Tag Extraction & Sanitization
    # ------------------------------------------------------------------
    def parse_and_save_memory_tags(self, speaker: str, response_text: str) -> str:
        """
        Scan response for any memory tags, save them, and strip them out.
        Tag format: [MEM: category | fact description]
        """
        if not response_text:
            return response_text
            
        pattern = r'\[MEM:\s*([^|]+)\s*\|\s*([^\]]+)\]'
        matches = re.findall(pattern, response_text)
        
        for category, fact_text in matches:
            self.save_fact(speaker, category, fact_text)
            
        # Strip all memory tags from final text
        cleaned = re.sub(pattern, '', response_text).strip()
        # Clean double spaces or clean punctuation residues
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned
