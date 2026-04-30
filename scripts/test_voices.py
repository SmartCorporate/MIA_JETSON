import os
from dotenv import load_dotenv
load_dotenv('.env')
api_key = os.getenv('ELEVENLABS_API_KEY')
print("Key length:", len(api_key) if api_key else "None")

from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key=api_key)
try:
    voices = client.voices.get_all()
    print("Found voices:", len(voices.voices))
    for v in voices.voices:
        if 'Rachel' in v.name:
            print("Rachel ID:", v.voice_id)
except Exception as e:
    print("Error:", e)
