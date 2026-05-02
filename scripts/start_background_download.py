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

    dest = "/home/mia/MIA_JETSON/models/llm/qwen2.5-7b-ita-v1.gguf"
    log = "/home/mia/MIA_JETSON/logs/download_7b.log"
    url = "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    
    # Run in background with nohup, redirecting output to a log file
    cmd = f"nohup curl -L -# -o {dest} {url} > {log} 2>&1 &"
    
    print(f"Starting background download to {dest}...")
    ssh.exec_command(cmd)
    
    # Wait 2 seconds and check if it's running
    import time
    time.sleep(2)
    _, out, _ = ssh.exec_command(f"ls -lh {dest}")
    print(f"File status: {out.read().decode().strip()}")
    
    ssh.close()

if __name__ == "__main__":
    main()
