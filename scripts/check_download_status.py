import os
import paramiko
from dotenv import load_dotenv

def check_models():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {project_path}/models/llm")
        print(stdout.read().decode())
    finally:
        ssh.close()

if __name__ == "__main__":
    check_models()
