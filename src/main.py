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

def is_online():
    """Check if the system has internet connectivity."""
    import socket
    try:
        # Try to connect to a reliable host (Google DNS)
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except (OSError, socket.timeout):
        return False

def main():
    print("Initializing MIA_JETSON...")
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    print("Loading configurations...")
    # TODO: Load configs from configs/
    
    print("Initializing core agents...")
    voice_agent = VoiceAgent()
    
    # Determine connectivity status for the greeting
    online_status = is_online()
    status_text = "online" if online_status else "offline"
    
    print(f"MIA is now {status_text} and listening...")
    
    # First spoken words reflect actual connectivity
    voice_agent.speak(f"Hello, I am Mia. My audio systems are {status_text}.")
    
    try:
        # Simple loop to keep the process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down MIA_JETSON...")

if __name__ == "__main__":
    main()
