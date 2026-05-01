import sounddevice as sd
for i, d in enumerate(sd.query_devices()):
    print(f"{i} | {d['name']} | In: {d['max_input_channels']} Out: {d['max_output_channels']}")
