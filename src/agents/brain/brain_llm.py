"""
MIA_JETSON - Brain LLM Module
Processes text input using local LLMs (llama.cpp).
STABLE VERSION.
"""
import os
import json
from datetime import datetime

class BrainLLM:
    def __init__(self, config_path="configs/llm_config.json"):
        self.base_dir = "/home/mia/MIA_JETSON"
        self.config = self._load_config(config_path)
        self.models = {}
        self.is_ready = False
        self.identity_path = os.path.join(self.base_dir, "MIA_Identity.md")

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

    def _build_system_prompt(self):
        now = datetime.now()
        identity = self._read_identity()
        return (
            f"{identity}\n\n"
            f"REGOLE ASSOLUTE:\n"
            f"- Sei MIA. Parli SOLO italiano.\n"
            f"- Rispondi SOLO alla domanda posta. Niente aggiunte.\n"
            f"- Massimo 2 frasi brevi. Mai elenchi.\n"
            f"- Tono diretto e amichevole. L'utente si chiama Michele. NON ripetere continuamente il suo nome (usalo solo se strettamente necessario, al massimo una volta ogni 4 o 5 risposte).\n"
            f"- Oggi: {now.strftime('%d %B %Y')}.\n"
        )

    def generate_response(self, text_input: str, lang: str = "it") -> str:
        if not self.is_ready: return "Non sono ancora pronta."
        
        # Get active model key and model instance
        model_key = next(iter(self.models.keys()))
        model = self.models[model_key]
        
        try:
            system_prompt = self._build_system_prompt()
            
            # Format using ChatML if it is a Qwen model
            if "qwen" in model_key.lower():
                prompt = (
                    f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
                    f"<|im_start|>user\n{text_input}<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                stop_tokens = ["<|im_end|>", "<|im_start|>", "<|user|>", "<|system|>", "\n\n", "Utente:"]
            else:
                # Fallback format
                prompt = f"{system_prompt}\nUtente: {text_input}\nMIA:"
                stop_tokens = ["<|user|>", "\n\n", "Michele:", "Utente:"]
            
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
