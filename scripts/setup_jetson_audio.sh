#!/bin/bash
echo "====================================="
echo "Installing Audio Dependencies for MIA"
echo "====================================="

sudo apt-get update
# Install mpv (required by elevenlabs for audio playback)
sudo apt-get install -y mpv

# Install espeak and alsa-utils (required by pyttsx3 for offline fallback)
sudo apt-get install -y espeak alsa-utils

# Install portaudio (often needed for PyAudio and microphone inputs later)
sudo apt-get install -y portaudio19-dev python3-pyaudio

echo "====================================="
echo "Dependencies installed successfully."
echo "Note: Ensure your USB speakers are set as the default output device."
echo "You can test audio by running: speaker-test -t wav -c 2"
echo "====================================="
