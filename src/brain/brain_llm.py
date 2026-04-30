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
        self.model = None
        self.is_ready = False
        
        # We don't load the heavy model here to avoid crash at startup
        # if the model file is missing or RAM is insufficient.
        # Initialization happens on demand or via explicit call.
        
    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[BrainLLM Warning] Could not load config: {e}")
            return {
                "offline_mode": True,
                "temperature": 0.7,
                "max_tokens": 100
            }

    def load_model(self):
        """
        Attempts to load the local LLM model.
        In a real scenario, this would initialize llama-cpp-python or similar.
        """
        model_path = self.config.get("model_path")
        if not model_path or not os.path.exists(model_path):
            print(f"[BrainLLM] Model not found at {model_path}. Running in Fallback Mode.")
            self.is_ready = False
            return False
        
        try:
            print(f"[BrainLLM] Loading model from {model_path}...")
            # Placeholder for actual LLM loading logic:
            # from llama_cpp import Llama
            # self.model = Llama(model_path=model_path, n_ctx=2048, n_threads=4)
            self.is_ready = True
            print("[BrainLLM] Model loaded successfully.")
            return True
        except Exception as e:
            print(f"[BrainLLM Error] Failed to load model: {e}")
            self.is_ready = False
            return False

    def generate_response(self, text_input):
        """
        Processes the input and returns a response string.
        """
        if not self.is_ready:
            return self._fallback_response(text_input)
            
        try:
            print(f"[BrainLLM] Processing input: {text_input}")
            # Placeholder for inference:
            # response = self.model(f"Q: {text_input}\nA:", max_tokens=self.config['max_tokens'])
            # return response['choices'][0]['text'].strip()
            return f"I understood your request about '{text_input}', but my local inference engine is still in simulation mode."
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
