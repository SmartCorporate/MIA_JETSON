import sounddevice as sd
for i, d in enumerate(sd.query_devices()):
    if "Yeti" in d['name']:
        print(f"FOUND YETI: Index {i}, Name: {d['name']}")
