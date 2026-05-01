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
import time

class STTAgent:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.models = {}  # Store models for different languages
        self.recognizers = {}
        self.current_lang = "en"
        
        # Auto-detect device and sample rate
        self.device_index, self.sample_rate = self._get_device_info()
        
        # Initialize Vosk
        self._initialize_vosk()

    def _get_device_info(self):
        """Force the use of plughw to allow 16000Hz resampling by ALSA."""
        # This device name is standard for ALSA when a USB mic is card 'Microphone'
        device_name = "plughw:CARD=Microphone,DEV=0"
        sample_rate = 16000
        print(f"[STT] Using device: {device_name} @ {sample_rate}Hz (ALSA Resampling)")
        return device_name, sample_rate

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
        Listens for a complete sentence using both EN and IT recognizers in parallel.
        Returns (text, lang) or (None, None).
        """
        if not self.recognizers:
            print("[STT Error] No recognizers loaded. Models might be missing.")
            return None, None

        print(f"[STT] Listening (Yeti Index: {self.device_index} @ {self.sample_rate}Hz)...")
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, 
                                   device=self.device_index,
                                   dtype='int16', channels=1, callback=self._audio_callback):
                
                # Clear queue
                while not self.audio_queue.empty(): 
                    try: self.audio_queue.get_nowait()
                    except queue.Empty: break

                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        data = self.audio_queue.get(timeout=0.2)
                        
                        for lang, rec in self.recognizers.items():
                            if rec.AcceptWaveform(data):
                                result = json.loads(rec.Result())
                                text = result.get("text", "").strip()
                                if text:
                                    print(f"[STT] Final Heard ({lang.upper()}): {text}")
                                    for r in self.recognizers.values(): r.Reset()
                                    return text, lang
                            else:
                                # Check partial result for very short phrases or quick interactions
                                partial = json.loads(rec.PartialResult())
                                p_text = partial.get("partial", "").strip()
                                if p_text and len(p_text.split()) > 3: # If more than 3 words, maybe it's enough
                                    # We still wait for AcceptWaveform usually, but this confirms it hears you
                                    pass
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"[STT Warning] Error processing audio chunk: {e}")
                        continue
                
                # If timeout reached, return empty
                return None, None

        except Exception as e:
            print(f"[STT Error] Could not open audio stream: {e}")
            # If device index failed, try to re-detect for next time
            self.device_index, _ = self._get_device_info()
        
        return None, None
