"""
MIA_JETSON - Speech-to-Text Agent
Handles real-time audio capture and transcription using Vosk.
"""
import os
import queue
import sounddevice as sd
import vosk
import json
import sys

class STTAgent:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.models = {}  # Store models for different languages
        self.recognizers = {}
        self.current_lang = "en"
        
        # Initialize Vosk
        self._initialize_vosk()

    def _initialize_vosk(self):
        # Paths for the models we are downloading
        model_paths = {
            "en": "models/stt/vosk-model-small-en-us-0.15",
            "it": "models/stt/vosk-model-small-it-0.22"
        }
        
        for lang, path in model_paths.items():
            if os.path.exists(path):
                try:
                    print(f"[STT] Loading Vosk {lang.upper()} model from {path}...")
                    self.models[lang] = vosk.Model(path)
                    self.recognizers[lang] = vosk.KaldiRecognizer(self.models[lang], self.sample_rate)
                except Exception as e:
                    print(f"[STT Error] Failed to load {lang} model: {e}")
            else:
                print(f"[STT Warning] {lang.upper()} model not found at {path}")

    def set_language(self, lang):
        if lang in self.recognizers:
            self.current_lang = lang
            print(f"[STT] Switched to language: {lang}")
            return True
        return False

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def listen(self, timeout=10):
        """
        Listens for a complete sentence and returns the transcribed text.
        Returns None if nothing is heard or an error occurs.
        """
        recognizer = self.recognizers.get(self.current_lang)
        if not recognizer:
            return None

        print(f"[STT] Listening ({self.current_lang})...")
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, 
                                   dtype='int16', channels=1, callback=self._audio_callback):
                
                # Clear the queue from any old audio
                while not self.audio_queue.empty():
                    self.audio_queue.get()

                # Process audio until a result is found
                import time
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    data = self.audio_queue.get()
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            print(f"[STT] Heard: {text}")
                            return text
                
                # If we timeout, return whatever we have in the final result
                result = json.loads(recognizer.FinalResult())
                text = result.get("text", "").strip()
                if text:
                    print(f"[STT] Heard (Timeout): {text}")
                    return text

        except Exception as e:
            print(f"[STT Error] During listening: {e}")
        
        return None
