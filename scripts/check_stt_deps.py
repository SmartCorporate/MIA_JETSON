try:
    import vosk
    import sounddevice
    print("Vosk and SoundDevice are installed.")
except ImportError as e:
    print(f"Missing dependency: {e}")
