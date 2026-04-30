import os
import paramiko
from dotenv import load_dotenv

def setup_service():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    remote_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} to setup systemd service...")
        ssh.connect(hostname=host, username=user, password=password, timeout=30)
        
        # 1. Upload service file
        print("Uploading mia_jetson.service...")
        sftp = ssh.open_sftp()
        sftp.put('mia_jetson.service', f'{remote_path}/mia_jetson.service')
        sftp.close()
        
        # 2. Install service
        print("Installing and enabling service...")
        # Move to /etc/systemd/system/
        install_cmd = (
            f"echo '{password}' | sudo -S cp {remote_path}/mia_jetson.service /etc/systemd/system/mia_jetson.service && "
            f"echo '{password}' | sudo -S systemctl daemon-reload && "
            f"echo '{password}' | sudo -S systemctl enable mia_jetson.service && "
            f"echo '{password}' | sudo -S systemctl restart mia_jetson.service"
        )
        
        stdin, stdout, stderr = ssh.exec_command(install_cmd)
        print(stdout.read().decode(errors='replace'))
        print(stderr.read().decode(errors='replace'))
        
        # 3. Check status
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active mia_jetson.service")
        status = stdout.read().decode().strip()
        print(f"\nService status: {status}")
        
        if status == "active":
            print("\nSUCCESS: MIA will now start automatically on power on.")
        else:
            print("\nWARNING: Service is not active. Check logs for details.")
            
    except Exception as e:
        print(f"Setup failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    setup_service()
