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

    print("Opening live monitor on Jetson display...")
    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'
    
    # We use a simple tail -f of the log we are writing to
    cmd = f"{display_prefix} gnome-terminal --geometry=110x30+50+50 --title='MIA - DOWNLOAD STATUS (LIVE)' -- bash -c 'tail -f /home/mia/MIA_JETSON/logs/wget_final.log'"
    
    ssh.exec_command(cmd)
    ssh.close()

if __name__ == "__main__":
    main()
