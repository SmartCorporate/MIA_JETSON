"""
MIA_JETSON - Cognitive Memory Consolidation Agent
Asynchronously extracts permanent profile facts (LTM) from conversational turns
using the local loaded Qwen instance without adding voice latency.
"""
import json
import re
import traceback

class MemoryAgent:
    def __init__(self, memory_manager, brain_llm):
        self.memory = memory_manager
        self.brain = brain_llm

    def consolidate_interaction(self, speaker: str, user_text: str, mia_response: str) -> bool:
        """
        Analyze the exchange, extract permanent facts in the background,
        and save them to long-term memory.
        """
        if not self.brain or not self.brain.is_ready:
            return False

        try:
            # Access the loaded model instance in BrainLLM
            model_key = next(iter(self.brain.models.keys()))
            model = self.brain.models[model_key]

            # Construct structured cognitive extraction prompt
            prompt = (
                "<|im_start|>system\n"
                "Sei il consolidatore di memoria cognitiva di MIA. Il tuo compito è analizzare lo scambio di battute avvenuto tra l'utente Michele e l'assistente MIA ed estrarre TUTTI i fatti personali permanenti, relazioni stabili o preferenze consolidate riguardanti l'utente o i suoi familiari da ricordare a lungo termine (ad esempio: nomi, legami di parentela, compleanni, cibi preferiti, possedimenti importanti, passioni, hobby, lavoro).\n"
                "Ignora i saluti, i convenevoli temporanei o le domande generali.\n"
                "Rispondi RIGIDAMENTE in formato JSON con un array di oggetti contenenti 'categoria' e 'testo'.\n"
                "Esempio:\n"
                "[\n"
                "  {\"categoria\": \"preferenze\", \"testo\": \"Ama il gelato al cioccolato\"},\n"
                "  {\"categoria\": \"famiglia\", \"testo\": \"La moglie si chiama Sofia\"}\n"
                "]\n"
                "Se non ci sono nuove informazioni permanenti da memorizzare, rispondi semplicemente con: []\n"
                "NON inserire alcun testo prima o dopo il blocco JSON.\n"
                "<|im_end|>\n"
                "<|im_start|>user\n"
                f"Utente: \"{user_text}\"\n"
                f"MIA: \"{mia_response}\"\n"
                "<|im_end|>\n"
                "<|im_start|>assistant\n"
            )

            # Generate with low temperature to force precise JSON output
            res = model(
                prompt,
                max_tokens=250,
                stop=["<|im_end|>", "<|im_start|>"],
                temperature=0.01,
                repeat_penalty=1.1
            )

            raw_output = res["choices"][0]["text"].strip()
            if not raw_output:
                return True

            # Safely extract JSON if wrapped in markdown fences
            if "```" in raw_output:
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_output, re.DOTALL)
                if match:
                    raw_output = match.group(1).strip()

            # Parse array
            try:
                facts = json.loads(raw_output)
                if isinstance(facts, list):
                    for item in facts:
                        category = item.get("categoria", "preferenze").strip()
                        text = item.get("testo", "").strip()
                        if text:
                            # Save each permanent fact to LTM
                            self.memory.save_fact(speaker, category, text)
                    return True
            except Exception as json_err:
                print(f"[MemoryAgent Error] Failed to parse Qwen memory JSON: {json_err}. Output was:\n{raw_output}")
                
        except Exception as e:
            print(f"[MemoryAgent Error] Cognitive consolidation failed: {e}")
            traceback.print_exc()

        return False
