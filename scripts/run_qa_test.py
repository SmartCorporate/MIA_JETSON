import os
import paramiko
from dotenv import load_dotenv

def run_qa_test():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # We need to set PYTHONPATH to include src
        cmd = f"cd {project_path} && export PYTHONPATH=$PYTHONPATH:$(pwd)/src && python3 scripts/test_qa_pipeline.py"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("--- Pipeline Test Results ---")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
    finally:
        ssh.close()

if __name__ == "__main__":
    run_qa_test()
