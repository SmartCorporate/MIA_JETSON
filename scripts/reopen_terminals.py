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

    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'

    print("Re-opening Background Logs terminal...")
    cmd_logs = f"{display_prefix} nohup gnome-terminal --geometry=80x24+0+0 --title='MIA - BACKGROUND LOGS' -- bash -c 'echo {password} | sudo -S journalctl -u mia_jetson -f' > /dev/null 2>&1 &"
    ssh.exec_command(cmd_logs)

    # Check if download script is already running
    stdin, stdout, stderr = ssh.exec_command('pgrep -f internal_download_v2.sh')
    is_running = stdout.read().decode().strip()

    if is_running:
        print("Download is already running in background. Opening a terminal to watch progress...")
        # If it's already running, we just tail the output (if we had a log) 
        # but wget --show-progress outputs to stderr/terminal.
        # To make it simple, if it's running, we just let it be or kill and restart so user sees progress.
        # Let's kill and restart to ensure the UI is visible.
        ssh.exec_command('pkill -f internal_download_v2.sh; pkill -f wget')
        
    print("Opening Download Progress terminal...")
    cmd_dl = f"{display_prefix} nohup gnome-terminal --geometry=80x24+500+0 --title='MIA - DOWNLOAD PROGRESS' -- /home/mia/MIA_JETSON/scripts/internal_download_v2.sh > /dev/null 2>&1 &"
    ssh.exec_command(cmd_dl)

    print("Done. Terminals re-opened on Jetson screen.")
    ssh.close()

if __name__ == "__main__":
    main()
