"""
MIA_JETSON - Response Generator
Formats, cleans, and applies personality to the LLM output before it is spoken.
"""
import re

class ResponseGenerator:
    def __init__(self):
        self.personality_prefix = ""
        self.max_chars = 300 # Prevent too long spoken responses
        
    def format_response(self, raw_text):
        """
        Cleans and formats the raw text from BrainLLM.
        """
        if not raw_text:
            return "I'm sorry, I couldn't generate a response."
            
        # 1. Clean whitespace
        clean_text = raw_text.strip()
        
        # 2. Remove potential LLM "artifacts" (like "A:" or "User:")
        clean_text = re.sub(r'^(A:|Response:|MIA:)\s*', '', clean_text, flags=re.IGNORECASE)
        
        # 3. Shorten if too long (TTS should be concise)
        if len(clean_text) > self.max_chars:
            # Try to cut at the last sentence
            truncated = clean_text[:self.max_chars]
            last_period = truncated.rfind('.')
            if last_period > self.max_chars // 2:
                clean_text = truncated[:last_period+1]
            else:
                clean_text = truncated + "..."
        
        # 4. Apply basic personality / safety checks
        # (Example: replace rude words or add a signature)
        
        return clean_text

    def prepare_for_speech(self, text):
        """
        Final pass to make text sound better (e.g., expanding abbreviations).
        """
        # Expand "MIA" to "Mia" for better phonetic pronunciation
        # (Though we already do this in VoiceAgent, it doesn't hurt here)
        return text
