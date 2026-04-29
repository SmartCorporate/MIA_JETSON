# MIA_JETSON

MIA_JETSON is a modular, offline-capable Artificial Intelligence system designed to run locally on an NVIDIA Jetson Orin Nano 8GB Developer Kit. The long-term goal of this project is to serve as the core "brain" and control system for a humanoid robot, starting with the head module.

## Core Capabilities

1. **Audio Interaction:** Local Speech-to-Text (Vosk) and Cloud/Local Text-to-Speech (ElevenLabs/Fallback).
2. **Vision System:** High-resolution face detection, recognition, and incremental learning of known individuals.
3. **Intelligence (Brain):** Integrates foundational knowledge (e.g., Bitcoin) and features a granular, multi-agent architecture.
4. **Memory:** Persistent local database (SQLite) to store faces, conversations, preferences, and learned behaviors.
5. **Hardware Integration:** GPU-accelerated processing with future expansion capabilities via ESP32, servos, and ROS.
6. **Interface:** Vertical 10" touch display serving as MIA's interactive animated "face."

## Project Philosophy

- **Evolutionary:** MIA is designed to evolve over time, learning from interactions.
- **Autonomous:** All critical functions have local fallbacks. The system is fully operational offline.
- **Master/Servant Dynamics:** Strict hierarchical guardrails; the owner has ultimate authority over allowable actions.
- **Modular:** Completely isolated subsystems ensuring stability, independent testing, and graceful degradation.

## Getting Started

*(Instructions for setting up the Python environment, installing requirements, and running the `src/main.py` entry point will be added here as the project develops).*
