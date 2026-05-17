"""
MIA_JETSON - Central Orchestrator
Coordinates modules and manages global system flow.
KEY: Greeting fires ONLY when LLM is fully loaded and ready.
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
        Startup sequence:
        1. Set state to loading (silent — no greeting yet)
        2. Load LLM in background thread
        3. When LLM is ready, THEN say greeting
        """
        self.status.set_state("loading")
        print("[Orchestrator] Caricamento LLM in background...")

        load_thread = threading.Thread(
            target=self._background_load_llm,
            name="LLM-Loader",
            daemon=True
        )
        load_thread.start()

    def _background_load_llm(self):
        """Loads the primary LLM in background; greets ONLY when done."""
        try:
            print("[Orchestrator] [Thread] Caricamento modello LLM...")
            success = self.brain.load_model()

            # Stabilize after VRAM allocation
            time.sleep(1.0)
            self._llm_ready.set()

            if success:
                print("[Orchestrator] [Thread] LLM pronto. MIA attiva.")
                self.status.set_state("speaking")
                # Greeting ONLY now — LLM is truly ready
                self.voice.speak("Ciao, sono MIA e sono pronta.", lang="it")
                self.status.set_state("idle")
            else:
                print("[Orchestrator] [Thread] LLM non caricato. Modalità fallback.")
                self.status.set_state("speaking")
                self.voice.speak("Ciao, sono MIA. Funziono in modalità ridotta.", lang="it")
                self.status.set_state("idle")
        except Exception as e:
            print(f"[Orchestrator] [Thread] Errore: {e}")
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
                        # Double-check that we are still in idle state (wasn't interrupted by speaking)
                        if self.status.current_state == "idle":
                            self.process_interaction(user_text, lang=detected_lang or "it")
                            # Aumentato a 3 secondi per evitare che senta l'eco della propria voce
                            time.sleep(3.0)
                            self.stt.flush_queue()
                        else:
                            print("[Orchestrator] Discarding STT input captured during non-idle state (echo prevention).")
                            self.stt.flush_queue()

                elif current == "loading":
                    # Still loading LLM — listen anyway (fallback will respond)
                    user_text, detected_lang = self.stt.listen(timeout=5)
                    if user_text:
                        # Double-check that the state didn't transition to speaking/idle during greeting
                        if self.status.current_state == "loading":
                            self.process_interaction(user_text, lang=detected_lang or "it")
                            self.stt.flush_queue()
                        else:
                            print("[Orchestrator] Discarding STT input captured during background greeting load.")
                            self.stt.flush_queue()

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("[Orchestrator] Spegnimento MIA...")
