import os
import sys
from huggingface_hub import hf_hub_download

# Log file for Antigravity to read
LOG_FILE = "/home/mia/MIA_JETSON/logs/download_7b_python.log"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def download_model():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    # EXACT CAPS VERIFIED: Qwen2.5-7B-Instruct-Q4_K_M.gguf
    model_id = "bartowski/Qwen2.5-7B-Instruct-GGUF"
    filename = "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    local_dir = "/home/mia/MIA_JETSON/models/llm"
    
    log(f"--- INIZIO DOWNLOAD ---")
    log(f"Repo: {model_id}")
    log(f"File: {filename}")
    log(f"Dir:  {local_dir}")
    
    try:
        log("Connessione a HuggingFace in corso...")
        path = hf_hub_download(
            repo_id=model_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        log(f"SUCCESSO! Il file è pronto in: {path}")
    except Exception as e:
        log(f"ERRORE CRITICO: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
