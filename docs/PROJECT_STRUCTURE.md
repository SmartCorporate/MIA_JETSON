# MIA_JETSON - Project Architecture & Directory Structure

This document outlines the professional directory structure for the MIA (Modular Artificial Intelligence) system on the NVIDIA Jetson.

```text
MIA_JETSON/
├── assets/                  # Static assets (images, sound effects, system icons)
├── configs/                 # JSON configuration files for all modules
├── data/                    # Persistent storage (SQLite databases, session data)
├── docs/                    # Documentation and architecture diagrams
├── logs/                    # System and module-specific log files
├── models/                  # Pre-trained models (GGUF LLMs, Vosk STT)
│   ├── llm/                 # Large Language Models (Qwen, Phi-2)
│   └── stt/                 # Speech-to-Text models (Vosk)
├── scripts/                 # Maintenance, setup, and diagnostic tools
├── src/                     # Core Source Code
│   ├── main.py              # System entry point
│   ├── core/                # System-wide logic
│   │   ├── orchestrator.py  # Central pipeline coordination
│   │   └── status_manager.py # Real-time state and connectivity tracking
│   ├── agents/              # Pipeline sub-agents (Modular & Independent)
│   │   ├── audio/           # Speech-to-Text and Text-to-Speech
│   │   ├── brain/           # LLM processing and Response Generation
│   │   └── vision/          # Camera processing and Object Detection
│   ├── hardware/            # Low-level hardware drivers (GPIO, Servos, I2C)
│   ├── memory/              # Memory management and Knowledge Base access
│   └── utils/               # Shared utilities (logging, networking, math)
├── tests/                   # Unit and integration tests
├── requirements.txt         # Project dependencies
└── mia_jetson.service       # Systemd service unit for background execution
```

## Naming Conventions
- **Modules:** Use clear, descriptive English nouns (e.g., `orchestrator`, `vision`, `memory`).
- **Files:** Use `snake_case` (e.g., `voice_agent.py`).
- **Classes:** Use `PascalCase` (e.g., `BrainLLM`).

## Pipeline Philosophy
Each module in `src/agents/` should be independent and follow the pattern:
`Input` -> `Process` -> `Output`

The `Orchestrator` is the only component allowed to bridge data between different agents.
