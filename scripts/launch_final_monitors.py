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

    # 1. Kill old monitors
    ssh.exec_command('pkill -f "tail -f /home/mia/MIA_JETSON/logs/wget_final.log"')
    ssh.exec_command('pkill -f jetson_status_monitor.py')

    display_prefix = 'DISPLAY=:0 XAUTHORITY=/home/mia/.Xauthority'

    # 1. CLEAN DOWNLOAD MONITOR
    cmd1 = f"{display_prefix} gnome-terminal --geometry=80x20+20+20 --title='MIA - AGGIORNAMENTO CERVELLO' -- bash -c 'python3 /home/mia/MIA_JETSON/scripts/clean_download_monitor.py'"
    ssh.exec_command(cmd1)

    # 2. UPDATED SYSTEM STATUS
    cmd2 = f"{display_prefix} gnome-terminal --geometry=110x30+100+100 --title='MIA - SYSTEM STATUS' -- bash -c 'python3 /home/mia/MIA_JETSON/scripts/jetson_status_monitor.py'"
    ssh.exec_command(cmd2)

    ssh.close()

if __name__ == "__main__":
    main()
