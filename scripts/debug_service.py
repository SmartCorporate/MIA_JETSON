import os
import paramiko
from dotenv import load_dotenv

def check_service_logs():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        print("--- Systemd Service Status ---")
        stdin, stdout, stderr = ssh.exec_command("systemctl status mia_jetson.service")
        print(stdout.read().decode(errors='ignore').encode('ascii', 'ignore').decode('ascii'))
        
        print("\n--- Recent Systemd Logs (journalctl) ---")
        stdin, stdout, stderr = ssh.exec_command("journalctl -u mia_jetson.service -n 50 --no-pager")
        print(stdout.read().decode(errors='ignore').encode('ascii', 'ignore').decode('ascii'))
        
    finally:
        ssh.close()

if __name__ == "__main__":
    check_service_logs()
