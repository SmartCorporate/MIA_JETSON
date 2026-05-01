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
    # Check if files exist
    qwen_path = brain.config['models']['qwen']['path']
    phi_path = brain.config['models']['phi']['path']
    print(f"Checking Qwen path: {qwen_path} -> {'EXISTS' if os.path.exists(qwen_path) else 'MISSING'}")
    print(f"Checking Phi path: {phi_path} -> {'EXISTS' if os.path.exists(phi_path) else 'MISSING'}")
    
    print("\nSYSTEM READY.")
except Exception as e:
    print(f"\nSYSTEM ERROR: {e}")
    sys.exit(1)
