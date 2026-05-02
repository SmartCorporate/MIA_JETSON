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

    # 1. Cleanup old junk and ensure directory
    print("Cleaning up and preparing directory...")
    ssh.exec_command('rm -f /home/mia/MIA_JETSON/models/llm/qwen2.5-7b-instruct-q4_k_m.gguf.tmp')
    ssh.exec_command('mkdir -p /home/mia/MIA_JETSON/models/llm')

    # 2. Download with CURL (better redirect handling)
    # Target: Qwen 2.5 7B Q4_K_M (Expected size: ~4.7GB)
    url = "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf?download=true"
    dest = "/home/mia/MIA_JETSON/models/llm/qwen2.5-7b-instruct-q4_k_m.gguf"
    
    print(f"Starting verified download of {dest}...")
    
    # Run download in a way that the user can see in the terminal
    download_cmd = (
        f"curl -L -o {dest}.tmp \"{url}\" && "
        f"mv {dest}.tmp {dest} && "
        "echo 'DOWNLOAD COMPLETE!'"
    )
    
    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    cmd = f"{display_prefix} nohup gnome-terminal --title='MIA - RECOVERY DOWNLOAD' -- bash -c '{download_cmd}; read' > /dev/null 2>&1 &"
    ssh.exec_command(cmd)

    print("Check the Jetson screen for the 'MIA - RECOVERY DOWNLOAD' window.")
    ssh.close()

if __name__ == "__main__":
    main()
