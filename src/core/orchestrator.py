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
        
    def _detect_language(self, text):
        """Simple heuristic to detect Italian vs English."""
        it_keywords = {"il", "lo", "la", "i", "gli", "le", "di", "a", "da", "in", "con", "su", "per", "tra", "fra", "ciao", "come", "perché", "quando", "chi", "cosa", "non", "sono", "sei", "è"}
        words = set(text.lower().split())
        it_count = len(words.intersection(it_keywords))
        
        # If at least 1-2 common Italian words are found, assume Italian
        detected = "it" if it_count >= 1 else "en"
        print(f"[Orchestrator] Detected language: {detected} (score: {it_count})")
        return detected

    def process_interaction(self, user_text):
        """Pipeline: Text -> Language Detect -> Brain -> Response Gen -> Voice"""
        if not user_text:
            return
            
        # 1. Detect Language
        lang = self._detect_language(user_text)
        self.status.language = lang
        
        # 2. Processing State
        self.status.set_state("processing")
        print(f"[Orchestrator] Processing user input ({lang}): {user_text}")
        
        # 3. Generate response via local LLM
        # We pass the detected language to the Brain if needed (LLM usually follows input language)
        raw_response = self.brain.generate_response(user_text)
        
        # 4. Clean and format response
        final_text = self.generator.format_response(raw_response)
        
        # 5. Speaking State
        self.status.set_state("speaking")
        print(f"[MIA Speaks] ({lang}): {final_text}")
        self.voice.speak(final_text, lang=lang)
        
        # 6. Return to idle
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
