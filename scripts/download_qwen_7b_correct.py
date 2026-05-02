import paramiko
import os
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    host = '10.0.0.9'
    user = 'mia'
    password = 'MIA_JETSON'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)

    dest = "/home/mia/MIA_JETSON/models/llm/qwen2.5-7b-instruct-q4_k_m.gguf"
    
    # Using a direct link from HuggingFace with wget and User-Agent
    # Qwen2.5-7B-Instruct-Q4_K_M.gguf is roughly 4.7GB
    url = "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    
    # -c for resume, --show-progress for terminal visibility
    wget_cmd = f"wget -c --user-agent='Mozilla/5.0' --show-progress -O {dest} {url}"
    
    print(f"Starting reliable download of Qwen 7B (4.7GB)...")
    
    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    cmd = f"{display_prefix} nohup gnome-terminal --geometry=100x25+100+100 --title='MIA - DOWNLOADING QWEN 7B (RECOVERY)' -- bash -c '{wget_cmd}; echo FINISHED; read' > /dev/null 2>&1 &"
    ssh.exec_command(cmd)

    ssh.close()

if __name__ == "__main__":
    main()
