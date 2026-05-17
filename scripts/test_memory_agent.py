"""
MIA_JETSON - Test Memory Agent
Verifies background cognitive consolidator logic, regex JSON extraction,
and LTM profile updating.
"""
import os
import shutil
import sys
import unittest
from unittest.mock import MagicMock

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from storage.memory_manager import MemoryManager
from agents.brain.memory_agent import MemoryAgent

class TestMemoryAgent(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memories_test")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        self.mm = MemoryManager(data_dir=self.test_dir)
        self.mock_brain = MagicMock()
        self.mock_brain.is_ready = True
        self.mock_brain.models = {"qwen_smart": MagicMock()}
        
        self.agent = MemoryAgent(self.mm, self.mock_brain)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_cognitive_consolidation_success(self):
        print("\n[TEST] Running TestMemoryAgent: cognitive consolidation with clean JSON...")
        # Simulate Qwen returning clean JSON array containing facts
        simulated_json = """
        [
          {"categoria": "famiglia", "testo": "Il figlio si chiama Luca"},
          {"categoria": "hobby", "testo": "Ama fare passeggiate in montagna"}
        ]
        """
        
        model_mock = self.mock_brain.models["qwen_smart"]
        model_mock.return_value = {
            "choices": [{"text": simulated_json}]
        }
        
        speaker = "Michele"
        success = self.agent.consolidate_interaction(
            speaker=speaker,
            user_text="Adoro fare passeggiate in montagna con mio figlio Luca.",
            mia_response="Che bello camminare nel verde!"
        )
        
        self.assertTrue(success)
        
        # Verify facts were committed to permanent memory
        facts = self.mm.get_long_term_facts(speaker)
        self.assertEqual(len(facts), 2)
        self.assertEqual(facts[0]["text"], "Il figlio si chiama Luca")
        self.assertEqual(facts[0]["category"], "famiglia")
        self.assertEqual(facts[1]["text"], "Ama fare passeggiate in montagna")
        self.assertEqual(facts[1]["category"], "hobby")
        print("[PASS] Permanent facts extracted, parsed, and populated perfectly.")

    def test_regex_cleaning_with_markdown_fences(self):
        print("\n[TEST] Running TestMemoryAgent: parsing markdown code fences...")
        # Simulate Qwen returning JSON wrapped in markdown formatting fences
        simulated_wrapped = """
        Ecco cosa ho trovato da ricordare:
        ```json
        [
          {"categoria": "preferenze", "testo": "Adora il gelato al pistacchio"}
        ]
        ```
        Spero sia utile!
        """
        
        model_mock = self.mock_brain.models["qwen_smart"]
        model_mock.return_value = {
            "choices": [{"text": simulated_wrapped}]
        }
        
        speaker = "Michele"
        success = self.agent.consolidate_interaction(
            speaker=speaker,
            user_text="Mi piace tantissimo il gelato al pistacchio.",
            mia_response="Ottima scelta!"
        )
        
        self.assertTrue(success)
        
        facts = self.mm.get_long_term_facts(speaker)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["text"], "Adora il gelato al pistacchio")
        self.assertEqual(facts[0]["category"], "preferenze")
        print("[PASS] Regex clean-up strips markdown fences and comments cleanly.")

    def test_empty_memory_response(self):
        print("\n[TEST] Running TestMemoryAgent: empty response...")
        # Simulate Qwen returning empty list (no facts to remember)
        simulated_empty = "[]"
        
        model_mock = self.mock_brain.models["qwen_smart"]
        model_mock.return_value = {
            "choices": [{"text": simulated_empty}]
        }
        
        speaker = "Michele"
        success = self.agent.consolidate_interaction(
            speaker=speaker,
            user_text="Che ore sono?",
            mia_response="Sono le tre del pomeriggio."
        )
        
        self.assertTrue(success)
        facts = self.mm.get_long_term_facts(speaker)
        self.assertEqual(len(facts), 0)
        print("[PASS] Empty response parsed cleanly; no facts written.")

if __name__ == "__main__":
    unittest.main()
