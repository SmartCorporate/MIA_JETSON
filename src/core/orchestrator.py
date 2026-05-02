"""
MIA_JETSON - Central Orchestrator
Coordinates modules and manages global system flow.
KEY OPTIMIZATION: Greeting fires IMMEDIATELY at boot,
then LLM loads in a background thread (masked loading).
"""
import os
import socket
import time
import threading
from dotenv import load_dotenv
from agents.audio import VoiceAgent, STTAgent
from agents.brain import BrainLLM, ResponseGenerator
from .status_manager import StatusManager


class Orchestrator:
    def __init__(self):
        # Load environment variables
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'
        )
        load_dotenv(env_path)

        print("[Orchestrator] Inizializzazione MIA...")
        self.status = StatusManager()
        self._llm_ready = threading.Event()  # Signals when LLM is loaded

        # 1. Init lightweight agents first (fast: <1s each)
        self.voice = VoiceAgent()
        self.stt   = STTAgent()
        self.brain = BrainLLM()
        self.generator = ResponseGenerator()

        # 2. Check connectivity (fast)
        self.check_connectivity()

    # ------------------------------------------------------------------
    # Connectivity
    # ------------------------------------------------------------------
    def check_connectivity(self):
        """Checks internet connectivity and updates status."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self.status.update_connectivity(True)
        except (OSError, socket.timeout):
            self.status.update_connectivity(False)

    # ------------------------------------------------------------------
    # Startup — MASKED LOADING
    # ------------------------------------------------------------------
    def startup(self):
        """
        Fast startup sequence:
        1. Say welcome greeting IMMEDIATELY
        2. Load LLM in background thread (user doesn't wait)
        3. Notify with a short sound/message when brain is ready
        """
        # Step 1: Greet immediately (before LLM loads)
        online_text = "online" if self.status.is_online else "offline"
        greeting = f"Ciao, sono MIA. Sistema {online_text}. Sto attivando il cervello."
        print(f"[Orchestrator] Saluto immediato: {greeting}")
        self.status.set_state("speaking")
        self.voice.speak(greeting, lang="it")
        self.status.set_state("loading")

        # Step 2: Start background LLM loading thread
        load_thread = threading.Thread(
            target=self._background_load_llm,
            name="LLM-Loader",
            daemon=True
        )
        load_thread.start()
        print("[Orchestrator] Caricamento LLM in background avviato...")

    def _background_load_llm(self):
        """Loads the primary LLM in background; signals when done."""
        try:
            print("[Orchestrator] [Thread] Caricamento modello LLM...")
            success = self.brain.load_model()  # Loads only primary (qwen)
            self._llm_ready.set()

            if success:
                print("[Orchestrator] [Thread] LLM caricato OK. MIA è pronta.")
                self.status.set_state("idle")
                self.voice.speak("Pronta.", lang="it")
            else:
                print("[Orchestrator] [Thread] LLM non trovato. Modalità fallback.")
                self.status.set_state("idle")
                self.voice.speak("Modalità ridotta attiva.", lang="it")
        except Exception as e:
            print(f"[Orchestrator] [Thread] Errore caricamento LLM: {e}")
            self._llm_ready.set()
            self.status.set_state("idle")

    # ------------------------------------------------------------------
    # Interaction pipeline
    # ------------------------------------------------------------------
    def process_interaction(self, user_text: str, lang: str = "it"):
        """Pipeline: Text → Brain → ResponseGen → Voice"""
        if not user_text:
            return

        self.status.language = lang
        self.status.set_state("processing")
        print(f"[Orchestrator] Input ({lang}): {user_text}")

        # Generate response
        raw_response = self.brain.generate_response(user_text, lang=lang)

        # Format
        final_text = self.generator.format_response(raw_response)

        # Speak
        self.status.set_state("speaking")
        print(f"[MIA] ({lang}): {final_text}")
        self.voice.speak(final_text, lang=lang)

        # Back to idle
        self.status.set_state("idle")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run_forever(self):
        """Main listen-respond loop. Waits until LLM is at least attempting to load."""
        print("[Orchestrator] MIA in ascolto...")
        try:
            while True:
                current = self.status.current_state

                if current == "idle":
                    # Listen (blocks for up to 5s)
                    user_text, detected_lang = self.stt.listen(timeout=5)
                    if user_text:
                        # If LLM is still loading, still process (fallback will handle it)
                        self.process_interaction(user_text, lang=detected_lang or "it")
                        time.sleep(0.8)
                        self.stt.flush_queue()

                elif current == "loading":
                    # Still loading LLM — listen anyway (fallback will respond)
                    user_text, detected_lang = self.stt.listen(timeout=5)
                    if user_text:
                        self.process_interaction(user_text, lang=detected_lang or "it")
                        self.stt.flush_queue()

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("[Orchestrator] Spegnimento MIA...")
