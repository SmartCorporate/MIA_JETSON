# MIA_JETSON - LLM Integration (Q&A System)

This document describes the implementation of the Question & Answer system for MIA.

## Architecture

The system follows a strict pipeline architecture:

`Audio Input` → `STT (Vosk)` → `Brain (Local LLM)` → `Response Generator` → `TTS` → `Audio Output`

### Modules

1. **Brain LLM (`src/brain/brain_llm.py`)**
   - Handles text-to-text inference using a local model.
   - **Stateless:** Does not directly write to persistent memory.
   - **Fallback Mode:** Uses rule-based responses if the model file is missing or inference fails.
   - **Configuration:** Managed via `configs/llm_config.json`.

2. **Response Generator (`src/brain/response_generator.py`)**
   - Cleans LLM output (removes artifacts like "A:" or "User:").
   - Enforces length limits for natural-sounding speech.
   - Applies personality and formatting.

3. **Orchestrator (`src/core/orchestrator.py`)**
   - Coordinates the flow between STT, Brain, and TTS.
   - **State Management:** Prevents audio feedback by ensuring the system doesn't listen while speaking.
   - Transitions: `listening` → `processing` → `speaking` → `idle`.

## Configuration (`configs/llm_config.json`)

```json
{
    "model_path": "models/llm/mistral-7b-v0.1.Q4_K_M.gguf",
    "max_tokens": 150,
    "temperature": 0.7,
    "offline_mode": true
}
```

## How to Load a Model

To enable the "real" brain, place a quantized GGUF model in the `models/llm/` directory and update the path in `llm_config.json`. 

Recommended model: `Mistral-7B-Instruct-v0.2.Q4_K_M.gguf` (approx 4.4GB, fits well in Jetson 8GB RAM).

## States

- **listening:** Audio is being captured and processed by Vosk.
- **processing:** The Brain is generating a response (STT is paused).
- **speaking:** TTS is outputting audio (STT is paused).
- **idle:** System is waiting or performing background checks.
