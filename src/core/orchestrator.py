"""
MIA_JETSON - Central Orchestrator
Coordinates modules and manages global system flow and state.
As per architecture, this module contains NO AI logic.
"""
import os
import socket
from dotenv import load_dotenv
from audio import VoiceAgent
from core.status_manager import StatusManager

class Orchestrator:
    def __init__(self):
        # Load environment variables (from project root)
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        load_dotenv(env_path)
        
        print("[Orchestrator] Initializing system...")
        self.status = StatusManager()
        
        # Initialize core agents
        self.voice = VoiceAgent()
        
        # Initial checks
        self.check_connectivity()
        
    def check_connectivity(self):
        """Checks internet connectivity and updates status."""
        try:
            # Check Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self.status.update_connectivity(True)
        except (OSError, socket.timeout):
            self.status.update_connectivity(False)
            
    def startup(self):
        """System startup sequence."""
        online_text = "ONLINE" if self.status.is_online else "OFFLINE"
        
        # Optimal syntax for clarity at power-on
        greeting = f"Hello. I am Mia. System {online_text}."
        
        print(f"[Orchestrator] Greeting: {greeting}")
        self.status.set_state("speaking")
        self.voice.speak(greeting)
        self.status.set_state("idle")
        
    def run_forever(self):
        """Main loop managed by orchestrator."""
        try:
            while True:
                # Basic heartbeat/maintenance tasks could go here
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("[Orchestrator] Shutting down...")
