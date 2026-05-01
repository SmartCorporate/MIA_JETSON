"""
MIA_JETSON - Brain LLM Module
Processes text input using a local LLM (e.g., Llama.cpp) and returns a text response.
This module is stateless and does not write to memory directly.
"""
import os
import json

class BrainLLM:
    def __init__(self, config_path="configs/llm_config.json"):
        self.config = self._load_config(config_path)
        self.models = {}  # Store multiple model instances
        self.is_ready = False
        
    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[BrainLLM Warning] Could not load config: {e}")
            return {"offline_mode": True}

    def load_model(self, model_key=None):
        """
        Attempts to load models. If model_key is None, attempts to load all configured models.
        """
        config_models = self.config.get("models", {})
        keys_to_load = [model_key] if model_key else config_models.keys()
        
        success_count = 0
        for key in keys_to_load:
            model_info = config_models.get(key)
            if not model_info: continue
            
            model_path = model_info.get("path")
            if not model_path or not os.path.exists(model_path):
                print(f"[BrainLLM] Model {key} not found at {model_path}.")
                continue
            
            try:
                print(f"[BrainLLM] Loading {model_info['name']} from {model_path}...")
                from llama_cpp import Llama
                self.models[key] = Llama(
                    model_path=model_path, 
                    n_ctx=2048, 
                    n_gpu_layers=-1, # Use all GPU layers on Jetson
                    n_threads=4
                )
                success_count += 1
            except Exception as e:
                print(f"[BrainLLM Error] Failed to load model {key}: {e}")
        
        self.is_ready = success_count > 0
        return self.is_ready

    def _select_model(self, text_input):
        """
        Decides which model to use based on the input text.
        """
        text = text_input.lower()
        # Keywords that trigger the 'Reasoning' (Phi-2) model
        reasoning_keywords = ["why", "how to", "solve", "calculate", "logic", "reason", "think", "compare", "explain", "code", "perché", "come"]
        
        if any(kw in text for kw in reasoning_keywords):
            return "phi" if "phi" in self.models else "qwen"
        
        return "qwen" if "qwen" in self.models else "phi"

    def generate_response(self, text_input, lang="en"):
        """
        Processes the input using the appropriate model.
        """
        model_key = self._select_model(text_input)
        
        if not self.is_ready:
            return self._fallback_response(text_input)
            
        try:
            print(f"[BrainLLM] Using model: {model_key} for input: {text_input} ({lang})")
            model = self.models.get(model_key)
            if model:
                # Force language and directness
                lang_instruction = "IMPORTANT: Respond ONLY in Italian." if lang == "it" else "IMPORTANT: Respond ONLY in English."
                system_p = self.config.get('system_prompt', '')
                
                # Enhanced ChatML for better adherence
                prompt = f"<|system|>\n{system_p}\n{lang_instruction}\nRespond directly. No stories.\n<|user|>\n{text_input}\n<|assistant|>\n"
                
                response = model(
                    prompt, 
                    max_tokens=self.config.get('max_tokens', 50), 
                    stop=["<|user|>", "<|system|>", "User:", "\n\n", "User"],
                    temperature=0.3 # Lower temperature for less 'nonsense'
                )
                return response['choices'][0]['text'].strip()
            
            return f"Error: Model {model_key} not found."
        except Exception as e:
            print(f"[BrainLLM Error] Inference failed: {e}")
            return self._fallback_response(text_input)

    def _fallback_response(self, text_input):
        """Rule-based fallback when LLM is unavailable."""
        text_input = text_input.lower()
        if "hello" in text_input or "hi" in text_input:
            return "Hello! I am MIA. I am currently running in offline fallback mode."
        if "status" in text_input:
            return "My systems are operational, but my large language model is not loaded."
        if "who are you" in text_input:
            return "I am MIA, your AI assistant running on NVIDIA Jetson."
            
        return "I heard you, but I cannot process complex requests without my local brain model."
