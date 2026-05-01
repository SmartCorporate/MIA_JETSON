import sounddevice as sd
print(sd.query_devices())
print(f"Default input device: {sd.default.device[0]}")
