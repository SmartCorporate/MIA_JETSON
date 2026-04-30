"""
MIA_JETSON - Voice Agent
Handles TTS (Text-to-Speech) via ElevenLabs with offline fallback.
Audio playback uses aplay with explicit ALSA device for maximum reliability on Jetson.
MP3 from ElevenLabs is converted to WAV via ffmpeg before playing through aplay.
"""
import os
import json
import subprocess
import tempfile
import shutil

class VoiceAgent:
    def __init__(self):
        # Carica configurazione
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'configs', 'config_voice.json')
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception:
            self.config = {"tts_engine": "elevenlabs", "voice_id": "Rachel", "fallback_tts": "pyttsx3"}
            
        # ElevenLabs Client
        api_key = os.getenv('ELEVENLABS_API_KEY')
        self.elevenlabs_client = None
        if api_key:
            try:
                from elevenlabs.client import ElevenLabs
                self.elevenlabs_client = ElevenLabs(api_key=api_key)
                print("[Audio] ElevenLabs client initialized OK")
            except Exception as e:
                print(f"[Audio Error] Failed to init ElevenLabs: {e}")
        else:
            print("[Audio Warning] ELEVENLABS_API_KEY not set")
        
        # Voce default ElevenLabs
        self.voice_id = self.config.get("voice_id", "Rachel")
        
        # Speaking rate (1.0 = normal, <1.0 = slower, >1.0 = faster)
        self.speaking_rate = self.config.get("speaking_rate", 0.85)
        
        # Detect the correct ALSA output device
        self.alsa_device = self._detect_alsa_device()
        print(f"[Audio] Using ALSA device: {self.alsa_device}")
        
        # Check available tools
        self.has_ffmpeg = shutil.which("ffmpeg") is not None
        self.has_aplay = shutil.which("aplay") is not None
        self.has_mpv = shutil.which("mpv") is not None
        self.has_espeak = shutil.which("espeak") is not None
        self.has_pico2wave = shutil.which("pico2wave") is not None
        
        print(f"[Audio] Tools: aplay={self.has_aplay}, ffmpeg={self.has_ffmpeg}, mpv={self.has_mpv}, espeak={self.has_espeak}, pico={self.has_pico2wave}")

    def _detect_alsa_device(self):
        """Auto-detect the correct ALSA playback device by checking aplay -l"""
        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            for line in lines:
                lower = line.lower()
                # Look for USB audio device
                if 'usb' in lower or 'speaker' in lower:
                    if 'card' in lower:
                        try:
                            card_num = line.split('card')[1].strip().split(':')[0].strip()
                            return f"plughw:{card_num},0"
                        except (IndexError, ValueError):
                            pass
            return "plughw:0,0"
        except Exception as e:
            print(f"[Audio Warning] Could not detect ALSA device: {e}")
            return "default"

    def _convert_mp3_to_wav(self, mp3_path):
        """Convert MP3 to WAV using ffmpeg for aplay compatibility.
        Also applies tempo adjustment if speaking_rate != 1.0"""
        wav_path = mp3_path.replace('.mp3', '.wav')
        try:
            cmd = ["ffmpeg", "-y", "-i", mp3_path]
            
            # Apply tempo change if speaking_rate is not 1.0
            # atempo filter: values < 1.0 = slower, > 1.0 = faster
            if self.speaking_rate != 1.0:
                cmd.extend(["-af", f"atempo={self.speaking_rate}"])
                print(f"[Audio] Applying tempo: {self.speaking_rate}x")
            
            cmd.extend(["-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", wav_path])
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and os.path.exists(wav_path):
                return wav_path
            else:
                print(f"[Audio Warning] ffmpeg conversion failed: {result.stderr[:300]}")
                return None
        except Exception as e:
            print(f"[Audio Error] ffmpeg error: {e}")
            return None

    def _play_audio_file(self, filepath):
        """Play an audio file using the most reliable method available"""
        
        # STRATEGY 1: Convert to WAV + aplay (MOST RELIABLE on Jetson)
        if self.has_aplay:
            play_path = filepath
            
            # If it's MP3, convert to WAV first
            if filepath.endswith('.mp3'):
                if self.has_ffmpeg:
                    wav_path = self._convert_mp3_to_wav(filepath)
                    if wav_path:
                        play_path = wav_path
                    else:
                        print("[Audio Warning] MP3->WAV conversion failed, trying mpv...")
                        return self._play_with_mpv(filepath)
                else:
                    # No ffmpeg, try mpv directly
                    print("[Audio Warning] ffmpeg not available, trying mpv...")
                    return self._play_with_mpv(filepath)
            
            # Play WAV with aplay
            cmd = ["aplay", "-D", self.alsa_device, play_path]
            print(f"[Audio] Playing: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                # Clean up converted WAV if we made one
                if play_path != filepath:
                    try:
                        os.unlink(play_path)
                    except Exception:
                        pass
                        
                if result.returncode == 0:
                    return True
                else:
                    print(f"[Audio Warning] aplay failed (code {result.returncode}): {result.stderr[:300]}")
                    # Try without explicit device
                    cmd2 = ["aplay", play_path]
                    result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
                    if result2.returncode == 0:
                        return True
            except subprocess.TimeoutExpired:
                print("[Audio Warning] aplay timed out")
            except Exception as e:
                print(f"[Audio Error] aplay error: {e}")
        
        # STRATEGY 2: mpv fallback
        return self._play_with_mpv(filepath)

    def _play_with_mpv(self, filepath):
        """Fallback: play with mpv"""
        if not self.has_mpv:
            print("[Audio Error] Neither aplay nor mpv available!")
            return False
        
        # Try multiple mpv audio device formats
        devices_to_try = [
            f"alsa/{self.alsa_device}",
            "alsa",
            None  # default
        ]
        
        for device in devices_to_try:
            try:
                cmd = ["mpv", "--no-video", "--no-terminal"]
                if device:
                    cmd.append(f"--audio-device={device}")
                cmd.append(filepath)
                
                print(f"[Audio] mpv trying: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return True
                print(f"[Audio] mpv returned code {result.returncode}")
            except Exception as e:
                print(f"[Audio] mpv error with device {device}: {e}")
                continue
        
        return False

    def speak(self, text):
        """Riproduce l'audio usando ElevenLabs, e se fallisce usa espeak/pyttsx3 (offline)"""
        print(f"[MIA Speaks]: {text}")
        
        if self.elevenlabs_client:
            try:
                # Mappa i nomi comuni agli ID
                voice_to_use = self.voice_id
                if voice_to_use.lower() == "rachel":
                    voice_to_use = "21m00Tcm4TlvDq8ikWAM"
                    
                audio_generator = self.elevenlabs_client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_to_use,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                
                # Save audio to temp file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name
                    for chunk in audio_generator:
                        if chunk:
                            tmp.write(chunk)
                
                file_size = os.path.getsize(tmp_path)
                print(f"[Audio] TTS audio saved: {tmp_path} ({file_size} bytes)")
                
                if file_size < 100:
                    print("[Audio Warning] Audio file too small, ElevenLabs may have returned empty audio")
                    os.unlink(tmp_path)
                    self._speak_offline(text)
                    return
                
                # Play the audio file
                success = self._play_audio_file(tmp_path)
                
                # Cleanup
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                
                if success:
                    return
                else:
                    print("[Audio Warning] Playback failed. Using offline fallback.")
                    
            except Exception as e:
                print(f"[Audio Warning] ElevenLabs error ({e}). Switching to offline fallback.")
        else:
            print("[Audio Warning] ElevenLabs non disponibile. Uso fallback offline.")
            
        # Fallback Offline
        self._speak_offline(text)
        
    def _speak_offline(self, text):
        """Offline TTS fallback using espeak-ng and mpv for better buffer management"""
        try:
            # Use a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            success = False
            
            # STRATEGY: espeak-ng + mpv (mpv is better at handling Jetson audio buffers)
            engine = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
            
            print(f"[Audio] {engine} generating offline voice (EN-US Female Smooth)...")
            # en-us+f5 is often smoother, -s 170 is a more natural pace
            cmd = [engine, "-s", "170", "-v", "en-us+f5", "-w", tmp_path, text]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                # Use mpv directly for offline voice to avoid aplay's "metallic/wave" issues on Jetson
                print(f"[Audio] Playing offline voice via mpv...")
                success = self._play_with_mpv(tmp_path)
            
            # Cleanup
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"[Audio Warning] Offline TTS error: {e}")
        
        if not success:
            print("[Audio Error] No offline TTS engine worked!")
