import os
import sys
import paramiko
from dotenv import load_dotenv

def run_cmd():
    if len(sys.argv) < 2:
        print("Usage: python run_cmd_on_jetson.py \"command\"")
        return

    cmd = sys.argv[1]
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        print(f"Running: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(f"cd {project_path} && {cmd}")
        print(stdout.read().decode())
        print(stderr.read().decode())
    finally:
        ssh.close()

if __name__ == "__main__":
    run_cmd()
