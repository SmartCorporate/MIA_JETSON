import os
import sys
import subprocess

try:
    import paramiko
    from dotenv import load_dotenv
except ImportError:
    print("Installing required packages (paramiko, python-dotenv)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "python-dotenv"])
    import paramiko
    from dotenv import load_dotenv

def sync_directory(sftp, local_dir, remote_dir):
    """Recursively upload a directory via SFTP."""
    for root, dirs, files in os.walk(local_dir):
        # Skip certain directories like __pycache__ or .git
        if '__pycache__' in root or '.git' in root:
            continue
            
        relative_path = os.path.relpath(root, local_dir)
        remote_path = os.path.join(remote_dir, relative_path).replace('\\', '/')
        
        # Create remote directory
        try:
            sftp.stat(remote_path)
        except IOError:
            print(f"Creating remote directory: {remote_path}")
            sftp.mkdir(remote_path)
            
        for file in files:
            # Skip python cache or specific files
            if file.endswith('.pyc') or file == '.env':
                continue
                
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace('\\', '/')
            print(f"Uploading: {local_file} -> {remote_file}")
            sftp.put(local_file, remote_file)

def main():
    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    host = os.getenv('JETSON_IP')
    user = os.getenv('JETSON_USER')
    password = os.getenv('JETSON_PASSWORD')
    remote_path = os.getenv('JETSON_PATH', '/home/mia/MIA_JETSON')
    
    if not all([host, user, password]):
        print("Error: Missing SSH configuration in .env file.")
        sys.exit(1)
        
    local_path = os.path.dirname(os.path.dirname(__file__))
    
    print(f"Connecting to {user}@{host}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname=host, username=user, password=password, timeout=10)
        print("Connected successfully!")
        
        # Execute command to create base directory if it doesn't exist
        print(f"Ensuring remote path exists: {remote_path}")
        ssh.exec_command(f"mkdir -p {remote_path}")
        
        sftp = ssh.open_sftp()
        print("Syncing files...")
        sync_directory(sftp, local_path, remote_path)
        
        sftp.close()
        print("\nDeployment completed successfully!")
        
        # Verify sync by listing files
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {remote_path}")
        print("\nRemote Directory Contents:")
        print(stdout.read().decode('utf-8'))
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
