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

    # Clean up any existing downloads to start fresh parallel downloads
    ssh.exec_command('pkill -f internal_download; pkill -f wget; pkill -f gnome-terminal')

    # Scripts for each model
    qwen_script = """#!/bin/bash
mkdir -p /home/mia/MIA_JETSON/models/llm
cd /home/mia/MIA_JETSON/models/llm
echo "Download Qwen 2.5 7B (~4.7GB)..."
wget -c --show-progress --user-agent="Mozilla/5.0" "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf" -O qwen2.5-7b-instruct-q4_k_m.gguf
echo "Qwen Download Finished!"
read -p "Premi Invio per chiudere..."
"""

    phi_script = """#!/bin/bash
mkdir -p /home/mia/MIA_JETSON/models/llm
cd /home/mia/MIA_JETSON/models/llm
echo "Download Phi-3.5 Mini (~2.4GB)..."
wget -c --show-progress --user-agent="Mozilla/5.0" "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf" -O phi-3.5-mini-instruct-q4_k_m.gguf
echo "Phi Download Finished!"
read -p "Premi Invio per chiudere..."
"""

    print("Uploading parallel download scripts...")
    sftp = ssh.open_sftp()
    with sftp.file('/home/mia/MIA_JETSON/scripts/download_qwen.sh', 'w') as f:
        f.write(qwen_script)
    with sftp.file('/home/mia/MIA_JETSON/scripts/download_phi.sh', 'w') as f:
        f.write(phi_script)
    sftp.close()
    
    ssh.exec_command('chmod +x /home/mia/MIA_JETSON/scripts/download_qwen.sh /home/mia/MIA_JETSON/scripts/download_phi.sh')

    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    
    print("Opening 3 terminals on Jetson screen...")
    # 1. Logs
    ssh.exec_command(f"{display_prefix} nohup gnome-terminal --geometry=80x20+0+0 --title='MIA - LOGS' -- bash -c 'echo {password} | sudo -S journalctl -u mia_jetson -f' > /dev/null 2>&1 &")
    
    # 2. Qwen Download
    ssh.exec_command(f"{display_prefix} nohup gnome-terminal --geometry=80x20+0+450 --title='DOWNLOAD QWEN (7B)' -- /home/mia/MIA_JETSON/scripts/download_qwen.sh > /dev/null 2>&1 &")
    
    # 3. Phi Download
    ssh.exec_command(f"{display_prefix} nohup gnome-terminal --geometry=80x20+700+450 --title='DOWNLOAD PHI (3.5)' -- /home/mia/MIA_JETSON/scripts/download_phi.sh > /dev/null 2>&1 &")

    print("Done. 3 windows should be visible now.")
    ssh.close()

if __name__ == "__main__":
    main()
