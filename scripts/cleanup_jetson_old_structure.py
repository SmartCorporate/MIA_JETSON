import os
import paramiko
from dotenv import load_dotenv

def cleanup_remote():
    load_dotenv('.env')
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    project_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host} for cleanup...")
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        
        # Remove old top-level src subfolders that were moved to agents/ or storage/
        # AND remove any temporary build/download logs to start fresh
        dirs_to_remove = [
            f"{project_path}/src/audio",
            f"{project_path}/src/brain",
            f"{project_path}/src/vision",
            f"{project_path}/src/memory",
            f"{project_path}/src/src" # Just in case
        ]
        
        for d in dirs_to_remove:
            print(f"Cleaning up old directory: {d}")
            ssh.exec_command(f"rm -rf {d}")
            
        print("\nCleanup completed.")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    cleanup_remote()
