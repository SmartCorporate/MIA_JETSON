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

    # Shell script for Jetson
    remote_script = """#!/bin/bash
mkdir -p /home/mia/MIA_JETSON/models/llm
cd /home/mia/MIA_JETSON/models/llm

echo "==========================================="
echo "   MIA JETSON - DOWNLOAD MODELLI LLM"
echo "==========================================="

# Qwen 2.5 7B
if [ ! -f qwen2.5-7b-instruct-q4_k_m.gguf ]; then
    echo "Downloading Qwen 2.5 7B (~4.7GB)..."
    wget -c "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf" -O qwen2.5-7b-instruct-q4_k_m.gguf
else
    echo "Qwen 2.5 7B gia' presente."
fi

# Phi-3.5 Mini
if [ ! -f phi-3.5-mini-instruct-q4_k_m.gguf ]; then
    echo "Downloading Phi-3.5 Mini (~2.4GB)..."
    wget -c "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf" -O phi-3.5-mini-instruct-q4_k_m.gguf
else
    echo "Phi-3.5 Mini gia' presente."
fi

echo ""
echo "Tutti i download sono terminati!"
echo "MIA e' pronta per essere riavviata."
echo "==========================================="
read -p "Premi Invio per chiudere questa finestra..."
"""

    print("Uploading download script to Jetson...")
    sftp = ssh.open_sftp()
    with sftp.file('/home/mia/MIA_JETSON/scripts/internal_download.sh', 'w') as f:
        f.write(remote_script)
    sftp.close()
    
    ssh.exec_command('chmod +x /home/mia/MIA_JETSON/scripts/internal_download.sh')

    print("Opening terminal on Jetson display :0...")
    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    # Start gnome-terminal on the Jetson screen to show the download
    cmd = f"{display_prefix} nohup gnome-terminal --title='MIA DOWNLOAD PROGRESS' -- /home/mia/MIA_JETSON/scripts/internal_download.sh > /dev/null 2>&1 &"
    ssh.exec_command(cmd)

    print("Done. Check the Jetson screen.")
    ssh.close()

if __name__ == "__main__":
    main()
