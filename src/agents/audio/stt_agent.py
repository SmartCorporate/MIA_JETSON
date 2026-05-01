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
        """Find Yeti index and its native sample rate with priority."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if "Yeti" in d['name'] and d['max_input_channels'] > 0:
                    rate = int(d['default_samplerate'])
                    print(f"[STT] Found Yeti at index {i} with rate {rate}Hz")
                    return i, rate
            # Fallback to index 2
            return 2, 44100
        except Exception as e:
            print(f"[STT Error] Failed to query audio devices: {e}")
            return 2, 44100

    def _initialize_vosk(self):
        # Paths for the models we are downloading
        model_paths = {
            "en": "models/stt/vosk-model-small-en-us-0.15",
            "it": "models/stt/vosk-model-small-it-0.22"
        }
        
        for lang, path in model_paths.items():
            if os.path.exists(path):
                try:
                    print(f"[STT] Loading Vosk {lang.upper()} model ({self.sample_rate}Hz) from {path}...")
                    self.models[lang] = vosk.Model(path)
                    self.recognizers[lang] = vosk.KaldiRecognizer(self.models[lang], self.sample_rate)
                except Exception as e:
                    print(f"[STT Error] Failed to load {lang} model: {e}")
            else:
                print(f"[STT Warning] {lang.upper()} model not found at {path}")

    def listen(self, timeout=10):
        """
        Listens for a complete sentence using both EN and IT recognizers.
        """
        if not self.recognizers:
            return None, None

        print(f"[STT] Listening (Device: {self.device_index} @ {self.sample_rate}Hz)...")
        try:
            # Use a larger blocksize to avoid overflow (16000 samples @ 44100Hz ~ 360ms)
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=16000, 
                                   device=self.device_index,
                                   dtype='int16', channels=1, callback=self._audio_callback):
                
                # Clear queue
                while not self.audio_queue.empty(): 
                    try: self.audio_queue.get_nowait()
                    except queue.Empty: break

                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                        
                        for lang, rec in self.recognizers.items():
                            if rec.AcceptWaveform(data):
                                result = json.loads(rec.Result())
                                text = result.get("text", "").strip()
                                if text:
                                    print(f"[STT] Final Heard ({lang.upper()}): {text}")
                                    for r in self.recognizers.values(): r.Reset()
                                    return text, lang
                            else:
                                # We skip partial results in the main loop to save CPU
                                pass
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"[STT Warning] Error in chunk processing: {e}")
                        continue
                
                return None, None

        except Exception as e:
            print(f"[STT Error] Stream error: {e}")
        
        return None, None

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(f"[STT Status] {status}", file=sys.stderr)
        self.audio_queue.put(bytes(indata))
