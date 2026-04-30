import os
import json
import pyttsx3
from elevenlabs.client import ElevenLabs
from elevenlabs import play

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
        self.elevenlabs_client = ElevenLabs(api_key=api_key) if api_key else None
        
        # Voce default ElevenLabs (Rachel è una voce femminile standard di alta qualità)
        self.voice_id = self.config.get("voice_id", "Rachel")
        
        # Inizializza Fallback (pyttsx3)
        try:
            self.offline_tts = pyttsx3.init()
            # Imposta voce femminile inglese (questo varia molto in base all'OS, cerchiamo di forzarlo su linux/windows)
            voices = self.offline_tts.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower() and ('female' in voice.name.lower() or 'zira' in voice.name.lower()):
                    self.offline_tts.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"[Audio Error] Failed to init offline TTS: {e}")
            self.offline_tts = None

    def speak(self, text):
        """Riproduce l'audio usando ElevenLabs, e se fallisce usa pyttsx3 (offline)"""
        print(f"[MIA Speaks]: {text}")
        
        if self.elevenlabs_client:
            try:
                # Tenta generazione e riproduzione online
                audio = self.elevenlabs_client.generate(
                    text=text,
                    voice=self.voice_id,
                    model="eleven_multilingual_v2"
                )
                play(audio)
                return
            except Exception as e:
                print(f"[Audio Warning] ElevenLabs fallito o disconnesso ({e}). Switching to offline fallback.")
        else:
            print("[Audio Warning] API Key di ElevenLabs mancante. Uso fallback offline.")
            
        # Fallback Offline
        self._speak_offline(text)
        
    def _speak_offline(self, text):
        if self.offline_tts:
            self.offline_tts.say(text)
            self.offline_tts.runAndWait()
        else:
            print("[Audio Error] Nessun motore TTS disponibile.")
