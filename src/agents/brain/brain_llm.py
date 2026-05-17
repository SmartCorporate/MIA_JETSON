"""
MIA_JETSON - Brain LLM Module
Processes text input using local LLMs (llama.cpp).
STABLE VERSION.
"""
import os
import json
from datetime import datetime

class BrainLLM:
    def __init__(self, config_path="configs/llm_config.json", memory_manager=None):
        self.base_dir = "/home/mia/MIA_JETSON"
        self.config = self._load_config(config_path)
        self.models = {}
        self.is_ready = False
        self.identity_path = os.path.join(self.base_dir, "MIA_Identity.md")
        self.memory = memory_manager

    def _load_config(self, path):
        try:
            full_path = os.path.join(self.base_dir, path)
            with open(full_path, 'r', encoding='utf-8') as f:
                base_cfg = json.load(f)
            return base_cfg
        except:
            return {"offline_mode": True}

    def load_model(self, model_key=None):
        # Default logic for stable loading
        key = "qwen_smart"
        success = self._load_single(key, self.config["models"].get(key, {}))
        if not success:
            success = self._load_single("qwen_fast", self.config["models"]["qwen_fast"])
        self.is_ready = success
        return success

    def _load_single(self, key, model_info):
        rel_path = model_info.get("path")
        model_path = os.path.join(self.base_dir, rel_path)
        if not os.path.exists(model_path): return False
        try:
            from llama_cpp import Llama
            import sys, os as _os
            # Suppress llama.cpp verbose stderr (KV cache, layer assignments)
            devnull = open(_os.devnull, 'w')
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                self.models[key] = Llama(
                    model_path=model_path,
                    n_ctx=model_info.get("n_ctx", 1024),  # Use configured context size (1024+) to fit identity + rules
                    n_gpu_layers=model_info.get("n_gpu_layers", -1),
                    n_threads=model_info.get("n_threads", 4),
                    n_batch=128,         # Smaller batch = lower power = less throttling
                    verbose=False
                )
            finally:
                sys.stderr = old_stderr
                devnull.close()
            # Save active model tag
            gpu_status = "[GPU]" if model_info.get("n_gpu_layers", -1) != 0 else "[CPU]"
            with open("/tmp/mia_active_model", "w") as f:
                f.write(f"{model_info.get('name', key)} {gpu_status}")
            return True
        except Exception as e:
            print(f"[Brain Error] Load failed: {e}")
            return False

    def _read_identity(self):
        try:
            if os.path.exists(self.identity_path):
                with open(self.identity_path, "r", encoding="utf-8") as f:
                    return f.read()
            return "Io sono MIA, un'assistente artificiale."
        except:
            return "Io sono MIA."
 
    def _build_system_prompt(self, speaker: str = "Michele"):
        now = datetime.now()
        identity = self._read_identity()
        
        # Gather dynamic facts from long term memory
        facts_block = ""
        if self.memory:
            facts = self.memory.get_long_term_facts(speaker)
            if facts:
                facts_block = f"\nINFORMAZIONI IMPORTANTI SU {speaker.upper()}:\n"
                for f in facts:
                    facts_block += f"- {f['text']}\n"

        return (
            f"{identity}\n\n"
            f"REGOLE ASSOLUTE:\n"
            f"- Sei MIA, un'assistente vocale empatica e solare. Parli SOLO in italiano.\n"
            f"- Rispondi sempre in modo naturale, fluido ed in perfetto italiano (evita assolutamente espressioni telegrafiche o robotiche come 'Ore 13:55', preferisci invece frasi complete come 'Sono le 13:55').\n"
            f"- Rispondi in modo estremamente conciso, diretto ed essenziale SOLO a quello che ti è stato espressamente chiesto. NON aggiungere mai saluti iniziali, introduzioni, preamboli o chiacchiere superflue non richieste.\n"
            f"- Massimo 1 o 2 frasi brevi. Evita assolutamente elenchi o spiegazioni prolisse.\n"
            f"- L'utente si chiama {speaker}. Mantieni un tono diretto, amichevole e naturale. NON ripetere continuamente il suo nome (usalo solo se strettamente necessario, al massimo una volta ogni 4 o 5 risposte).\n"
            f"- Oggi: {now.strftime('%d %B %Y')}. Ora corrente: {now.strftime('%H:%M')}.\n"
            f"{facts_block}"
        )

    def generate_response(self, text_input: str, lang: str = "it", speaker: str = "Michele") -> str:
        if not self.is_ready: return "Non sono ancora pronta."
        
        # Get active model key and model instance
        model_key = next(iter(self.models.keys()))
        model = self.models[model_key]
        
        try:
            system_prompt = self._build_system_prompt(speaker)
            
            # Format using ChatML if it is a Qwen model
            if "qwen" in model_key.lower():
                # Start ChatML with system prompt
                prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
                
                # Fetch and inject Short-Term Memory rolling history (last 60m)
                if self.memory:
                    history = self.memory.get_short_term_context(speaker)
                    # Inject last 8 turns (4 full exchanges) to maintain rich context without bloating prompt
                    for turn in history[-8:]:
                        role = turn.get("role")
                        text = turn.get("text")
                        if role and text:
                            chat_role = "user" if role == "user" else "assistant"
                            prompt += f"<|im_start|>{chat_role}\n{text}<|im_end|>\n"
                
                # Append current user input
                prompt += (
                    f"<|im_start|>user\n{text_input}<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                stop_tokens = ["<|im_end|>", "<|im_start|>", "<|user|>", "<|system|>", "Utente:", f"{speaker}:", "MIA:", "\n\n"]
            else:
                # Fallback format
                history_str = ""
                if self.memory:
                    history = self.memory.get_short_term_context(speaker)
                    for turn in history[-6:]:
                        role = "Utente" if turn.get("role") == "user" else "MIA"
                        history_str += f"{role}: {turn.get('text')}\n"
                
                prompt = f"{system_prompt}\n{history_str}Utente: {text_input}\nMIA:"
                stop_tokens = ["<|user|>", "\n\n", f"{speaker}:", "Utente:", "MIA:"]
            
            # Generate
            res = model(
                prompt,
                max_tokens=100,          # Allow complete, natural sentences
                stop=stop_tokens,
                temperature=0.2,         # Low temp = highly focused & deterministic
                repeat_penalty=1.1
            )
            
            answer = res["choices"][0]["text"].strip()
            # Strip any self-referencing prefix like "MIA:" or "Risposta:"
            for prefix in ["MIA:", "Risposta:", "A:", "R:"]:
                if answer.lower().startswith(prefix.lower()):
                    answer = answer[len(prefix):].strip()
            return answer
        except Exception as e:
            print(f"[Brain Error] {e}")
            return "Ho avuto un problema tecnico."
