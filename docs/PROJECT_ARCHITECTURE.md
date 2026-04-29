# Project Architecture

The MIA_JETSON system follows a strictly granular, modular architecture. This separation of concerns guarantees that each component can be developed, tested, and upgraded independently.

## Agentic Hierarchy

The system operates via a multi-agent framework:
- **Main Assistant Agent:** The orchestrator. It acts as the central router, receiving inputs from peripheral agents, consulting the brain/memory, and dispatching commands.
- **Sub-Agents:** Specialized agents managing their respective domains (Vision Agent, Audio Agent, etc.).

## Core Modules (`src/`)

### 1. `audio/`
Manages all auditory inputs and outputs.
- **Input:** Streams data from the USB microphone.
- **STT:** Local speech recognition (Vosk).
- **TTS:** Text synthesis via ElevenLabs (primary) with a local pyttsx3/coqui fallback for offline mode.

### 2. `vision/`
Handles visual processing via the 4K webcam.
- **Detection & Recognition:** Identifies faces in the frame.
- **Learning:** Incremental model updates to associate new faces with names, roles, and behavioral profiles.

### 3. `brain/`
The logic center and decision-making hub.
- **LLM Integration:** Interfaces with local or remote Large Language Models.
- **Knowledge Base:** Maintains foundational data (e.g., Bitcoin information).
- **Personality:** Enforces guardrails, persona constraints, and the master-authority dynamic.

### 4. `memory/`
The persistence layer.
- **Storage:** Local SQLite databases and file-based caching.
- **Data:** Logs conversations, user profiles, recognized face embeddings, and system state across reboots.

### 5. `hardware/`
Interfaces with the physical world beyond standard I/O.
- **Jetson Optimizations:** Manages GPU utilization and thermal states.
- **Peripherals:** Future support for ESP32 serial communication, servo motor control, and ROS node integration.

### 6. `interface/`
The graphical and interactive layer.
- **Display:** Drives the 10" vertical screen.
- **UI/UX:** Renders the animated face, status indicators, and provides a touch-friendly configuration panel.
