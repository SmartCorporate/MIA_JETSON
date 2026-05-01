import os
import paramiko
from dotenv import load_dotenv

def open_progress_terminal():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} to open progress terminal...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # Command to open a terminal on the Jetson's display showing the log
        # DISPLAY=:0 is usually the local monitor
        cmd = f"DISPLAY=:0 gnome-terminal --title='MIA Installation Progress' -- bash -c 'tail -f {project_path}/install_llama.log; exec bash'"
        
        ssh.exec_command(cmd)
        print("\nSUCCESS: A terminal window should have opened on the Jetson screen showing the installation progress.")
        
    except Exception as e:
        print(f"Failed to open terminal: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    open_progress_terminal()
