"""
Test script for the MIA Q&A Pipeline logic.
Simulates a user speaking and tracks the flow through Brain and Response Generator.
"""
from core.orchestrator import Orchestrator
import time

def test_pipeline():
    print("--- MIA Q&A Pipeline Test ---")
    mia = Orchestrator()
    
    # Simulate user input
    test_inputs = [
        "Hello Mia, how are you today?",
        "What is your status?",
        "Tell me about yourself."
    ]
    
    for user_text in test_inputs:
        print(f"\n[User]: {user_text}")
        mia.process_interaction(user_text)
        time.sleep(1)
    
    print("\nTest completed.")

if __name__ == "__main__":
    test_pipeline()
