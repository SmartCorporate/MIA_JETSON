import os
import sys
import paramiko
from dotenv import load_dotenv

def run_remote_setup():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        script_path = f"{project_path}/scripts/setup_jetson_audio.sh"
        command = f"echo '{password}' | sudo -S bash {script_path}"
        
        print("Running setup script remotely with sudo...")
        # get_pty=True helps with some sudo implementations
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        
        # Print output in real-time
        for line in iter(stdout.readline, ""):
            print(line, end="")
            
        exit_status = stdout.channel.recv_exit_status()
        print(f"\nCommand finished with exit status: {exit_status}")
        
    except Exception as e:
        print(f"Failed to run script: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    run_remote_setup()
