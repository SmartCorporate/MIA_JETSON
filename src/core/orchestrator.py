"""
MIA_JETSON - Central Orchestrator
Coordinates modules and manages global system flow and state.
As per architecture, this module contains NO AI logic.
"""
import os
import socket
import time
from dotenv import load_dotenv
from audio import VoiceAgent, STTAgent
from core.status_manager import StatusManager
from brain.brain_llm import BrainLLM
from brain.response_generator import ResponseGenerator

class Orchestrator:
    def __init__(self):
        # Load environment variables (from project root)
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        load_dotenv(env_path)
        
        print("[Orchestrator] Initializing system...")
        self.status = StatusManager()
        
        # Initialize core agents
        self.voice = VoiceAgent()
        self.stt = STTAgent()
        self.brain = BrainLLM()
        self.generator = ResponseGenerator()
        
        # Initial checks
        self.check_connectivity()
        
        # Attempt to load models at start (Conversation & Reasoning)
        self.brain.load_model()
        
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
        
    def process_interaction(self, user_text):
        """Pipeline: Text -> Brain -> Response Gen -> Voice"""
        if not user_text:
            return
            
        # 1. Processing State
        self.status.set_state("processing")
        print(f"[Orchestrator] Processing user input: {user_text}")
        
        # 2. Generate response via local LLM
        raw_response = self.brain.generate_response(user_text)
        
        # 3. Clean and format response
        final_text = self.generator.format_response(raw_response)
        
        # 4. Speaking State
        self.status.set_state("speaking")
        print(f"[MIA Speaks]: {final_text}")
        self.voice.speak(final_text)
        
        # 5. Return to idle
        self.status.set_state("idle")

    def run_forever(self):
        """Main loop managed by orchestrator."""
        print("[Orchestrator] MIA is ready and listening...")
        try:
            while True:
                # Only listen if we are idle
                if self.status.current_state == "idle":
                    # Potentially check for wake word here
                    # For now, we simulate a polling mechanism
                    # user_text = self.stt.listen()
                    # if user_text:
                    #     self.process_interaction(user_text)
                    pass
                
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("[Orchestrator] Shutting down...")
