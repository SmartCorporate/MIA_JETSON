import os
import time
import sys

def get_size(path):
    try:
        return os.path.getsize(path)
    except:
        return 0

def main():
    target_file = "/home/mia/MIA_JETSON/models/llm/QWEN_7B_SMART.gguf"
    total_size = 4683074240  # 4.4 GB in bytes
    
    while True:
        os.system('clear')
        current_size = get_size(target_file)
        
        if total_size > 0:
            pct = (current_size / total_size) * 100
        else:
            pct = 0
            
        mb_current = current_size / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        
        print("\n" * 5)
        print("    " + "=" * 50)
        print("    MIA JETSON - AGGIORNAMENTO CERVELLO")
        print("    " + "=" * 50)
        print(f"\n    FILE:    QWEN_7B_SMART.gguf")
        print(f"    STATO:   {pct:>.1f}% COMPLETATO")
        print(f"\n    SCARICATI: {mb_current:>.0f} MB / {mb_total:>.0f} MB")
        
        # Simple progress bar
        bar_len = 40
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\n    [{bar}]")
        
        print("\n    " + "=" * 50)
        print("    Rimani sintonizzato, MIA sta diventando più intelligente...")
        
        if pct >= 100:
            print("\n    DOWNLOAD COMPLETATO! RIAVVIO IN CORSO...")
            time.sleep(5)
            break
            
        time.sleep(2)

if __name__ == "__main__":
    main()
