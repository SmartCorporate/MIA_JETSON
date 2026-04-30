import elevenlabs
print("ElevenLabs version:", getattr(elevenlabs, '__version__', 'unknown'))
print("Dir of elevenlabs:", dir(elevenlabs))
from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key="test")
print("Dir of client:", dir(client))
try:
    print("Has client.generate?", hasattr(client, 'generate'))
except Exception as e:
    print(e)
