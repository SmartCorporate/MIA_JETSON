import os
import paramiko
from dotenv import load_dotenv

def run_diagnostic():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        sftp = ssh.open_sftp()
        sftp.put('scripts/check_tts_engines.py', f'{project_path}/scripts/check_tts_engines.py')
        sftp.close()
        
        stdin, stdout, stderr = ssh.exec_command(f"python3 {project_path}/scripts/check_tts_engines.py")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
    finally:
        ssh.close()

if __name__ == "__main__":
    run_diagnostic()
