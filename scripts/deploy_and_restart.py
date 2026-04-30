import os
import paramiko
from dotenv import load_dotenv
import subprocess
import sys

def deploy_and_restart():
    # 1. First run the normal deploy script
    print("Step 1: Deploying files to Jetson...")
    subprocess.run([sys.executable, "scripts/deploy_to_jetson.py"])
    
    # 2. Restart the process
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\nStep 2: Restarting MIA process on {host}...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # Kill existing process
        print("Stopping any running MIA processes...")
        ssh.exec_command("pkill -f 'python3 src/main.py'")
        
        # Start new process in background (using nohup)
        # We redirect output to a log file
        print("Starting MIA in background...")
        start_cmd = f"cd {project_path} && nohup python3 -u src/main.py > mia.log 2>&1 &"
        ssh.exec_command(start_cmd)
        
        print("\nMIA has been restarted. You can check logs with 'tail -f mia.log' on the Jetson.")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy_and_restart()
