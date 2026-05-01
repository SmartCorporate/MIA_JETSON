import sounddevice as sd
for i, d in enumerate(sd.query_devices()):
    if "Microphone" in d['name'] and "plughw" in d['name'].lower():
        print(f"MATCH: {i} {d['name']}")
