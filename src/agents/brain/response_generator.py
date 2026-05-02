"""
MIA_JETSON - Response Generator
Formats, cleans, and applies personality to LLM output before it is spoken.
All user-facing error messages are in Italian.
"""
import re


class ResponseGenerator:
    def __init__(self):
        self.max_chars = 400  # Max spoken characters

    def format_response(self, raw_text: str) -> str:
        """Clean and format raw LLM output for TTS."""
        if not raw_text:
            return "Non sono riuscita a generare una risposta."

        clean = raw_text.strip()

        # Remove LLM artifacts (ChatML tags, prefixes, trailing hallucinations)
        artifacts = [
            r'^(A:|R:|MIA:|Risposta:|Response:|Assistant:)\s*',
            r'<\|.*?\|>',        # ChatML tags
            r'User:.*',          # Trailing "User: ..." hallucinations
            r'Assistant:.*',
            r'\[.*?\]',          # Remove [stuff] annotations sometimes generated
        ]
        for pattern in artifacts:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE | re.MULTILINE).strip()

        # Collapse excessive whitespace
        clean = re.sub(r'\n{2,}', ' ', clean)
        clean = re.sub(r'\s{2,}', ' ', clean).strip()

        # Truncate if too long, breaking at sentence boundary
        if len(clean) > self.max_chars:
            truncated = clean[:self.max_chars]
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last_period > self.max_chars // 2:
                clean = truncated[:last_period + 1]
            else:
                clean = truncated + "..."

        # Final safety: if empty after cleaning
        if not clean:
            return "Non ho capito. Puoi ripetere?"

        return clean

    def prepare_for_speech(self, text: str) -> str:
        """Final phonetic adjustments for TTS engines."""
        # 'MIA' → 'Mia' for correct Italian pronunciation
        text = re.sub(r'\bMIA\b', 'Mia', text)
        return text
