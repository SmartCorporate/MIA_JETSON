import sounddevice as sd
try:
    info = sd.query_devices(2)
    print(info)
    print(f"Default sample rate: {info['default_samplerate']}")
except Exception as e:
    print(f"Error: {e}")
