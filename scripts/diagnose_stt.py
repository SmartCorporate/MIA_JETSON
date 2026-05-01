import sounddevice as sd
import vosk
import os
import sys
import json

def test_stt():
    model_path = "models/stt/vosk-model-small-en-us-0.15"
    if not os.path.exists(model_path):
        print(f"Model missing at {model_path}")
        return

    print("Opening microphone...")
    try:
        model = vosk.Model(model_path)
        rec = vosk.KaldiRecognizer(model, 16000)
        
        def callback(indata, frames, time, status):
            if status:
                print(status)
            if rec.AcceptWaveform(bytes(indata)):
                print(rec.Result())
            else:
                print(rec.PartialResult())

        print("Listening for 5 seconds... say something!")
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            sd.sleep(5000)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_stt()
