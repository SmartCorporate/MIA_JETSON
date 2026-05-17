"""
MIA_JETSON - Test Memory Manager
Programmatic verification of STM sliding window, LTM profile persistence,
and auto-extraction tag parser.
"""
import os
import shutil
import time
import sys

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from storage.memory_manager import MemoryManager

def run_tests():
    print("=== STARTING MEMORY MANAGER UNIT TESTS ===")
    
    # Use a temporary testing memory folder
    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memories_test")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    mm = MemoryManager(data_dir=test_dir)
    
    speaker = "Michele"
    
    # ---------------------------------------------------------
    # TEST 1: Short-Term Memory Rolling & Pruning
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Short-Term Memory rolling history...")
    mm.add_interaction(speaker, "user", "Ciao MIA")
    mm.add_interaction(speaker, "assistant", "Ciao Michele!")
    
    history = mm.get_short_term_context(speaker)
    assert len(history) == 2, f"Expected 2 interactions, got {len(history)}"
    assert history[0]["text"] == "Ciao MIA"
    assert history[1]["text"] == "Ciao Michele!"
    print("[PASS] Rolling short-term memory registers turns correctly.")
    
    # ---------------------------------------------------------
    # TEST 2: STM Sliding Window Pruning (Backdating turns)
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing 60-minute pruning window...")
    # Add a backdated turn (65 minutes ago)
    old_time = time.time() - 3900
    mm.short_term_history[speaker.lower()].append({
        "role": "user",
        "text": "Questa è una vecchia frase di più di un'ora fa",
        "timestamp": old_time
    })
    
    # Trigger interaction to run prune
    mm.add_interaction(speaker, "user", "Che tempo fa oggi?")
    
    history2 = mm.get_short_term_context(speaker)
    # The 65 minute old turn should be pruned, leaving 3 items (2 from Test 1 + 1 new)
    assert len(history2) == 3, f"Pruning failed. Expected 3 turns, got {len(history2)}"
    # Check that old turn is indeed gone
    for turn in history2:
        assert turn["text"] != "Questa è una vecchia frase di più di un'ora fa", "Pruning failed. Old turn survived!"
    print("[PASS] Turns older than 60 minutes are successfully pruned automatically.")
    
    # ---------------------------------------------------------
    # TEST 3: LTM Profile JSON Serialization & Duplicate Prevention
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Long-Term Profile facts and duplicate prevention...")
    mm.save_fact(speaker, "preferenze", "Ama il caffè amaro al mattino")
    mm.save_fact(speaker, "preferenze", "Ama il caffè amaro al mattino") # Duplicate
    mm.save_fact(speaker, "famiglia", "Sua moglie si chiama Sofia")
    
    facts = mm.get_long_term_facts(speaker)
    assert len(facts) == 2, f"Expected 2 permanent facts, got {len(facts)}"
    assert facts[0]["text"] == "Ama il caffè amaro al mattino"
    assert facts[1]["text"] == "Sua moglie si chiama Sofia"
    print("[PASS] LTM facts serialized correctly and duplicates are automatically ignored.")
    
    # ---------------------------------------------------------
    # TEST 4: Auto-Extraction Tag Parser
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing [MEM: ...] Tag Extraction & Text Sanitization...")
    raw_response = "Perfetto Michele, me lo ricorderò! [MEM: preferenze | Gli piace viaggiare in treno]"
    
    cleaned = mm.parse_and_save_memory_tags(speaker, raw_response)
    
    # Verify tag was cleanly stripped
    assert cleaned == "Perfetto Michele, me lo ricorderò!", f"Text cleaning failed: '{cleaned}'"
    
    # Verify fact was saved to LTM
    facts2 = mm.get_long_term_facts(speaker)
    assert len(facts2) == 3, f"Expected 3 permanent facts, got {len(facts2)}"
    assert facts2[2]["text"] == "Gli piace viaggiare in treno"
    assert facts2[2]["category"] == "preferenze"
    print("[PASS] Dynamic [MEM: ...] tags are correctly saved and stripped from response text.")
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    print("\n=== ALL MEMORY MANAGER TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
