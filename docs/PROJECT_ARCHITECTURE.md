# MIA_JETSON Project Architecture

## Overview
MIA_JETSON is a modular Artificial Intelligence system designed to run on the **NVIDIA Jetson Orin Nano 8GB** (1TB SSD). The system is built in Python and is designed for SSH control while maintaining the capability to function completely offline.

The primary architectural goal is to establish a scalable, pipeline-based system managed by a central orchestrator, ensuring modularity, clear separation of concerns, and future compatibility with robotics frameworks like ROS.

---

## 1. System Pipeline
The architecture follows a modular pipeline flow where data moves sequentially (or in parallel when applicable) through independent components. 

**Example Flow:**
`Audio Input` → `Speech-to-Text` → `Brain` → `Response Generator` → `Text-to-Speech` → `Audio Output`

### Modular Constraints
- Each module performs a specific task: receiving input, processing it, and returning output.
- **No direct dependencies:** Modules must never call each other directly.
- **Interchangeability:** Any module can be swapped or upgraded without affecting the internal logic of others.

---

## 2. Core Modules
The system is divided into the following specialized modules:

| Module | Description | Hardware/Tech |
| :--- | :--- | :--- |
| **audio_input** | Captures ambient audio. | Blue Yeti (Device 25) |
| **speech_to_text** | Converts audio to text. | Local Vosk |
| **brain** | Core AI logic and decision making. | Future MIA Bitcoin integration |
| **response_generator**| Constructs textual responses. | Template or LLM based |
| **text_to_speech** | Converts text to spoken audio. | ElevenLabs (Online) / Local Fallback |
| **audio_output** | Handles playback of generated audio. | USB Audio (Device 0) |
| **vision** | Image capture and analysis. | Webcam (/dev/video0) |
| **memory** | Long-term data storage and retrieval. | Local SQLite Database |
| **hardware** | Management of physical device states. | Jetson GPIO / System status |
| **ui** | Visual feedback and interface. | Vertical Display / Virtual Face |

---

## 3. Central Orchestrator
The system is governed by a central controller located at `core/orchestrator.py`.

### Responsibilities
- **Initialization:** Starting and verifying all modules upon boot.
- **Flow Control:** Managing the movement of data through the pipeline.
- **Data Coordination:** Ensuring messages reach the correct destination.
- **Global State Management:** Tracking the current system status.
- **Conflict Resolution:** Preventing issues such as audio feedback (echo) or resource locking.

**CRITICAL RULE:** The Orchestrator MUST NOT contain AI logic. It acts strictly as a "traffic controller."

---

## 4. Communication Protocol
Modules communicate exclusively through structured messaging.

- **Mechanism:** Queues and events.
- **Data Format:** Structured dictionaries or JSON messages.
- **Prohibited:** 
    - Direct function calls between modules.
    - Cross-dependencies.
    - Uncontrolled use of global variables.

---

## 5. Execution Modes (Online vs. Offline)
MIA_JETSON is designed to be "Offline-First" but "Online-Enhanced."

- **Online Mode:** Utilizes ElevenLabs TTS, advanced Cloud APIs, and remote AI models for high-fidelity performance.
- **Offline Mode:** Falls back to Vosk (STT), local TTS engines, and base logic stored on the SSD.
- **Automatic Fallback:** The orchestrator detects internet availability and switches modes dynamically to ensure uninterrupted service.

---

## 6. Runtime State vs. Persistent Memory

A clear distinction is maintained between temporary operational data and long-term knowledge.

### Temporary Runtime Status
Managed by the **Orchestrator**, this data exists only during the current execution session and is not saved permanently (except for diagnostic logs).

**Examples:**
- Current State (`idle`, `listening`, `processing`, `speaking`).
- Hardware status (Mic/Camera active or inactive).
- Environmental data (current audio levels, internet connectivity).
- Active session data (last command received, current user present).

### Persistent Memory
Managed by the **Memory** module using a local **SQLite** database. This data survives system restarts.

**Examples:**
- **Facial Recognition:** Known faces, user embeddings, names, and roles.
- **User Preferences:** Personalized settings and recurring routines.
- **Consolidated Knowledge:** Important facts shared by the user, event history, and behavioral patterns.

### Memory Management Rules
1. **The Brain proposes, the Memory Manager disposes:** The `brain` can suggest information to be saved, but the `memory` module applies logic to decide if it is useful, recurring, or confirmed before committing to the database.
2. **Incremental Learning:** Facial recognition uses a confidence-based factor:
    - **High Confidence:** Automatic recognition.
    - **Medium Confidence:** Ask for confirmation.
    - **Low Confidence:** Treat as unknown.
    - **New Faces:** Trigger registration process.
3. **Data Integrity:** The system distinguishes between "observation" (temporary) and "fact" (consolidated memory) to avoid polluting the database with noise.

---

## 7. Global System States
The Orchestrator manages the following primary states:
- **IDLE:** Waiting for a trigger (wake word or motion).
- **LISTENING:** Capturing audio input for processing.
- **PROCESSING:** Analyzing data and generating a response.
- **SPEAKING:** Playing back audio output.

---

## 8. Hardware Specifications
- **Microphone:** Blue Yeti (Card 25).
- **Speakers:** USB Audio Speakers (Card 0).
- **Camera:** Standard Webcam (/dev/video0).
- **Control:** SSH-based remote management.

---

## 9. Architectural Principles
- **Total Modularity:** Every component is a self-contained unit.
- **Separation of Concerns:** Logic is decoupled from hardware and communication.
- **Scalability:** The architecture is ready for future integration with agents and ROS.
- **Guaranteed Offline Functionality:** Primary features must work without an internet connection.
