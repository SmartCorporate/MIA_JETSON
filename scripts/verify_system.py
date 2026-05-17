import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Testing imports...")
    from agents.audio import VoiceAgent, STTAgent
    from agents.brain import BrainLLM, ResponseGenerator
    from core.orchestrator import Orchestrator
    print("Core imports SUCCESSFUL.")
    
    import llama_cpp
    print(f"llama-cpp-python SUCCESSFUL. Version: {llama_cpp.__version__}")
    
    print("\nAttempting to initialize BrainLLM (dual model check)...")
    brain = BrainLLM()
    qwen_smart = os.path.join(brain.base_dir, brain.config['models']['qwen_smart']['path'])
    qwen_fast = os.path.join(brain.base_dir, brain.config['models']['qwen_fast']['path'])
    phi = os.path.join(brain.base_dir, brain.config['models']['phi']['path'])
    print(f"Checking Qwen Smart path: {qwen_smart} -> {'EXISTS' if os.path.exists(qwen_smart) else 'MISSING'}")
    print(f"Checking Qwen Fast path: {qwen_fast} -> {'EXISTS' if os.path.exists(qwen_fast) else 'MISSING'}")
    print(f"Checking Phi path: {phi} -> {'EXISTS' if os.path.exists(phi) else 'MISSING'}")
    
    print("\nSYSTEM READY.")
except Exception as e:
    print(f"\nSYSTEM ERROR: {e}")
    sys.exit(1)
