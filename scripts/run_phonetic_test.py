import os
import paramiko
from dotenv import load_dotenv

def run_phonetic_test():
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
        sftp.put('scripts/test_phonetics.py', f'{project_path}/scripts/test_phonetics.py')
        sftp.close()
        
        stdin, stdout, stderr = ssh.exec_command(f"python3 {project_path}/scripts/test_phonetics.py")
        print(stdout.read().decode())
        
    finally:
        ssh.close()

if __name__ == "__main__":
    run_phonetic_test()
