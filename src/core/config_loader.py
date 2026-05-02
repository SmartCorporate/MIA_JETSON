import os

def load_general_config():
    """Reads MIA_General.config from Desktop and returns a dictionary of values."""
    config = {
        "TONO": 3,
        "LUNGHEZZA": 2,
        "VELOCITA_VOCE": 3,
        "CREATIVITA": 3,
        "EMOZIONE": 3,
        "FORMALITA": 3,
        "CONCISIONE": 3,
        "INTELLIGENZA": 3,
        "VOCE_NATIVA": 5,
        "LOG_DETAIL": 3
    }
    
    # Try multiple paths for Desktop (English/Italian)
    paths = [
        "/home/mia/Desktop/MIA_General.config",
        "/home/mia/Scrivania/MIA_General.config",
        "MIA_General.config" # local fallback
    ]
    
    found_path = None
    for p in paths:
        if os.path.exists(p):
            found_path = p
            break
            
    if not found_path:
        return config

    try:
        with open(found_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    # Remove comments from the end of the value
                    val = val.split('#')[0].strip()
                    try:
                        config[key.strip()] = int(val)
                    except:
                        pass
    except Exception as e:
        print(f"[ConfigLoader] Error reading config: {e}")
        
    return config
