import os
import sys
import paramiko
from dotenv import load_dotenv

def test_remote():
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
        
        # Install Python dependencies
        print("Installing Python requirements on Jetson (output hidden to avoid encoding errors)...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {project_path} && pip3 install -r requirements.txt")
        exit_status = stdout.channel.recv_exit_status()
        print(f"Pip install finished with status {exit_status}")
            
        # Run main.py unbuffered
        print("\nRunning MIA_JETSON remotely for testing...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {project_path} && python3 -u src/main.py")
        
        # We will read for a few seconds or until it crashes
        import time
        end_time = time.time() + 10  # Test for 10 seconds
        
        while time.time() < end_time:
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode('utf-8'), end="")
            if stderr.channel.recv_ready():
                print(f"[ERR] {stderr.channel.recv(1024).decode('utf-8')}", end="")
            
            if stdout.channel.exit_status_ready():
                print(f"\nProcess exited with status: {stdout.channel.recv_exit_status()}")
                break
            time.sleep(0.5)
            
        print("\nTest finished.")
        
        # Kill the process if it's still running (since it's an infinite loop)
        if not stdout.channel.exit_status_ready():
            print("Stopping remote MIA_JETSON process...")
            ssh.exec_command(f"pkill -f 'python3 src/main.py'")
            
    except Exception as e:
        print(f"Failed to test remotely: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    test_remote()
