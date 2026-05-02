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
        # Load voice config
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'configs', 'config_voice.json'
        )
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception:
            self.config = {"tts_engine": "elevenlabs", "voice_id": "Rachel", "fallback_tts": "pyttsx3"}

        # Load audio config (for output device name)
        audio_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'configs', 'config_audio.json'
        )
        try:
            with open(audio_config_path, 'r') as f:
                audio_cfg = json.load(f)
            self.output_device_name = audio_cfg.get("output_device_name", "USB Audio")
        except Exception:
            self.output_device_name = "USB Audio"

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

        # Voice settings
        self.voice_id = self.config.get("voice_id", "Rachel")
        self.speaking_rate = self.config.get("speaking_rate", 0.85)

        # Detect ALSA output device pinned by name
        self.alsa_device = self._detect_alsa_device()
        print(f"[Audio] Using ALSA output device: {self.alsa_device}")

        # Check available tools
        self.has_ffmpeg    = shutil.which("ffmpeg") is not None
        self.has_aplay     = shutil.which("aplay") is not None
        self.has_mpv       = shutil.which("mpv") is not None
        self.has_espeak    = shutil.which("espeak") is not None
        self.has_pico2wave = shutil.which("pico2wave") is not None

        print(f"[Audio] Tools: aplay={self.has_aplay}, ffmpeg={self.has_ffmpeg}, "
              f"mpv={self.has_mpv}, espeak={self.has_espeak}, pico={self.has_pico2wave}")

    def _detect_alsa_device(self):
        """
        Detect ALSA output device pinned by name from config.
        Searches aplay -l for the configured output_device_name.
        Falls back to first USB audio device found, then plughw:0,0.
        """
        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            target = self.output_device_name.lower()

            # Pass 1: match by configured name
            for line in lines:
                if target in line.lower() and 'card' in line.lower():
                    try:
                        card_num = line.split('card')[1].strip().split(':')[0].strip()
                        device = f"plughw:{card_num},0"
                        print(f"[Audio] Output device '{self.output_device_name}' → {device}")
                        return device
                    except (IndexError, ValueError):
                        pass

            # Pass 2: any USB audio device
            for line in lines:
                lower = line.lower()
                if ('usb' in lower or 'speaker' in lower) and 'card' in lower:
                    try:
                        card_num = line.split('card')[1].strip().split(':')[0].strip()
                        device = f"plughw:{card_num},0"
                        print(f"[Audio] USB fallback device → {device}")
                        return device
                    except (IndexError, ValueError):
                        pass

            print("[Audio Warning] No USB audio output found, using plughw:0,0")
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
            
            # Play WAV with aplay (up to 3 attempts for busy device)
            cmd = ["aplay", "-D", self.alsa_device, play_path]
            print(f"[Audio] Playing: {' '.join(cmd)}")
            for attempt in range(3):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    # Clean up converted WAV if we made one
                    if play_path != filepath and os.path.exists(play_path):
                        try:
                            os.unlink(play_path)
                        except Exception:
                            pass

                    if result.returncode == 0:
                        return True
                    else:
                        err = result.stderr[:200]
                        print(f"[Audio Warning] aplay attempt {attempt+1} failed (code {result.returncode}): {err}")
                        if "Device or resource busy" in err:
                            import time as _time
                            _time.sleep(1)
                            continue
                        # Try without explicit device as last resort
                        cmd2 = ["aplay", play_path]
                        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
                        if result2.returncode == 0:
                            return True
                        break
                except subprocess.TimeoutExpired:
                    print("[Audio Warning] aplay timed out")
                    break
                except Exception as e:
                    print(f"[Audio Error] aplay error: {e}")
                    break
        
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

    def speak(self, text, lang="en"):
        """Riproduce l'audio usando ElevenLabs, e se fallisce usa espeak/pyttsx3 (offline)"""
        print(f"[MIA Speaks] ({lang}): {text}")
        
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
                    self._speak_offline(text, lang=lang)
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
        self._speak_offline(text, lang=lang)
        
    def _speak_offline(self, text, lang="en"):
        """Offline TTS fallback prioritizing pico2wave (much better quality)"""
        try:
            import re
            # Pre-process text for better offline pronunciation
            # Replace 'MIA' with 'Mee-uh' (phonetic spelling to avoid 'Maia')
            processed_text = re.sub(r'\bmia\b', 'Mee-uh', text, flags=re.IGNORECASE)
            
            # Use a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            success = False
            
            # Determine engine language parameters
            pico_lang = "it-IT" if lang == "it" else "en-US"
            espeak_lang = "it" if lang == "it" else "en-us+f5"
            
            # STRATEGY 1: pico2wave (SVOX Pico) - High quality offline female voice
            pico_path = shutil.which("pico2wave")
            if pico_path:
                print(f"[Audio] pico2wave generating offline voice ({pico_lang})...")
                cmd = [pico_path, f"-l={pico_lang}", f"-w={tmp_path}", processed_text]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    success = True
            
            # STRATEGY 2: espeak-ng fallback
            if not success:
                engine = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
                print(f"[Audio] {engine} generating fallback voice ({espeak_lang})...")
                cmd = [engine, "-s", "165", "-v", espeak_lang, "-w", tmp_path, processed_text]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    success = True
            
            if success:
                # Use our standard hardware-optimized logic (aplay -D ...)
                # aplay is more reliable than mpv when running as a systemd service
                print(f"[Audio] Playing offline voice via aplay...")
                self._play_audio_file(tmp_path)
            else:
                print("[Audio Error] No offline TTS engine worked!")
            
            # Cleanup
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"[Audio Warning] Offline TTS error: {e}")
