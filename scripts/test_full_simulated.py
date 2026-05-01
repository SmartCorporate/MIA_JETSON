import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.orchestrator import Orchestrator

def test_simulated():
    print("Initializing Orchestrator for Simulated Test...")
    mia = Orchestrator()
    
    # Wait for models to load
    print("Waiting 10s for models to load...")
    time.sleep(10)
    
    test_cases = [
        ("Ciao Mia", "it"),
        ("How are you today?", "en")
    ]
    
    for text, lang in test_cases:
        print(f"\n--- SIMULATING INPUT: '{text}' ({lang}) ---")
        try:
            mia.process_interaction(text, lang=lang)
            print("Interaction completed successfully.")
        except Exception as e:
            print(f"Interaction FAILED: {e}")
        time.sleep(2)

if __name__ == "__main__":
    test_simulated()
