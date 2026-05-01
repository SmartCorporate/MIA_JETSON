import os
import paramiko
from dotenv import load_dotenv

def check_disk():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        stdin, stdout, stderr = ssh.exec_command("df -h /home")
        print(stdout.read().decode())
    finally:
        ssh.close()

if __name__ == "__main__":
    check_disk()
