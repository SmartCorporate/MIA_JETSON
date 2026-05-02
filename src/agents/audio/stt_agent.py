"""
MIA_JETSON - Speech-to-Text Agent
Handles real-time audio capture and transcription using Vosk.
Device is PINNED BY NAME (Blue Yeti) — never by index.
Forces mono (channels=1) and 44100Hz to prevent 'invalid number of channels' errors.
Includes automatic stream recovery on crash.
"""
import os
import queue
import json
import sys
import time
import sounddevice as sd
import vosk

class STTAgent:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.models = {}
        self.recognizers = {}
        self.current_lang = "it"

        # Load audio config
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'configs', 'config_audio.json'
        )
        try:
            with open(config_path, 'r') as f:
                self.audio_cfg = json.load(f)
        except Exception:
            self.audio_cfg = {}

        self.target_device_name = self.audio_cfg.get("input_device_name", "Blue Yeti")
        self.sample_rate = self.audio_cfg.get("sample_rate", 44100)
        self.blocksize   = self.audio_cfg.get("blocksize", 16000)
        self.channels    = 1  # ALWAYS MONO — prevents "invalid number of channels"
        self.retry_attempts = self.audio_cfg.get("device_retry_attempts", 5)
        self.retry_delay    = self.audio_cfg.get("device_retry_delay_sec", 2)

        # Find device index (pinned by name, with retry)
        self.device_index = self._find_device_by_name(self.target_device_name)

        # Load Vosk model
        self._initialize_vosk()

    # ------------------------------------------------------------------
    # Device detection — pinned by name, retry loop
    # ------------------------------------------------------------------
    def _find_device_by_name(self, name: str) -> int:
        """
        Search for input device by name with retry.
        Since USB ports are fixed, this is deterministic.
        """
        for attempt in range(1, self.retry_attempts + 1):
            try:
                devices = sd.query_devices()
                for i, d in enumerate(devices):
                    if name.lower() in d['name'].lower() and d['max_input_channels'] > 0:
                        print(f"[STT] Found '{name}' at index {i} (attempt {attempt}) "
                              f"— {d['default_samplerate']:.0f}Hz, "
                              f"max_ch={d['max_input_channels']}")
                        return i
                print(f"[STT Warning] '{name}' not found (attempt {attempt}/{self.retry_attempts}). "
                      f"Retrying in {self.retry_delay}s...")
            except Exception as e:
                print(f"[STT Error] Device query failed: {e}")
            time.sleep(self.retry_delay)

        # Last resort: default input device
        print(f"[STT Warning] Could not find '{name}' after {self.retry_attempts} attempts. Using default input.")
        return None  # sd.RawInputStream will use system default

    def _initialize_vosk(self):
        """Load the Italian Vosk model."""
        path = self.audio_cfg.get("vosk_model_path", "models/stt/vosk-model-small-it-0.22")
        if os.path.exists(path):
            try:
                print(f"[STT] Loading Italian Vosk model from '{path}' @ {self.sample_rate}Hz...")
                self.models["it"] = vosk.Model(path)
                self.recognizers["it"] = vosk.KaldiRecognizer(self.models["it"], self.sample_rate)
                print("[STT] Vosk model loaded OK.")
            except Exception as e:
                print(f"[STT Error] Failed to load Vosk model: {e}")
        else:
            print(f"[STT Warning] Vosk model not found at '{path}'")

    # ------------------------------------------------------------------
    # Main listen loop with automatic stream recovery
    # ------------------------------------------------------------------
    def listen(self, timeout=10) -> tuple:
        """
        Listen for a complete Italian sentence.
        Auto-recovers if the audio stream crashes (e.g. USB reconnect).
        Returns (text, "it") or (None, None).
        """
        rec = self.recognizers.get("it")
        if not rec:
            print("[STT Error] No Italian recognizer loaded.")
            return None, None

        for stream_attempt in range(3):  # up to 3 stream retries
            try:
                return self._do_listen(rec, timeout)
            except sd.PortAudioError as e:
                print(f"[STT Error] PortAudio stream error (attempt {stream_attempt+1}): {e}")
                print("[STT] Waiting 3s before retrying stream...")
                time.sleep(3)
                # Re-detect device in case it was re-enumerated
                self.device_index = self._find_device_by_name(self.target_device_name)
            except Exception as e:
                print(f"[STT Error] Unexpected listen error: {e}")
                return None, None

        print("[STT Error] All stream attempts failed.")
        return None, None

    def _do_listen(self, rec, timeout: float) -> tuple:
        """Internal: open the audio stream and listen once."""
        print(f"[STT] Listening (IT) — device={self.device_index}, "
              f"{self.sample_rate}Hz, ch={self.channels}, block={self.blocksize}...")

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self.blocksize,
            device=self.device_index,
            dtype='int16',
            channels=self.channels,          # Always 1 (MONO)
            callback=self._audio_callback
        ):
            # Flush any stale audio
            self.flush_queue()

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data = self.audio_queue.get(timeout=0.5)
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").strip()
                        if text:
                            print(f"[STT] Heard: '{text}'")
                            rec.Reset()
                            return text, "it"
                except queue.Empty:
                    continue

        return None, None

    # ------------------------------------------------------------------
    # Callbacks & helpers
    # ------------------------------------------------------------------
    def _audio_callback(self, indata, frames, time_info, status):
        """Called from a separate thread for each audio block."""
        if status:
            print(f"[STT Status] {status}", file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def flush_queue(self):
        """Clear all buffered audio (call after MIA finishes speaking)."""
        cleared = 0
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                cleared += 1
            except queue.Empty:
                break
        if cleared:
            print(f"[STT] Audio queue flushed ({cleared} blocks).")
