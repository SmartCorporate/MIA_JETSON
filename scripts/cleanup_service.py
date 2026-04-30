import os
import paramiko
from dotenv import load_dotenv

def cleanup_and_start_service():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # 1. Kill everything related to MIA
        print("Cleaning up all existing MIA processes...")
        ssh.exec_command("pkill -f 'src/main.py'")
        
        # 2. Restart the systemd service
        print("Restarting the systemd service...")
        ssh.exec_command(f"echo '{password}' | sudo -S systemctl restart mia_jetson.service")
        
        print("\nCleanup complete. MIA is now running exclusively as a systemd service.")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    cleanup_and_start_service()
