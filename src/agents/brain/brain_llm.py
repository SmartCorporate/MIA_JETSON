"""
MIA_JETSON - Brain LLM Module
Processes text input using local LLMs (llama.cpp).
Integrates Identity from MIA_Identity.md.
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
            
            # Desktop Config
            try:
                from core.config_loader import load_general_config
                gen_cfg = load_general_config()
                base_cfg["general"] = gen_cfg
                # Check for QWEN_7B_SMART
                smart_path = os.path.join(self.base_dir, base_cfg["models"]["qwen_smart"]["path"])
                if os.path.exists(smart_path):
                    base_cfg["default_model"] = "qwen_smart"
                else:
                    base_cfg["default_model"] = "qwen_fast"
            except:
                base_cfg["general"] = {}
                base_cfg["default_model"] = "qwen_fast"
                 
            return base_cfg
        except Exception as e:
            print(f"[BrainLLM Warning] {e}")
            return {"offline_mode": True}

    def load_model(self, model_key=None):
        default_key = self.config.get("default_model", "qwen_smart")
        key = model_key if model_key else default_key
        success = self._load_single(key, self.config["models"].get(key, {}))
        
        if not success and key == "qwen_smart":
            print("[BrainLLM] Fallback automatico su 1.5B...")
            success = self._load_single("qwen_fast", self.config["models"]["qwen_fast"])
            
        self.is_ready = success
        return success

    def _load_single(self, key, model_info):
        rel_path = model_info.get("path")
        if not rel_path: return False
        model_path = os.path.join(self.base_dir, rel_path)
        
        if not os.path.exists(model_path): return False
        
        try:
            from llama_cpp import Llama
            print(f"[BrainLLM] Caricamento {key}...")
            self.models[key] = Llama(
                model_path=model_path,
                n_ctx=1024,
                n_gpu_layers=-1,
                n_threads=4,
                n_batch=512,
                f16_kv=True,
                use_mmap=True,
                verbose=False,
            )
            # SALVA MODELLO ATTIVO PER IL MONITOR
            with open("/tmp/mia_active_model", "w") as f:
                f.write(model_info.get("name", key))
            return True
        except Exception as e:
            print(f"[BrainLLM Error] {e}")
            return False

    def _read_identity(self):
        try:
            if os.path.exists(self.identity_path):
                with open(self.identity_path, "r", encoding="utf-8") as f:
                    return f.read()
            return "Sei MIA, un'assistente umanoide femminile empatica."
        except:
            return "Sei MIA, assistente umanoide."

    def _build_system_prompt(self):
        gen = self.config.get("general", {})
        conc = gen.get("CONCISIONE", 3)
        identity_text = self._read_identity()
        
        # INSTRUCTIONS
        conc_instr = "Rispondi in massimo 15 parole." if conc >= 4 else "Puoi essere discorsiva."
        
        system = f"""
{identity_text}

ISTRUZIONI DI SICUREZZA IDENTITÀ:
- TU SEI MIA. L'UTENTE È MICHELE.
- Parla SEMPRE in prima persona (IO). Usa il possessivo "MIO/MIA" per te stessa.
- Il TUO creatore è Michele Zaniolo.
- Tono: Sii sempre FELICE, POSITIVA e SOLARE. Ispira fiducia.
- Rispondi sempre in ITALIANO.
- {conc_instr}
Data/Ora corrente: {datetime.now().strftime('%d/%m %H:%M')}
"""
        return system.strip()

    def generate_response(self, text_input: str, lang: str = "it") -> str:
        if not self.is_ready: return "Caricamento..."
        model = next(iter(self.models.values()))
        
        try:
            gen = self.config.get("general", {})
            max_t = {1:15, 2:40, 3:80, 4:150, 5:300}.get(gen.get("LUNGHEZZA", 2), 40)
            
            prompt = f"<|system|>\n{self._build_system_prompt()}\n<|user|>\n{text_input}\n<|assistant|>\n"
            response = model(
                prompt,
                max_tokens=max_t,
                stop=["<|user|>", "<|system|>"],
                temperature=0.5, # Slightly higher for "personality"
                repeat_penalty=1.1,
            )
            reply = response['choices'][0]['text'].strip()
            if not reply: return "Scusa, non ho capito."
            return reply
        except:
            return "Errore di elaborazione."
