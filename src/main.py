"""
MIA_JETSON - Main Orchestrator
This simple entry point will initialize the main AI assistant agent, 
which in turn manages the sub-agents (Audio, Vision, Memory, Brain).
"""
import os
import time
from dotenv import load_dotenv

# Import core modules
from audio import VoiceAgent

def main():
    print("Initializing MIA_JETSON...")
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    print("Loading configurations...")
    # TODO: Load configs from configs/
    
    print("Initializing core agents...")
    voice_agent = VoiceAgent()
    
    print("MIA is now online and listening...")
    
    # First spoken words
    voice_agent.speak("Hello, I am Mia. My audio systems are online.")
    
    try:
        # Simple loop to keep the process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down MIA_JETSON...")

if __name__ == "__main__":
    main()
