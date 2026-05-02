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

    # 1. CLEANUP
    ssh.exec_command('rm -f /home/mia/MIA_JETSON/models/llm/*7b*')
    ssh.exec_command('rm -rf /home/mia/MIA_JETSON/models/llm/.cache')
    ssh.exec_command('rm -f /home/mia/MIA_JETSON/logs/wget_final.log')

    # 2. DOWNLOAD
    url = "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf?download=true"
    dest = "/home/mia/MIA_JETSON/models/llm/QWEN_7B_SMART.gguf"
    
    # Using wget with background execution
    cmd = f'nohup wget --user-agent="Mozilla/5.0" -O {dest} "{url}" > /home/mia/MIA_JETSON/logs/wget_final.log 2>&1 &'
    
    print("Launching final background wget...")
    ssh.exec_command(cmd)
    
    import time
    time.sleep(5)
    
    print("--- WGET LOG OUTPUT ---")
    _, out, _ = ssh.exec_command('cat /home/mia/MIA_JETSON/logs/wget_final.log')
    print(out.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    main()
