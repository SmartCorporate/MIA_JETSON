"""
MIA_JETSON - Main Orchestrator
This simple entry point will initialize the main AI assistant agent, 
which in turn manages the sub-agents (Audio, Vision, Memory, Brain).
"""
# Import core orchestrator
from core.orchestrator import Orchestrator

def main():
    # Initialize the orchestrator (it handles .env, voice_agent, and status)
    mia = Orchestrator()
    
    # Run the startup sequence (Greetings and status check)
    mia.startup()
    
    # Hand over to the main loop
    mia.run_forever()

if __name__ == "__main__":
    main()
