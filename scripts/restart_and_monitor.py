import paramiko
import os
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    host = '10.0.0.9'
    user = 'mia'
    password = 'MIA_JETSON'
    base = '/home/mia/MIA_JETSON'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)

    # 1. Restart Service
    print("Restarting MIA_JETSON service...")
    commands = [
        f"echo {password} | sudo -S systemctl restart mia_jetson"
    ]
    for cmd in commands:
        ssh.exec_command(cmd)

    # 2. Open Terminals on Jetson Display
    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    
    print("Opening monitoring terminals on Jetson display...")
    # Terminal 1: Live Logs
    cmd_logs = f"{display_prefix} nohup gnome-terminal --geometry=90x20+0+0 --title='MIA - LIVE LOGS' -- bash -c 'tail -f {base}/logs/mia.log' > /dev/null 2>&1 &"
    ssh.exec_command(cmd_logs)

    # Terminal 2: System Status
    cmd_status = f"{display_prefix} nohup gnome-terminal --geometry=90x20+0+500 --title='MIA - SYSTEM STATUS' -- bash -c 'python3 {base}/scripts/jetson_status_monitor.py' > /dev/null 2>&1 &"
    ssh.exec_command(cmd_status)

    print("Done. MIA is restarting with the new models.")
    ssh.close()

if __name__ == "__main__":
    main()
