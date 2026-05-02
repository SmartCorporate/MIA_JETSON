"""
MIA_JETSON - Brain LLM Module
Processes text input using local LLMs (llama.cpp) and returns a text response.
- Primary model: Qwen 2.5 7B Instruct (conversation, Italian)
- Reasoning model: Phi-3.5 Mini Instruct (lazy-loaded on demand)
- Injects current date/time into every prompt
- Optimized for NVIDIA Jetson GPU (n_gpu_layers=-1, f16_kv, low threads)
"""
import os
import json
from datetime import datetime

class BrainLLM:
    def __init__(self, config_path="configs/llm_config.json"):
        self.config = self._load_config(config_path)
        self.models = {}       # Loaded model instances
        self.is_ready = False  # True once at least one model is loaded

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[BrainLLM Warning] Could not load config: {e}")
            return {"offline_mode": True}

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------
    def load_model(self, model_key=None):
        """
        Load models from config.
        If model_key is None, loads only the DEFAULT (primary) model.
        The reasoning model is lazy-loaded the first time it is needed.
        """
        config_models = self.config.get("models", {})
        default_key = self.config.get("default_model", "qwen")

        # At startup, only load the primary model to be fast
        keys_to_load = [model_key] if model_key else [default_key]

        for key in keys_to_load:
            if key in self.models:
                continue  # Already loaded
            model_info = config_models.get(key)
            if not model_info:
                continue
            self._load_single(key, model_info)

        self.is_ready = len(self.models) > 0
        return self.is_ready

    def _load_single(self, key, model_info):
        """Load one model and store it."""
        model_path = model_info.get("path")
        if not model_path or not os.path.exists(model_path):
            print(f"[BrainLLM] Model '{key}' not found at '{model_path}'. Skipping.")
            return False
        try:
            print(f"[BrainLLM] Loading '{model_info['name']}' from {model_path}...")
            from llama_cpp import Llama
            self.models[key] = Llama(
                model_path=model_path,
                n_ctx=model_info.get("n_ctx", 1024),
                n_gpu_layers=model_info.get("n_gpu_layers", -1),  # All layers on GPU
                n_threads=model_info.get("n_threads", 2),          # Low: GPU does the work
                n_batch=model_info.get("n_batch", 256),            # GPU batch size
                f16_kv=model_info.get("f16_kv", True),             # Save VRAM with fp16 KV
                use_mmap=model_info.get("use_mmap", True),         # Fast load
                verbose=model_info.get("verbose", False),          # No llama.cpp spam
            )
            print(f"[BrainLLM] '{model_info['name']}' loaded OK.")
            return True
        except Exception as e:
            print(f"[BrainLLM Error] Failed to load '{key}': {e}")
            return False

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------
    def _select_model(self, text_input: str) -> str:
        """
        Choose which model to use:
        - Phi-3.5 Mini for heavy reasoning/math/code/logic
        - Qwen 2.5 7B for everything else (including Italian conversation)
        Lazy-loads the reasoning model on first use.
        """
        text = text_input.lower()
        reasoning_keywords = [
            "perché", "come funziona", "come si calcola", "calcola", "risolvi",
            "spiega in dettaglio", "logica", "confronta", "codice", "programma",
            "why", "how to", "solve", "calculate", "logic", "code", "compare",
            "explain", "formula", "math", "matematica", "algoritmo"
        ]

        if any(kw in text for kw in reasoning_keywords):
            # Lazy-load reasoning model if not already loaded
            if "phi" not in self.models:
                config_models = self.config.get("models", {})
                phi_info = config_models.get("phi")
                if phi_info:
                    print("[BrainLLM] Lazy-loading reasoning model (Phi-3.5 Mini)...")
                    self._load_single("phi", phi_info)
            if "phi" in self.models:
                return "phi"

        return "qwen" if "qwen" in self.models else next(iter(self.models), None)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def _build_system_prompt(self, is_verbose: bool) -> str:
        """Build system prompt enriched with real-time date/time."""
        now = datetime.now()
        date_str = now.strftime("%A %d %B %Y")   # e.g. "Venerdì 02 Maggio 2025"
        time_str = now.strftime("%H:%M")          # e.g. "14:35"

        # Italian day/month names
        it_days = {
            "Monday": "Lunedì", "Tuesday": "Martedì", "Wednesday": "Mercoledì",
            "Thursday": "Giovedì", "Friday": "Venerdì", "Saturday": "Sabato", "Sunday": "Domenica"
        }
        it_months = {
            "January": "Gennaio", "February": "Febbraio", "March": "Marzo",
            "April": "Aprile", "May": "Maggio", "June": "Giugno",
            "July": "Luglio", "August": "Agosto", "September": "Settembre",
            "October": "Ottobre", "November": "Novembre", "December": "Dicembre"
        }
        for en, it in {**it_days, **it_months}.items():
            date_str = date_str.replace(en, it)

        base = self.config.get("verbose_system_prompt" if is_verbose else "system_prompt",
                               "Sei MIA, l'assistente vocale di IMPERIUM. Rispondi in italiano.")
        return (
            f"{base}\n"
            f"Data odierna: {date_str}. Ora corrente: {time_str}.\n"
            f"Quando ti chiedono la data o l'ora, rispondi con queste informazioni esatte."
        )

    def generate_response(self, text_input: str, lang: str = "it") -> str:
        """Main inference pipeline."""
        if not self.is_ready:
            return self._fallback_response(text_input)

        model_key = self._select_model(text_input)
        model = self.models.get(model_key)
        if not model:
            return self._fallback_response(text_input)

        try:
            text_lower = text_input.lower()
            verbose_kw = [
                "spiegamelo meglio", "spiega meglio", "approfondisci",
                "spiegami", "dimmi di più", "più dettagli", "come funziona",
                "in dettaglio", "voglio sapere"
            ]
            is_verbose = any(kw in text_lower for kw in verbose_kw)

            max_t  = self.config.get("max_tokens", 60)
            max_t  = max_t * 3 if is_verbose else max_t

            system_p = self._build_system_prompt(is_verbose)

            print(f"[BrainLLM] model={model_key}, verbose={is_verbose}, max_tokens={max_t}")

            prompt = (
                f"<|system|>\n{system_p}\n"
                f"<|user|>\n{text_input}\n"
                f"<|assistant|>\n"
            )

            response = model(
                prompt,
                max_tokens=max_t,
                stop=["<|user|>", "<|system|>", "User:", "\n\n", "User"],
                temperature=self.config.get("temperature", 0.35),
                top_p=self.config.get("top_p", 0.9),
                top_k=self.config.get("top_k", 40),
                repeat_penalty=self.config.get("repeat_penalty", 1.1),
            )
            return response['choices'][0]['text'].strip()

        except Exception as e:
            print(f"[BrainLLM Error] Inference failed: {e}")
            return self._fallback_response(text_input)

    # ------------------------------------------------------------------
    # Fallback (no LLM available)
    # ------------------------------------------------------------------
    def _fallback_response(self, text_input: str) -> str:
        """Rule-based Italian fallback when LLM is unavailable."""
        t = text_input.lower()
        now = datetime.now()

        # Date/time — always available even without LLM
        if any(w in t for w in ["ora", "che ore", "orario"]):
            return f"Sono le {now.strftime('%H:%M')}."
        if any(w in t for w in ["giorno", "data", "oggi", "che giorno"]):
            it_days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            it_months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                         "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
            day_name = it_days[now.weekday()]
            month_name = it_months[now.month - 1]
            return f"Oggi è {day_name} {now.day} {month_name} {now.year}."

        # Basic greetings
        if any(w in t for w in ["ciao", "salve", "hello", "hi"]):
            return "Ciao! Sono MIA. Il modello linguistico non è ancora caricato."
        if any(w in t for w in ["status", "come stai", "funzioni"]):
            return "I miei sistemi operativi. Il modello LLM è in caricamento."
        if any(w in t for w in ["chi sei", "who are you", "presentati"]):
            return "Sono MIA, la tua assistente vocale su NVIDIA Jetson."

        return "Ti sento. Sto ancora caricando il modello linguistico, attendi."
