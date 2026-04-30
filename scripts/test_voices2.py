import os
from dotenv import load_dotenv
load_dotenv('.env')
api_key = os.getenv('ELEVENLABS_API_KEY')
from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key=api_key)
voices = client.voices.get_all()
for v in voices.voices:
    if 'female' in v.labels.get('gender', '').lower() or 'american' in v.labels.get('accent', '').lower():
        print(f"Name: {v.name}, ID: {v.voice_id}, Labels: {v.labels}")
