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

    # 1. Kill old processes
    print("Cleaning up old processes...")
    ssh.exec_command('pkill -f internal_download.sh; pkill -f wget; pkill -f gnome-terminal')

    # 1b. Update and Restart Service (Remove Watchdog)
    print("Updating service (removing watchdog to stop restarts)...")
    sftp = ssh.open_sftp()
    sftp.put('mia_jetson.service', '/home/mia/MIA_JETSON/mia_jetson.service')
    sftp.close()
    
    commands = [
        f"echo {password} | sudo -S cp /home/mia/MIA_JETSON/mia_jetson.service /etc/systemd/system/mia_jetson.service",
        f"echo {password} | sudo -S systemctl daemon-reload",
        f"echo {password} | sudo -S systemctl restart mia_jetson"
    ]
    for cmd in commands:
        ssh.exec_command(cmd)
    
    print("Service updated and restarted.")
    stdin, stdout, stderr = ssh.exec_command('ls -lh /home/mia/MIA_JETSON/models/llm/')
    print('Current models folder content:')
    print(stdout.read().decode())

    # 3. Create v2 download script
    remote_script = """#!/bin/bash
mkdir -p /home/mia/MIA_JETSON/models/llm
cd /home/mia/MIA_JETSON/models/llm

echo "===================================================="
echo "      MIA JETSON - DOWNLOAD REPAIR & RESUME"
echo "===================================================="

# Download Qwen 2.5 7B
echo "Target 1: Qwen 2.5 7B Instruct (~4.7GB)"
# Bartowski mirror is more reliable for direct GGUF wget
URL_QWEN="https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"

echo "Downloading/Resuming Qwen..."
wget -c --show-progress --user-agent="Mozilla/5.0" "$URL_QWEN" -O qwen2.5-7b-instruct-q4_k_m.gguf

echo ""
echo "----------------------------------------------------"

# Download Phi-3.5 Mini
echo "Target 2: Phi-3.5 Mini Instruct (~2.4GB)"
URL_PHI="https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf"

echo "Downloading/Resuming Phi-3.5..."
wget -c --show-progress --user-agent="Mozilla/5.0" "$URL_PHI" -O phi-3.5-mini-instruct-q4_k_m.gguf

echo ""
echo "===================================================="
echo "DOWNLOADS FINISHED!"
echo "MIA e' pronta per caricare i nuovi modelli."
echo "===================================================="
read -p "Premi Invio per chiudere questa finestra..."
"""

    print("Uploading v2 download script to Jetson...")
    sftp = ssh.open_sftp()
    with sftp.file('/home/mia/MIA_JETSON/scripts/internal_download_v2.sh', 'w') as f:
        f.write(remote_script)
    sftp.close()
    
    ssh.exec_command('chmod +x /home/mia/MIA_JETSON/scripts/internal_download_v2.sh')

    # 4. Open TWO terminals on Jetson screen
    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    
    print("Opening background logs terminal on Jetson display...")
    cmd_logs = f"{display_prefix} nohup gnome-terminal --geometry=80x24+0+0 --title='MIA - BACKGROUND LOGS' -- bash -c 'tail -f /home/mia/MIA_JETSON/logs/mia.log' > /dev/null 2>&1 &"
    ssh.exec_command(cmd_logs)

    print("Opening download progress terminal on Jetson display...")
    cmd_dl = f"{display_prefix} nohup gnome-terminal --geometry=80x24+500+0 --title='MIA - DOWNLOAD PROGRESS' -- /home/mia/MIA_JETSON/scripts/internal_download_v2.sh > /dev/null 2>&1 &"
    ssh.exec_command(cmd_dl)

    print("Done. Two terminals should be visible on the Jetson screen.")
    ssh.close()

if __name__ == "__main__":
    main()
